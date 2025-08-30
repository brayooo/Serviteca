import os
import requests
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.environ.get("API_BASE", "http://127.0.0.1:8000")
API_TIMEOUT = float(os.environ.get("API_TIMEOUT", "30"))

st.set_page_config(page_title="Serviteca", page_icon="🟢", layout="wide")
st.title("Serviteca – Gestión de inventario y venta de llantas")


# --- Helpers ---
def rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()


def api_get(path: str, params=None):
    r = requests.get(f"{API_BASE}{path}", params=params, timeout=API_TIMEOUT)
    r.raise_for_status()
    return r.json()


def api_post(path: str, json=None, params=None):
    r = requests.post(f"{API_BASE}{path}", json=json, params=params, timeout=API_TIMEOUT)
    r.raise_for_status()
    return r.json()


# ------- Estado de la API -------
def ensure_api_up():
    try:
        r = requests.get(f"{API_BASE}/health", timeout=5)
        r.raise_for_status()
    except Exception as e:
        st.error(f"No logro conectarme a la API en **{API_BASE}**. "
                 f"¿Está encendida? Ejecuta: `uvicorn app.api:app --reload`.\n\nDetalle: {e}")
        st.stop()


# --------- Pages ---------
def page_dashboard():
    st.subheader("Dashboard")
    inv = pd.DataFrame(api_get("/inventario"))
    ventas = pd.DataFrame(api_get("/ventas"))

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Llantas diferentes", 0 if inv.empty else inv["llanta_id"].nunique())
    with c2:
        st.metric("Unidades en stock", 0 if inv.empty else int(inv["cantidad_disponible"].sum()))
    with c3:
        st.metric("Total ventas", f"${0:,.2f}" if ventas.empty else f"${float(ventas['total'].sum()):,.2f}")

    st.divider()


def page_llantas():
    st.subheader("Llantas")
    with st.form("form_ll"):
        sku = st.text_input("SKU")
        marca = st.text_input("Marca")
        modelo = st.text_input("Modelo")
        medida = st.text_input("Medida", value="205/55 R16")
        precio = st.number_input("Precio de venta", min_value=0.0, step=10.0, value=120.0)
        ok = st.form_submit_button("Crear llanta")
    if ok:
        if not sku or not marca or not modelo:
            st.warning("Completa SKU, Marca y Modelo.")
        else:
            try:
                api_post("/llantas", json={
                    "sku": sku, "marca": marca, "modelo": modelo, "medida": medida,
                    "precio_venta": precio
                })
                st.success("Llanta creada (stock inicial 0, umbral 0).")
                rerun()
            except requests.HTTPError as e:
                st.error(e.response.text)

    ll = pd.DataFrame(api_get("/llantas"))
    st.divider()
    st.dataframe(ll if not ll.empty else pd.DataFrame(), use_container_width=True)


