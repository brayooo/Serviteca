# Serviteca — Gestión de inventario y venta de llantas

Sistema para gestionar **llantas, inventario, clientes, asesores y ventas.**
## Arquitectura

- **Backend**: FastAPI + SQLModel (SQLite)
  - Reglas de negocio en `services.py`
  - Esquemas (DTOs) en `schemas.py` 
  - Base de datos SQLite para persistencia
- **Frontend**: Streamlit
  - Interfaz de usuario que consume la API vía HTTP
---

## Funcionalidades 

### Gestión de Llantas
- Crear y consulta llantas

### Control de Inventario
- Ajuste de stock 
- Configuración de umbrales mínimos

### Ventas
- Verificación de stock disponible
- Descuento automático del inventario
- Cálculo de totales de venta

### Gestión de clientes y asesores
- Registro de clientes y asesores
- Vinculación con ventas

---

## 📁 Estructura del Proyecto

```
serviteca/
├─ app/
│  ├─ api.py              # FastAPI: endpoints y rutas
│  ├─ db.py               # Configuración de base de datos
│  ├─ models.py           # Modelos SQLModel (tablas)
│  ├─ schemas.py          # DTOs de entrada y salida
│  └─ services.py         # Lógica de negocio
├─ ui/
│  └─ streamlit_app.py    # Interfaz de usuario
├─ requirements.txt
└─ README.md
```

---

## 🔧 Requisitos del Sistema

- **Python 3.12**
- **pip** para instalación de dependencias
- Entorno virtual

---

## Instalación y Configuración

### 1. Clonar el Repositorio
```bash
git clone <url-del-repositorio>
cd serviteca
```

### 2. Crear y Activar Entorno Virtual
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Ejecutar el Backend
```bash
uvicorn app.api:app --reload --port 8001
```
- **URL del Backend**: http://127.0.0.1:8001

### 5. Ejecutar el Frontend
```bash
streamlit run ui/streamlit_app.py
```
- **URL del Frontend**: http://localhost:8501

---