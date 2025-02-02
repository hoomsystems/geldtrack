import streamlit as st
import sqlite3
import pandas as pd
import bcrypt
from database import get_db_connection

# Al inicio del archivo, después de los imports
TRANSLATIONS = {
    'es': {
        'configuracion': '⚙️ Configuración',
        'gestion_usuarios': 'Gestión de Usuarios',
        'nuevo_usuario': 'Nuevo Usuario',
        'mi_cuenta': 'Mi Cuenta',
        'usuarios_registrados': '👥 Usuarios Registrados',
        'editar': '✏️ Editar',
        'eliminar': '🗑️ Eliminar',
        'editando_usuario': 'Editando usuario',
        'nombre': 'Nombre',
        'email': 'Email',
        'cambiar_password': 'Cambiar contraseña',
        'nueva_password': 'Nueva Contraseña',
        'confirmar_password': 'Confirmar Contraseña',
        'guardar': 'Guardar',
        'cancelar': 'Cancelar',
        'agregar_usuario': '➕ Agregar Nuevo Usuario',
        'acceso_cuentas': 'Acceso a Cuentas',
        'info_acceso': 'Selecciona las cuentas a las que tendrá acceso el usuario y su rol en cada una',
        'acceso_a': 'Acceso a',
        'rol': 'Rol',
        'rol_help': 'admin: control total, editor: puede agregar/editar gastos, viewer: solo puede ver',
        'no_cuentas': 'No hay cuentas disponibles',
        'crear_usuario': 'Crear Usuario',
        'campos_obligatorios': 'Todos los campos son obligatorios',
        'passwords_no_coinciden': 'Las contraseñas no coinciden',
        'password_corta': 'La contraseña debe tener al menos 6 caracteres',
        'seleccionar_cuenta': 'Debe seleccionar al menos una cuenta',
        'usuario': 'Usuario',
        'cambiar_mi_password': '🔐 Cambiar Mi Contraseña',
        'password_actual': 'Contraseña Actual',
        'complete_campos': 'Por favor complete todos los campos',
        'idiomas': 'Idiomas',
        'seleccionar_idioma': 'Seleccionar Idioma',
        'idioma_actual': 'Idioma actual',
        'espanol': 'Español',
        'ingles': 'Inglés',
        'aleman': 'Alemán',
        'idioma_cambiado': 'Idioma cambiado exitosamente',
        'usuario_eliminado': 'Usuario eliminado exitosamente',
        'error_eliminar': 'Error al eliminar usuario',
        'no_eliminar_propio': 'No puedes eliminar tu propio usuario',
        'email_registrado': 'El email ya está registrado por otro usuario',
        'usuario_actualizado': 'Usuario actualizado exitosamente',
        'error_actualizar': 'Error al actualizar usuario',
        'usuario_registrado': 'Usuario registrado exitosamente',
        'error_registrar': 'Error al registrar usuario'
    },
    'en': {
        'configuracion': '⚙️ Settings',
        'gestion_usuarios': 'User Management',
        'nuevo_usuario': 'New User',
        'mi_cuenta': 'My Account',
        'usuarios_registrados': '👥 Registered Users',
        'editar': '✏️ Edit',
        'eliminar': '🗑️ Delete',
        'editando_usuario': 'Editing user',
        'nombre': 'Name',
        'email': 'Email',
        'cambiar_password': 'Change password',
        'nueva_password': 'New Password',
        'confirmar_password': 'Confirm Password',
        'guardar': 'Save',
        'cancelar': 'Cancel',
        'agregar_usuario': '➕ Add New User',
        'acceso_cuentas': 'Account Access',
        'info_acceso': 'Select the accounts the user will have access to and their role',
        'acceso_a': 'Access to',
        'rol': 'Role',
        'rol_help': 'admin: full control, editor: can add/edit expenses, viewer: can only view',
        'no_cuentas': 'No accounts available',
        'crear_usuario': 'Create User',
        'campos_obligatorios': 'All fields are required',
        'passwords_no_coinciden': 'Passwords do not match',
        'password_corta': 'Password must be at least 6 characters long',
        'seleccionar_cuenta': 'You must select at least one account',
        'usuario': 'User',
        'cambiar_mi_password': '🔐 Change My Password',
        'password_actual': 'Current Password',
        'complete_campos': 'Please complete all fields',
        'idiomas': 'Languages',
        'seleccionar_idioma': 'Select Language',
        'idioma_actual': 'Current language',
        'espanol': 'Spanish',
        'ingles': 'English',
        'aleman': 'German',
        'idioma_cambiado': 'Language changed successfully',
        'usuario_eliminado': 'User successfully deleted',
        'error_eliminar': 'Error deleting user',
        'no_eliminar_propio': 'You cannot delete your own user',
        'email_registrado': 'Email is already registered by another user',
        'usuario_actualizado': 'User successfully updated',
        'error_actualizar': 'Error updating user',
        'usuario_registrado': 'User successfully registered',
        'error_registrar': 'Error registering user'
    },
    'de': {
        'configuracion': '⚙️ Einstellungen',
        'gestion_usuarios': 'Benutzerverwaltung',
        'nuevo_usuario': 'Neuer Benutzer',
        'mi_cuenta': 'Mein Konto',
        'usuarios_registrados': '👥 Registrierte Benutzer',
        'editar': '✏️ Bearbeiten',
        'eliminar': '🗑️ Löschen',
        'editando_usuario': 'Benutzer bearbeiten',
        'nombre': 'Name',
        'email': 'E-Mail',
        'cambiar_password': 'Passwort ändern',
        'nueva_password': 'Neues Passwort',
        'confirmar_password': 'Passwort bestätigen',
        'guardar': 'Speichern',
        'cancelar': 'Abbrechen',
        'agregar_usuario': '➕ Neuen Benutzer hinzufügen',
        'acceso_cuentas': 'Kontozugriff',
        'info_acceso': 'Wählen Sie die Konten aus, auf die der Benutzer Zugriff haben soll, und ihre Rolle',
        'acceso_a': 'Zugriff auf',
        'rol': 'Rolle',
        'rol_help': 'admin: volle Kontrolle, editor: kann Ausgaben hinzufügen/bearbeiten, viewer: kann nur ansehen',
        'no_cuentas': 'Keine Konten verfügbar',
        'crear_usuario': 'Benutzer erstellen',
        'campos_obligatorios': 'Alle Felder sind erforderlich',
        'passwords_no_coinciden': 'Passwörter stimmen nicht überein',
        'password_corta': 'Passwort muss mindestens 6 Zeichen lang sein',
        'seleccionar_cuenta': 'Sie müssen mindestens ein Konto auswählen',
        'usuario': 'Benutzer',
        'cambiar_mi_password': '🔐 Mein Passwort ändern',
        'password_actual': 'Aktuelles Passwort',
        'complete_campos': 'Bitte füllen Sie alle Felder aus',
        'idiomas': 'Sprachen',
        'seleccionar_idioma': 'Sprache auswählen',
        'idioma_actual': 'Aktuelle Sprache',
        'espanol': 'Spanisch',
        'ingles': 'Englisch',
        'aleman': 'Deutsch',
        'idioma_cambiado': 'Sprache erfolgreich geändert',
        'usuario_eliminado': 'Benutzer erfolgreich gelöscht',
        'error_eliminar': 'Fehler beim Löschen des Benutzers',
        'no_eliminar_propio': 'Sie können Ihren eigenen Benutzer nicht löschen',
        'email_registrado': 'E-Mail ist bereits von einem anderen Benutzer registriert',
        'usuario_actualizado': 'Benutzer erfolgreich aktualisiert',
        'error_actualizar': 'Fehler beim Aktualisieren des Benutzers',
        'usuario_registrado': 'Benutzer erfolgreich registriert',
        'error_registrar': 'Fehler beim Registrieren des Benutzers'
    }
}

