import streamlit as st
from datetime import datetime, timedelta
import extra_streamlit_components as stx

def get_cookie_manager():
    return stx.CookieManager(key="cookies_manager")

def set_current_account(cuenta_id):
    st.session_state.cuenta_actual = cuenta_id
    cookie_manager = get_cookie_manager()
    expiry = datetime.now() + timedelta(days=30)
    cookie_manager.set('cuenta_actual', str(cuenta_id), expires_at=expiry)

def clear_session():
    # Limpiar cookies
    cookie_manager = get_cookie_manager()
    cookie_manager.delete('user_id')
    cookie_manager.delete('user_name')
    cookie_manager.delete('user_email')
    cookie_manager.delete('cuenta_actual')
    
    # Limpiar variables de sesión específicas
    keys_to_clear = [
        'user_id', 
        'user_name', 
        'user_email', 
        'is_authenticated',
        'cuenta_actual',
        'usuario_editando',
        'nombre_editando',
        'email_editando'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Forzar la limpieza completa
    st.session_state.clear() 