import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from components.sidebar import show_sidebar
from translations import get_text
import calendar
import time

def get_categorias(cuenta_id):
    conn = sqlite3.connect('finanzas.db')
    query = "SELECT id, nombre FROM categorias WHERE cuenta_id = ? ORDER BY nombre"
    df = pd.read_sql_query(query, conn, params=(cuenta_id,))
    conn.close()
    return df

def get_usuarios_cuenta(cuenta_id):
    conn = sqlite3.connect('finanzas.db')
    query = """
    SELECT u.id, u.nombre 
    FROM usuarios u
    JOIN usuarios_cuentas uc ON u.id = uc.usuario_id
    WHERE uc.cuenta_id = ?
    """
    df = pd.read_sql_query(query, conn, params=(cuenta_id,))
    conn.close()
    return df

def registrar_gasto(cuenta_id, categoria_id, cantidad, lugar, fecha, usuario_id, notas):
    conn = sqlite3.connect('finanzas.db')
    c = conn.cursor()
    try:
        # Imprimir valores para debug
        print(f"Insertando gasto: {cuenta_id}, {categoria_id}, {cantidad}, {lugar}, {fecha}, {usuario_id}, {notas}")
        
        c.execute("""
            INSERT INTO gastos 
                (cuenta_id, categoria_id, cantidad, lugar, fecha, usuario_id, notas)
            VALUES 
                (?, ?, ?, ?, ?, ?, ?)
        """, (
            cuenta_id,
            int(categoria_id),  # Asegurar que sea entero
            float(cantidad),    # Asegurar que sea float
            str(lugar),        # Asegurar que sea string
            fecha.strftime('%Y-%m-%d'),  # Formatear fecha correctamente
            int(usuario_id),   # Asegurar que sea entero
            str(notas) if notas else None  # Manejar notas vacías
        ))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error SQL: {e}")  # Debug
        return False
    except Exception as e:
        print(f"Error general: {e}")  # Debug
        return False
    finally:
        conn.close()

def get_gastos_recientes(cuenta_id, mes=None, anio=None):
    conn = sqlite3.connect('finanzas.db')
    
    query = """
    SELECT g.id, g.cantidad, g.lugar, g.fecha, c.nombre as categoria, 
           u.nombre as usuario, g.notas
    FROM gastos g
    JOIN categorias c ON g.categoria_id = c.id
    JOIN usuarios u ON g.usuario_id = u.id
    WHERE g.cuenta_id = ?
    """
    
    params = [cuenta_id]
    
    if mes and anio:
        query += " AND strftime('%m-%Y', g.fecha) = ?"
        params.append(f"{mes:02d}-{anio}")
    elif anio:
        query += " AND strftime('%Y', g.fecha) = ?"
        params.append(str(anio))
        
    query += " ORDER BY g.fecha DESC"
    
    df = pd.read_sql_query(query, conn, params=tuple(params))
    conn.close()
    return df