def get_text(key):
    lang = st.session_state.get('language', 'es')
    return TRANSLATIONS[lang][key]

def get_todos_usuarios():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, nombre, email FROM usuarios ORDER BY nombre")
    usuarios = c.fetchall()
    conn.close()
    return usuarios

def eliminar_usuario(user_id):
    if user_id == st.session_state.user_id:
        return False, get_text('no_eliminar_propio')
    
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
        conn.commit()
        return True, get_text('usuario_eliminado')
    except Exception as e:
        return False, f"{get_text('error_eliminar')}: {str(e)}"
    finally:
        conn.close()

def actualizar_usuario(user_id, nombre, email, nueva_password=None):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT id FROM usuarios WHERE email = ? AND id != ?", (email, user_id))
        if c.fetchone():
            return False, get_text('email_registrado')
        
        if nueva_password:
            hashed = bcrypt.hashpw(nueva_password.encode('utf-8'), bcrypt.gensalt())
            c.execute(
                "UPDATE usuarios SET nombre = ?, email = ?, password = ? WHERE id = ?",
                (nombre, email, hashed, user_id)
            )
        else:
            c.execute(
                "UPDATE usuarios SET nombre = ?, email = ? WHERE id = ?",
                (nombre, email, user_id)
            )
        conn.commit()
        return True, get_text('usuario_actualizado')
    except Exception as e:
        return False, f"{get_text('error_actualizar')}: {str(e)}"
    finally:
        conn.close()

