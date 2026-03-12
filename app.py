import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px

# 1. Configuración de la página
st.set_page_config(page_title="Dashboard CCTV", page_icon="📹", layout="wide")

# --- CSS SÚPER COMPACTO ---
st.markdown("""
    <style>
    /* Reducir al máximo los márgenes de la página */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }
    /* Achicar título principal */
    h1 {
        font-size: 1.5rem !important;
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        margin-bottom: 0rem !important;
    }
    /* Achicar números de KPIs (Tarjetas) */
    [data-testid="stMetricValue"] {
        font-size: 1.4rem !important;
    }
    /* Achicar los textos encima de los números */
    [data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
        color: #555555;
    }
    /* Juntar más las filas y columnas */
    div[data-testid="stVerticalBlock"] {
        gap: 0.2rem !important;
    }
    /* Ocultar el encabezado por defecto de Streamlit para ganar espacio */
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Panel de Control CCTV")

# 2. Conexión segura a Google Sheets
@st.cache_data(ttl=600)
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

try:
    df = cargar_datos()
    
    tab1, tab2 = st.tabs(["📊 Panel General", "🏢 Análisis por Local"])
    
    # ==========================================
    # PESTAÑA 1: DASHBOARD (SIN FILTROS Y PEQUEÑO)
    # ==========================================
    with tab1:
        df_mostrar = df.copy()

        # --- TARJETAS DE MÉTRICAS (KPIs) pegadas arriba ---
        kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
        
        kpi1.metric("Backlog Total", len(df_mostrar))
        kpi2.metric("CCTV", len(df_mostrar)) 
        
        total_dcero = len(df_mostrar[df_mostrar['PROVEDDOR'].astype(str).str.contains('DCERO', case=False, na=False)])
        kpi3.metric("DCERO", total_dcero)
        
        total_secomp = len(df_mostrar[df_mostrar['PROVEDDOR'].astype(str).str.contains('SECOMP', case=False, na=False)])
        kpi4.metric("SECOMP", total_secomp)
        
        total_ejecucion = len(df_mostrar[df_mostrar['ESTADO_SN'] == 'En Proceso']) 
        kpi5.metric("En ejecución", total_ejecucion)
        
        total_pendientes = len(df_mostrar[df_mostrar['ESTADO_SN'] != 'Cerrado'])
        kpi6.metric("Pendientes", total_pendientes)

        st.markdown("---")

        # --- GRÁFICOS COMPACTOS ---
        graf_sup1, graf_sup2, graf_sup3 = st.columns(3)
        
        # Redujimos la altura a 220px para que quede todo en un solo pantallazo
        altura_grafico = 220 
        
        with graf_sup1:
            st.markdown("**TOP 10 LOCALES**")
            top_locales = df_mostrar['LOCAL'].value_counts().head(10).reset_index()
            top_locales.columns = ['Local', 'Cantidad']
            fig1 = px.bar(top_locales, x='Local', y='Cantidad', text_auto=True, color_discrete_sequence=['#008080'])
            # Eliminamos los márgenes (l=0, r=0...) para aprovechar el 100% del cuadro
            fig1.update_layout(height=altura_grafico, margin=dict(l=0, r=0, t=0, b=0), xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig1, use_container_width=True)

        with graf_sup2:
            st.markdown("**ESTADO DE ATENCIONES**")
            conteo_estados = df_mostrar['ESTADO_SN'].value_counts().reset_index()
            conteo_estados.columns = ['Estado', 'Cantidad']
            fig2 = px.pie(conteo_estados, values='Cantidad', names='Estado', hole=0.5)
            fig2.update_layout(height=altura_grafico, margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
            fig2.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig2, use_container_width=True)

        with graf_sup3:
            st.markdown("**GRUPO ASIGNADO**")
            conteo_prov = df_mostrar['PROVEDDOR'].value_counts().reset_index()
            conteo_prov.columns = ['Proveedor', 'Cantidad']
            fig3 = px.pie(conteo_prov, values='Cantidad', names='Proveedor')
            fig3.update_layout(height=altura_grafico, margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
            fig3.update_traces(textposition='inside', textinfo='percent+label')
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
