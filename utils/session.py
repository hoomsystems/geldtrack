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
    # Primero limpiar el state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # Luego limpiar cookies
    cookie_manager = get_cookie_manager()
    all_cookies = cookie_manager.get_all()
    for cookie_name in all_cookies:
        cookie_manager.delete(cookie_name)
    
    # Forzar rerun
    st.rerun() 