def get_todas_cuentas():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, nombre FROM cuentas ORDER BY nombre")
    cuentas = c.fetchall()
    conn.close()
    return cuentas

def registrar_usuario_con_cuentas(nombre, email, password, cuentas_acceso):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT 1 FROM usuarios WHERE email = ?", (email,))
        if c.fetchone():
            return False, get_text('email_registrado')
        
        # Crear usuario
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        c.execute(
            "INSERT INTO usuarios (nombre, email, password) VALUES (?, ?, ?)",
            (nombre, email, hashed)
        )
        usuario_id = c.lastrowid
        
        # Asignar accesos a cuentas
        for cuenta_id, rol in cuentas_acceso:
            if cuenta_id and rol:  # Solo si se seleccionó una cuenta y un rol
                c.execute(
                    "INSERT INTO usuarios_cuentas (usuario_id, cuenta_id, rol) VALUES (?, ?, ?)",
                    (usuario_id, cuenta_id, rol)
                )
        
        conn.commit()
        return True, get_text('usuario_registrado')
    except Exception as e:
        return False, f"{get_text('error_registrar')}: {str(e)}"
    finally:
        conn.close()

def get_nombre_idioma(codigo):
    nombres = {
        'es': 'Español',
        'en': 'English',
        'de': 'Deutsch'
    }
    return nombres.get(codigo, 'Español')

