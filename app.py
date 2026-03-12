import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px

# 1. Configuración de la página
st.set_page_config(page_title="Dashboard CCTV", page_icon="📹", layout="wide")

# --- MAGIA CSS PARA HACER TODO MÁS COMPACTO ---
st.markdown("""
    <style>
    /* Reducir el espacio en blanco superior de la página */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    /* Achicar el título principal */
    h1 {
        font-size: 1.8rem !important;
        padding-bottom: 0px !important;
    }
    /* Achicar los números de las tarjetas (KPIs) */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
        color: #555555;
    }
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
    
    tab1, tab2 = st.tabs(["📊 Dashboard General", "🏢 Análisis por Local"])
    
    # ==========================================
    # PESTAÑA 1: DASHBOARD COMPACTO
    # ==========================================
    with tab1:
        # --- FILA 1: FILTROS SUPERIORES ---
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filtro_estado = st.selectbox("ESTADO GESTIÓN", ["Todos"] + list(df['ESTADO_SN'].unique()))
        with col_f2:
            filtro_mes = st.selectbox("MES PRESUPUESTO", ["Todos"]) 
        with col_f3:
            filtro_prov = st.selectbox("PROVEEDOR", ["Todos"] + list(df['PROVEDDOR'].unique()))

        df_mostrar = df.copy()

        # --- FILA 2: TARJETAS DE MÉTRICAS (KPIs) ---
        st.markdown("---")
        kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
        
        kpi1.metric("Backlog Total", len(df_mostrar))
        kpi2.metric("CCTV", len(df_mostrar)) 
        
        total_dcero = len(df_mostrar[df_mostrar['PROVEDDOR'].astype(str).str.contains('DCERO', case=False, na=False)])
        kpi3.metric("DCERO", total_dcero)
        
        total_secomp = len(df_mostrar[df_mostrar['PROVEDDOR'].astype(str).str.contains('SECOMP', case=False, na=False)])
        kpi4.metric("SECOMP", total_secomp)
        
        # Ajusta el texto 'En Proceso' según lo que diga exactamente en tu hoja
        total_ejecucion = len(df_mostrar[df_mostrar['ESTADO_SN'] == 'En Proceso']) 
        kpi5.metric("En ejecución", total_ejecucion)
        
        total_pendientes = len(df_mostrar[df_mostrar['ESTADO_SN'] != 'Cerrado'])
        kpi6.metric("Pendientes", total_pendientes)

        st.markdown("---")

        # --- FILA 3: GRÁFICOS COMPACTOS ---
        graf_sup1, graf_sup2, graf_sup3 = st.columns(3)
        
        # Altura fija para que los gráficos no se alarguen
        altura_grafico = 280 
        
        with graf_sup1:
            st.markdown("**TOP 10 LOCALES**")
            top_locales = df_mostrar['LOCAL'].value_counts().head(10).reset_index()
            top_locales.columns = ['Local', 'Cantidad']
            fig1 = px.bar(top_locales, x='Local', y='Cantidad', text_auto=True, color_discrete_sequence=['#008080'])
            fig1.update_layout(height=altura_grafico, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig1, use_container_width=True)

        with graf_sup2:
            st.markdown("**ESTADO DE ATENCIONES**")
            conteo_estados = df_mostrar['ESTADO_SN'].value_counts().reset_index()
            conteo_estados.columns = ['Estado', 'Cantidad']
            fig2 = px.pie(conteo_estados, values='Cantidad', names='Estado', hole=0.5)
            fig2.update_layout(height=altura_grafico, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
            fig2.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig2, use_container_width=True)

        with graf_sup3:
            st.markdown("**GRUPO ASIGNADO**")
            conteo_prov = df_mostrar['PROVEDDOR'].value_counts().reset_index()
            conteo_prov.columns = ['Proveedor', 'Cantidad']
            fig3 = px.pie(conteo_prov, values='Cantidad', names='Proveedor')
            fig3.update_layout(height=altura_grafico, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
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
