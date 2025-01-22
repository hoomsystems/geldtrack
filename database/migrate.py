import sqlite3

def migrate_database():
    conn = sqlite3.connect('finanzas.db')
    c = conn.cursor()
    
    try:
        # Verificar si la columna existe
        c.execute("SELECT notas FROM gastos LIMIT 1")
    except sqlite3.OperationalError:
        # La columna no existe, agregarla
        print("Agregando columna 'notas' a la tabla gastos...")
        c.execute("ALTER TABLE gastos ADD COLUMN notas TEXT")
        conn.commit()
        print("Migración completada exitosamente")
    
    conn.close()

if __name__ == "__main__":
    migrate_database() 