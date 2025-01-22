import sqlite3
import bcrypt
from datetime import datetime

CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    nombre TEXT NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cuentas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    creador_id INTEGER,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (creador_id) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS usuarios_cuentas (
    usuario_id INTEGER,
    cuenta_id INTEGER,
    rol TEXT CHECK(rol IN ('admin', 'usuario')) DEFAULT 'usuario',
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (cuenta_id) REFERENCES cuentas(id),
    PRIMARY KEY (usuario_id, cuenta_id)
);

CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cuenta_id INTEGER,
    nombre TEXT NOT NULL,
    presupuesto_mensual REAL,
    FOREIGN KEY (cuenta_id) REFERENCES cuentas(id)
);

CREATE TABLE IF NOT EXISTS gastos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cuenta_id INTEGER,
    categoria_id INTEGER,
    cantidad REAL NOT NULL,
    lugar TEXT,
    fecha DATE NOT NULL,
    usuario_id INTEGER,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cuenta_id) REFERENCES cuentas(id),
    FOREIGN KEY (categoria_id) REFERENCES categorias(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);
""" 