import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
from datetime import datetime

# 1. Configuración de la página
st.set_page_config(page_title="Dashboard CCTV", page_icon="📹", layout="wide")

# ==========================================
# CSS DISEÑO DE ALTO NIVEL (COMPACTO)
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FB !important; }
    .block-container { padding-top: 0rem !important; padding-bottom: 0rem !important; max-width: 95% !important; }
    
    .card-container {
        background-color: white;
        padding: 12px 10px;
        border-radius: 10px;
        border-bottom: 4px solid #E0E4E8;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        text-align: center;
        margin-bottom: 10px;
    }
    .card-label { margin: 0; font-size: 0.65rem !important; color: #7F8C8D; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; }
    .card-value { margin: 0; font-size: 1.6rem !important; color: #2C3E50; font-weight: 800; line-height: 1.1; }

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

    # --- LIMPIEZA INICIAL ---
    df['ESTADO_SN'] = df['ESTADO_SN'].astype(str).str.strip().upper()
    df['ESTADO_ATENCION'] = df['ESTADO_ATENCION'].astype(str).str.strip().upper()

    # --- FILTRO MAESTRO (REGLAS KOKE) ---
    # 1. Columna N: Solo Asignado, En Progreso, En Espera
    estados_validos = ['ASIGNADO', 'EN PROGRESO', 'EN ESPERA']
    df_filtrado = df[df['ESTADO_SN'].isin(estados_validos)].copy()
    
    # 2. Columna O: Excluir DUPLICADO y OTRO SERVICIO
    excluir_atencion = ['DUPLICADO', 'OTRO SERVICIO']
    df_filtrado = df_filtrado[~df_filtrado['ESTADO_ATENCION'].isin(excluir_atencion)]

    return df_filtrado

def crear_tarjeta_pro(titulo, valor, color_top):
    html = f"""
    <div class="card-container" style="border-top: 4px solid {color_top};">
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
        df['GRUPO_ASIGNADO'] = df['GRUPO_ASIGNADO'].astype(str).str.strip()
        t_cctv = len(df[df['GRUPO_ASIGNADO'] == 'Soporte Circuito Cerrado de Televisin (CCTV)'])
        t_dcero = len(df[df['GRUPO_ASIGNADO'] == 'Soporte Dcero'])
        t_secomp = len(df[df['GRUPO_ASIGNADO'] == 'Soporte Secomp'])
        t_en_ejecucion = t_dcero + t_secomp
        
        # Pendientes (Columna S vacía)
        t_pendientes = len(df[df['PROVEDDOR'].astype(str).str.strip().isin(['', 'nan', 'None'])])

        # --- FILA DE TARJETAS ---
        kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
        with kpi1: st.markdown(crear_tarjeta_pro("Casos Abiertos", t_total_abiertos, "#E74C3C"), unsafe_allow_html=True) 
        with kpi2: st.markdown(crear_tarjeta_pro("Soporte CCTV", t_cctv, "#2980B9"), unsafe_allow_html=True) 
        with kpi3: st.markdown(crear_tarjeta_pro("Soporte Dcero", t_dcero, "#3498DB"), unsafe_allow_html=True) 
        with kpi4: st.markdown(crear_tarjeta_pro("Soporte Secomp", t_secomp, "#5DADE2"), unsafe_allow_html=True) 
        with kpi5: st.markdown(crear_tarjeta_pro("En Ejecución", t_en_ejecucion, "#E67E22"), unsafe_allow_html=True)
        with kpi6: st.markdown(crear_tarjeta_pro("Pendientes", t_pendientes, "#34495E"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ==========================================
        # GRÁFICO 1: ANTIGÜEDAD DEL REPORTE
        # ==========================================
        st.subheader("⏱️ Antigüedad de Reportes Abiertos")
        
        if 'FECHA' in df.columns: # Asumiendo que la columna J se llama FECHA
            # 1. Convertir Columna J a Datetime (formato 28-02-2026 8:22)
            df['FECHA_DT'] = pd.to_datetime(df['FECHA'], dayfirst=True, errors='coerce')
            
            # 2. Calcular días de diferencia con hoy
            hoy = datetime.now()
            df['Dias_Abierto'] = (hoy - df['FECHA_DT']).dt.days
            
            # 3. Agrupar para el gráfico
            antiguedad_df = df['Dias_Abierto'].value_counts().reset_index()
            antiguedad_df.columns = ['Días', 'Cantidad de Reportes']
            antiguedad_df = antiguedad_df.sort_values(by='Días')

            # 4. Crear gráfico de barras
            fig_ant = px.bar(
                antiguedad_df, 
                x='Días', 
                y='Cantidad de Reportes',
                text_auto=True,
                color_discrete_sequence=['#2980B9']
            )
            
            fig_ant.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=30, b=0),
                height=350,
                xaxis_title="Días transcurridos desde el reporte",
                yaxis_title="N° de Reportes"
            )
            
            st.plotly_chart(fig_ant, use_container_width=True)
        else:
            st.warning("No se encontró la columna de fecha (Columna J). Revisa el nombre en el Excel.")

    with tab2:
        st.header("Análisis por Local")
        if 'LOCAL' in df.columns:
            lista_locales = df['LOCAL'].unique()
            local_seleccionado = st.selectbox("🏢 Selecciona un Local:", lista_locales)
            datos_local = df[df['LOCAL'] == local_seleccionado]
            columnas_mostrar = [c for c in ['REPORTE', 'TIENDA', 'ESTADO_SN', 'PROVEDDOR', 'COMENTARIO'] if c in df.columns]
            st.dataframe(datos_local[columnas_mostrar], use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error en la aplicación: {e}")
