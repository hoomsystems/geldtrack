import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from components.sidebar import show_sidebar
from translations import get_text
import time

def get_gastos_mes(cuenta_id, mes=None, anio=None):
    conn = sqlite3.connect('finanzas.db')
    
    if not mes or not anio:
        hoy = datetime.now()
        mes = mes or hoy.month
        anio = anio or hoy.year
    
    query = """
    SELECT 
        c.nombre as categoria,
        c.presupuesto_mensual,
        COALESCE(SUM(g.cantidad), 0) as total_gastado,
        COUNT(g.id) as num_gastos
    FROM categorias c
    LEFT JOIN gastos g ON c.id = g.categoria_id 
        AND strftime('%m-%Y', g.fecha) = ?
    WHERE c.cuenta_id = ?
    GROUP BY c.nombre, c.presupuesto_mensual
    ORDER BY total_gastado DESC
    """
    
    df = pd.read_sql_query(query, conn, params=(f"{mes:02d}-{anio}", cuenta_id))
    conn.close()
    return df

def eliminar_gasto(gasto_id):
    conn = sqlite3.connect('finanzas.db')
    c = conn.cursor()
    try:
        c.execute("DELETE FROM gastos WHERE id = ?", (gasto_id,))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error al eliminar: {str(e)}")
        return False
    finally:
        conn.close()

def get_gastos_detallados(cuenta_id, mes, anio, categoria=None):
    conn = sqlite3.connect('finanzas.db')
    
    query = """
    SELECT 
        g.id,
        g.fecha,
        g.lugar,
        g.cantidad,
        c.nombre as categoria,
        g.notas,
        u.nombre as usuario
    FROM gastos g
    JOIN categorias c ON g.categoria_id = c.id
    JOIN usuarios u ON g.usuario_id = u.id
    WHERE g.cuenta_id = ?
    AND strftime('%m-%Y', g.fecha) = ?
    """
    
    params = [cuenta_id, f"{mes:02d}-{anio}"]
    
    if categoria:
        query += " AND c.nombre = ?"
        params.append(categoria)
    
    query += " ORDER BY g.fecha DESC"
    
    df = pd.read_sql_query(query, conn, params=tuple(params))
    conn.close()
    return df

def mostrar_analisis(show_sidebar_param=True):
    if 'user_id' not in st.session_state:
        st.error("Por favor inicia sesión")
        return
    
    # Solo mostrar el sidebar si se pasa True
    if show_sidebar_param:
        opcion = show_sidebar("analisis")
        if opcion != "Análisis":
            if opcion == "Dashboard":
                from app import show_main_dashboard
                show_main_dashboard()
            elif opcion == "Gastos":
                from pages.gastos import mostrar_gastos
                mostrar_gastos()
            elif opcion == "Categorías":
                from pages.categorias import mostrar_categorias
                mostrar_categorias()
            elif opcion == "Configuración":
                from pages.configuracion import mostrar_configuracion
                mostrar_configuracion()
            return
    
    st.title("Análisis de Gastos")
    
    if 'cuenta_actual' not in st.session_state:
        st.error("Por favor seleccione una cuenta primero")
        return
    
    # Selector de mes
    hoy = datetime.now()
    primer_dia_mes = datetime(hoy.year, hoy.month, 1)
    meses_atras = []
    for i in range(12):
        mes = primer_dia_mes - timedelta(days=32*i)
        meses_atras.append(mes.strftime("%Y-%m"))
    
    mes_seleccionado = st.selectbox("Seleccione mes", meses_atras)
    año, mes = map(int, mes_seleccionado.split('-'))
    fecha_inicio = datetime(año, mes, 1)
    if mes == 12:
        fecha_fin = datetime(año + 1, 1, 1)
    else:
        fecha_fin = datetime(año, mes + 1, 1)
    
    # Obtener datos
    df = get_gastos_mes(st.session_state.cuenta_actual, fecha_inicio.strftime('%m'), fecha_inicio.strftime('%Y'))
    
    # Mostrar resumen
    st.subheader("Resumen por Categorías")
    
    if not df.empty:
        # Formatear DataFrame para mostrar
        df_display = df.copy()
        df_display['total_gastado'] = df_display['total_gastado'].apply(lambda x: f"${x:,.2f}")
        df_display['presupuesto_mensual'] = df_display['presupuesto_mensual'].apply(
            lambda x: f"${x:,.2f}" if x else "No definido"
        )
        
        # Aplicar colores según el porcentaje
        def get_color(porcentaje):
            if porcentaje <= 80:
                return 'green'
            elif porcentaje <= 100:
                return 'yellow'
            return 'red'
        
        # Crear tabla estilizada
        for _, row in df_display.iterrows():
            col1, col2, col3, col4 = st.columns([2,1,1,1])
            with col1:
                st.write(row['categoria'])
            with col2:
                st.write(row['total_gastado'])
            with col3:
                st.write(row['presupuesto_mensual'])
            with col4:
                if row['presupuesto_mensual'] != "No definido":
                    porcentaje = float(row['porcentaje_presupuesto'])
                    color = get_color(porcentaje)
                    st.markdown(f"<span style='color:{color}'>{porcentaje:.1f}%</span>", 
                              unsafe_allow_html=True)
                else:
                    st.write("N/A")
        
        # Gráficas
        st.subheader("Visualizaciones")
        
        # Gráfica de barras - Gastos por categoría
        fig1 = px.bar(
            df,
            x='categoria',
            y='total_gastado',
            title='Gastos por Categoría',
            labels={'total_gastado': 'Total Gastado', 'categoria': 'Categoría'}
        )
        st.plotly_chart(fig1)
        
        # Gráfica de pie - Distribución de gastos
        fig2 = px.pie(
            df,
            values='total_gastado',
            names='categoria',
            title='Distribución de Gastos'
        )
        st.plotly_chart(fig2)
        
    else:
        st.info("No hay gastos registrados para este mes")

