import streamlit as st
import pandas as pd
import requests
import psycopg2
import hashlib

# Conexión a la base de datos
def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname="consultaETAS",
            user="postgres",
            password="Daniel2030#",
            host="localhost",
            port="5432"
        )
        return conn
    except psycopg2.Error as e:
        st.error(f"Error al conectar a la base de datos: {e}")
        return None

# Función para hashear la contraseña
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Función para registrar al usuario en la base de datos
def register_user(username, password):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        hashed_password = hash_password(password)
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
            conn.commit()
            st.success("El registro ha sido exitoso")
        except psycopg2.Error as e:
            st.error(f"Error al registrar el usuario: {e}")
        finally:
            cursor.close()
            conn.close()

# Función para verificar el login del usuario
def login_user(username, password):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        hashed_password = hash_password(password)
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, hashed_password))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result:
            return True
    return False

# Vista de registro e inicio de sesión
def register_or_login_view():
    st.markdown("""
    <h1 style='text-align: center;'>Alerta de ETAs</h1>
    <h3 style='text-align: left;'>Registro o Login</h3>
    """, unsafe_allow_html=True)
    
    usuario = st.text_input("Usuario", key="usuario_input")
    contrasena = st.text_input("Contraseña", type="password", key="contrasena_input")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Registrarse"):
            if usuario and contrasena:
                register_user(usuario, contrasena)
            else:
                st.error("Por favor complete todos los campos")
    
    with col2:
        if st.button("Entrar"):
            if usuario and contrasena:
                if login_user(usuario, contrasena):
                    st.session_state['current_view'] = 'main'
                    st.success("Inicio de sesión exitoso")
                else:
                    st.error("Usuario o contraseña incorrectos")
            else:
                st.error("Por favor complete todos los campos")

# Vista principal de la aplicación después de iniciar sesión
def main_view():
    st.title("Alerta de ETAs")
    
    correo = st.text_input("Correo de notificación")
    uploaded_file = st.file_uploader("Excel con ETAs a validar", type=['xlsx'])
    
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        st.write("Vista previa del archivo:")
        st.dataframe(df.head())
        
        url_flujo = 'https://prod-43.westus.logic.azure.com:443/workflows/92297bf73c4b494ea9c4668c7a9569fe/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=aoHBBza4EuOoUsRdxDJFM_0N6Gf-jLR4tWCx3etWLP8'
        if st.button("Ejecutar"):
            with st.spinner("Consultando ETAs..."):
                resultado = ejecucion_flujo_url(url_flujo)
            st.write(resultado)

# Función para ejecutar un flujo a través de una URL
def ejecucion_flujo_url(url):
    try:
        headers = {'Content-Type': 'application/json'}
        data = {}
        response = requests.post(url, headers=headers, json=data)
        if response.status_code in (200, 202):
            return "Consultando ETAs..."
        else:
            return f"Error al ejecutar el flujo. Código de estado: {response.status_code}"
    except Exception as e:
        return f"Ocurrió un error al ejecutar el flujo: {str(e)}"

# Control de flujo entre vistas
def main():
    if 'current_view' not in st.session_state:
        st.session_state['current_view'] = 'login'

    if st.session_state['current_view'] == 'login':
        register_or_login_view()
    elif st.session_state['current_view'] == 'main':
        main_view()

if __name__ == "__main__":
    main()


#https://prod-43.westus.logic.azure.com:443/workflows/92297bf73c4b494ea9c4668c7a9569fe/triggers/manual/paths/invoke?api-version=2016-06-01