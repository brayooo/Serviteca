from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


class Llanta(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sku: str = Field(index=True, unique=True)
    marca: str
    modelo: str
    medida: str
    precio_venta: float
    activa: bool = True
    inventario: Optional["Inventario"] = Relationship(back_populates="llanta")


class Inventario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    llanta_id: int = Field(foreign_key="llanta.id", unique=True)
    cantidad_disponible: int
    umbral_minimo: int = 0
    llanta: Llanta = Relationship(back_populates="inventario")


class Cliente(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    documento: str = Field(index=True, unique=True)
    telefono: Optional[str] = None
    email: Optional[str] = None


class Asesor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    documento: str = Field(index=True, unique=True)
    email: Optional[str] = None


class Venta(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    fecha: datetime = Field(default_factory=datetime.utcnow)
    cliente_id: int = Field(foreign_key="cliente.id")
    asesor_id: int = Field(foreign_key="asesor.id")
    total: float = 0.0
    detalles: List["DetalleVenta"] = Relationship(back_populates="venta")


class DetalleVenta(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    venta_id: int = Field(foreign_key="venta.id")
    llanta_id: int = Field(foreign_key="llanta.id")
    cantidad: int
    precio_unitario: float
    subtotal: float
    venta: Venta = Relationship(back_populates="detalles")
