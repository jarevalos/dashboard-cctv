import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 1. Configuración de la página
st.set_page_config(page_title="Dashboard CCTV", page_icon="📹", layout="wide")
st.title("📊 Panel de Atenciones por Local")

# 2. Conexión segura a Google Sheets
@st.cache_data(ttl=600) # Actualiza los datos cada 10 minutos
def cargar_datos():
    # Leer las credenciales ocultas en Streamlit
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    skey = st.secrets["gcp_service_account"]
    credentials = Credentials.from_service_account_info(skey, scopes=scopes)
    gc = gspread.authorize(credentials)
    
    # Abrir la planilla por su ID y seleccionar la hoja BASE
    spreadsheet_id = '1fyZCiYawIQWrzD5WaTfNeWT5fYtRneozHQ8bg2KTDuk'
    sh = gc.open_by_key(spreadsheet_id)
    worksheet = sh.worksheet("BASE")
    
    # Transformar a tabla de Pandas
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

try:
    df = cargar_datos()
    
    # 3. Crear el Filtro Lateral
    st.sidebar.header("Filtros de Búsqueda")
    lista_locales = df['LOCAL'].unique()
    local_seleccionado = st.sidebar.selectbox("🏢 Selecciona un Local:", lista_locales)
    
    # 4. Filtrar datos
    datos_local = df[df['LOCAL'] == local_seleccionado]
    
    # 5. Tarjetas de Resumen
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total de Atenciones", value=len(datos_local))
    with col2:
        cerrados = len(datos_local[datos_local['ESTADO_SN'] == 'Cerrado'])
        st.metric(label="Reportes Cerrados", value=cerrados)
    with col3:
        abiertos = len(datos_local[datos_local['ESTADO_SN'] != 'Cerrado'])
        st.metric(label="Reportes Pendientes", value=abiertos)
    
    # 6. Tabla de Detalles
    st.divider()
    st.subheader(f"Detalle de incidencias para: {local_seleccionado}")
    st.dataframe(
        datos_local[['REPORTE', 'TIENDA', 'ESTADO_SN', 'PROVEDDOR', 'COMENTARIO']], 
        use_container_width=True,
        hide_index=True
    )
except Exception as e:
    st.error(f"Falta configurar las credenciales o hay un error de conexión: {e}")
