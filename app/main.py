from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
import os

# Importar tus módulos
from .database import get_session, init_db, test_connection
from .models import Llanta, Cliente, Asesor, Venta, Inventario, DetalleVenta
from .schemas import (
    LlantaIn, LlantaRead, ClienteIn, ClienteRead,
    AsesorIn, AsesorRead, VentaIn, VentaRead,
    AjusteInventarioIn, InventarioRead
)
from .services import crear_llanta_con_inventario, ajustar_inventario, crear_venta, StockError

app = FastAPI(
    title="🚗 Serviteca Llantas API",
    description="API para gestión de inventario y ventas de llantas",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    print("🚀 Iniciando Serviteca Llantas API...")

    if not test_connection():
        print("⚠️ Problema de conexión a BD, pero continuando...")

    if init_db():
        print("✅ Base de datos lista para usar")


# ========== ENDPOINTS BÁSICOS ==========

@app.get("/")
def read_root():
    return {
        "message": "🚗 API Serviteca Llantas",
        "version": "1.0.0",
        "database": "PostgreSQL",
        "endpoints": ["/llantas", "/clientes", "/asesores", "/ventas", "/inventario"]
    }


@app.get("/health")
def health_check(session: Session = Depends(get_session)):
    try:
        # Contar registros en tablas principales
        llantas_count = len(session.exec(select(Llanta)).all())
        clientes_count = len(session.exec(select(Cliente)).all())
        ventas_count = len(session.exec(select(Venta)).all())

        return {
            "status": "healthy",
            "database": "connected",
            "stats": {
                "llantas": llantas_count,
                "clientes": clientes_count,
                "ventas": ventas_count
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ========== ENDPOINTS DE LLANTAS ==========

@app.post("/llantas", response_model=LlantaRead)
def crear_llanta(llanta_data: LlantaIn, session: Session = Depends(get_session)):
    """Crear nueva llanta con inventario inicial en 0"""
    try:
        llanta = crear_llanta_con_inventario(
            session,
            sku=llanta_data.sku,
            marca=llanta_data.marca,
            modelo=llanta_data.modelo,
            medida=llanta_data.medida,
            precio_venta=llanta_data.precio_venta
        )
        return llanta
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/llantas", response_model=List[LlantaRead])
def listar_llantas(session: Session = Depends(get_session)):
    """Listar todas las llantas activas"""
    llantas = session.exec(select(Llanta).where(Llanta.activa == True)).all()
    return llantas


@app.get("/llantas/{llanta_id}", response_model=LlantaRead)
def obtener_llanta(llanta_id: int, session: Session = Depends(get_session)):
    llanta = session.get(Llanta, llanta_id)
    if not llanta:
        raise HTTPException(status_code=404, detail="Llanta no encontrada")
    return llanta


# ========== ENDPOINTS DE INVENTARIO ==========

@app.get("/inventario", response_model=List[dict])
def listar_inventario(session: Session = Depends(get_session)):
    """Listar inventario con información de llantas"""
    query = select(Inventario, Llanta).join(Llanta).where(Llanta.activa == True)
    results = session.exec(query).all()

    inventario = []
    for inv, llanta in results:
        inventario.append({
            "id": inv.id,
            "llanta_id": llanta.id,
            "sku": llanta.sku,
            "marca": llanta.marca,
            "modelo": llanta.modelo,
            "medida": llanta.medida,
            "precio_venta": llanta.precio_venta,
            "cantidad_disponible": inv.cantidad_disponible,
            "umbral_minimo": inv.umbral_minimo,
            "estado": "BAJO STOCK" if inv.cantidad_disponible <= inv.umbral_minimo else "OK"
        })
    return inventario


@app.put("/inventario/{llanta_id}/ajustar")
def ajustar_stock(
        llanta_id: int,
        ajuste: AjusteInventarioIn,
        session: Session = Depends(get_session)
):
    """Ajustar inventario de una llanta (positivo = entrada, negativo = salida)"""
    try:
        inventario = ajustar_inventario(
            session,
            llanta_id=llanta_id,
            delta=ajuste.delta,
            nuevo_umbral_minimo=ajuste.umbral_minimo
        )
        return {
            "message": f"Inventario ajustado en {ajuste.delta} unidades",
            "nueva_cantidad": inventario.cantidad_disponible,
            "umbral_minimo": inventario.umbral_minimo
        }
    except StockError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== ENDPOINTS DE CLIENTES ==========

@app.post("/clientes", response_model=ClienteRead)
def crear_cliente(cliente: ClienteIn, session: Session = Depends(get_session)):
    try:
        db_cliente = Cliente(**cliente.model_dump())
        session.add(db_cliente)
        session.commit()
        session.refresh(db_cliente)
        return db_cliente
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creando cliente: {str(e)}")


@app.get("/clientes", response_model=List[ClienteRead])
def listar_clientes(session: Session = Depends(get_session)):
    return session.exec(select(Cliente)).all()


# ========== ENDPOINTS DE ASESORES ==========

@app.post("/asesores", response_model=AsesorRead)
def crear_asesor(asesor: AsesorIn, session: Session = Depends(get_session)):
    try:
        db_asesor = Asesor(**asesor.model_dump())
        session.add(db_asesor)
        session.commit()
        session.refresh(db_asesor)
        return db_asesor
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creando asesor: {str(e)}")


@app.get("/asesores", response_model=List[AsesorRead])
def listar_asesores(session: Session = Depends(get_session)):
    return session.exec(select(Asesor)).all()


# ========== ENDPOINTS DE VENTAS ==========

@app.post("/ventas", response_model=dict)
def crear_nueva_venta(venta_data: VentaIn, session: Session = Depends(get_session)):
    """Crear nueva venta y actualizar inventario automáticamente"""
    try:
        items = [{"llanta_id": item.llanta_id, "cantidad": item.cantidad}
                 for item in venta_data.items]

        venta = crear_venta(
            session,
            cliente_id=venta_data.cliente_id,
            asesor_id=venta_data.asesor_id,
            items=items
        )

        return {
            "message": "Venta creada exitosamente",
            "venta_id": venta.id,
            "total": venta.total,
            "fecha": venta.fecha.isoformat(),
            "items_vendidos": len(items)
        }
    except StockError as e:
        raise HTTPException(status_code=400, detail=f"Error de stock: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando venta: {str(e)}")


@app.get("/ventas", response_model=List[dict])
def listar_ventas(limit: int = 50, session: Session = Depends(get_session)):
    """Listar ventas con información completa"""
    query = select(Venta, Cliente, Asesor).join(Cliente).join(Asesor).limit(limit)
    results = session.exec(query).all()

    ventas = []
    for venta, cliente, asesor in results:
        ventas.append({
            "id": venta.id,
            "fecha": venta.fecha.isoformat(),
            "total": venta.total,
            "cliente": cliente.nombre,
            "asesor": asesor.nombre
        })

    return sorted(ventas, key=lambda x: x["fecha"], reverse=True)


@app.get("/ventas/{venta_id}/detalle")
def obtener_detalle_venta(venta_id: int, session: Session = Depends(get_session)):
    """Obtener detalle completo de una venta"""
    venta = session.get(Venta, venta_id)
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")

    query = select(DetalleVenta, Llanta).join(Llanta).where(DetalleVenta.venta_id == venta_id)
    detalles = session.exec(query).all()

    items = []
    for detalle, llanta in detalles:
        items.append({
            "sku": llanta.sku,
            "marca": llanta.marca,
            "modelo": llanta.modelo,
            "medida": llanta.medida,
            "cantidad": detalle.cantidad,
            "precio_unitario": detalle.precio_unitario,
            "subtotal": detalle.subtotal
        })

    return {
        "venta_id": venta.id,
        "fecha": venta.fecha.isoformat(),
        "total": venta.total,
        "items": items
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)