from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from sqlmodel import Session, select

from .database import init_db, get_session
from .models import Llanta, Inventario, Cliente, Asesor, Venta, DetalleVenta
from .services import crear_llanta_con_inventario, ajustar_inventario, crear_venta, StockError
from .schemas import (
    LlantaIn, AjusteInventarioIn, ClienteIn, AsesorIn, VentaIn,
    LlantaRead, InventarioRead, ClienteRead, AsesorRead, VentaRead, DetalleVentaRead
)

app = FastAPI(title="SERVITECA API", version="1.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}

# ---------- LLANTAS ----------
@app.post("/llantas", response_model=LlantaRead)
def post_llanta(payload: LlantaIn, session: Session = Depends(get_session)):
    return crear_llanta_con_inventario(
        session,
        sku=payload.sku, marca=payload.marca, modelo=payload.modelo,
        medida=payload.medida, precio_venta=float(payload.precio_venta)
    )


@app.get("/llantas", response_model=List[LlantaRead])
def get_llantas(session: Session = Depends(get_session)):
    return session.exec(select(Llanta)).all()


# ---------- INVENTARIO ----------
@app.get("/inventario", response_model=List[InventarioRead])
def get_inventario(session: Session = Depends(get_session)):
    return session.exec(select(Inventario)).all()


@app.post("/inventario/{llanta_id}/ajustar", response_model=InventarioRead)
def post_ajustar_inventario(llanta_id: int, payload: AjusteInventarioIn, session: Session = Depends(get_session)):
    try:
        return ajustar_inventario(
            session,
            llanta_id=llanta_id,
            delta=int(payload.delta),
            nuevo_umbral_minimo=int(payload.umbral_minimo),
        )
    except StockError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------- CLIENTES ----------
@app.post("/clientes", response_model=ClienteRead)
def post_cliente(payload: ClienteIn, session: Session = Depends(get_session)):
    c = Cliente(**payload.model_dump())
    session.add(c)
    session.commit()
    session.refresh(c)
    return c


@app.get("/clientes", response_model=List[ClienteRead])
def get_clientes(session: Session = Depends(get_session)):
    return session.exec(select(Cliente)).all()


# ---------- ASESORES ----------
@app.post("/asesores", response_model=AsesorRead)
def post_asesor(payload: AsesorIn, session: Session = Depends(get_session)):
    a = Asesor(**payload.model_dump())
    session.add(a)
    session.commit()
    session.refresh(a)
    return a


@app.get("/asesores", response_model=List[AsesorRead])
def get_asesores(session: Session = Depends(get_session)):
    return session.exec(select(Asesor)).all()


# ---------- VENTAS ----------
@app.post("/ventas", response_model=VentaRead)
def post_venta(payload: VentaIn, session: Session = Depends(get_session)):
    try:
        items = [i.model_dump() for i in payload.items]
        return crear_venta(
            session,
            cliente_id=payload.cliente_id,
            asesor_id=payload.asesor_id,
            items=items,
        )
    except StockError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/ventas", response_model=List[VentaRead])
def get_ventas(session: Session = Depends(get_session)):
    return session.exec(select(Venta)).all()


@app.get("/ventas/{venta_id}/detalles", response_model=List[DetalleVentaRead])
def get_detalles_venta(venta_id: int, session: Session = Depends(get_session)):
    return session.exec(select(DetalleVenta).where(DetalleVenta.venta_id == venta_id)).all()