def page_inventario():
    st.subheader("Inventario")

    inv = pd.DataFrame(api_get("/inventario"))
    llantas = pd.DataFrame(api_get("/llantas"))

    if llantas.empty:
        st.info("No hay llantas registradas.")
        return
    if inv.empty:
        st.warning("Aún no hay inventario registrado (se crea automáticamente al crear llantas).")

    llantas["label"] = llantas.apply(lambda r: f'[{r["id"]}] {r["sku"]} - {r["marca"]} {r["modelo"]}', axis=1)
    sel_label = st.selectbox("Llanta", options=llantas["label"].tolist())
    sel_id = int(sel_label.split("]")[0].strip("["))

    inv_row = None
    if not inv.empty:
        match = inv.loc[inv["llanta_id"] == sel_id]
        if not match.empty:
            inv_row = match.iloc[0]

    if inv_row is None:
        st.error("No existe registro de inventario para esta llanta.")
        return

    current_qty = int(inv_row["cantidad_disponible"])
    current_thr = int(inv_row["umbral_minimo"])

    st.markdown("### Editar inventario")
    new_qty = st.number_input(
        "Cantidad disponible",
        min_value=0,
        step=1,
        value=current_qty,
        key=f"qty_{sel_id}",
        help="Puedes sobrescribir la cantidad disponible. Calcularemos el delta automáticamente."
    )
    new_thr = st.number_input(
        "Umbral mínimo",
        min_value=0,
        step=1,
        value=current_thr,
        key=f"thr_{sel_id}",
        help="Si la cantidad disponible queda por debajo o igual a este umbral, se mostrará alerta."
    )

    if st.button("Guardar cambios"):
        delta = int(new_qty - current_qty)  # convertimos cantidad absoluta a delta
        try:
            api_post(f"/inventario/{sel_id}/ajustar",
                     json={"delta": delta, "umbral_minimo": int(new_thr)})
            st.success("Inventario actualizado.")
            rerun()
        except requests.HTTPError as e:
            try:
                st.error(e.response.json().get("detail", e.response.text))
            except Exception:
                st.error(str(e))

    st.divider()
    st.markdown("### Inventario completo")
    st.dataframe(inv if not inv.empty else pd.DataFrame(), use_container_width=True)


def page_personas():
    st.subheader("Clientes y Asesores")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Registrar cliente")
        with st.form("f_cli"):
            nombre = st.text_input("Nombre", key="c_nombre")
            doc = st.text_input("Documento", key="c_doc")
            tel = st.text_input("Teléfono", key="c_tel")
            email = st.text_input("Email", key="c_email")
            ok = st.form_submit_button("Crear cliente")
        if ok:
            try:
                api_post("/clientes", json={"nombre": nombre, "documento": doc, "telefono": tel, "email": email})
                st.success("Cliente creado.")
                rerun()
            except requests.HTTPError as e:
                st.error(e.response.text)
        st.markdown("#### Clientes")
        st.dataframe(pd.DataFrame(api_get("/clientes")), use_container_width=True)

    with col2:
        st.markdown("#### Registrar asesor")
        with st.form("f_ase"):
            nombre_a = st.text_input("Nombre", key="a_nombre")
            doc_a = st.text_input("Documento", key="a_doc")
            email_a = st.text_input("Email", key="a_email")
            ok2 = st.form_submit_button("Crear asesor")
        if ok2:
            try:
                api_post("/asesores", json={"nombre": nombre_a, "documento": doc_a, "email": email_a})
                st.success("Asesor creado.")
                rerun()
            except requests.HTTPError as e:
                st.error(e.response.text)
        st.markdown("#### Asesores")
        st.dataframe(pd.DataFrame(api_get("/asesores")), use_container_width=True)


