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
    with st.sidebar:
        st.write(f"{get_text('hola')}, {st.session_state.user_name}!")
        
        # Selector de cuenta
        st.subheader(get_text('seleccionar_cuenta'))
        
        # Obtener cuentas del usuario
        conn = sqlite3.connect('finanzas.db')
        c = conn.cursor()
        c.execute("""
            SELECT c.id, c.nombre 
            FROM cuentas c
            JOIN usuarios_cuentas uc ON c.id = uc.cuenta_id
            WHERE uc.usuario_id = ?
        """, (st.session_state.user_id,))
        cuentas = c.fetchall()
        conn.close()
        
        # Crear lista de opciones
        opciones = ["-- Seleccione una cuenta --"] + [cuenta[1] for cuenta in cuentas]
        cuenta_index = 0
        
        # Si hay una cuenta actual, seleccionarla
        if 'cuenta_actual' in st.session_state:
            for i, cuenta in enumerate(cuentas):
                if cuenta[0] == st.session_state.cuenta_actual:
                    cuenta_index = i + 1
                    break
        
        cuenta_seleccionada = st.selectbox(
            get_text('cuenta'),
            opciones,
            index=cuenta_index
        )
        
        if cuenta_seleccionada != "-- Seleccione una cuenta --":
            cuenta_id = next(cuenta[0] for cuenta in cuentas if cuenta[1] == cuenta_seleccionada)
            if cuenta_id != st.session_state.get('cuenta_actual'):
                set_current_account(cuenta_id)
                st.rerun()
    
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