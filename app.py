import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 1. Configuración de la página (Layout wide para aprovechar todo el ancho)
st.set_page_config(page_title="Dashboard CCTV", page_icon="📹", layout="wide")

# ==========================================
# CSS ULTRA COMPACTO: MÁXIMO APROVECHAMIENTO
# ==========================================
st.markdown("""
    <style>
    /* Fondo gris claro corporativo */
    .stApp { background-color: #F0F2F6 !important; }
    
    /* Subir todo el contenido al tope eliminando paddings */
    .block-container { 
        padding-top: 0rem !important; 
        padding-bottom: 0rem !important; 
        max-width: 98% !important; 
    }
    
    /* Estilo para etiquetas de tarjetas (Pequeñas y discretas) */
    .card-label {
        margin: 0; 
        font-size: 0.65rem !important; 
        color: #666666; 
        font-weight: 700; 
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }
    
    /* Estilo para los números grandes */
    .card-value {
        margin: 0; 
        font-size: 1.7rem !important; 
        color: #1E2433; 
        font-weight: 800;
        line-height: 1;
        padding-top: 2px;
    }

    /* Ocultar elementos nativos de Streamlit */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Pegar las pestañas arriba */
    .stTabs { margin-top: 0px !important; }
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

    # --- FILTRO MAESTRO GLOBAL ---
    col_estado = 'ESTADO_SN'          
    col_atencion = 'ESTADO_ATENCION'  

    if col_estado in df.columns:
        df[col_estado] = df[col_estado].astype(str).str.strip() 
        estados_excluidos = ['CERRADO', 'CERRADO COMPLETO', 'RESUELTO', 'CERRADO INCOMPLETO', 'REVISAR']
        df = df[~df[col_estado].str.upper().isin(estados_excluidos)]
    
    if col_atencion in df.columns:
        df[col_atencion] = df[col_atencion].astype(str).str.strip()
        df = df[df[col_atencion].str.upper() != 'OTRO SERVICIO']

    return df

def crear_tarjeta(titulo, valor, color_acento):
    html = f"""
    <div style="background-color: white; padding: 8px 5px; border-radius: 6px; border-top: 3px solid {color_acento}; box-shadow: 0 1px 2px rgba(0,0,0,0.05); text-align: center; border-left: 1px solid #eee; border-right: 1px solid #eee; border-bottom: 1px solid #eee;">
        <p class="card-label">{titulo}</p>
        <h2 class="card-value">{valor}</h2>
    </div>
    """
    return html

try:
    df = cargar_datos()
    
    # Pestañas directo al inicio
    tab1, tab2 = st.tabs(["📊 Panel General", "🏢 Análisis por Local"])
    
    with tab1:
        df_mostrar = df.copy()

        # --- LÓGICA DE DATOS ---
        if 'ESTADO_SN' in df_mostrar.columns:
            estados_backlog = ['ASIGNADO', 'EN ESPERA', 'EN PROGRESO']
            filtro_gestion = df_mostrar['ESTADO_SN'].str.upper().isin(estados_backlog)
            t_total_abiertos = len(df_mostrar[filtro_gestion])
        else:
            filtro_gestion = pd.Series(False, index=df_mostrar.index)
            t_total_abiertos = 0

        if 'GRUPO_ASIGNADO' in df_mostrar.columns:
            df_mostrar['GRUPO_ASIGNADO'] = df_mostrar['GRUPO_ASIGNADO'].astype(str).str.strip()
            g_cctv = 'Soporte Circuito Cerrado de Televisin (CCTV)'
            g_dcero = 'Soporte Dcero'
            g_secomp = 'Soporte Secomp'
            
            t_cctv = len(df_mostrar[filtro_gestion & (df_mostrar['GRUPO_ASIGNADO'] == g_cctv)])
            t_dcero = len(df_mostrar[filtro_gestion & (df_mostrar['GRUPO_ASIGNADO'] == g_dcero)])
            t_secomp = len(df_mostrar[filtro_gestion & (df_mostrar['GRUPO_ASIGNADO'] == g_secomp)])
            t_en_ejecucion = t_dcero + t_secomp
        else:
            t_cctv = t_dcero = t_secomp = t_en_ejecucion = 0

        if 'PROVEDDOR' in df_mostrar.columns:
            filtro_prov_vacio = df_mostrar['PROVEDDOR'].astype(str).str.strip().isin(['', 'nan', 'None'])
            t_pendientes = len(df_mostrar[filtro_gestion & filtro_prov_vacio])
        else:
            t_pendientes = 0

        # --- FILA DE TARJETAS (Ahora más pegadas al borde superior) ---
        kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
        with kpi1: st.markdown(crear_tarjeta("Casos Abiertos", t_total_abiertos, "#D92B38"), unsafe_allow_html=True) 
        with kpi2: st.markdown(crear_tarjeta("CCTV", t_cctv, "#1F4E79"), unsafe_allow_html=True) 
        with kpi3: st.markdown(crear_tarjeta("DCERO", t_dcero, "#4DA6FF"), unsafe_allow_html=True) 
        with kpi4: st.markdown(crear_tarjeta("SECOMP", t_secomp, "#4DA6FF"), unsafe_allow_html=True) 
        with kpi5: st.markdown(crear_tarjeta("En ejecución", t_en_ejecucion, "#D92B38"), unsafe_allow_html=True)
        with kpi6: st.markdown(crear_tarjeta("PENDIENTES", t_pendientes, "#1E2433"), unsafe_allow_html=True)

    with tab2:
        st.header("Análisis por Local")
        if 'LOCAL' in df.columns:
            lista_locales = df['LOCAL'].unique()
            local_seleccionado = st.selectbox("🏢 Selecciona un Local:", lista_locales)
            datos_local = df[df['LOCAL'] == local_seleccionado]
            columnas_mostrar = [c for c in ['REPORTE', 'TIENDA', 'ESTADO_SN', 'PROVEDDOR', 'COMENTARIO'] if c in df.columns]
            st.dataframe(datos_local[columnas_mostrar], use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error cargando la aplicación: {e}")
