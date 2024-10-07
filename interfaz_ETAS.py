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
            host="6.tcp.ngrok.io",
            port="15745"
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
            cursor.execute("INSERT INTO usuario (username, password) VALUES (%s, %s)", (username, hashed_password))
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
        cursor.execute("SELECT * FROM usuario WHERE username = %s AND password = %s", (username, hashed_password))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result:
            return result[0] #retorna el id del usuario
    return None

# Función para agregar los datos de contenedores a la tabla "consulta"
def add_container_data(user_id, container_data):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        insert_query = """
        INSERT INTO consulta (num_contenedor, doc_transporte, naviera, usuario_id)
        VALUES (%s, %s, %s, %s)
        """
        try:
            for data in container_data:
                cursor.execute(insert_query, (data["num_contenedor"], data["doc_transporte"], data["naviera"], user_id))
            conn.commit()
            st.success("Información cargada, pronto recibirá un email dando inicio al proceso de consulta de ETAS.")
        except psycopg2.Error as e:
            st.error(f"Error al cargar los datos: {e}")
        finally:
            cursor.close()
            conn.close()


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
                user_id = login_user(usuario, contrasena)
                if user_id:
                    st.session_state['current_view'] = 'main'
                    st.session_state['id'] = user_id
                    st.success("Inicio de sesión exitoso")
                else:
                    st.error("Usuario o contraseña incorrectos")
            else:
                st.error("Por favor complete todos los campos")

# Vista principal de la aplicación después de iniciar sesión
def main_view():
    url_flujo = 'https://prod-43.westus.logic.azure.com:443/workflows/92297bf73c4b494ea9c4668c7a9569fe/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=aoHBBza4EuOoUsRdxDJFM_0N6Gf-jLR4tWCx3etWLP8'

    st.title("Alerta de ETAs")
    
    correo = st.text_input("Correo de notificación")
    
    # Inicializar el contador de entradas si no existe
    if 'container_entries' not in st.session_state:
        st.session_state.container_entries = 1

    # Crear un formulario dinámico
    for i in range(st.session_state.container_entries):
        st.subheader(f"Entrada {i + 1}")
        
        # Crear tres columnas para alinear los campos horizontalmente
        col1, col2, col3 = st.columns(3)
        with col1:
            st.text_input(f"**Número de contenedor**", key=f"container_number_{i}")
        with col2:
            st.text_input(f"**Documento de transporte (opcional)**", key=f"transport_document_{i}")
        with col3:
            st.text_input(f"**Naviera**", key=f"shipping_company_{i}")
            
    col_add, col_delete = st.columns(2)
    with col_add:
        # Botón para agregar otra entrada
        if st.button("Agregar otra entrada"):
            st.session_state.container_entries += 1
    if st.session_state.container_entries > 1:
        with col_delete:
            if st.button("Eliminar entrada")and st.session_state.container_entries > 1:
                st.session_state.container_entries -= 1
    # Botón para enviar los datos ingresados
    if st.button("ENVIAR", key="send_button"):
        container_data = []
        for i in range(st.session_state.container_entries):
            container_data.append({
                "num_contenedor": st.session_state[f"container_number_{i}"],
                "doc_transporte": st.session_state.get(f"transport_document_{i}", ""),
                "naviera": st.session_state[f"shipping_company_{i}"]
            })
        
        # Obtener el user_id del estado de sesión y enviar los datos a la base de datos
        user_id = st.session_state.get('id')
        if user_id:
            add_container_data(user_id, container_data)
        else:
            st.error("No se ha encontrado el id del usuario. Por favor, inicie sesión nuevamente.")
    #uploaded_file = st.file_uploader("Excel con ETAs a validar", type=['xlsx'])
    
    #if uploaded_file is not None:
        #df = pd.read_excel(uploaded_file)
        #st.write("Vista previa del archivo:")
        #st.dataframe(df.head())
        
        #url_flujo = 'https://prod-43.westus.logic.azure.com:443/workflows/92297bf73c4b494ea9c4668c7a9569fe/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=aoHBBza4EuOoUsRdxDJFM_0N6Gf-jLR4tWCx3etWLP8'
        #if st.button("Ejecutar"):
            #with st.spinner("Consultando ETAs..."):
                #resultado = ejecucion_flujo_url(url_flujo)
            #st.write(resultado)

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