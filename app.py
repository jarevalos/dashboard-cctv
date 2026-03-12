import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px

# 1. Configuración de la página
st.set_page_config(page_title="Dashboard CCTV", page_icon="📹", layout="wide")

# ==========================================
# CSS ESTILO POWER BI / EXCEL CORPORATIVO
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #F0F2F6 !important; }
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; max-width: 98% !important; }
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- BANNER SUPERIOR OSCURO ---
st.markdown("""
    <div style="background-color: #1E2433; padding: 20px 30px; border-radius: 10px; margin-bottom: 20px; display: flex; align-items: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <div style="font-size: 40px; margin-right: 20px;">📹</div>
        <div>
            <h1 style="color: white; margin: 0; padding: 0; font-size: 26px; font-weight: 700;">Dashboard - Panel de Control CCTV</h1>
            <p style="color: #A0AAB5; margin: 0; font-size: 14px;">Características que describen el estado de atenciones a nivel nacional</p>
        </div>
    </div>
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

    # --- FILTRO MAESTRO DE DATOS ABIERTOS ---
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
    <div style="background-color: white; padding: 15px 10px; border-radius: 8px; border-top: 4px solid {color_acento}; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center; margin-bottom: 15px; border-left: 1px solid #eee; border-right: 1px solid #eee; border-bottom: 1px solid #eee;">
        <p style="margin: 0; font-size: 0.85rem; color: #555555; font-weight: 600; text-transform: uppercase;">{titulo}</p>
        <h2 style="margin: 0; font-size: 2.2rem; color: #1E2433; font-weight: 800;">{valor}</h2>
    </div>
    """
    return html

try:
    df = cargar_datos()
    
    tab1, tab2 = st.tabs(["📊 Panel General", "🏢 Análisis por Local"])
    
    with tab1:
        df_mostrar = df.copy()

        # ==========================================
        # LÓGICA DE KPIs (TARJETAS)
        # ==========================================
        # 1. Filtro base de Casos Abiertos (Backlog)
        if 'ESTADO_SN' in df_mostrar.columns:
            estados_backlog = ['ASIGNADO', 'EN ESPERA', 'EN PROGRESO']
            filtro_abiertos = df_mostrar['ESTADO_SN'].str.upper().isin(estados_backlog)
            t_abiertos = len(df_mostrar[filtro_abiertos])
        else: 
            filtro_abiertos = pd.Series(False, index=df_mostrar.index)
            t_abiertos = 0

        # 2. Filtros por GRUPO_ASIGNADO (Columna U)
        if 'GRUPO_ASIGNADO' in df_mostrar.columns:
            g_cctv = 'Soporte Circuito Cerrado de Televisin (CCTV)'
            g_dcero = 'Soporte Dcero'
            g_secomp = 'Soporte Secomp'
            
            # Contamos cruzando: Abierto Y Grupo específico en Columna U
            t_cctv = len(df_mostrar[filtro_abiertos & (df_mostrar['GRUPO_ASIGNADO'].astype(str).str.strip() == g_cctv)])
            t_dcero = len(df_mostrar[filtro_abiertos & (df_mostrar['GRUPO_ASIGNADO'].astype(str).str.strip() == g_dcero)])
            t_secomp = len(df_mostrar[filtro_abiertos & (df_mostrar['GRUPO_ASIGNADO'].astype(str).str.strip() == g_secomp)])
        else:
            t_cctv = t_dcero = t_secomp = 0

        # 3. Otros KPIs
        t_ejecucion = len(df_mostrar[df_mostrar['ESTADO_SN'].str.upper() == 'EN PROCESO']) if 'ESTADO_SN' in df_mostrar.columns else 0
        t_sin_estado = len(df_mostrar[df_mostrar['ESTADO_SN'] == '']) if 'ESTADO_SN' in df_mostrar.columns else 0

        # --- DIBUJAR LAS TARJETAS ---
        kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
        with kpi1: st.markdown(crear_tarjeta("Casos Abiertos", t_abiertos, "#D92B38"), unsafe_allow_html=True) 
        with kpi2: st.markdown(crear_tarjeta("CCTV", t_cctv, "#1F4E79"), unsafe_allow_html=True) 
        with kpi3: st.markdown(crear_tarjeta("DCERO", t_dcero, "#4DA6FF"), unsafe_allow_html=True) 
        with kpi4: st.markdown(crear_tarjeta("SECOMP", t_secomp, "#4DA6FF"), unsafe_allow_html=True) 
        with kpi5: st.markdown(crear_tarjeta("En ejecución", t_ejecucion, "#D92B38"), unsafe_allow_html=True)
        with kpi6: st.markdown(crear_tarjeta("Sin Estado", t_sin_estado, "#1E2433"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- GRÁFICOS ---
        graf_sup1, graf_sup2, graf_sup3 = st.columns(3)
        layout_blanco = dict(paper_bgcolor='white', plot_bgcolor='white', font_color='#333333', height=320, margin=dict(l=20, r=20, t=50, b=20), title_font=dict(size=14, color='#1E2433'))
        paleta_colores = ['#1F4E79', '#D92B38', '#4DA6FF', '#8CA3B5', '#1E2433']
        
        with graf_sup1:
            if 'LOCAL' in df_mostrar.columns:
                top_locales = df_mostrar['LOCAL'].value_counts().head(10).reset_index()
                top_locales.columns = ['Local', 'Cantidad']
                fig1 = px.bar(top_locales, x='Local', y='Cantidad', title="<b>TOP 10 LOCALES CRÍTICOS</b>", text_auto=True, color_discrete_sequence=['#1F4E79'])
                fig1.update_layout(**layout_blanco)
                fig1.update_yaxes(showgrid=True, gridcolor='#f0f0f0') 
                st.plotly_chart(fig1, use_container_width=True)

        with graf_sup2:
            if 'ESTADO_SN' in df_mostrar.columns:
                conteo_estados = df_mostrar['ESTADO_SN'].value_counts().reset_index()
                conteo_estados.columns = ['Estado', 'Cantidad']
                fig2 = px.pie(conteo_estados, values='Cantidad', names='Estado', title="<b>ESTADO (SOLO ABIERTOS)</b>", hole=0.6, color_discrete_sequence=paleta_colores)
                fig2.update_layout(**layout_blanco, showlegend=False)
                fig2.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='white', width=2)))
                st.plotly_chart(fig2, use_container_width=True)

        with graf_sup3:
            if 'PROVEDDOR' in df_mostrar.columns:
                conteo_prov = df_mostrar['PROVEDDOR'].value_counts().reset_index()
                conteo_prov.columns = ['Proveedor', 'Cantidad']
                fig3 = px.pie(conteo_prov, values='Cantidad', names='Proveedor', title="<b>ASIGNACIÓN ACTUAL</b>", hole=0.4, color_discrete_sequence=paleta_colores)
                fig3.update_layout(**layout_blanco, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
                fig3.update_traces(textposition='inside', textinfo='percent', marker=dict(line=dict(color='white', width=2)))
                st.plotly_chart(fig3, use_container_width=True)

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
