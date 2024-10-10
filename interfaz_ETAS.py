import streamlit as st
import pandas as pd
import requests
import psycopg2
import hashlib

# Limpiar la caché al inicio
st.cache_data.clear()
st.cache_resource.clear()

# Conexión a la base de datos
def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname="consultaETAS",
            user="postgres",
            password="Daniel2030#",
            host="6.tcp.ngrok.io",
            port="15124"
        )
        return conn
    except psycopg2.Error as e:
        st.error(f"Error al conectar a la base de datos: {e}")
        return None

# Inicializar lista de entradas
entries = [{"num_contenedor": "", "doc_transporte": "", "naviera": ""}]

# Función para agregar una nueva entrada
def add_entry():
    entries.append({"num_contenedor": "", "doc_transporte": "", "naviera": ""})

# Función para eliminar la última entrada
def remove_entry():
    if len(entries) > 1:
        entries.pop()

# Función para hashear la contraseña
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Función para registrar al usuario en la base de datos
def register_user(username, password, company):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        hashed_password = hash_password(password)
        try:
            cursor.execute("INSERT INTO usuario (username, password, company) VALUES (%s, %s, %s)", (username, hashed_password, company))
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
        cursor.execute("SELECT id, email FROM usuario WHERE username = %s AND password = %s", (username, hashed_password))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result:
            return result[0], result[1] #retorna el id del usuario y el correo
    return None, None

# Función para agregar los datos de contenedores a la tabla "consulta"
def add_container_data(user_id, container_data, correo):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        insert_query = """
        INSERT INTO consulta (num_contenedor, doc_transporte, naviera, usuario_id)
        VALUES (%s, %s, %s, %s)
        """
        
        #Consulta para actualizar el correo en la tabla 'usuario'
        update_email ="""
        UPDATE usuario SET email = %s WHERE id = %s
        """
        try:
            # Si el correo es nuevo o cambió, actualizar el correo en la tabla usuario
            if st.session_state.get('email') != correo:
                cursor.execute(update_email, (correo, user_id))
                st.session_state['email'] = correo  # Actualiza el estado con el nuevo correo
            
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
    empresa = st.text_input("Organización a la que pertenece: **(solo necesario en el registro)**", key="empresa_input")
    contrasena = st.text_input("Contraseña", type="password", key="contrasena_input")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Registrarse"):
            if usuario and contrasena and empresa:
                register_user(usuario, contrasena, empresa)
            else:
                st.error("Por favor complete todos los campos")
    
    with col2:
        if st.button("Entrar"):
            if usuario and contrasena:
                user_id, email = login_user(usuario, contrasena)
                if user_id:
                    st.session_state['current_view'] = 'main'
                    st.session_state['id'] = user_id
                    st.session_state['email'] = email
                    st.success("Inicio de sesión exitoso")
                else:
                    st.error("Usuario o contraseña incorrectos")
            else:
                st.error("Por favor complete todos los campos")

#Enviar datos al flujo de Power Automate Nube
def send_to_power_automate(correo, num_contenedor):
    url_flujo = 'https://prod-43.westus.logic.azure.com:443/workflows/92297bf73c4b494ea9c4668c7a9569fe/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=aoHBBza4EuOoUsRdxDJFM_0N6Gf-jLR4tWCx3etWLP8'
    headers = {'Content-Type': 'application/json'}
    data = {
        "correo": correo,
        "num_contenedor": num_contenedor
    }
    response = requests.post(url_flujo, headers=headers, json=data)
    if response.status_code in (200, 202):
        #st.success("Datos enviados a Power Automate correctamente.")
        print("Datos enviados a Power Automate correctamente.")

    else:
        #st.error(f"Error al enviar los datos a Power Automate: {response.status_code}")
        print(f"Error al enviar los datos a Power Automate: {response.status_code}")



# Vista principal de la aplicación después de iniciar sesión
def main_view():
    #url_flujo = 'https://prod-43.westus.logic.azure.com:443/workflows/92297bf73c4b494ea9c4668c7a9569fe/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=aoHBBza4EuOoUsRdxDJFM_0N6Gf-jLR4tWCx3etWLP8'

    st.title("Alerta de ETAs")
    
    registered_email = st.session_state.get('email', '')
    
    #correo = st.text_input("Correo de notificación", value=st.session_state.get('email."'))
    
    # Establecer el correo electrónico registrado como valor predeterminado en el campo de entrada
    correo = st.text_input("Correo de notificación", value=registered_email)
    
    # Inicializar el contador de entradas si no existe
    #if 'container_entries' not in st.session_state:
        #st.session_state.container_entries = 1
        
    col_add, col_delete = st.columns(2)
    with col_add:
        # Botón para agregar otra entrada
        if st.button("Agregar otra entrada"):
            add_entry()
            #st.session_state.container_entries += 1
    #if st.session_state.container_entries > 1:
    with col_delete:
        if len(entries) > 1 and st.button("Eliminar entrada"):
            remove_entry()    
            #st.session_state.container_entries -= 1
    
    # Crear un formulario dinámico
    for i in range(st.session_state.container_entries):
        st.subheader(f"Entrada {i + 1}")
        
        # Crear tres columnas para alinear los campos horizontalmente
        col1, col2, col3 = st.columns(3)
        with col1:
            st.text_input(f"**Número de contenedor**", key=f"container_number_{i}")
        with col2:
            st.text_input(f"**Documento de transporte**", key=f"transport_document_{i}")
        with col3:
            st.selectbox("**Naviera**",["Evergreen","CMA-CGM","Maersk","ONE","Hapag-Lloyd", "Otra"], key=f"shipping_company_{i}")
    
        
   
    # Botón para enviar los datos ingresados
    if st.button("Enviar", key="send_button"):
        #Inicializar bandera para verificar que todos los campos estén completos
        all_fields = True
        missing_fields_messages = []
        
        # Verificar si el correo está completo
        if not correo:
            all_fields = False
            missing_fields_messages.append("El campo 'Correo de notificación' es obligatorio.")
        
        container_data = []
        for i in range(st.session_state.container_entries):
            num_contenedor = st.session_state[f"container_number_{i}"].strip()
            doc_transporte = st.session_state.get(f"transport_document_{i}", "").strip()
            naviera = st.session_state[f"shipping_company_{i}"]
            
            # Validar campos
            if not num_contenedor:
                all_fields = False
                missing_fields_messages.append(f"El campo 'Número de contenedor' en la entrada {i+1} es obligatorio.")
            if not doc_transporte:
                all_fields = False
                missing_fields_messages.append(f"El campo 'Documento de transporte' en la entrada {i+1} es obligatorio.")
            if not naviera:
                all_fields = False
                missing_fields_messages.append(f"El campo 'Naviera' en la entrada {i+1} es obligatorio.")
            
            container_data.append({
                "num_contenedor": num_contenedor,
                "doc_transporte": doc_transporte,
                "naviera": naviera
            })
        if all_fields:
            # Obtener el user_id del estado de sesión y enviar los datos a la base de datos
            user_id = st.session_state.get('id')
            if user_id:
                add_container_data(user_id, container_data, correo)
                # Enviar el correo y el primer número de contenedor a Power Automate
                send_to_power_automate(correo, container_data[0]["num_contenedor"])
            else:
                st.error("No se ha encontrado el id del usuario. Por favor, inicie sesión nuevamente.")
        else:
            st.error ("Hay campos sin completar")

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