def mostrar_contenido_configuracion():
    st.title(get_text('configuracion'))
    
    tab1, tab2, tab3, tab4 = st.tabs([
        get_text('gestion_usuarios'),
        get_text('nuevo_usuario'),
        get_text('mi_cuenta'),
        get_text('idiomas')
    ])
    
    with tab1:
        st.header(get_text('usuarios_registrados'))
        usuarios = get_todos_usuarios()
        
        for user_id, nombre, email in usuarios:
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.write(f"**{nombre}**")
                st.write(f"_{email}_")
            
            with col2:
                if st.button(get_text('editar'), key=f"edit_{user_id}"):
                    st.session_state.usuario_editando = user_id
                    st.session_state.nombre_editando = nombre
                    st.session_state.email_editando = email
            
            with col3:
                if user_id != st.session_state.user_id:  # No permitir eliminar el propio usuario
                    if st.button(get_text('eliminar'), key=f"delete_{user_id}"):
                        exito, mensaje = eliminar_usuario(user_id)
                        if exito:
                            st.success(mensaje)
                            st.rerun()
                        else:
                            st.error(mensaje)
            
            # Mostrar formulario de edición si este es el usuario que se está editando
            if hasattr(st.session_state, 'usuario_editando') and st.session_state.usuario_editando == user_id:
                with st.expander(get_text('editando_usuario'), expanded=True):
                    st.write(f"{get_text('editando_usuario')}: **{nombre}**")
                    
                    nuevo_nombre = st.text_input(get_text('nombre'), value=nombre, key=f"name_{user_id}")
                    nuevo_email = st.text_input(get_text('email'), value=email, key=f"email_{user_id}")
                    
                    cambiar_pass = st.checkbox(get_text('cambiar_password'), key=f"check_pass_{user_id}")
                    
                    nueva_password = None
                    confirmar_password = None
                    
                    if cambiar_pass:
                        nueva_password = st.text_input(get_text('nueva_password'), type="password", key=f"new_pass_{user_id}")
                        confirmar_password = st.text_input(get_text('confirmar_password'), type="password", key=f"confirm_{user_id}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(get_text('guardar'), key=f"save_{user_id}"):
                            if not nuevo_nombre or not nuevo_email:
                                st.error(get_text('campos_obligatorios'))
                            elif cambiar_pass:
                                if not nueva_password:
                                    st.error(get_text('password_corta'))
                                elif nueva_password != confirmar_password:
                                    st.error(get_text('passwords_no_coinciden'))
                                elif len(nueva_password) < 6:
                                    st.error(get_text('password_corta'))
                                else:
                                    exito, mensaje = actualizar_usuario(user_id, nuevo_nombre, nuevo_email, nueva_password)
                                    if exito:
                                        st.success(mensaje)
                                        del st.session_state.usuario_editando
                                        st.rerun()
                                    else:
                                        st.error(mensaje)
                            else:
                                exito, mensaje = actualizar_usuario(user_id, nuevo_nombre, nuevo_email)
                                if exito:
                                    st.success(mensaje)
                                    del st.session_state.usuario_editando
                                    st.rerun()
                                else:
                                    st.error(mensaje)
                    
                    with col2:
                        if st.button(get_text('cancelar'), key=f"cancel_{user_id}"):
                            del st.session_state.usuario_editando
                            st.rerun()
            
            st.divider()
    
    with tab2:
        st.header(get_text('agregar_usuario'))
        with st.form(get_text('nuevo_usuario'), clear_on_submit=True):
            nuevo_nombre = st.text_input(get_text('nombre'))
            nuevo_email = st.text_input(get_text('email'))
            password = st.text_input(get_text('cambiar_password'), type="password")
            confirmar_password = st.text_input(get_text('confirmar_password'), type="password")
            
            st.subheader(get_text('acceso_cuentas'))
            st.info(get_text('info_acceso'))
            
            cuentas = get_todas_cuentas()
            cuentas_acceso = []
            
            if cuentas:
                for cuenta_id, nombre_cuenta in cuentas:
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        tiene_acceso = st.checkbox(f"{get_text('acceso_a')} {nombre_cuenta}", key=f"acceso_{cuenta_id}")
                    with col2:
                        rol = st.selectbox(
                            get_text('rol'),
                            options=['viewer', 'editor', 'admin'],
                            key=f"rol_{cuenta_id}",
                            help=get_text('rol_help')
                        )
                    if tiene_acceso:
                        cuentas_acceso.append((cuenta_id, rol))
            else:
                st.warning(get_text('no_cuentas'))
            
            if st.form_submit_button(get_text('crear_usuario')):
                if not nuevo_nombre or not nuevo_email or not password or not confirmar_password:
                    st.error(get_text('campos_obligatorios'))
                elif password != confirmar_password:
                    st.error(get_text('passwords_no_coinciden'))
                elif len(password) < 6:
                    st.error(get_text('password_corta'))
                elif not any(cuenta for cuenta in cuentas_acceso if cuenta):
                    st.error(get_text('seleccionar_cuenta'))
                else:
                    # Filtrar solo las cuentas seleccionadas
                    cuentas_seleccionadas = [cuenta for cuenta in cuentas_acceso if cuenta]
                    exito, mensaje = registrar_usuario_con_cuentas(
                        nuevo_nombre, 
                        nuevo_email, 
                        password,
                        cuentas_seleccionadas
                    )
                    if exito:
                        st.success(mensaje)
                        st.rerun()
                    else:
                        st.error(mensaje)
    
    with tab3:
        st.header(get_text('mi_cuenta'))
        st.info(f"""
        **{get_text('usuario')}**: {st.session_state.user_name}  
        **{get_text('email')}**: {st.session_state.user_email}
        """)
        
        st.header(get_text('cambiar_mi_password'))
        with st.form(get_text('cambiar_password'), clear_on_submit=True):
            password_actual = st.text_input(get_text('password_actual'), type="password")
            nueva_password = st.text_input(get_text('nueva_password'), type="password")
            confirmar_password = st.text_input(get_text('confirmar_password'), type="password")
            
            if st.form_submit_button(get_text('cambiar_password')):
                if not password_actual or not nueva_password or not confirmar_password:
                    st.error(get_text('complete_campos'))
                elif nueva_password != confirmar_password:
                    st.error(get_text('passwords_no_coinciden'))
                elif len(nueva_password) < 6:
                    st.error(get_text('password_corta'))
                else:
                    exito, mensaje = actualizar_usuario(
                        st.session_state.user_id,
                        st.session_state.user_name,
                        st.session_state.user_email,
                        nueva_password
                    )
                    if exito:
                        st.success(mensaje)
                    else:
                        st.error(mensaje)
    
    with tab4:
        st.header(get_text('idiomas'))
        
        # Mostrar idioma actual
        idioma_actual = st.session_state.get('language', 'es')
        st.info(f"**{get_text('idioma_actual')}:** {get_nombre_idioma(idioma_actual)}")
        
        # Selector de idioma
        idioma = st.selectbox(
            get_text('seleccionar_idioma'),
            options=['es', 'en', 'de'],
            format_func=lambda x: {
                'es': get_text('espanol'),
                'en': get_text('ingles'),
                'de': get_text('aleman')
            }[x],
            index=['es', 'en', 'de'].index(idioma_actual)
        )
        
        # Botón para cambiar idioma
        if st.button(get_text('guardar')):
            st.session_state.language = idioma
            st.success(get_text('idioma_cambiado'))
            st.rerun() 