def importar_gastos_desde_csv(cuenta_id, archivo_csv):
    try:
        # Leer el CSV
        df = pd.read_csv(archivo_csv)
        
        conn = sqlite3.connect('finanzas.db')
        c = conn.cursor()
        
        # Obtener gastos existentes para verificar duplicados
        c.execute("""
            SELECT fecha, lugar, cantidad 
            FROM gastos 
            WHERE cuenta_id = ?
        """, (cuenta_id,))
        gastos_existentes = set(map(lambda x: (x[0], x[1].lower(), float(x[2])), c.fetchall()))
        
        # Mapeo de categorías existentes
        c.execute("SELECT id, nombre FROM categorias WHERE cuenta_id = ?", (cuenta_id,))
        categorias = dict(c.fetchall())
        categorias_inv = {v.lower(): k for k, v in categorias.items()}
        
        gastos_importados = 0
        errores = 0
        duplicados = 0
        
        for _, row in df.iterrows():
            try:
                # Convertir fecha del formato DD/MM/YY a YYYY-MM-DD
                fecha = datetime.strptime(row['date'], '%d/%m/%y').strftime('%Y-%m-%d')
                
                # Verificar si el gasto ya existe
                gasto_key = (fecha, row['store'].lower(), float(row['amount']))
                if gasto_key in gastos_existentes:
                    duplicados += 1
                    continue
                
                # Buscar la categoría
                categoria_id = categorias_inv.get(row['category'].lower())
                if not categoria_id:
                    c.execute(
                        "INSERT INTO categorias (nombre, cuenta_id) VALUES (?, ?)",
                        (row['category'], cuenta_id)
                    )
                    categoria_id = c.lastrowid
                    categorias_inv[row['category'].lower()] = categoria_id
                
                # Insertar el gasto
                c.execute("""
                    INSERT INTO gastos 
                    (cuenta_id, categoria_id, cantidad, lugar, fecha, usuario_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    cuenta_id,
                    categoria_id,
                    float(row['amount']),
                    row['store'],
                    fecha,
                    st.session_state.user_id
                ))
                gastos_importados += 1
                
            except Exception as e:
                errores += 1
                st.error(f"Error en fila {gastos_importados + errores + duplicados}: {str(e)}")
                continue
        
        conn.commit()
        conn.close()
        
        mensaje = f"Se importaron {gastos_importados} gastos nuevos."
        if duplicados > 0:
            mensaje += f" Se omitieron {duplicados} gastos duplicados."
        if errores > 0:
            mensaje += f" Errores: {errores}"
            
        return True, mensaje
        
    except Exception as e:
        return False, f"Error al importar: {str(e)}"

def mostrar_contenido_gastos():
    if not st.session_state.cuenta_actual:
        st.warning(get_text('seleccione_cuenta'))
        return
        
    st.title(get_text('registro_gastos'))
    
    # Obtener categorías
    categorias = get_categorias(st.session_state.cuenta_actual)
    if categorias.empty:
        st.warning(get_text('sin_categorias'))
        return
    
    # Tabs para nuevo gasto e historial
    tab1, tab2, tab3 = st.tabs([
        get_text('nuevo_gasto'), 
        get_text('historial_gastos'),
        "Importar CSV"
    ])
    
    # Tab para nuevo gasto
    with tab1:
        st.subheader(get_text('registro_gastos'))
        
        # Generar nueva key de formulario si se acaba de registrar un gasto
        if 'last_submit' not in st.session_state:
            st.session_state.last_submit = time.time()
        
        # Key única para el formulario
        form_key = f"registro_gasto_{st.session_state.last_submit}"
        
        with st.form(form_key):
            col1, col2 = st.columns(2)
            
            with col1:
                cantidad = st.number_input(
                    get_text('cantidad'), 
                    min_value=0.01,
                    step=0.01,
                    format="%.2f",
                    value=0.01
                )
                categoria_seleccionada = st.selectbox(
                    get_text('categoria'),
                    options=categorias['nombre'].tolist()
                )
            
            with col2:
                lugar = st.text_input(get_text('lugar'))
                fecha = st.date_input(get_text('fecha'), datetime.now())
            
            notas = st.text_area(get_text('notas'), height=100)
            
            submitted = st.form_submit_button(get_text('registrar_gasto'))
            if submitted:
                if not lugar:
                    st.error(get_text('ingrese_lugar'))
                else:
                    try:
                        # Obtener el ID de la categoría seleccionada
                        categoria_id = categorias[
                            categorias['nombre'] == categoria_seleccionada
                        ]['id'].iloc[0]
                        
                        # Intentar registrar el gasto
                        if registrar_gasto(
                            st.session_state.cuenta_actual,
                            categoria_id,
                            cantidad,
                            lugar,
                            fecha,
                            st.session_state.user_id,
                            notas
                        ):
                            st.success(get_text('gasto_registrado'))
                            # Actualizar key del formulario para la próxima vez
                            st.session_state.last_submit = time.time()
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(get_text('error_gasto'))
                    except Exception as e:
                        st.error(f"Error al registrar gasto: {str(e)}")

    # Tab para historial de gastos
    with tab2:
        st.subheader(get_text('historial_gastos'))
        
        # Obtener lista de meses disponibles
        conn = sqlite3.connect('finanzas.db')
        meses_df = pd.read_sql_query("""
            SELECT DISTINCT 
                strftime('%m', fecha) as mes,
                strftime('%Y', fecha) as anio
            FROM gastos
            WHERE cuenta_id = ?
            ORDER BY fecha DESC
        """, conn, params=(st.session_state.cuenta_actual,))
        
        # Crear opciones de meses
        meses_opciones = []
        mes_actual = datetime.now().strftime('%m')
        anio_actual = datetime.now().strftime('%Y')
        
        # Agregar opción "Todos los meses"
        meses_opciones.append(("00", "0000", get_text('todos_meses')))
        
        # Mapeo de números de mes a claves de traducción
        meses_keys = {
            1: 'enero',
            2: 'febrero',
            3: 'marzo',
            4: 'abril',
            5: 'mayo',
            6: 'junio',
            7: 'julio',
            8: 'agosto',
            9: 'septiembre',
            10: 'octubre',
            11: 'noviembre',
            12: 'diciembre'
        }
        
        # Agregar meses disponibles
        for _, row in meses_df.iterrows():
            mes_num = int(row['mes'])
            anio = row['anio']
            nombre_mes = get_text(meses_keys[mes_num])
            meses_opciones.append((row['mes'], anio, f"{nombre_mes} {anio}"))
        
        # Encontrar índice del mes actual
        mes_actual_idx = 0
        for i, (mes, anio, _) in enumerate(meses_opciones):
            if mes == mes_actual and anio == anio_actual:
                mes_actual_idx = i
                break
        
        # Selector de mes
        mes_seleccionado = st.selectbox(
            get_text('mes'),
            options=meses_opciones,
            format_func=lambda x: x[2],
            index=mes_actual_idx
        )
        
        # Construir la consulta SQL según el mes seleccionado
        query = """
            SELECT 
                strftime('%d/%m/%Y', g.fecha) as fecha,
                g.lugar,
                g.cantidad,
                c.nombre as categoria,
                g.notas,
                u.nombre as usuario
            FROM gastos g
            JOIN categorias c ON g.categoria_id = c.id
            JOIN usuarios u ON g.usuario_id = u.id
            WHERE g.cuenta_id = ?
        """
        params = [st.session_state.cuenta_actual]
        
        if mes_seleccionado[0] != "00":  # Si no es "Todos los meses"
            query += " AND strftime('%m-%Y', g.fecha) = ?"
            params.append(f"{mes_seleccionado[0]}-{mes_seleccionado[1]}")
        
        query += " ORDER BY g.fecha DESC, g.id DESC"
        
        # Obtener y mostrar los gastos
        gastos_df = pd.read_sql_query(query, conn, params=params)
        
        if not gastos_df.empty:
            st.dataframe(
                gastos_df,
                column_config={
                    "fecha": st.column_config.TextColumn(
                        get_text('fecha')
                    ),
                    "lugar": get_text('lugar'),
                    "cantidad": st.column_config.NumberColumn(
                        get_text('cantidad'),
                        format="$%.2f"
                    ),
                    "categoria": get_text('categoria'),
                    "notas": get_text('notas'),
                    "usuario": get_text('pagado_por')
                },
                hide_index=True
            )
            
            # Mostrar total
            st.info(f"Total: ${gastos_df['cantidad'].sum():,.2f}")
            
            # Botón para exportar a CSV
            csv = gastos_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                get_text('descargar_csv'),
                csv,
                "gastos.csv",
                "text/csv",
                key='download-csv'
            )
        else:
            st.info(get_text('sin_gastos'))
        
        conn.close()

    # Tab para importar CSV
    with tab3:
        st.subheader("Importar gastos desde CSV")
        with st.form("importar_csv"):
            st.info("""
            El archivo CSV debe contener las siguientes columnas:
            - date (DD/MM/YY)
            - store (lugar del gasto)
            - amount (cantidad)
            - category (categoría)
            """)
            
            archivo_csv = st.file_uploader(
                "Seleccionar archivo CSV", 
                type=['csv'],
                help="El archivo debe estar en formato CSV"
            )
            
            submitted = st.form_submit_button("Importar gastos")
            if submitted and archivo_csv:
                try:
                    df = pd.read_csv(archivo_csv)
                    gastos_importados = 0
                    errores = 0
                    
                    # Obtener mapeo de categorías existentes
                    conn = sqlite3.connect('finanzas.db')
                    c = conn.cursor()
                    c.execute("SELECT id, nombre FROM categorias WHERE cuenta_id = ?", 
                            (st.session_state.cuenta_actual,))
                    categorias = dict(c.fetchall())
                    categorias_inv = {v.lower(): k for k, v in categorias.items()}
                    
                    for _, row in df.iterrows():
                        try:
                            # Buscar o crear la categoría
                            categoria = row['category'].strip()
                            categoria_id = categorias_inv.get(categoria.lower())
                            
                            if not categoria_id:
                                # Crear nueva categoría
                                c.execute("""
                                    INSERT INTO categorias (nombre, cuenta_id) 
                                    VALUES (?, ?)
                                """, (categoria, st.session_state.cuenta_actual))
                                categoria_id = c.lastrowid
                                categorias_inv[categoria.lower()] = categoria_id
                            
                            # Convertir fecha
                            fecha = datetime.strptime(row['date'], '%d/%m/%y').strftime('%Y-%m-%d')
                            
                            # Insertar gasto
                            c.execute("""
                                INSERT INTO gastos 
                                (cuenta_id, categoria_id, cantidad, lugar, fecha, usuario_id)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (
                                st.session_state.cuenta_actual,
                                categoria_id,
                                float(row['amount']),
                                row['store'],
                                fecha,
                                st.session_state.user_id
                            ))
                            gastos_importados += 1
                            
                        except Exception as e:
                            errores += 1
                            st.error(f"Error en fila {gastos_importados + errores}: {str(e)}")
                    
                    conn.commit()
                    conn.close()
                    
                    if gastos_importados > 0:
                        st.success(f"Se importaron {gastos_importados} gastos exitosamente. Errores: {errores}")
                        st.rerun()
                    else:
                        st.error("No se pudo importar ningún gasto")
                        
                except Exception as e:
                    st.error(f"Error al procesar el archivo: {str(e)}")

if __name__ == "__main__":
    mostrar_contenido_gastos() 