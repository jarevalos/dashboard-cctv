import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px

# 1. Configuración de la página
st.set_page_config(page_title="Dashboard CCTV Pro", page_icon="📹", layout="wide")

# ==========================================
# CSS DISEÑO PROFESIONAL (ESTILO MODERNO)
# ==========================================
st.markdown("""
    <style>
    /* Fondo gris ultra suave */
    .stApp { background-color: #F4F7F9 !important; }
    
    /* Eliminar márgenes superiores */
    .block-container { 
        padding-top: 0.5rem !important; 
        padding-bottom: 0rem !important; 
        max-width: 98% !important; 
    }
    
    /* Tarjetas de KPI Estilizadas */
    .card-pro {
        background-color: white;
        padding: 12px 5px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        text-align: center;
        border: 1px solid #E1E8ED;
        margin-bottom: 10px;
    }
    
    .card-label { 
        margin: 0; 
        font-size: 0.65rem !important; 
        color: #657786; 
        font-weight: 700; 
        text-transform: uppercase; 
        letter-spacing: 0.5px;
    }
    
    .card-value { 
        margin: 0; 
        font-size: 1.6rem !important; 
        color: #14171A; 
        font-weight: 800; 
        line-height: 1.1; 
    }

    /* Ocultar elementos de Streamlit */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Contenedores de gráficos */
    .plot-container {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid #E1E8ED;
    }
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

def crear_tarjeta_pro(titulo, valor, color_borde):
    html = f"""
    <div class="card-pro" style="border-top: 4px solid {color_borde};">
        <p class="card-label">{titulo}</p>
        <h2 class="card-value">{valor}</h2>
    </div>
    """
    return html

try:
    df = cargar_datos()
    
    tab1, tab2 = st.tabs(["📊 Vista Ejecutiva", "🏢 Detalle por Local"])
    
    with tab1:
        # --- CÁLCULO DE DATOS ---
        t_total_abiertos = len(df)
        col_u = 'GRUPO_ASIGNADO'
        col_s = 'PROVEDDOR'
        
        if col_u in df.columns:
            df[col_u] = df[col_u].astype(str).str.strip()
            g_cctv_txt = 'Soporte Circuito Cerrado de Televisin (CCTV)'
            g_dcero_txt = 'Soporte Dcero'
            g_secomp_txt = 'Soporte Secomp'
            
            t_cctv = len(df[df[col_u] == g_cctv_txt])
            t_dcero = len(df[df[col_u] == g_dcero_txt])
            t_secomp = len(df[df[col_u] == g_secomp_txt])
            t_en_ejecucion = t_dcero + t_secomp
        else:
            t_cctv = t_dcero = t_secomp = t_en_ejecucion = 0
        
        if col_s in df.columns:
            t_pendientes = len(df[df[col_s].astype(str).str.strip().isin(['', 'nan', 'None'])])
        else:
            t_pendientes = 0

        # --- FILA DE KPIs (5 Tarjetas principales) ---
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        with kpi1: st.markdown(crear_tarjeta_pro("Total Abiertos", t_total_abiertos, "#E0245E"), unsafe_allow_html=True) 
        with kpi2: st.markdown(crear_tarjeta_pro("Soporte CCTV", t_cctv, "#1DA1F2"), unsafe_allow_html=True) 
        with kpi3: st.markdown(crear_tarjeta_pro("Soporte Dcero", t_dcero, "#71C9F8"), unsafe_allow_html=True) 
        with kpi4: st.markdown(crear_tarjeta_pro("Soporte Secomp", t_secomp, "#A5D8FF"), unsafe_allow_html=True) 
        with kpi5: st.markdown(crear_tarjeta_pro("En Ejecución", t_en_ejecucion, "#F58220"), unsafe_allow_html=True)

        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

        # ========================================================
        # BLOQUE DE GRÁFICOS PRO
        # ========================================================
        graf_col1, graf_col2 = st.columns(2)
        col_j = 'FECHA_REPORTE'
        color_pendiente = "#008080" # Turquesa Pro
        color_ejecucion = "#F58220" # Naranja Pro

        # --- GRÁFICO 1: ANTIGUEDAD DEL BACKLOG ---
        with graf_col1:
            if col_j in df.columns:
                df['FECHA_DT'] = pd.to_datetime(df[col_j], dayfirst=True, errors='coerce')
                df_fechas = df.dropna(subset=['FECHA_DT']).copy()
                df_fechas['Periodo'] = df_fechas['FECHA_DT'].dt.strftime('%b %y').str.lower()
                df_fechas['Orden'] = df_fechas['FECHA_DT'].dt.to_period('M')
                mensual_df = df_fechas.groupby(['Orden', 'Periodo']).size().reset_index(name='Cantidad')
                mensual_df = mensual_df.sort_values('Orden')

                fig_mes = px.bar(
                    mensual_df, x='Periodo', y='Cantidad', 
                    title="<b>Antigüedad del backlog</b>", 
                    text_auto=True, 
                    color_discrete_sequence=[color_pendiente]
                )
                fig_mes.update_layout(
                    paper_bgcolor='white', plot_bgcolor='white', 
                    height=400, margin=dict(l=10, r=10, t=50, b=10),
                    xaxis_title=None, yaxis_title=None,
                    font=dict(family="Arial", size=12)
                )
                fig_mes.update_yaxes(showgrid=True, gridcolor='#F0F2F5')
                fig_mes.update_traces(textposition='outside', marker_line_width=0)
                st.plotly_chart(fig_mes, use_container_width=True)

        # --- GRÁFICOS 2: REPORTES EN EJECUCION ---
        with graf_col2:
            if col_j in df.columns and col_u in df.columns:
                df['FECHA_DT'] = pd.to_datetime(df[col_j], dayfirst=True, errors='coerce')
                df_apilado = df.dropna(subset=['FECHA_DT']).copy()
                df_apilado['Periodo'] = df_apilado['FECHA_DT'].dt.strftime('%b %y').str.lower()
                df_apilado['Orden'] = df_apilado['FECHA_DT'].dt.to_period('M')

                def clasificar(fila):
                    if fila in ['Soporte Dcero', 'Soporte Secomp']: return 'Ejecución'
                    elif fila == 'Soporte Circuito Cerrado de Televisin (CCTV)': return 'Pendiente'
                    else: return 'Otros'

                df_apilado['Categoria'] = df_apilado[col_u].apply(clasificar)
                df_apilado = df_apilado[df_apilado['Categoria'] != 'Otros']

                mensual_grp = df_apilado.groupby(['Orden', 'Periodo', 'Categoria']).size().reset_index(name='Cantidad')
                mensual_grp = mensual_grp.sort_values('Orden')

                fig_apilado = px.bar(
                    mensual_grp, x='Periodo', y='Cantidad', color='Categoria',
                    title="<b>Reportes en ejecución</b>",
                    text_auto=True,
                    color_discrete_map={'Pendiente': color_pendiente, 'Ejecución': color_ejecucion}
                )
                fig_apilado.update_layout(
                    paper_bgcolor='white', plot_bgcolor='white', 
                    height=400, margin=dict(l=10, r=10, t=50, b=10),
                    legend=dict(orientation="h", title=None, yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis_title=None, yaxis_title=None
                )
                fig_apilado.update_yaxes(showgrid=True, gridcolor='#F0F2F5')
                fig_apilado.update_traces(marker_line_width=0)
                st.plotly_chart(fig_apilado, use_container_width=True)

    with tab2:
        st.header("Análisis por Local")
        if 'LOCAL' in df.columns:
            lista_locales = sorted(df['LOCAL'].unique())
            local_sel = st.selectbox("🏢 Selecciona un Local:", lista_locales)
            res = df[df['LOCAL'] == local_sel]
            st.dataframe(res[['REPORTE', 'ESTADO_SN', 'PROVEDDOR', 'COMENTARIO']], use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error en el procesamiento: {e}")
