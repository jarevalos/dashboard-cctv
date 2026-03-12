import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px

# 1. Configuración de la página
st.set_page_config(page_title="Dashboard CCTV", page_icon="📹", layout="wide")

# --- CSS PROFESIONAL ---
st.markdown("""
    <style>
    /* Reducir márgenes */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 95% !important;
    }
    /* Título principal */
    h1 {
        font-size: 1.8rem !important;
        font-weight: 600 !important;
        color: #e0e0e0;
        margin-bottom: 1rem !important;
    }
    /* Ocultar elementos por defecto de Streamlit */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Panel de Control CCTV")

# 2. Conexión a Google Sheets (Actualizado a 60 seg para casi tiempo real)
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
    return pd.DataFrame(data)

# --- FUNCIÓN PARA CREAR TARJETAS PROFESIONALES ---
def crear_tarjeta(titulo, valor, color_borde):
    html = f"""
    <div style="
        background-color: #262730; 
        padding: 15px 20px; 
        border-radius: 8px; 
        border-left: 5px solid {color_borde};
        box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
        margin-bottom: 10px;
    ">
        <p style="margin: 0; font-size: 0.85rem; color: #a5a5a5; font-weight: 600; text-transform: uppercase;">{titulo}</p>
        <h2 style="margin: 0; font-size: 2rem; color: #ffffff; font-weight: 700;">{valor}</h2>
    </div>
    """
    return html

try:
    df = cargar_datos()
    
    tab1, tab2 = st.tabs(["📊 Panel General", "🏢 Análisis por Local"])
    
    # ==========================================
    # PESTAÑA 1: DASHBOARD PROFESIONAL
    # ==========================================
    with tab1:
        df_mostrar = df.copy()

        # Cálculos de KPIs
        t_backlog = len(df_mostrar)
        t_cctv = len(df_mostrar) 
        t_dcero = len(df_mostrar[df_mostrar['PROVEDDOR'].astype(str).str.contains('DCERO', case=False, na=False)])
        t_secomp = len(df_mostrar[df_mostrar['PROVEDDOR'].astype(str).str.contains('SECOMP', case=False, na=False)])
        t_ejecucion = len(df_mostrar[df_mostrar['ESTADO_SN'] == 'En Proceso']) 
        t_pendientes = len(df_mostrar[df_mostrar['ESTADO_SN'] != 'Cerrado'])

        # --- FILA 1: KPIs CON DISEÑO DE TARJETAS ---
        kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
        
        with kpi1: st.markdown(crear_tarjeta("Backlog Total", t_backlog, "#008080"), unsafe_allow_html=True)
        with kpi2: st.markdown(crear_tarjeta("CCTV", t_cctv, "#4682B4"), unsafe_allow_html=True)
        with kpi3: st.markdown(crear_tarjeta("DCERO", t_dcero, "#FF8C00"), unsafe_allow_html=True)
        with kpi4: st.markdown(crear_tarjeta("SECOMP", t_secomp, "#9370DB"), unsafe_allow_html=True)
        with kpi5: st.markdown(crear_tarjeta("En ejecución", t_ejecucion, "#32CD32"), unsafe_allow_html=True)
        with kpi6: st.markdown(crear_tarjeta("Pendientes", t_pendientes, "#DC143C"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True) # Espacio

        # --- FILA 2: GRÁFICOS CON FONDO TRANSPARENTE ---
        graf_sup1, graf_sup2, graf_sup3 = st.columns(3)
        altura_grafico = 280 
        
        # Configuración común para que los gráficos se vean limpios
        layout_transparente = dict(
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#e0e0e0',
            height=altura_grafico,
            margin=dict(l=10, r=10, t=30, b=10)
        )
        
        with graf_sup1:
            top_locales = df_mostrar['LOCAL'].value_counts().head(10).reset_index()
            top_locales.columns = ['Local', 'Cantidad']
            fig1 = px.bar(top_locales, x='Local', y='Cantidad', title="<b>TOP 10 LOCALES</b>", text_auto=True, color_discrete_sequence=['#008080'])
            fig1.update_layout(**layout_transparente)
            fig1.update_yaxes(showgrid=False, visible=False) # Ocultar cuadrícula trasera
            st.plotly_chart(fig1, use_container_width=True)

        with graf_sup2:
            conteo_estados = df_mostrar['ESTADO_SN'].value_counts().reset_index()
            conteo_estados.columns = ['Estado', 'Cantidad']
            fig2 = px.pie(conteo_estados, values='Cantidad', names='Estado', title="<b>ESTADO DE ATENCIONES</b>", hole=0.6, color_discrete_sequence=px.colors.sequential.Teal)
            fig2.update_layout(**layout_transparente, showlegend=False)
            fig2.update_traces(textposition='inside', textinfo='percent+label', textfont_size=12)
            st.plotly_chart(fig2, use_container_width=True)

        with graf_sup3:
            conteo_prov = df_mostrar['PROVEDDOR'].value_counts().reset_index()
            conteo_prov.columns = ['Proveedor', 'Cantidad']
            fig3 = px.pie(conteo_prov, values='Cantidad', names='Proveedor', title="<b>GRUPO ASIGNADO</b>", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig3.update_layout(**layout_transparente, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
            fig3.update_traces(textposition='inside', textinfo='percent')
            st.plotly_chart(fig3, use_container_width=True)

    # ==========================================
    # PESTAÑA 2: BÚSQUEDA ESPECÍFICA POR LOCAL
    # ==========================================
    with tab2:
        st.header("Análisis por Local")
        lista_locales = df['LOCAL'].unique()
        local_seleccionado = st.selectbox("🏢 Selecciona un Local:", lista_locales)
        
        datos_local = df[df['LOCAL'] == local_seleccionado]
        st.dataframe(
            datos_local[['REPORTE', 'TIENDA', 'ESTADO_SN', 'PROVEDDOR', 'COMENTARIO']], 
            use_container_width=True, hide_index=True
        )

except Exception as e:
    st.error(f"Error cargando la aplicación: {e}")
