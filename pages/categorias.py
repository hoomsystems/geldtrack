import streamlit as st
import sqlite3
import pandas as pd
from components.sidebar import show_sidebar
from translations import get_text

def get_categorias(cuenta_id):
    conn = sqlite3.connect('finanzas.db')
    query = """
    SELECT 
        c.id,
        c.nombre,
        c.presupuesto_mensual,
        COALESCE(SUM(g.cantidad), 0) as gasto_actual
    FROM categorias c
    LEFT JOIN gastos g ON c.id = g.categoria_id 
        AND strftime('%Y-%m', g.fecha) = strftime('%Y-%m', 'now')
    WHERE c.cuenta_id = ?
    GROUP BY c.id, c.nombre, c.presupuesto_mensual
    ORDER BY c.nombre
    """
    df = pd.read_sql_query(query, conn, params=(cuenta_id,))
    conn.close()
    return df

def crear_categoria(nombre, presupuesto, cuenta_id):
    try:
        conn = sqlite3.connect('finanzas.db')
        c = conn.cursor()
        c.execute(
            "INSERT INTO categorias (nombre, presupuesto_mensual, cuenta_id) VALUES (?, ?, ?)",
            (nombre, presupuesto, cuenta_id)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error:
        return False

def actualizar_categoria(categoria_id, nombre, presupuesto):
    try:
        conn = sqlite3.connect('finanzas.db')
        c = conn.cursor()
        c.execute(
            "UPDATE categorias SET nombre = ?, presupuesto_mensual = ? WHERE id = ?",
            (nombre, presupuesto, categoria_id)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error:
        return False

def eliminar_categoria(categoria_id):
    try:
        conn = sqlite3.connect('finanzas.db')
        c = conn.cursor()
        # Verificar si hay gastos asociados
        c.execute("SELECT COUNT(*) FROM gastos WHERE categoria_id = ?", (categoria_id,))
        if c.fetchone()[0] > 0:
            conn.close()
            return False, "No se puede eliminar una categoría que tiene gastos asociados"
        
        c.execute("DELETE FROM categorias WHERE id = ?", (categoria_id,))
        conn.commit()
        conn.close()
        return True, "Categoría eliminada exitosamente"
    except sqlite3.Error as e:
        return False, f"Error al eliminar la categoría: {str(e)}"

def mostrar_contenido_categorias():
    if not st.session_state.cuenta_actual:
        st.warning(get_text('seleccione_cuenta'))
        return
        
    st.title(get_text('gestion_categorias'))
    
    # Formulario para nueva categoría
    with st.form("nueva_categoria"):
        nombre = st.text_input(get_text('nombre_categoria'))
        presupuesto = st.number_input(get_text('presupuesto'), min_value=0.0, step=1000.0)
        
        if st.form_submit_button(get_text('crear_categoria')):
            if crear_categoria(nombre, presupuesto, st.session_state.cuenta_actual):
                st.success(get_text('categoria_creada'))
            else:
                st.error(get_text('error_categoria'))
    
    # Mostrar categorías existentes
    st.subheader("Categorías Existentes")
    categorias = get_categorias(st.session_state.cuenta_actual)
    
    if not categorias.empty:
        for _, categoria in categorias.iterrows():
            with st.expander(f"📁 {categoria['nombre']}"):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    nuevo_nombre = st.text_input(
                        "Nombre",
                        value=categoria['nombre'],
                        key=f"nombre_{categoria['id']}"
                    )
                
                with col2:
                    nuevo_presupuesto = st.number_input(
                        "Presupuesto Mensual",
                        value=float(categoria['presupuesto_mensual']),
                        min_value=0.0,
                        step=100.0,
                        format="%.2f",
                        key=f"presupuesto_{categoria['id']}"
                    )
                
                with col3:
                    if st.button("Actualizar", key=f"actualizar_{categoria['id']}"):
                        if actualizar_categoria(categoria['id'], nuevo_nombre, nuevo_presupuesto):
                            st.success("Categoría actualizada")
                            st.rerun()
                        else:
                            st.error("Error al actualizar")
                    
                    if st.button("Eliminar", key=f"eliminar_{categoria['id']}"):
                        exito, mensaje = eliminar_categoria(categoria['id'])
                        if exito:
                            st.success(mensaje)
                            st.rerun()
                        else:
                            st.error(mensaje)
                
                # Mostrar gastos del mes actual
                gasto_actual = categoria['gasto_actual']
                presupuesto = categoria['presupuesto_mensual']
                if presupuesto > 0:
                    porcentaje = (gasto_actual / presupuesto) * 100
                    color = 'green' if porcentaje < 80 else 'orange' if porcentaje < 100 else 'red'
                    st.markdown(f"""
                    **Gastos del mes actual:** ${gasto_actual:,.2f} / ${presupuesto:,.2f}  
                    <span style='color:{color}'>{porcentaje:.1f}% del presupuesto</span>
                    """, unsafe_allow_html=True)
                else:
                    st.write(f"**Gastos del mes actual:** ${gasto_actual:,.2f}")
    else:
        st.info("No hay categorías creadas")

if __name__ == "__main__":
    mostrar_contenido_categorias() 