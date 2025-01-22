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
    cookie_manager = get_cookie_manager()
    cookie_manager.delete('user_id')
    cookie_manager.delete('user_name')
    cookie_manager.delete('user_email')
    cookie_manager.delete('cuenta_actual')
    st.session_state.clear() 