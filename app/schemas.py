from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel
from pydantic import ConfigDict


# ------- Inputs -------
class LlantaIn(SQLModel):
    sku: str
    marca: str
    modelo: str
    medida: str
    precio_venta: float


class AjusteInventarioIn(SQLModel):
    delta: int
    umbral_minimo: int


class ClienteIn(SQLModel):
    nombre: str
    documento: str
    telefono: Optional[str] = None
    email: Optional[str] = None


class AsesorIn(SQLModel):
    nombre: str
    documento: str
    email: Optional[str] = None


class VentaItemIn(SQLModel):
    llanta_id: int
    cantidad: int


class VentaIn(SQLModel):
    cliente_id: int
    asesor_id: int
    items: List[VentaItemIn]


# ------- Reads -------
class LlantaRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sku: str
    marca: str
    modelo: str
    medida: str
    precio_venta: float
    activa: bool


class InventarioRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    llanta_id: int
    cantidad_disponible: int
    umbral_minimo: int


class ClienteRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    documento: str
    telefono: Optional[str] = None
    email: Optional[str] = None


class AsesorRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    documento: str
    email: Optional[str] = None


class VentaRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    fecha: datetime
    cliente_id: int
    asesor_id: int
    total: float


class DetalleVentaRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    venta_id: int
    llanta_id: int
    cantidad: int
    precio_unitario: float
    subtotal: float
