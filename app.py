import streamlit as st
import sqlite3
import bcrypt
import pandas as pd
from datetime import datetime, date, timedelta
import extra_streamlit_components as stx
from database import initialize_db as init_db, get_db_connection
from components.sidebar import show_sidebar, apply_custom_css
from translations import get_text
from utils.session import get_cookie_manager, clear_session, set_current_account
import plotly.express as px

def registrar_usuario(nombre, email, password):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        c.execute(
            "INSERT INTO usuarios (nombre, email, password) VALUES (?, ?, ?)",
            (nombre, email, hashed)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def verificar_usuario(email, password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, password, nombre, email FROM usuarios WHERE email = ?", (email,))
    resultado = c.fetchone()
    conn.close()
    
    if resultado and bcrypt.checkpw(password.encode('utf-8'), resultado[1]):
        return resultado[0], resultado[2], resultado[3]

def save_session(user_id, nombre, email, remember=False):
    st.session_state.clear()  # Limpiar sesión anterior
    st.session_state.user_id = user_id
    st.session_state.user_name = nombre
    st.session_state.user_email = email
    st.session_state.is_authenticated = True
    st.session_state.cuenta_actual = None
    
    if remember:
        cookie_manager = get_cookie_manager()
        expiry = datetime.now() + timedelta(days=30)
        
        cookie_manager.set('user_id', str(user_id), expires_at=expiry)
        cookie_manager.set('user_name', nombre, expires_at=expiry)
        cookie_manager.set('user_email', email, expires_at=expiry)

def check_saved_session():
    # Si ya está autenticado, no hacer nada
    if st.session_state.get('is_authenticated', False):
        return
    
    # Intentar restaurar desde cookies
    cookie_manager = get_cookie_manager()
    user_id = cookie_manager.get('user_id')
    
    if user_id:
        try:
            user_id = int(user_id)
            nombre = cookie_manager.get('user_name')
            email = cookie_manager.get('user_email')
            
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT id FROM usuarios WHERE id = ?", (user_id,))
            
            if c.fetchone():
                st.session_state.user_id = user_id
                st.session_state.user_name = nombre
                st.session_state.user_email = email
                st.session_state.is_authenticated = True
                st.session_state.cuenta_actual = None
                
                # Restaurar cuenta actual
                cuenta_id = cookie_manager.get('cuenta_actual')
                if cuenta_id:
                    st.session_state.cuenta_actual = int(cuenta_id)
            conn.close()
        except Exception as e:
            print(f"Error restaurando sesión: {e}")
            clear_session()

def show_login():
    st.title(get_text('bienvenido'))
    
    tab1, tab2 = st.tabs([get_text('iniciar_sesion'), get_text('registrarse')])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input(get_text('email'))
            password = st.text_input(get_text('password'), type="password")
            remember = st.checkbox(get_text('mantener_sesion'))
            
            if st.form_submit_button(get_text('iniciar_sesion')):
                if email and password:
                    resultado = verificar_usuario(email, password)
                    if resultado:
                        user_id, nombre, email = resultado
                        save_session(user_id, nombre, email, remember)
                        st.rerun()
                    else:
                        st.error(get_text('error_credenciales'))
                else:
                    st.error(get_text('campos_requeridos'))
    
    with tab2:
        with st.form("registro_form"):
            nuevo_nombre = st.text_input("Nombre")
            nuevo_email = st.text_input("Email")
            nueva_password = st.text_input("Contraseña", type="password")
            confirmar_password = st.text_input("Confirmar Contraseña", type="password")
            submitted = st.form_submit_button("Registrarse")
            
            if submitted:
                if not nuevo_nombre or not nuevo_email or not nueva_password:
                    st.error("Todos los campos son obligatorios")
                elif nueva_password != confirmar_password:
                    st.error("Las contraseñas no coinciden")
                else:
                    if registrar_usuario(nuevo_nombre, nuevo_email, nueva_password):
                        st.success("Usuario registrado exitosamente. Por favor inicia sesión.")
                    else:
                        st.error("El email ya está registrado")

def show_account_selector():
    # Ocultar el texto inicial con CSS
    st.markdown("""
        <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.sidebar.title(f"👋 Hola, {st.session_state.user_name}")
    
    # Obtener cuentas del usuario
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT c.id, c.nombre 
        FROM cuentas c
        JOIN usuarios_cuentas uc ON c.id = uc.cuenta_id
        WHERE uc.usuario_id = ?
    """, (st.session_state.user_id,))
    cuentas = c.fetchall()
    conn.close()
    
    # Crear diccionario de cuentas
    cuentas_dict = {cuenta[1]: cuenta[0] for cuenta in cuentas}
    cuentas_dict["+ Crear Nueva Cuenta"] = -1
    
    # Selector de cuenta
    cuenta_seleccionada = st.sidebar.selectbox(
        "📊 Seleccionar Cuenta",
        options=list(cuentas_dict.keys()),
        key="selector_cuenta_main"
    )
    
    if cuenta_seleccionada == "+ Crear Nueva Cuenta":
        with st.sidebar.form("nueva_cuenta"):
            nombre_cuenta = st.text_input("Nombre de la nueva cuenta")
            if st.form_submit_button("Crear Cuenta"):
                if nombre_cuenta:
                    conn = get_db_connection()
                    c = conn.cursor()
                    c.execute(
                        "INSERT INTO cuentas (nombre, creador_id) VALUES (?, ?)",
                        (nombre_cuenta, st.session_state.user_id)
                    )
                    cuenta_id = c.lastrowid
                    c.execute(
                        "INSERT INTO usuarios_cuentas (usuario_id, cuenta_id, rol) VALUES (?, ?, ?)",
                        (st.session_state.user_id, cuenta_id, 'admin')
                    )
                    conn.commit()
                    conn.close()
                    st.rerun()
    else:
        st.session_state.cuenta_actual = cuentas_dict[cuenta_seleccionada]

def show_main_menu():
    if 'cuenta_actual' not in st.session_state:
        st.session_state.cuenta_actual = None
        
    opcion = show_sidebar("main")
    
    if opcion == "App":
        show_main_dashboard()
    elif opcion == "Gastos":
        from pages.gastos import mostrar_contenido_gastos
        mostrar_contenido_gastos()
    elif opcion == "Categorías":
        from pages.categorias import mostrar_contenido_categorias
        mostrar_contenido_categorias()
    elif opcion == "Análisis":
        from pages.analisis import mostrar_contenido_analisis
        mostrar_contenido_analisis()
    elif opcion == "Configuración":
        from pages.configuracion import mostrar_contenido_configuracion
        mostrar_contenido_configuracion()

def show_main_dashboard():
    if not st.session_state.get('cuenta_actual'):
        st.warning(get_text('seleccione_cuenta_dashboard'))
        return
    
    # Obtener datos generales
    conn = get_db_connection()
    
    # Total gastado este mes
    total_mes = pd.read_sql_query("""
        SELECT COALESCE(SUM(cantidad), 0) as total
        FROM gastos 
        WHERE cuenta_id = ? 
        AND strftime('%Y-%m', fecha) = ?
    """, conn, params=(st.session_state.cuenta_actual, datetime.now().strftime('%Y-%m'))).iloc[0]['total']
    
    # Total gastado mes anterior
    total_mes_anterior = pd.read_sql_query("""
        SELECT COALESCE(SUM(cantidad), 0) as total
        FROM gastos 
        WHERE cuenta_id = ? 
        AND strftime('%Y-%m', fecha) = ?
    """, conn, params=(st.session_state.cuenta_actual, (datetime.now() - timedelta(days=30)).strftime('%Y-%m'))).iloc[0]['total']
    
    # Presupuesto total
    presupuesto_total = pd.read_sql_query("""
        SELECT COALESCE(SUM(presupuesto_mensual), 0) as total
        FROM categorias
        WHERE cuenta_id = ?
    """, conn, params=(st.session_state.cuenta_actual,)).iloc[0]['total']
    
    # Últimos 10 gastos (sin filtro de mes)
    ultimos_gastos = pd.read_sql_query("""
        SELECT 
            strftime('%d/%m/%Y', g.fecha) as fecha,
            g.cantidad,
            g.lugar,
            c.nombre as categoria,
            g.notas
        FROM gastos g
        JOIN categorias c ON g.categoria_id = c.id
        WHERE g.cuenta_id = ?
        ORDER BY g.fecha DESC, g.id DESC
        LIMIT 10
    """, conn, params=(st.session_state.cuenta_actual,))
    
    conn.close()
    
    # Mostrar información en el dashboard
    st.title("Dashboard")
    
    # Métricas principales
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            get_text('total_mes'),
            f"${total_mes:,.2f}",
            f"{((total_mes - total_mes_anterior) / total_mes_anterior * 100):,.1f}% {get_text('vs_mes_anterior')}" if total_mes_anterior > 0 else "N/A"
        )
    
    with col2:
        porcentaje_presupuesto = (total_mes / presupuesto_total * 100) if presupuesto_total > 0 else 0
        st.metric(
            get_text('presupuesto_mensual'),
            f"${presupuesto_total:,.2f}",
            f"{get_text('usado')}: {porcentaje_presupuesto:.1f}%"
        )
    
    with col3:
        dias_restantes = (date(datetime.now().year, datetime.now().month + 1 if datetime.now().month < 12 else 1, 1) - date(datetime.now().year, datetime.now().month, datetime.now().day)).days
        gasto_diario = total_mes / datetime.now().day if datetime.now().day > 0 else 0
        st.metric(
            get_text('promedio_diario'),
            f"${gasto_diario:,.2f}",
            f"{dias_restantes} {get_text('dias_restantes')}"
        )
    
    # Últimos gastos
    st.subheader(get_text('ultimos_gastos'))
    if not ultimos_gastos.empty:
        # Contenedor más estrecho para los gastos
        with st.container():
            for _, gasto in ultimos_gastos.iterrows():
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                with col1:
                    st.write(f"**{gasto['lugar']}** - {gasto['categoria']}")
                with col2:
                    if pd.notna(gasto['notas']):
                        st.write(f"💭 {gasto['notas']}")
                    else:
                        st.write("")
                with col3:
                    st.write(f"💰 ${gasto['cantidad']:,.2f}")
                with col4:
                    st.write(f"📅 {gasto['fecha']}")
                st.markdown("<hr style='margin: 3px 0;'>", unsafe_allow_html=True)
    else:
        st.info(get_text('no_hay_gastos'))

def main():
    # Inicialización básica
    if 'language' not in st.session_state:
        st.session_state.language = 'es'
    
    # Asegurar que las variables de sesión existan
    if 'is_authenticated' not in st.session_state:
        st.session_state.is_authenticated = False
    
    if 'cuenta_actual' not in st.session_state:
        st.session_state.cuenta_actual = None
    
    apply_custom_css()
    check_saved_session()
    
    # Mostrar la interfaz apropiada
    if not st.session_state.get('is_authenticated', False):
        show_login()
    else:
        show_main_menu()

if __name__ == "__main__":
    st.set_page_config(
        page_title="Sistema de Finanzas Personales",
        page_icon="💰",
        layout="wide"
    )
    init_db()
    main()