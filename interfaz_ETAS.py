import streamlit as st
import pandas as pd
import requests
import psycopg2
import hashlib
import secrets
import datetime

# Limpiar la caché al inicio
st.cache_data.clear()
st.cache_resource.clear()

def generate_reset_token():
    return secrets.token_urlsafe(32)

# Conexión a la base de datos
def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname="consultaETAS",
            user="postgres",
            password="Daniel2030#",
            host="2.tcp.ngrok.io",
            port="16511"
        )
        return conn
    except psycopg2.Error as e:
        st.error(f"Error al conectar a la base de datos: {e}")
        return None

# Inicializar lista de entradas
entries = [{"num_contenedor": "", "naviera": ""}]

# Función para agregar una nueva entrada
def add_entry():
    entries.append({"num_contenedor": "", "naviera": ""})

# Función para eliminar la última entrada
def remove_entry():
    if len(entries) > 1:
        entries.pop()

# Función para hashear la contraseña
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Función para registrar al usuario en la base de datos
def register_user(username, password, company, fullname, cellnumber, email_registro):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        hashed_password = hash_password(password)
        try:
            cursor.execute("INSERT INTO usuario (username, password, company, fullname, cellnumber, email_registro) VALUES (%s, %s, %s, %s, %s, %s)", (username, hashed_password, company, fullname, cellnumber, email_registro))
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
        INSERT INTO consulta (num_contenedor, naviera, usuario_id)
        VALUES (%s, %s, %s)
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
                cursor.execute(insert_query, (data["num_contenedor"], data["naviera"], user_id))
            conn.commit()
            st.success("Información cargada, pronto recibirá un email dando inicio al proceso de consulta de ETAS.")
        except psycopg2.Error as e:
            st.error(f"Error al cargar los datos: {e}")
        finally:
            cursor.close()
            conn.close()

def history_view():
    st.title("Historial de Registro de Contenedores")
    
    user_id = st.session_state.get('id')
    if not user_id:
        st.error("No se ha enocntrado el id del usuario. Por favor inicie sesión nuevamente.")
        return
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            # Consulta SQL para obtener los registros del usuario
            query = """
            SELECT c.num_contenedor, c.naviera, r.eta
            FROM consulta c
            LEFT JOIN resultado r ON c.id = r.id_consulta
            WHERE c.usuario_id = %s
            ORDER BY c.id DESC
            """
            cursor.execute(query, (user_id,))
            records = cursor.fetchall()
            
            if records:
                for idx, record in enumerate(records):
                    num_contenedor, naviera, eta = record
                # Crear un DataFrame para mostrar los datos
                #df = pd.DataFrame(records, columns=['Número de Contenedor', 'Naviera', 'ETA'])
                #df['ETA'] = df['ETA'].fillna('No disponible')
                #st.dataframe(df)
                
                    # Organizar los campos en columnas
                    col1, col2, col3 = st.columns(3)
    
                    with col1:
                        st.text_input("Número de Contenedor", value=num_contenedor, key=f'num_contenedor_{idx}', disabled=False)
                    with col2:
                        st.text_input("Naviera", value=naviera, key=f'naviera_{idx}', disabled=False)
                    with col3:
                        st.text_input("ETA", value=eta, key=f'eta_{idx}', disabled=False)

    
                    st.markdown("---")  # Línea de separación entre registros
                
            else:
                st.info("No se han encontrado registros.")
        except psycopg2.Error as e:
            st.error(f"Error al obtener los registros: {e}")
        finally:
            cursor.close()
            conn.close()
    else:
        st.error("No se pudo conectar a la base de datos.")

    # Botón para regresar a la vista principal
    if st.button("Volver"):
        st.session_state['current_view'] = 'main'
        st.rerun()
        
# Vista de registro e inicio de sesión
def register_or_login_view():
    st.markdown("""
    <h1 style='text-align: center;'>Alerta de ETAs</h1>
    """, unsafe_allow_html=True)

    # Radio buttons para seleccionar Registro o Login
    option = st.radio("Seleccione una opción:", ("Registro", "Login"))
    
    if option == "Registro":
        nombre_completo = st.text_input("Nombre Completo", key="nombre_input")
        correo = st.text_input("Correo electrónico", key="correo_input")
        num_celular = st.text_input("Número de celular", key="celular_input")
        usuario = st.text_input("Usuario", key="usuario_registro")
        empresa = st.text_input("Organización a la que pertenece", key="empresa_registro")
        contrasena = st.text_input("Contraseña", type="password", key="contrasena_registro")
        
        if st.button("Registrarse"):
            if usuario and contrasena and empresa and nombre_completo and correo and num_celular :
                register_user(usuario, contrasena, empresa, nombre_completo, num_celular, correo)
            else:
                st.error("Por favor complete todos los campos")
                
    elif option == "Login":
        usuario = st.text_input("Usuario", key="usuario_login")
        contrasena = st.text_input("Contraseña", type="password", key="contrasena_login")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Entrar"):
                if usuario and contrasena:
                    user_id, email = login_user(usuario, contrasena)
                    if user_id:
                        st.session_state['current_view'] = 'main'
                        st.session_state['id'] = user_id
                        st.session_state['email'] = email
                        #st.success("Inicio de sesión exitoso")
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos")
                else:
                    st.error("Por favor complete todos los campos")
        with col2:
            if st.button("¿Olvidaste tu contraseña?"):
                st.session_state['current_view'] = 'forgot_password'
                st.rerun()

