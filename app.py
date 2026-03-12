import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px

# 1. Configuración de la página
st.set_page_config(page_title="CCTV Control Center", page_icon="📹", layout="wide")

# ==========================================
# CSS ESTILO DASHPRO (GLASSMORPHISM)
# ==========================================
st.markdown("""
    <style>
    /* Fondo con degradado sutil */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
    }
    
    /* Barra lateral estilizada */
    section[data-testid="stSidebar"] {
        background-color: #1E2433 !important;
        border-right: 1px solid #34495E;
    }
    section[data-testid="stSidebar"] .stMarkdown h2, section[data-testid="stSidebar"] .stMarkdown p {
        color: white !important;
    }

    /* Contenedores Blancos con Sombra (Cards) */
    .css-card {
        background: rgba(255, 255, 255, 0.9);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
        border: 1px solid rgba(255, 255, 255, 0.18);
        margin-bottom: 20px;
    }

    /* Títulos y Etiquetas */
    .kpi-label { color: #657786; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }
    .kpi-value { color: #14171A; font-size: 1.8rem; font-weight: 800; line-height: 1; }

    /* Ocultar elementos nativos */
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

    # --- FILTRO MAESTRO ---
    col_n = 'ESTADO_SN'
    col_o = 'ESTADO_ATENCION'

    if col_n in df.columns and col_o in df.columns:
        estados_validos = ['ASIGNADO', 'EN PROGRESO', 'EN ESPERA']
        mask_n = df[col_n].astype(str).str.upper().str.strip().isin(estados_validos)
        excluir_o = ['DUPLICADO', 'OTRO SERVICIO']
        mask_o = ~df[col_o].astype(str).str.upper().str.strip().isin(excluir_o)
        df = df[mask_n & mask_o].copy()

    return df

def crear_kpi_pro(titulo, valor, color_top):
    return f"""
    <div style="background: white; padding: 15px; border-radius: 12px; border-top: 5px solid {color_top}; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
        <p class="kpi-label">{titulo}</p>
        <h2 class="kpi-value">{valor}</h2>
    </div>
    """

try:
    df = cargar_datos()

    # --- BARRA LATERAL (SIDEBAR) ---
    with st.sidebar:
        st.markdown("<h2 style='text-align: center;'>📹 DashPro CCTV</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 0.8rem;'>Centro de Control Nacional</p>", unsafe_allow_html=True)
        st.divider()
        st.markdown("### Filtros Rápidos")
        tiendas = sorted(df['LOCAL'].unique()) if 'LOCAL' in df.columns else []
        local_sel = st.multiselect("Seleccionar Locales", tiendas)
        
        st.divider()
        st.info("Datos actualizados automáticamente desde Google Sheets.")

    # Filtrar DF si hay selección
    if local_sel:
        df = df[df['LOCAL'].isin(local_sel)]

    # --- CONTENIDO PRINCIPAL ---
    # Fila de KPIs
    t_total = len(df)
    col_u = 'GRUPO_ASIGNADO'
    col_s = 'PROVEDDOR'
    
    t_cctv = len(df[df[col_u] == 'Soporte Circuito Cerrado de Televisin (CCTV)']) if col_u in df.columns else 0
    t_dcero = len(df[df[col_u] == 'Soporte Dcero']) if col_u in df.columns else 0
    t_secomp = len(df[df[col_u] == 'Soporte Secomp']) if col_u in df.columns else 0
    t_en_ejecucion = t_dcero + t_secomp
    t_pendientes = len(df[df[col_s].astype(str).str.strip().isin(['', 'nan', 'None'])]) if col_s in df.columns else 0

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1: st.markdown(crear_kpi_pro("Total Abiertos", t_total, "#1E2433"), unsafe_allow_html=True)
    with k2: st.markdown(crear_kpi_pro("Interno CCTV", t_cctv, "#1DA1F2"), unsafe_allow_html=True)
    with k3: st.markdown(crear_kpi_pro("Externo Dcero", t_dcero, "#71C9F8"), unsafe_allow_html=True)
    with k4: st.markdown(crear_kpi_pro("Externo Secomp", t_secomp, "#A5D8FF"), unsafe_allow_html=True)
    with k5: st.markdown(crear_kpi_pro("Pendientes", t_pendientes, "#E0245E"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Fila de Gráficos en contenedores estilizados
    c1, c2 = st.columns(2)
    col_j = 'FECHA_REPORTE'

    with c1:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        if col_j in df.columns:
            df['FECHA_DT'] = pd.to_datetime(df[col_j], dayfirst=True, errors='coerce')
            df_fechas = df.dropna(subset=['FECHA_DT']).copy()
            df_fechas['Periodo'] = df_fechas['FECHA_DT'].dt.strftime('%b %y').str.lower()
            df_fechas['Orden'] = df_fechas['FECHA_DT'].dt.to_period('M')
            mensual_df = df_fechas.groupby(['Orden', 'Periodo']).size().reset_index(name='Cantidad').sort_values('Orden')
            
            fig_mes = px.line(mensual_df, x='Periodo', y='Cantidad', title="<b>Tendencia: Antigüedad del Backlog</b>", markers=True)
            fig_mes.update_traces(line_color='#1DA1F2', line_width=3, marker=dict(size=8, color='white', line=dict(width=2, color='#1DA1F2')))
            fig_mes.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=350, margin=dict(l=0,r=0,t=40,b=0))
            st.plotly_chart(fig_mes, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        if col_j in df.columns and col_u in df.columns:
            df_apilado = df.dropna(subset=['FECHA_DT']).copy()
            df_apilado['Periodo'] = df_apilado['FECHA_DT'].dt.strftime('%b %y').str.lower()
            df_apilado['Orden'] = df_apilado['FECHA_DT'].dt.to_period('M')
            
            def clasificar(fila):
                if fila in ['Soporte Dcero', 'Soporte Secomp']: return 'Ejecución'
                elif fila == 'Soporte Circuito Cerrado de Televisin (CCTV)': return 'Pendiente'
                else: return 'Otros'
            
            df_apilado['Categoria'] = df_apilado[col_u].apply(clasificar)
            mensual_grp = df_apilado[df_apilado['Categoria'] != 'Otros'].groupby(['Orden', 'Periodo', 'Categoria']).size().reset_index(name='Cantidad').sort_values('Orden')
            
            fig_bar = px.bar(mensual_grp, x='Periodo', y='Cantidad', color='Categoria', title="<b>Distribución: Ejecución vs Pendiente</b>",
                             color_discrete_map={'Pendiente': '#008080', 'Ejecución': '#F58220'}, barmode='group')
            fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=350, margin=dict(l=0,r=0,t=40,b=0), legend=dict(orientation="h", y=1.1, x=1))
            st.plotly_chart(fig_bar, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Tabla de Detalle al final
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.markdown("### 📝 Detalle de Reportes Seleccionados")
    st.dataframe(df[['REPORTE', 'LOCAL', 'ESTADO_SN', 'PROVEDDOR', 'COMENTARIO']], use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Error en el sistema: {e}")
