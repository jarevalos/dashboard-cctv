import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px

st.set_page_config(page_title="Dashboard CCTV", page_icon="📹", layout="wide")

st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; max-width: 95% !important; }
    h1 { font-size: 1.8rem !important; font-weight: 600 !important; color: #e0e0e0; margin-bottom: 1rem !important; }
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Panel de Control CCTV")

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

    # ==========================================
    # FILTRO MAESTRO DE DATOS (LIMPIEZA INICIAL)
    # ==========================================
    col_estado = 'ESTADO_SN'          
    col_atencion = 'ESTADO_ATENCION'  

    # 1. Limpiar y filtrar la columna N (ESTADO_SN)
    if col_estado in df.columns:
        df[col_estado] = df[col_estado].astype(str).str.strip() 
        estados_excluidos = ['CERRADO', 'CERRADO COMPLETO', 'RESUELTO', 'CERRADO INCOMPLETO', 'REVISAR']
        df = df[~df[col_estado].str.upper().isin(estados_excluidos)]
    
    # 2. Limpiar y filtrar la columna O (ESTADO_ATENCION)
    if col_atencion in df.columns:
        df[col_atencion] = df[col_atencion].astype(str).str.strip()
        df = df[df[col_atencion].str.upper() != 'OTRO SERVICIO']

    return df

def crear_tarjeta(titulo, valor, color_borde):
    html = f"""
    <div style="background-color: #262730; padding: 15px 20px; border-radius: 8px; border-left: 5px solid {color_borde}; box-shadow: 2px 2px 5px rgba(0,0,0,0.2); margin-bottom: 10px;">
        <p style="margin: 0; font-size: 0.85rem; color: #a5a5a5; font-weight: 600; text-transform: uppercase;">{titulo}</p>
        <h2 style="margin: 0; font-size: 2rem; color: #ffffff; font-weight: 700;">{valor}</h2>
    </div>
    """
    return html

try:
    df = cargar_datos()
    
    tab1, tab2 = st.tabs(["📊 Panel General", "🏢 Análisis por Local"])
    
    with tab1:
        df_mostrar = df.copy()

        # ==========================================
        # CÁLCULO DE KPIs EXACTOS
        # ==========================================
        # 1. Casos Abiertos: "Asignado", "En espera" y "En Progreso"
        if 'ESTADO_SN' in df_mostrar.columns:
            estados_backlog = ['ASIGNADO', 'EN ESPERA', 'EN PROGRESO']
            t_abiertos = len(df_mostrar[df_mostrar['ESTADO_SN'].str.upper().isin(estados_backlog)])
        else:
            t_abiertos = 0

        t_cctv = len(df_mostrar) 
        t_dcero = len(df_mostrar[df_mostrar['PROVEDDOR'].astype(str).str.contains('DCERO', case=False, na=False)]) if 'PROVEDDOR' in df_mostrar.columns else 0
        t_secomp = len(df_mostrar[df_mostrar['PROVEDDOR'].astype(str).str.contains('SECOMP', case=False, na=False)]) if 'PROVEDDOR' in df_mostrar.columns else 0
        
        t_ejecucion = len(df_mostrar[df_mostrar['ESTADO_SN'].str.upper() == 'EN PROCESO']) if 'ESTADO_SN' in df_mostrar.columns else 0
        
        t_sin_estado = len(df_mostrar[df_mostrar['ESTADO_SN'] == '']) if 'ESTADO_SN' in df_mostrar.columns else 0

        # --- DIBUJAR LAS TARJETAS ---
        kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
        
        with kpi1: st.markdown(crear_tarjeta("Casos Abiertos", t_abiertos, "#008080"), unsafe_allow_html=True)
        with kpi2: st.markdown(crear_tarjeta("CCTV", t_cctv, "#4682B4"), unsafe_allow_html=True)
        with kpi3: st.markdown(crear_tarjeta("DCERO", t_dcero, "#FF8C00"), unsafe_allow_html=True)
        with kpi4: st.markdown(crear_tarjeta("SECOMP", t_secomp, "#9370DB"), unsafe_allow_html=True)
        with kpi5: st.markdown(crear_tarjeta("En ejecución", t_ejecucion, "#32CD32"), unsafe_allow_html=True)
        with kpi6: st.markdown(crear_tarjeta("Sin Estado", t_sin_estado, "#DC143C"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- GRÁFICOS ---
        graf_sup1, graf_sup2, graf_sup3 = st.columns(3)
        layout_transparente = dict(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#e0e0e0', height=280, margin=dict(l=10, r=10, t=30, b=10))
        
        with graf_sup1:
            if 'LOCAL' in df_mostrar.columns:
                top_locales = df_mostrar['LOCAL'].value_counts().head(10).reset_index()
                top_locales.columns = ['Local', 'Cantidad']
                fig1 = px.bar(top_locales, x='Local', y='Cantidad', title="<b>TOP 10 LOCALES CRÍTICOS</b>", text_auto=True, color_discrete_sequence=['#008080'])
                fig1.update_layout(**layout_transparente)
                fig1.update_yaxes(showgrid=False, visible=False)
                st.plotly_chart(fig1, use_container_width=True)

        with graf_sup2:
            if 'ESTADO_SN' in df_mostrar.columns:
                conteo_estados = df_mostrar['ESTADO_SN'].value_counts().reset_index()
                conteo_estados.columns = ['Estado', 'Cantidad']
                fig2 = px.pie(conteo_estados, values='Cantidad', names='Estado', title="<b>ESTADO (SOLO ABIERTOS)</b>", hole=0.6, color_discrete_sequence=px.colors.sequential.Teal)
                fig2.update_layout(**layout_transparente, showlegend=False)
                fig2.update_traces(textposition='inside', textinfo='percent+label', textfont_size=12)
                st.plotly_chart(fig2, use_container_width=True)

        with graf_sup3:
            if 'PROVEDDOR' in df_mostrar.columns:
                conteo_prov = df_mostrar['PROVEDDOR'].value_counts().reset_index()
                conteo_prov.columns = ['Proveedor', 'Cantidad']
                fig3 = px.pie(conteo_prov, values='Cantidad', names='Proveedor', title="<b>ASIGNACIÓN ACTUAL</b>", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig3.update_layout(**layout_transparente, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
                fig3.update_traces(textposition='inside', textinfo='percent')
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