def send_password_reset_email(email):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM usuario WHERE email_registro = %s", (email,))
        result = cursor.fetchone()
        if result:
            user_id = result[0]
            token = generate_reset_token()
            expiration = datetime.datetime.now() + datetime.timedelta(hours=1)  # Token válido por 1 hora
            cursor.execute("""
                UPDATE usuario SET reset_token = %s, token_expiration = %s WHERE id = %s
            """, (token, expiration, user_id))
            conn.commit()
            cursor.close()
            conn.close()
            # Construye el enlace de restablecimiento
            reset_link = f"{st.secrets['app_url']}?token={token}"
            # Envía el correo electrónico
            send_reset_email_via_power_automate(email, reset_link)
            st.success("Se ha enviado un enlace de recuperación a su correo electrónico")
        else:
            st.error("El correo electrónico no está registrado")
    else:
        st.error("No se pudo conectar a la base de datos")

def forgot_password_view():
    st.title("Recuperar contraseña")
    email = st.text_input("Ingrese su correo electrónico registrado")

    if st.button("Enviar enlace de recuperación"):
        if email:
            # Aquí llamas a la función para generar y enviar el token de recuperación
            send_password_reset_email(email)
        else:
            st.error("Por favor ingrese su correo electrónico")
            
    # Botón para regresar a la vista principal
    if st.button("Volver"):
        st.session_state['current_view'] = 'login'
        st.rerun()

# Vista de registro e inicio de sesión
#def register_or_login_view():
    #st.markdown("""
    #<h1 style='text-align: center;'>Alerta de ETAs</h1>
    #<h3 style='text-align: left;'>Registro o Login</h3>
    #""", unsafe_allow_html=True)
    
    #nombre_completo = st.text_input("Nombre Completo", key="nombre_input")
    #correo = st.text_input("Correo electrónico", key="correo_input")
    #num_celular = st.text_input("Número de celular", key="celular_input")
    #usuario = st.text_input("Usuario", key="usuario_input")
    #empresa = st.text_input("Organización a la que pertenece: **(solo necesario en el registro)**", key="empresa_input")
    #contrasena = st.text_input("Contraseña", type="password", key="contrasena_input")
    
    #col1, col2 = st.columns(2)
    #with col1:
        #if st.button("Registrarse"):
            #if usuario and contrasena and empresa:
                #register_user(usuario, contrasena, empresa)
            #else:
                #st.error("Por favor complete todos los campos")
    
    #with col2:
        #if st.button("Entrar"):
            #if usuario and contrasena:
                #user_id, email = login_user(usuario, contrasena)
                #if user_id:
                    #st.session_state['current_view'] = 'main'
                    #st.session_state['id'] = user_id
                    #st.session_state['email'] = email
                    #st.success("Inicio de sesión exitoso")
                #else:
                    #st.error("Usuario o contraseña incorrectos")
            #else:
                #st.error("Por favor complete todos los campos")

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

def reset_password_view():
    st.title("Restablecer contraseña")
    new_password = st.text_input("Nueva contraseña", type="password")
    confirm_password = st.text_input("Confirmar nueva contraseña", type="password")

    if st.button("Restablecer contraseña"):
        if new_password and confirm_password:
            if new_password == confirm_password:
                reset_token = st.session_state.get('reset_token')
                if reset_token:
                    reset_user_password(reset_token, new_password)
                else:
                    st.error("Token inválido o expirado")
            else:
                st.error("Las contraseñas no coinciden")
        else:
            st.error("Por favor complete todos los campos")