def page_ventas():
    st.subheader("Registrar venta")

    clientes = pd.DataFrame(api_get("/clientes"))
    asesores = pd.DataFrame(api_get("/asesores"))
    llantas = pd.DataFrame(api_get("/llantas"))
    inventario = pd.DataFrame(api_get("/inventario"))

    if clientes.empty or asesores.empty or llantas.empty:
        st.info("Necesitas al menos 1 cliente, 1 asesor y 1 llanta.")
        return

    cli_map = {f'{r["nombre"]} ({r["documento"]})': int(r["id"]) for _, r in clientes.iterrows()}
    ase_map = {f'{r["nombre"]} ({r["documento"]})': int(r["id"]) for _, r in asesores.iterrows()}
    stock_map = {int(r["llanta_id"]): int(r["cantidad_disponible"]) for _, r in inventario.iterrows()}

    def ll_label(row):
        sid = int(row["id"])
        stock = stock_map.get(sid, 0)
        return f'[{sid}] {row["sku"]} - {row["marca"]} {row["modelo"]} | ${row["precio_venta"]} | stock={stock}'

    llantas["label"] = llantas.apply(ll_label, axis=1)
    lmap = {row["label"]: int(row["id"]) for _, row in llantas.iterrows()}

    with st.form("f_venta"):
        c_sel = st.selectbox("Cliente", options=list(cli_map.keys()))
        a_sel = st.selectbox("Asesor", options=list(ase_map.keys()))
        st.markdown("**Ítems**")
        items = []
        for i in range(1, 4):
            s = st.selectbox(f"Llanta {i}", options=["(ninguno)"] + list(lmap.keys()), key=f"ll{i}")
            q = st.number_input(f"Cantidad {i}", min_value=0, step=1, value=0, key=f"q{i}")
            if s != "(ninguno)" and q > 0:
                items.append({"llanta_id": lmap[s], "cantidad": int(q)})
        ok = st.form_submit_button("Confirmar venta")

    if ok:
        if not items:
            st.warning("Agrega al menos un ítem con cantidad > 0.")
        else:
            try:
                res = api_post("/ventas", json={
                    "cliente_id": cli_map[c_sel],
                    "asesor_id": ase_map[a_sel],
                    "items": items
                })
                st.success(f'Venta #{res["id"]} creada. Total: ${res["total"]}')
                rerun()
            except requests.HTTPError as e:
                try:
                    st.error(e.response.json().get("detail", e.response.text))
                except Exception:
                    st.error(str(e))

    st.divider()
    st.markdown("### Ventas registradas")

    ventas = pd.DataFrame(api_get("/ventas"))
    if ventas.empty:
        st.info("No hay ventas registradas aún.")
        return
    cli_name = {int(r["id"]): f'{r["nombre"]} ({r["documento"]})' for _, r in clientes.iterrows()}
    ase_name = {int(r["id"]): f'{r["nombre"]} ({r["documento"]})' for _, r in asesores.iterrows()}

    ventas_disp = ventas.copy()
    ventas_disp["Fecha (UTC)"] = pd.to_datetime(ventas_disp["fecha"]).dt.strftime("%Y-%m-%d %H:%M")
    ventas_disp["Cliente"] = ventas_disp["cliente_id"].map(cli_name).fillna(ventas_disp["cliente_id"].astype(str))
    ventas_disp["Asesor"] = ventas_disp["asesor_id"].map(ase_name).fillna(ventas_disp["asesor_id"].astype(str))
    ventas_disp = ventas_disp.rename(columns={"id": "ID", "total": "Total"})
    ventas_disp = ventas_disp[["ID", "Fecha (UTC)", "Cliente", "Asesor", "Total"]]

    st.dataframe(ventas_disp, use_container_width=True)

    v_id = st.selectbox("Ver detalles de venta", options=ventas_disp["ID"].tolist())
    detalles = pd.DataFrame(api_get(f"/ventas/{v_id}/detalles"))
    if detalles.empty:
        st.info("La venta no tiene detalles.")
        return

    ll_map_by_id = {int(r["id"]): f'{r["sku"]} - {r["marca"]} {r["modelo"]}' for _, r in llantas.iterrows()}
    detalles_disp = detalles.copy()
    detalles_disp["Llanta"] = detalles_disp["llanta_id"].map(ll_map_by_id).fillna(
        detalles_disp["llanta_id"].astype(str))
    detalles_disp = detalles_disp.rename(columns={
        "cantidad": "Cantidad",
        "precio_unitario": "Precio unitario",
        "subtotal": "Subtotal"
    })
    detalles_disp = detalles_disp[["Llanta", "Cantidad", "Precio unitario", "Subtotal"]]

    st.dataframe(detalles_disp, use_container_width=True)


# --------- Router ---------
ensure_api_up()

page = st.sidebar.radio("Navegación", ["Dashboard", "Llantas", "Inventario", "Clientes/Asesores", "Ventas"], index=0)
if page == "Dashboard":
    page_dashboard()
elif page == "Llantas":
    page_llantas()
elif page == "Inventario":
    page_inventario()
elif page == "Clientes/Asesores":
    page_personas()
elif page == "Ventas":
    page_ventas()
