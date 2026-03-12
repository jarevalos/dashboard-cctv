import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px

# 1. Configuración de la página
st.set_page_config(page_title="CCTV Control Center", page_icon="📹", layout="wide")

# ==========================================
# CSS DISEÑO ULTRA MODERNO (DEEP DARK)
# ==========================================
st.markdown("""
    <style>
    /* Fondo Oscuro Principal */
    .stApp {
        background-color: #0F172A !important;
        color: #F8FAFC !important;
    }
    
    /* Barra lateral estilo Sidebar Pro */
    section[data-testid="stSidebar"] {
        background-color: #1E293B !important;
        border-right: 1px solid #334155;
    }
    section[data-testid="stSidebar"] .stMarkdown h2, 
    section[data-testid="stSidebar"] .stMarkdown p {
        color: #38BDF8 !important;
    }
    
    /* Estilo de los Radio Buttons del Menú */
    .stRadio > label { color: #94A3B8 !important; font-weight: 600 !important; }
    div[data-testid="stMarkdownContainer"] p { color: #94A3B8; }

    /* Tarjetas de KPI (Modo Oscuro) */
    .kpi-card {
        background: #1E293B;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #334155;
        text-align: center;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .kpi-label { color: #94A3B8; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-bottom: 8px; }
    .kpi-value { color: #F8FAFC; font-size: 2rem; font-weight: 800; line-height: 1; }

    /* Contenedores de Gráficos */
    .plot-box {
        background: #1E293B;
        padding: 24px;
        border-radius: 20px;
        border: 1px solid #334155;
    }

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

def render_kpi(titulo, valor, color_accent):
    st.markdown(f"""
    <div class="kpi-card" style="border-bottom: 4px solid {color_accent};">
        <p class="kpi-label">{titulo}</p>
        <h2 class="kpi-value">{valor}</h2>
    </div>
    """, unsafe_allow_html=True)

try:
    df = cargar_datos()

    # --- BARRA LATERAL ---
    with st.sidebar:
        st.markdown("<h2 style='text-align: center; color: #38BDF8;'>CENTER OS</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 0.8rem;'>NOC Monitoring v3.0</p>", unsafe_allow_html=True)
        st.divider()
        pagina = st.radio("NAVEGACIÓN", ["⚡ Dashboard", "📋 Reportes"])
        st.divider()

    # --- LÓGICA DE PÁGINAS ---
    if pagina == "⚡ Dashboard":
        # KPIs
        t_total = len(df)
        col_u = 'GRUPO_ASIGNADO'
        col_s = 'PROVEDDOR'
        
        t_cctv = len(df[df[col_u] == 'Soporte Circuito Cerrado de Televisin (CCTV)']) if col_u in df.columns else 0
        t_dcero = len(df[df[col_u] == 'Soporte Dcero']) if col_u in df.columns else 0
        t_secomp = len(df[df[col_u] == 'Soporte Secomp']) if col_u in df.columns else 0
        t_en_ejecucion = t_dcero + t_secomp
        t_pendientes = len(df[df[col_s].astype(str).str.strip().isin(['', 'nan', 'None'])]) if col_s in df.columns else 0

        k1, k2, k3, k4, k5 = st.columns(5)
        with k1: render_kpi("Backlog Total", t_total, "#38BDF8")
        with k2: render_kpi("Interno CCTV", t_cctv, "#818CF8")
        with k3: render_kpi("Dcero", t_dcero, "#FB923C")
        with k4: render_kpi("Secomp", t_secomp, "#FACC15")
        with k5: render_kpi("Pendientes", t_pendientes, "#F87171")

        st.markdown("<br>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        col_j = 'FECHA_REPORTE'

        with c1:
            st.markdown('<div class="plot-box">', unsafe_allow_html=True)
            if col_j in df.columns:
                df['FECHA_DT'] = pd.to_datetime(df[col_j], dayfirst=True, errors='coerce')
                df_fechas = df.dropna(subset=['FECHA_DT']).copy()
                df_fechas['Periodo'] = df_fechas['FECHA_DT'].dt.strftime('%b %y').str.lower()
                df_fechas['Orden'] = df_fechas['FECHA_DT'].dt.to_period('M')
                mensual_df = df_fechas.groupby(['Orden', 'Periodo']).size().reset_index(name='Cantidad').sort_values('Orden')
                
                fig_line = px.area(mensual_df, x='Periodo', y='Cantidad', title="<b>ANTIGÜEDAD DEL BACKLOG</b>")
                fig_line.update_traces(line_color='#38BDF8', fillcolor='rgba(56, 189, 248, 0.1)')
                fig_line.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                    font_color="#94A3B8", height=350, margin=dict(l=0,r=0,t=40,b=0),
                    xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#334155')
                )
                st.plotly_chart(fig_line, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="plot-box">', unsafe_allow_html=True)
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
                
                fig_bar = px.bar(mensual_grp, x='Periodo', y='Cantidad', color='Categoria', title="<b>REPORTES EN EJECUCIÓN</b>",
                                 color_discrete_map={'Pendiente': '#38BDF8', 'Ejecución': '#FB923C'}, barmode='group', text_auto=True)
                fig_bar.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                    font_color="#94A3B8", height=350, margin=dict(l=0,r=0,t=40,b=0),
                    legend=dict(orientation="h", y=1.1, x=1), xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#334155')
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    elif pagina == "📋 Reportes":
        st.markdown('<div class="plot-box">', unsafe_allow_html=True)
        st.markdown("### DETALLE DE CASOS ACTIVOS")
        busqueda = st.text_input("🔍 FILTRAR POR LOCAL O REPORTE...")
        if busqueda:
            df_filtered = df[df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]
        else:
            df_filtered = df
        st.dataframe(df_filtered[['REPORTE', 'LOCAL', 'ESTADO_SN', 'PROVEDDOR', 'COMENTARIO']], use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Error: {e}")
