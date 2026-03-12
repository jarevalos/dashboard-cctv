import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
from datetime import datetime

# 1. Configuración de la página
st.set_page_config(page_title="Dashboard CCTV", page_icon="📹", layout="wide")

# ==========================================
# CSS DISEÑO ULTRA COMPACTO PROFESIONAL
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FB !important; }
    .block-container { padding-top: 0rem !important; padding-bottom: 0rem !important; max-width: 98% !important; }
    
    .card-container {
        background-color: white;
        padding: 8px 5px;
        border-radius: 8px;
        border-bottom: 3px solid #E0E4E8;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        text-align: center;
        margin-bottom: 5px;
    }
    .card-label { margin: 0; font-size: 0.6rem !important; color: #7F8C8D; font-weight: 700; text-transform: uppercase; }
    .card-value { margin: 0; font-size: 1.4rem !important; color: #2C3E50; font-weight: 800; line-height: 1; }

    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=60)
def cargar_datos():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    skey = st.secrets["gcp_service_account"]
    credentials = Credentials.from_service_account_info(skey, scopes=scopes)
    gc = gspread.authorize(credentials)
    
    spreadsheet_id = '1fyZCiYawIQWrzD5WaTfNeWT5fYtRneozHQ8bg2KTDuk'
    sh = gc.open_by_key(spreadsheet_id)
    worksheet = sh.worksheet("BASE")
    
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)

    # --- FILTRO MAESTRO (REGLAS KOKE) ---
    # Convertimos a string y mayúsculas de forma segura elemento por elemento
    col_n = 'ESTADO_SN'
    col_o = 'ESTADO_ATENCION'

    if col_n in df.columns and col_o in df.columns:
        # 1. Filtro Columna N: Solo Abiertos
        estados_validos = ['ASIGNADO', 'EN PROGRESO', 'EN ESPERA']
        mask_n = df[col_n].astype(str).str.upper().str.strip().isin(estados_validos)
        
        # 2. Filtro Columna O: Excluir Duplicados y Otro Servicio
        excluir_o = ['DUPLICADO', 'OTRO SERVICIO']
        mask_o = ~df[col_o].astype(str).str.upper().str.strip().isin(excluir_o)
        
        df = df[mask_n & mask_o].copy()

    return df

def crear_tarjeta_pro(titulo, valor, color_top):
    html = f"""
    <div class="card-container" style="border-top: 3px solid {color_top};">
        <p class="card-label">{titulo}</p>
        <h2 class="card-value">{valor}</h2>
    </div>
    """
    return html

try:
    df = cargar_datos()
    
    tab1, tab2 = st.tabs(["📊 Vista Ejecutiva", "🏢 Detalle por Local"])
    
    with tab1:
        # --- CÁLCULO DE KPIs ---
        t_total_abiertos = len(df)
        
        # Filtros por GRUPO_ASIGNADO (Columna U)
        col_u = 'GRUPO_ASIGNADO'
        if col_u in df.columns:
            df[col_u] = df[col_u].astype(str).str.strip()
            t_cctv = len(df[df[col_u] == 'Soporte Circuito Cerrado de Televisin (CCTV)'])
            t_dcero = len(df[df[col_u] == 'Soporte Dcero'])
            t_secomp = len(df[df[col_u] == 'Soporte Secomp'])
            t_en_ejecucion = t_dcero + t_secomp
        else:
            t_cctv = t_dcero = t_secomp = t_en_ejecucion = 0
        
        # Pendientes (Columna S: PROVEDDOR vacía)
        col_s = 'PROVEDDOR'
        if col_s in df.columns:
            t_pendientes = len(df[df[col_s].astype(str).str.strip().isin(['', 'nan', 'None'])])
        else:
            t_pendientes = 0

        # --- FILA DE TARJETAS ---
        kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
        with kpi1: st.markdown(crear_tarjeta_pro("Casos Abiertos", t_total_abiertos, "#E74C3C"), unsafe_allow_html=True) 
        with kpi2: st.markdown(crear_tarjeta_pro("Soporte CCTV", t_cctv, "#2980B9"), unsafe_allow_html=True) 
        with kpi3: st.markdown(crear_tarjeta_pro("Soporte Dcero", t_dcero, "#3498DB"), unsafe_allow_html=True) 
        with kpi4: st.markdown(crear_tarjeta_pro("Soporte Secomp", t_secomp, "#5DADE2"), unsafe_allow_html=True) 
        with kpi5: st.markdown(crear_tarjeta_pro("En Ejecución", t_en_ejecucion, "#F39C12"), unsafe_allow_html=True)
        with kpi6: st.markdown(crear_tarjeta_pro("Pendientes", t_pendientes, "#34495E"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ==========================================
        # GRÁFICO 1: ANTIGÜEDAD DEL REPORTE (COLUMNA J)
        # ==========================================
        # CAMBIA 'FECHA_REPORTE' por el nombre real de tu columna J
        col_j = 'FECHA_REPORTE' 
        
        if col_j in df.columns:
            # Convertir a fecha real
            df['FECHA_DT'] = pd.to_datetime(df[col_j], dayfirst=True, errors='coerce')
            
            # Quitar errores de fecha si los hay
            df_fechas = df.dropna(subset=['FECHA_DT']).copy()
            
            # Calcular días
            hoy = datetime.now()
            df_fechas['Dias'] = (hoy - df_fechas['FECHA_DT']).dt.days
            
            # Agrupar y ordenar
            ant_df = df_fechas['Dias'].value_counts().reset_index()
            ant_df.columns = ['Días', 'Cantidad']
            ant_df = ant_df.sort_values('Días')

            fig = px.bar(
                ant_df, x='Días', y='Cantidad', 
                title="<b>Antigüedad de Reportes (Días)</b>",
                text_auto=True,
                color_discrete_sequence=['#2980B9']
            )
            
            fig.update_layout(
                paper_bgcolor='white', plot_bgcolor='white',
                height=300, margin=dict(l=10, r=10, t=40, b=10),
                xaxis_title="Días de atraso", yaxis_title="N° Casos"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"Columna '{col_j}' no detectada. Verifica el encabezado de la columna J.")

    with tab2:
        st.header("Análisis por Local")
        if 'LOCAL' in df.columns:
            lista_locales = sorted(df['LOCAL'].unique())
            local_sel = st.selectbox("🏢 Selecciona un Local:", lista_locales)
            res = df[df['LOCAL'] == local_sel]
            st.dataframe(res[['REPORTE', 'ESTADO_SN', 'PROVEDDOR', 'COMENTARIO']], use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error en la aplicación: {e}")
