import sqlite3
from datetime import datetime

def get_db_connection():
    conn = sqlite3.connect('finanzas.db')
    conn.row_factory = sqlite3.Row
    return conn

def initialize_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Crear tablas si no existen
    c.executescript('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS cuentas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            creador_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (creador_id) REFERENCES usuarios (id)
        );
        
        CREATE TABLE IF NOT EXISTS usuarios_cuentas (
            usuario_id INTEGER NOT NULL,
            cuenta_id INTEGER NOT NULL,
            rol TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (usuario_id, cuenta_id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
            FOREIGN KEY (cuenta_id) REFERENCES cuentas (id)
        );
        
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            cuenta_id INTEGER NOT NULL,
            presupuesto_mensual REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cuenta_id) REFERENCES cuentas (id)
        );
        
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cuenta_id INTEGER NOT NULL,
            categoria_id INTEGER NOT NULL,
            cantidad REAL NOT NULL,
            lugar TEXT NOT NULL,
            fecha DATE NOT NULL,
            usuario_id INTEGER NOT NULL,
            notas TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cuenta_id) REFERENCES cuentas (id),
            FOREIGN KEY (categoria_id) REFERENCES categorias (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        );
    ''')
    
    conn.commit()
    conn.close()

def get_user_by_email(email):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()
    conn.close()
    return user

def create_user(nombre, email, password_hash):
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO usuarios (nombre, email, password) VALUES (?, ?, ?)',
            (nombre, email, password_hash)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user_accounts(user_id):
    conn = get_db_connection()
    accounts = conn.execute('''
        SELECT c.* 
        FROM cuentas c
        JOIN usuarios_cuentas uc ON c.id = uc.cuenta_id
        WHERE uc.usuario_id = ?
        ORDER BY c.nombre
    ''', (user_id,)).fetchall()
    conn.close()
    return accounts

def create_account(nombre, user_id):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('INSERT INTO cuentas (nombre, creador_id) VALUES (?, ?)', (nombre, user_id))
        cuenta_id = c.lastrowid
        c.execute(
            'INSERT INTO usuarios_cuentas (usuario_id, cuenta_id, rol) VALUES (?, ?, ?)',
            (user_id, cuenta_id, 'admin')
        )
        conn.commit()
        return cuenta_id
    except:
        conn.rollback()
        return None
    finally:
        conn.close()

# Renombrar init_db a initialize_db
init_db = initialize_db