import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px

# 1. Configuración de la página (Layout 'wide' para que ocupe toda la pantalla)
st.set_page_config(page_title="Dashboard CCTV", page_icon="📹", layout="wide")
st.title("📊 Panel de Control CCTV")

# 2. Conexión segura a Google Sheets
@st.cache_data(ttl=600)
def cargar_datos():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    skey = st.secrets["gcp_service_account"]
    credentials = Credentials.from_service_account_info(skey, scopes=scopes)
    gc = gspread.authorize(credentials)
    
    # Asegúrate de que el ID sea el de tu planilla CCTV 6.0
    spreadsheet_id = '1fyZCiYawIQWrzD5WaTfNeWT5fYtRneozHQ8bg2KTDuk'
    sh = gc.open_by_key(spreadsheet_id)
    worksheet = sh.worksheet("BASE")
    
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

try:
    df = cargar_datos()
    
    # --- CREACIÓN DE PESTAÑAS ---
    tab1, tab2 = st.tabs(["📊 Dashboard General", "🏢 Análisis por Local"])
    
    # ==========================================
    # PESTAÑA 1: DASHBOARD ESTILO POWER BI
    # ==========================================
    with tab1:
        # --- FILA 1: FILTROS SUPERIORES ---
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filtro_estado = st.selectbox("ESTADO GESTION", ["Todos"] + list(df['ESTADO_SN'].unique()))
        with col_f2:
            # Reemplaza 'MES_ASIGNACION' si en tu planilla se llama distinto
            columnas_mes = 'MES' if 'MES' in df.columns else 'REPORTE' # Placeholder temporal
            filtro_mes = st.selectbox("MES PRESUPUESTO", ["Todos"]) # Aquí luego anclamos los meses
        with col_f3:
            filtro_prov = st.selectbox("PROVEDDOR", ["Todos"] + list(df['PROVEDDOR'].unique()))

        # (Aquí iría la lógica para aplicar los filtros al dataframe, por ahora mostramos todo)
        df_mostrar = df.copy()

        # --- FILA 2: TARJETAS DE MÉTRICAS (KPIs) ---
        st.markdown("---")
        kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
        
        kpi1.metric("Backlog Total", len(df_mostrar))
        kpi2.metric("CCTV", len(df_mostrar)) # Aquí puedes poner tu propio filtro
        
        # Conteo rápido de proveedores si existen
        total_dcero = len(df_mostrar[df_mostrar['PROVEDDOR'].astype(str).str.contains('DCERO', case=False, na=False)])
        kpi3.metric("DCERO", total_dcero)
        
        total_secomp = len(df_mostrar[df_mostrar['PROVEDDOR'].astype(str).str.contains('SECOMP', case=False, na=False)])
        kpi4.metric("SECOMP", total_secomp)
        
        total_ejecucion = len(df_mostrar[df_mostrar['ESTADO_SN'] == 'En Proceso']) # Ajusta 'En Proceso' al estado real
        kpi5.metric("En ejecución", total_ejecucion)
        
        total_pendientes = len(df_mostrar[df_mostrar['ESTADO_SN'] != 'Cerrado'])
        kpi6.metric("Pendientes", total_pendientes)

        st.markdown("---")

        # --- FILA 3: GRÁFICOS SUPERIORES ---
        graf_sup1, graf_sup2, graf_sup3 = st.columns(3)
        
        with graf_sup1:
            st.markdown("**TOP 10 LOCALES (Remplazo Antigüedad)**")
            top_locales = df_mostrar['LOCAL'].value_counts().head(10).reset_index()
            top_locales.columns = ['Local', 'Cantidad']
            fig1 = px.bar(top_locales, x='Local', y='Cantidad', text_auto=True, color_discrete_sequence=['#008080'])
            fig1.update_layout(margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig1, use_container_width=True)

        with graf_sup2:
            st.markdown("**ESTADO DE ATENCIONES**")
            # Gráfico de dona usando el estado
            conteo_estados = df_mostrar['ESTADO_SN'].value_counts().reset_index()
            conteo_estados.columns = ['Estado', 'Cantidad']
            fig2 = px.pie(conteo_estados, values='Cantidad', names='Estado', hole=0.5)
            fig2.update_layout(margin=dict(l=20, r=20, t=30, b=20), showlegend=False)
            fig2.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig2, use_container_width=True)

        with graf_sup3:
            st.markdown("**GRUPO ASIGNADO (PROVEEDORES)**")
            conteo_prov = df_mostrar['PROVEDDOR'].value_counts().reset_index()
            conteo_prov.columns = ['Proveedor', 'Cantidad']
            fig3 = px.pie(conteo_prov, values='Cantidad', names='Proveedor')
            fig3.update_layout(margin=dict(l=20, r=20, t=30, b=20), showlegend=False)
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
