import streamlit as st
import sqlite3
from translations import get_text
from utils.session import set_current_account, clear_session

def get_cuentas_usuario(user_id):
    conn = sqlite3.connect('finanzas.db')
    c = conn.cursor()
    c.execute("""
        SELECT c.id, c.nombre 
        FROM cuentas c
        JOIN usuarios_cuentas uc ON c.id = uc.cuenta_id
        WHERE uc.usuario_id = ?
        ORDER BY c.nombre
    """, (user_id,))
    cuentas = c.fetchall()
    conn.close()
    return cuentas

def crear_cuenta(nombre, user_id):
    conn = sqlite3.connect('finanzas.db')
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO cuentas (nombre, creador_id) VALUES (?, ?)",
            (nombre, user_id)
        )
        cuenta_id = c.lastrowid
        c.execute(
            "INSERT INTO usuarios_cuentas (usuario_id, cuenta_id, rol) VALUES (?, ?, ?)",
            (user_id, cuenta_id, 'admin')
        )
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()

def apply_custom_css():
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        section[data-testid="stSidebar"] div.block-container {margin-top: 0;}
        section[data-testid="stSidebar"] div:has(>.streamlit-expanderHeader) {display: none;}
        section[data-testid="stSidebar"] button[kind="header"] {display: none;}
        section[data-testid="stSidebar"] div[data-testid="stSidebarNav"] {display: none;}
        header[data-testid="stHeader"] {display: none;}
        div[data-testid="collapsedControl"] {display: none;}
        </style>
    """, unsafe_allow_html=True)

def show_sidebar(active_page=""):
    apply_custom_css()
    
    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        return None
        
    st.sidebar.title(f"{get_text('hola')}, {st.session_state.user_name}")
    st.sidebar.divider()
    
    # Menú principal
    st.sidebar.markdown(get_text('menu_principal'))
    
    opciones = {
        get_text('inicio'): "App",
        get_text('gastos'): "Gastos",
        get_text('categorias'): "Categorías",
        get_text('analisis'): "Análisis",
        get_text('configuracion'): "Configuración"
    }
    
    opcion = st.sidebar.radio("", list(opciones.keys()), label_visibility="collapsed")
    
    # Botón de cerrar sesión
    st.sidebar.divider()
    if st.sidebar.button(get_text('cerrar_sesion')):
        clear_session()
        st.rerun()
    
    return opciones[opcion] 