def reset_user_password(token, new_password):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, token_expiration FROM usuario WHERE reset_token = %s
        """, (token,))
        result = cursor.fetchone()
        if result:
            user_id, token_expiration = result
            if datetime.datetime.now() <= token_expiration:
                hashed_password = hash_password(new_password)
                cursor.execute("""
                    UPDATE usuario SET password = %s, reset_token = NULL, token_expiration = NULL WHERE id = %s
                """, (hashed_password, user_id))
                conn.commit()
                st.success("Su contraseña ha sido restablecida con éxito")
                # Redirige al inicio de sesión
                st.session_state['current_view'] = 'login'
                st.rerun()
            else:
                st.error("El token ha expirado")
        else:
            st.error("Token inválido")
        cursor.close()
        conn.close()
    else:
        st.error("No se pudo conectar a la base de datos")
        
def send_reset_email_via_power_automate(email, reset_link):
    url_flujo = 'https://prod-46.westus.logic.azure.com:443/workflows/2c790776e8dc4d4da8b989951118c351/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=kN1PXGi0pFFHgrI7lls5DNNstlBg8YtEApIBkrlwYkE'
    headers = {'Content-Type': 'application/json'}
    data = {
        "correo": email,
        "reset_link": reset_link
    }
    response = requests.post(url_flujo, headers=headers, json=data)
    if response.status_code in (200, 202):
        print("Correo de restablecimiento enviado correctamente.")
    else:
        print(f"Error al enviar el correo de restablecimiento: {response.status_code}")        
        
# Vista principal de la aplicación después de iniciar sesión
def main_view():
    #url_flujo = 'https://prod-43.westus.logic.azure.com:443/workflows/92297bf73c4b494ea9c4668c7a9569fe/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=aoHBBza4EuOoUsRdxDJFM_0N6Gf-jLR4tWCx3etWLP8'

    st.title("Alerta de ETAs")
    
    registered_email = st.session_state.get('email', '')
    
    #correo = st.text_input("Correo de notificación", value=st.session_state.get('email."'))
    
    # Establecer el correo electrónico registrado como valor predeterminado en el campo de entrada
    correo = st.text_input("Correo de notificación", value=registered_email)
    
    # Inicializar el contador de entradas si no existe
    if 'container_entries' not in st.session_state:
        st.session_state.container_entries = 1

    # Crear un formulario dinámico
    for i in range(st.session_state.container_entries):
        st.subheader(f"Entrada {i + 1}")
        
        # Crear dos columnas para alinear los campos horizontalmente
        col1, col2 = st.columns(2)
        with col1:
            st.text_input(f"**Número de contenedor**", key=f"container_number_{i}")
        #with col2:
            #st.text_input(f"**Documento de transporte**", key=f"transport_document_{i}")
        with col2:
            st.selectbox("**Naviera**",["Evergreen","CMA-CGM","Maersk","ONE","Hapag-Lloyd", "Otra"], key=f"shipping_company_{i}")
    
        
    #col_add, col_delete = st.columns(2)
    #with col_add:
        # Botón para agregar otra entrada
        #if st.button("Agregar otra entrada"):
            #st.session_state.container_entries += 1
    #if st.session_state.container_entries > 1:
        #with col_delete:
            #if st.button("Eliminar entrada")and st.session_state.container_entries > 1:
                #st.session_state.container_entries -= 1
    col1, col2 = st.columns(2)
    with col1:
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
                #doc_transporte = st.session_state.get(f"transport_document_{i}", "").strip()
                naviera = st.session_state[f"shipping_company_{i}"]
                
                # Validar campos
                if not num_contenedor:
                    all_fields = False
                    missing_fields_messages.append(f"El campo 'Número de contenedor' en la entrada {i+1} es obligatorio.")
                #if not doc_transporte:
                    #all_fields = False
                    #missing_fields_messages.append(f"El campo 'Documento de transporte' en la entrada {i+1} es obligatorio.")
                if not naviera:
                    all_fields = False
                    missing_fields_messages.append(f"El campo 'Naviera' en la entrada {i+1} es obligatorio.")
                
                container_data.append({
                    "num_contenedor": num_contenedor,
                    #doc_transporte": doc_transporte,
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
    with col2:
        if st.button("Historial de Registro"):
            st.session_state['current_view'] = 'history'
            st.rerun()

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
    # Verificar si hay un token de restablecimiento en los parámetros de la URL
    query_params = st.experimental_get_query_params()
    if 'token' in query_params:
        token = query_params['token'][0]
        st.session_state['reset_token'] = token
        st.session_state['current_view'] = 'reset_password'
        # Limpiar los parámetros de la URL para evitar bucles infinitos
        st.experimental_set_query_params()
        st.rerun()
        
    if 'current_view' not in st.session_state:
        st.session_state['current_view'] = 'login'

    if st.session_state['current_view'] == 'login':
        register_or_login_view()
    elif st.session_state['current_view'] == 'main':
        main_view()
    elif st.session_state['current_view'] == 'forgot_password':
        forgot_password_view()
    elif st.session_state['current_view'] == 'reset_password':
        reset_password_view()
    elif st.session_state['current_view'] == 'history':
        history_view()

if __name__ == "__main__":
    main()


#https://prod-43.westus.logic.azure.com:443/workflows/92297bf73c4b494ea9c4668c7a9569fe/triggers/manual/paths/invoke?api-version=2016-06-01