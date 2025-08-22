from typing import List, Dict
from sqlmodel import Session, select
from .models import Llanta, Inventario, Venta, DetalleVenta


class StockError(Exception):
    pass


def crear_llanta_con_inventario(session: Session, *, sku: str, marca: str, modelo: str,
                                medida: str, precio_venta: float) -> Llanta:
    llanta = Llanta(sku=sku, marca=marca, modelo=modelo, medida=medida,
                    precio_venta=precio_venta, activa=True)
    session.add(llanta)
    session.flush()  # para obtener id
    inv = Inventario(llanta_id=llanta.id, cantidad_disponible=0, umbral_minimo=0)
    session.add(inv)
    session.commit()
    session.refresh(llanta)
    return llanta


def ajustar_inventario(session: Session, *, llanta_id: int, delta: int, nuevo_umbral_minimo: int):
    inv = session.exec(select(Inventario).where(Inventario.llanta_id == llanta_id)).one()
    nuevo_stock = inv.cantidad_disponible + delta
    if nuevo_stock < 0:
        raise StockError("No se puede dejar inventario negativo")
    inv.cantidad_disponible = nuevo_stock
    inv.umbral_minimo = int(nuevo_umbral_minimo)
    session.add(inv)
    session.commit()
    return inv


def crear_venta(session: Session, *, cliente_id: int, asesor_id: int,
                items: List[Dict[str, int]]) -> Venta:
    ids = [i["llanta_id"] for i in items]
    llantas = {l.id: l for l in session.exec(select(Llanta).where(Llanta.id.in_(ids))).all()}
    inventarios = {inv.llanta_id: inv for inv in
                   session.exec(select(Inventario).where(Inventario.llanta_id.in_(ids))).all()}

    for it in items:
        llanta_id, qty = it["llanta_id"], it["cantidad"]
        if llanta_id not in inventarios:
            raise StockError(f"No hay inventario registrado para la llanta {llanta_id}.")
        if inventarios[llanta_id].cantidad_disponible < qty:
            sku = llantas[llanta_id].sku if llanta_id in llantas else llanta_id
            raise StockError(f"Stock insuficiente para LLANTA {sku}")

    venta = Venta(cliente_id=cliente_id, asesor_id=asesor_id, total=0.0)
    session.add(venta)
    session.flush()

    total = 0.0
    for it in items:
        l = llantas[it["llanta_id"]]
        qty = it["cantidad"]
        precio = l.precio_venta
        subtotal = precio * qty
        det = DetalleVenta(venta_id=venta.id, llanta_id=l.id, cantidad=qty,
                           precio_unitario=precio, subtotal=subtotal)
        session.add(det)
        total += subtotal

        inv = inventarios[l.id]
        inv.cantidad_disponible -= qty
        session.add(inv)

    venta.total = total
    session.add(venta)
    session.commit()
    session.refresh(venta)
    return venta
