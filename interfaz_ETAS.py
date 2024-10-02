import streamlit as st
import pandas as pd
import os
import subprocess


# Inicializar listas para almacenar usuarios y contraseñas
if 'usuarios' not in st.session_state:
    st.session_state['usuarios'] = []
if 'contrasenas' not in st.session_state:
    st.session_state['contrasenas'] = []

def ejecucion_flujo_url(url):
    try:
        os.startfile(url)
        return ("Consultando ETA´s")
    except Exception as e:
        return (f"Ocurrió un error al ejecutar el flujo: {str(e)}")

def register_or_login_view():
    """Vista inicial donde el usuario puede registrarse o entrar con usuario existente."""
    st.markdown("""
    <h1 style='text-align: center;'>Alerta de ETAs</h1>
    <h3 style='text-align: left;'>Registro o Login</h3>
    """, unsafe_allow_html=True)
    #st.title("Registro o Login")
    
    # Inputs para el usuario y la contraseña
    usuario = st.text_input("Usuario")
    contrasena = st.text_input("Contraseña", type="password")
    
    # Botones para registrarse o entrar
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Registrarse"):
            if usuario and contrasena:
                # Almacenar el nuevo usuario y contraseña
                st.session_state['usuarios'].append(usuario)
                st.session_state['contrasenas'].append(contrasena)
                st.success("El registro ha sido exitoso")
            else:
                st.error("Por favor complete todos los campos")
    with col2:
        if st.button("Entrar"):
            if usuario and contrasena:
                # Verificar si el usuario y la contraseña existen en las listas
                if usuario in st.session_state['usuarios']:
                    index = st.session_state['usuarios'].index(usuario)
                    if st.session_state['contrasenas'][index] == contrasena:
                        st.session_state['current_view'] = 'main'
                    else:
                        st.error("Contraseña incorrecta")
                else:
                    st.error("Usuario no registrado")
            else:
                st.error("Por favor complete todos los campos")

def main_view():
    """Vista principal después de entrar, para correo y carga de Excel."""
    st.title("Alerta de ETAS")
    
    correo = st.text_input("Correo de notificación")
    uploaded_file = st.file_uploader("Excel con ETAs a validar", type=['xlsx'])
    
    # Botón para ejecutar alguna acción con el archivo Excel cargado
    if uploaded_file is not None:
        # Leer el archivo como un DataFrame
        df = pd.read_excel(uploaded_file)
        # Mostrar una vista previa del archivo
        st.write("Vista previa del archivo:")
        st.dataframe(df.head())
        #url_flujo = "ms-powerautomate:/console/flow/run?environmentid=Default-f20cbde7-1c45-44a0-89c5-63a25c557ef8&workflowid=64f3cd77-3e25-4f1f-8118-3ceb41d3b88d&source=Other"
        url_flujo = "ms-powerautomate:/console/flow/run?environmentid=Default-f20cbde7-1c45-44a0-89c5-63a25c557ef8&workflowid=d936338d-84f3-4891-9909-1e020b3f21b6&source=Other"
        if st.button("Ejecutar"):
            #st.success("Ejecución completada con éxito")
            with st.spinner("Consultando ETA´s"):
                resultado = ejecucion_flujo_url(url_flujo)
            st.write(resultado)

def main():
    if 'current_view' not in st.session_state:
        st.session_state['current_view'] = 'login'

    if st.session_state['current_view'] == 'login':
        register_or_login_view()
    elif st.session_state['current_view'] == 'main':
        main_view()

if __name__ == "__main__":
    main()