def mostrar_contenido_analisis():
    if not st.session_state.cuenta_actual:
        st.warning(get_text('seleccione_cuenta'))
        return
        
    st.title(get_text('analisis_gastos'))
    
    # Filtros de fecha
    col1, col2 = st.columns(2)
    
    # Obtener años únicos
    conn = sqlite3.connect('finanzas.db')
    years_df = pd.read_sql_query("""
        SELECT DISTINCT strftime('%Y', fecha) as year 
        FROM gastos 
        WHERE cuenta_id = ?
        ORDER BY year DESC
    """, conn, params=(st.session_state.cuenta_actual,))
    conn.close()
    
    years = years_df['year'].tolist() if not years_df.empty else [datetime.now().year]
    
    with col1:
        anio_seleccionado = st.selectbox(
            "Año",
            options=years,
            index=0,
            key="analisis_anio"
        )
    
    with col2:
        mes_seleccionado = st.selectbox(
            "Mes",
            options=[
                (1, get_text('enero')), (2, get_text('febrero')), (3, get_text('marzo')),
                (4, get_text('abril')), (5, get_text('mayo')), (6, get_text('junio')),
                (7, get_text('julio')), (8, get_text('agosto')), (9, get_text('septiembre')),
                (10, get_text('octubre')), (11, get_text('noviembre')), (12, get_text('diciembre'))
            ],
            format_func=lambda x: x[1],
            index=datetime.now().month - 1,
            key="analisis_mes"
        )
    
    # Obtener datos del mes seleccionado
    df_mes = get_gastos_mes(
        st.session_state.cuenta_actual,
        mes_seleccionado[0],
        anio_seleccionado
    )
    
    # Tabs para diferentes vistas
    tab1, tab2, tab3 = st.tabs([
        get_text('resumen_mensual'),
        get_text('gastos_categoria'),
        get_text('tendencias')
    ])
    
    # Agregar estado para confirmación de eliminación
    if 'gasto_a_eliminar' not in st.session_state:
        st.session_state.gasto_a_eliminar = None

    with tab1:
        # Métricas principales
        total_gastado = df_mes['total_gastado'].sum()
        total_presupuesto = df_mes['presupuesto_mensual'].sum()
        porcentaje_usado = (total_gastado / total_presupuesto * 100) if total_presupuesto > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                get_text('total_gastado'),
                f"${total_gastado:,.2f}"
            )
        with col2:
            st.metric(
                get_text('presupuesto_restante'),
                f"${(total_presupuesto - total_gastado):,.2f}"
            )
        with col3:
            st.metric(
                get_text('porcentaje_usado'),
                f"{porcentaje_usado:.1f}%"
            )
        
        # Tabla de análisis por categoría
        st.subheader(get_text('analisis_categorias'))
        
        # Contenedor para la tabla más compacta
        table_container = st.container()
        with table_container:
            if 'categoria_expandida' not in st.session_state:
                st.session_state.categoria_expandida = None

            for _, row in df_mes.iterrows():
                porcentaje = (row['total_gastado'] / row['presupuesto_mensual'] * 100) if row['presupuesto_mensual'] > 0 else 0
                color = 'green' if porcentaje < 80 else 'orange' if porcentaje < 100 else 'red'
                
                # Barra de progreso y nombre de categoría
                st.markdown(f"""
                <div style='padding: 5px; margin-bottom: 10px;'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;'>
                        <span style='font-weight: bold;'>{row['categoria']}</span>
                        <span style='color: {color}'>${row['total_gastado']:,.2f} / ${row['presupuesto_mensual']:,.2f} ({porcentaje:.1f}%)</span>
                    </div>
                    <div style='background-color: #eee; height: 8px; border-radius: 4px;'>
                        <div style='background-color: {color}; width: {min(porcentaje, 100)}%; height: 100%; border-radius: 4px;'></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Toggle para mostrar detalles
                if st.button('Ver detalles', key=f"toggle_{row['categoria']}"):
                    st.session_state.categoria_expandida = row['categoria']
                    st.rerun()
                
                # Mostrar detalles si la categoría está expandida
                if st.session_state.categoria_expandida == row['categoria']:
                    gastos_cat = get_gastos_detallados(
                        st.session_state.cuenta_actual,
                        mes_seleccionado[0],
                        anio_seleccionado,
                        row['categoria']
                    )
                    
                    if not gastos_cat.empty:
                        st.markdown("---")
                        
                        # Mostrar cada gasto
                        for _, gasto in gastos_cat.iterrows():
                            with st.container():
                                col1, col2, col3 = st.columns([4, 1, 1])
                                
                                with col1:
                                    st.write(f"📅 {gasto['fecha']} | 🏢 {gasto['lugar']} | 💰 ${gasto['cantidad']:,.2f}")
                                    if gasto['notas']:
                                        st.caption(f"📝 {gasto['notas']}")
                                
                                with col2:
                                    if st.button("✏️", key=f"edit_{gasto['id']}"):
                                        st.session_state.gasto_a_editar = gasto['id']
                                        st.session_state.categoria_expandida = row['categoria']
                                        st.rerun()
                                
                                with col3:
                                    if st.button("🗑️", key=f"del_{gasto['id']}"):
                                        if eliminar_gasto(gasto['id']):
                                            st.success("Gasto eliminado exitosamente")
                                            time.sleep(0.5)
                                            st.session_state.categoria_expandida = row['categoria']
                                            st.rerun()
                                
                                st.divider()
                        
                        # Botón para cerrar detalles
                        if st.button("Cerrar detalles", key=f"close_{row['categoria']}"):
                            st.session_state.categoria_expandida = None
                            st.rerun()
                
                st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)

        # Modal de edición
        if 'gasto_a_editar' in st.session_state:
            gasto_id = st.session_state.gasto_a_editar
            conn = sqlite3.connect('finanzas.db')
            gasto_df = pd.read_sql_query("""
                SELECT g.*, c.nombre as categoria
                FROM gastos g
                JOIN categorias c ON g.categoria_id = c.id
                WHERE g.id = ?
            """, conn, params=(gasto_id,))
            conn.close()
            
            if not gasto_df.empty:
                gasto = gasto_df.iloc[0]
                
                st.markdown("### Editar Gasto")
                with st.form(key="editar_gasto"):
                    cantidad = st.number_input(
                        "Cantidad", 
                        value=float(gasto['cantidad']), 
                        step=0.01,
                        format="%.2f"
                    )
                    lugar = st.text_input("Lugar", value=gasto['lugar'])
                    fecha = st.date_input("Fecha", value=pd.to_datetime(gasto['fecha']))
                    notas = st.text_area("Notas", value=gasto['notas'] if gasto['notas'] else "")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Guardar"):
                            conn = sqlite3.connect('finanzas.db')
                            c = conn.cursor()
                            try:
                                c.execute("""
                                    UPDATE gastos 
                                    SET cantidad = ?, lugar = ?, fecha = ?, notas = ?
                                    WHERE id = ?
                                """, (cantidad, lugar, fecha, notas, gasto_id))
                                conn.commit()
                                st.success("Gasto actualizado exitosamente")
                                del st.session_state.gasto_a_editar
                                time.sleep(0.5)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al actualizar: {str(e)}")
                            finally:
                                conn.close()
                    
                    with col2:
                        if st.form_submit_button("Cancelar"):
                            del st.session_state.gasto_a_editar
                            st.rerun()
    
    with tab2:
        # Gráficas en la parte superior
        col1, col2 = st.columns(2)
        
        with col1:
            fig_pie = px.pie(
                df_mes,
                values='total_gastado',
                names='categoria',
                title=get_text('distribucion_gastos')
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            fig_bar = px.bar(
                df_mes,
                x='categoria',
                y=['total_gastado', 'presupuesto_mensual'],
                title=get_text('comparativa_presupuesto'),
                barmode='group',
                labels={
                    'value': 'Cantidad',
                    'variable': 'Tipo',
                    'categoria': 'Categoría'
                }
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # Selector de categoría para ver detalle
        categorias = df_mes['categoria'].tolist()
        categoria_seleccionada = st.selectbox(
            get_text('seleccionar_categoria'),
            options=['Todas las categorías'] + categorias
        )
        
        # Obtener y mostrar gastos detallados
        gastos_detallados = get_gastos_detallados(
            st.session_state.cuenta_actual,
            mes_seleccionado[0],
            anio_seleccionado,
            None if categoria_seleccionada == 'Todas las categorías' else categoria_seleccionada
        )
        
        if not gastos_detallados.empty:
            # Mostrar total de la categoría seleccionada
            total_categoria = gastos_detallados['cantidad'].sum()
            st.metric(
                f"Total {categoria_seleccionada}",
                f"${total_categoria:,.2f}"
            )
            
            # Mostrar tabla de gastos detallados
            st.dataframe(
                gastos_detallados,
                column_config={
                    "fecha": st.column_config.DateColumn(
                        get_text('fecha'),
                        format="DD/MM/YYYY"
                    ),
                    "lugar": get_text('lugar'),
                    "cantidad": st.column_config.NumberColumn(
                        get_text('cantidad'),
                        format="$%.2f"
                    ),
                    "categoria": get_text('categoria'),
                    "notas": st.column_config.TextColumn(
                        get_text('notas'),
                        width="medium"
                    ),
                    "usuario": get_text('pagado_por')
                },
                hide_index=True
            )
            
            # Mostrar total de registros
            st.info(f"Total de gastos: {len(gastos_detallados)}")
            
            # Exportar a CSV
            csv = gastos_detallados.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Descargar como CSV",
                csv,
                f"gastos_{categoria_seleccionada}_{mes_seleccionado[0]}-{anio_seleccionado}.csv",
                "text/csv",
                key='download-csv'
            )
        else:
            st.info(get_text('sin_gastos'))
    
    with tab3:
        # Análisis de tendencias
        meses_atras = 6
        
        # Obtener datos históricos
        conn = sqlite3.connect('finanzas.db')
        query_tendencias = """
        SELECT 
            strftime('%m-%Y', fecha) as mes,
            c.nombre as categoria,
            SUM(g.cantidad) as total
        FROM gastos g
        JOIN categorias c ON g.categoria_id = c.id
        WHERE g.cuenta_id = ?
        AND fecha >= date('now', ?)
        GROUP BY mes, c.nombre
        ORDER BY mes
        """
        
        df_tendencias = pd.read_sql_query(
            query_tendencias, 
            conn, 
            params=(st.session_state.cuenta_actual, f'-{meses_atras} months')
        )
        conn.close()
        
        if not df_tendencias.empty:
            # Gráfica de líneas para tendencias
            fig_trend = px.line(
                df_tendencias,
                x='mes',
                y='total',
                color='categoria',
                title=get_text('tendencia_gastos'),
                labels={
                    'mes': 'Mes',
                    'total': 'Total Gastado',
                    'categoria': 'Categoría'
                }
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info(get_text('sin_datos_tendencia'))

if __name__ == "__main__":
    mostrar_contenido_analisis() 