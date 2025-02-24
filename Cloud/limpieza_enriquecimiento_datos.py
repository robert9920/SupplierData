from flask import Flask, request, jsonify
import pandas as pd
import warnings
import re
from sqlalchemy import create_engine
from sqlalchemy import text
import os
from google.cloud import storage

### Se deben establecer como variables de environment a bd_password y GOOGLE_APPLICATION_CREDENTIALS

# Ignorar todas las advertencias
warnings.filterwarnings("ignore")
app = Flask(__name__)

######## Configuraciones conexión a base de datos de Render #######

db_user = "provdata_user"
db_password = os.getenv("db_password")
db_host = "dpg-cupo701u0jms73bq5ng0-a.virginia-postgres.render.com"
db_port = "5432"
db_name = "provdata_db"
table_name_sunat = "sunat_ruc_reducida"
table_name_buenos_contribuyentes = "sunat_buenos_contribuyentes"
table_name_agente_retencion = "sunat_agente_retencion"

######## Funciones #############

# Lectura de datos
def leer_datos(nombre_BD, n_row, sheet_name):
    file_path = "./BDInit/" + nombre_BD # Ruta base de datos
    print(file_path)
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, skiprows=n_row, header=0, sheet_name = sheet_name) # Se empieza con la lectura del csv desde la fila n_row
        elif file_path.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path, skiprows=n_row, header=0, sheet_name = sheet_name) # Se empieza con la lectura del excel desde la fila n_row
        else:
            raise ValueError("El archivo debe ser de tipo .csv, .xls o .xlsx")
        
        print("Archivo leído exitosamente")
        return df

    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return None
    
# Lectura de datos de la nube
def leer_datos_cloud(nombre_BD, n_row, sheet_name, bucket_name="bdprovinit"):
    # Inicializa el cliente de GCS
    client = storage.Client()

    # Obtiene el bucket
    bucket = client.bucket(bucket_name)

    # Obtiene el archivo (blob) desde el bucket
    blob = bucket.blob(nombre_BD)

    # Crea un archivo temporal para descargar el archivo
    temp_file = "/tmp/temp_file"  # Ruta temporal
    #temp_file = os.path.join(os.getcwd(), "temp_file")  # Ruta temporal en el directorio actual

    try:
        # Descarga el archivo a un archivo temporal
        blob.download_to_filename(temp_file)

        # Lee el archivo según su extensión
        if nombre_BD.endswith('.csv'):
            df = pd.read_csv(temp_file, skiprows=n_row, header=0)
        elif nombre_BD.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(temp_file, skiprows=n_row, header=0, sheet_name=sheet_name)
        else:
            raise ValueError("El archivo debe ser de tipo .csv, .xls o .xlsx")

        print("Archivo leído exitosamente desde GCS")
        return df

    except Exception as e:
        print(f"Error al leer el archivo desde GCS: {e}")
        return None
    finally:
        # Elimina el archivo temporal después de leerlo
        if os.path.exists(temp_file):
            os.remove(temp_file)
    
# Función para guardar datos en Google Cloud Storage    
def guardar_datos_gcp(df, nombre_archivo, bucket_name="bdprovmid"):
    # Inicializa el cliente de GCS
    client = storage.Client()

    # Obtiene el bucket
    bucket = client.bucket(bucket_name)

    # Crea un archivo temporal para guardar el DataFrame
    temp_file = "/tmp/temp_file.xlsx"
    #temp_file = os.path.join(os.getcwd(), "temp_file.xlsx")  # Ruta temporal en el directorio actual
    df.to_excel(temp_file, index=False)  # Guarda el DataFrame en un archivo Excel

    try:
        # Sube el archivo temporal al bucket de GCS
        blob = bucket.blob(nombre_archivo)
        blob.upload_from_filename(temp_file)
        print(f"Archivo {nombre_archivo} guardado exitosamente en GCS")
    except Exception as e:
        print(f"Error al guardar el archivo en GCS: {e}")
    finally:
        # Elimina el archivo temporal después de subirlo
        if os.path.exists(temp_file):
            os.remove(temp_file)

# Función para capitalizar la primera letra de cada nombre o apellido
def format_name(name):
    if pd.notna(name):
        return True, name.strip().title()  # Primra letra mayuscula, el resto minúscula
    else:
        return False, "Falta nombre/apellido"

# Función para validar correos electrónicos
def validate_email(email):
    regex = r'^[A-Za-z0-9áéíóúÁÉÍÓÚ._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}$'
    if pd.notna(email):
        separators = r"[ /;,]"
        emails = re.split(separators, email.strip())
        for e in emails:
            # Se revisa que no haya ningún "_" al inicio
            if e.startswith("_"):
                return False, "Formato de correo inválido: inicia con '_'"
            # Se revisa el formato del correo
            if not (re.fullmatch(regex, email.strip())):
                return False, "Formato de correo inválido"
        else:
            return True, None  # Todos los correos son válidos
    return False, "Falta correo"  

# Función para validar números de Perú
def validate_phone(phone):
    if pd.notna(phone):
        # Limpieza del número
        phone_str = str(phone).strip()
        phone_str = phone_str.replace(" ","")
        phone_str = phone_str.replace("+","")
        phone_str = phone_str.replace("-","")
        phone_str = phone_str.replace("(","")
        phone_str = phone_str.replace(")","")
        # Verficaciones del número, presenta diversos formatos
        if phone_str.isdigit():
            if len(phone_str) < 7:
                return False, "Longitud de número de teléfono no válida"
            if phone_str[0:3] == "051" and phone_str[3] == "9" and len(phone_str) == 12:
                num_real = phone_str[3:]
                return False, f"El número telefónico móvil presenta código de Perú y es el siguiente: {num_real}"
            elif phone_str[0:2] == "51" and phone_str[2] == "9" and len(phone_str) == 11:
                num_real = phone_str[2:]
                return False, f"El número telefónico móvil presenta código de Perú y es el siguiente: {num_real}"
            elif phone_str[2] == "9" and len(phone_str) == 11:
                num_real = phone_str[2:]
                cod_num = phone_str[0:2]
                return False, f"El número telefónico móvil identificado es el siguiente: {num_real}, con código: {cod_num}"
            elif phone_str[3] == "9" and len(phone_str) == 12:
                num_real = phone_str[3:]
                cod_num = phone_str[0:3]
                return False, f"El número telefónico móvil identificado es el siguiente: {num_real}, con código: {cod_num}"  
            elif len(phone_str) == 9 and phone_str.startswith("9"):  # Teléfono Móvil
                return True, None
            elif len(phone_str) == 7:  # Teléfono Fijo
                return True, None
            else:
                return False, "Longitud de número de teléfono no válida"
        else:
            return False, "El número telefónico contiene caracteres no numéricos"
    return False, "Falta numero telefónico"

# Función para validar el número de RUC
def validate_id_number(id_number):
    if pd.notna(id_number):
        id_str = str(id_number).strip()
        if id_str.isdigit() and len(id_str) == 11:
            return True, None
        else:
            return False, "RUC inválido (debe poseer 11 dígitos numéricos)"
    return False, "Falta el número de RUC"


################ Fin de funciones ######################

@app.route("/procesar", methods=["POST"])
def procesar():
    # Obtener los parámetros de la solicitud JSON
    data = request.json
    print("Datos recibidos:", data) # Depuración

    nombre_bd = data.get("nombre_bd")
    sheet_name = data.get("sheet_name")
    n_row = data.get("n_row")
    n_row = n_row - 1
    n_razonsocial = data.get("n_razonsocial")
    n_name = data.get("n_name")
    n_lastname = data.get("n_lastname")
    n_email = data.get("n_email")
    n_phone = data.get("n_phone")
    n_ruc = data.get("n_ruc")


    try:
        # Lectura de datos
        print(f"Leyendo archivo: {nombre_bd}, hoja: {sheet_name}")  # Depuración
        df = leer_datos_cloud(nombre_bd, n_row, sheet_name)
       
        if df is None:
            return jsonify({"message": "Error al leer el archivo desde GCS"}), 500
        
        # Se inicializa nueva columna para descripción de errores
        df['Descripción del error'] = ""
        # Se inicializan nuevas columnas para identificar el estado contribuyente y la condición de domicilio
        df['Estado Contribuyente'] = ""
        df["Condición Domicilio"] = ""
        # Se inicializan nuevas columnas para identificar agentes de retención y su fecha
        df['Agente Retención'] = ""
        df["Fecha Agente Retención"] = ""
        # Se inicializan nuevas columnas para identificar buenos contribuyentes y su fecha
        df['Buenos Contribuyentes'] = ""
        df["Fecha Buenos Contribuyentes"] = ""

        # Conexión a PostgreSQL
        engine = create_engine(f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")
        print("Conexión a la base de datos exitosa")

        # Diccionario de reemplazos para limpiar strings con tilde y puntos no deseados
        reemplazos = {
            'á': 'a',
            'é': 'e',
            'í': 'i',
            'ó': 'o',
            'ú': 'u',
            'Á': 'A',
            'É': 'E',
            'Í': 'I',
            'Ó': 'O',
            'Ú': 'U',
            '.': ''
        }
        tabla = str.maketrans(reemplazos)


        # Se realizan validaciones, correcciones y enriquecimiento de datos
        for index, row in df.iterrows():
            errors = []

            # Validar razón social con base de datos postgresql

            ruc = row[n_ruc - 1]
            razon_social = row[n_razonsocial - 1]

            if pd.notna(ruc):  # Revisar que RUC no sea nulo
                # Query para obtener la razon social utilizando el RUC
                query = text(f"SELECT nombre_razonsocial FROM {table_name_sunat} WHERE ruc = '{ruc}'")
                with engine.connect() as connection:
                    result = connection.execute(query).fetchone()
                
                if result:
                    correct_name = result[0]  # Se obtiene la razón social de la base de datos
                    if razon_social.strip().lower().translate(tabla) != correct_name.strip().lower().replace('.',''):
                        # Si los nombres no coinciden
                        error_message = f"Nombre de razón social incorrecto. Nombre correcto: {correct_name}"
                        errors.append(error_message)
                else:
                    # RUC no encontrado en la base de datos
                    error_message = "RUC no se encontró en la base de datos"
                    errors.append(error_message)

            if n_name != 999:
                # Validar / formatear "Nombre"
                name_valid, name_error_corrected = format_name(row[n_name-1])
                if  name_valid:
                    df.iloc[index, n_name-1] = name_error_corrected
                else:
                    errors.append(name_error_corrected)
            else:
                pass

            if n_lastname != 999:
                # Validar / formatear "Apellido"
                lastname_valid, lastname_error_corrected = format_name(row[n_lastname-1])
                if  lastname_valid:
                    df.iloc[index, n_lastname-1] = lastname_error_corrected
                else:
                    errors.append(lastname_error_corrected)
            else:
                pass

            if n_email != 999:
                # Validar "E-mail"
                email_valid, email_error = validate_email(row[n_email-1])
                if not email_valid:
                    errors.append(email_error)
            else:
                pass

            if n_phone != 999:
                # Validar "Teléfono"
                phone_valid, phone_error = validate_phone(row[n_phone-1])
                if not phone_valid:
                    errors.append(phone_error)
            else:
                pass

            # Validar "Número de identificación (RUC)"
            id_valid, id_error = validate_id_number(row[n_ruc-1])
            if not id_valid:
                errors.append(id_error)

            # Añadir errores encontrados a la columna "Descripción del error" 
            df.at[index, 'Descripción del error'] = "; ".join(errors)

            ###### Enriquecimiento de datos ######

            # Agentes de retención
            if pd.notna(ruc):  # Revisar que RUC no sea nulo
                # Query para verificar que RUC se encuentre en tabla de agentes de renteción
                query = text(f"SELECT a_partir_de FROM {table_name_agente_retencion} WHERE ruc = '{ruc}'")
                with engine.connect() as connection:
                    result = connection.execute(query).fetchone()
                if result:
                    fecha_agente_retencion = result[0]  # Se obtiene la fecha del agente de retención de la base de datos
                    df.at[index, 'Agente Retención'] = "Si"
                    df.at[index, 'Fecha Agente Retención'] = fecha_agente_retencion


            # Buenos Contribuyentes
            if pd.notna(ruc):  # Revisar que RUC no sea nulo
                # Query para verificar que RUC se encuentre en tabla de buenos contribuyentes
                query = text(f"SELECT a_partir_de FROM {table_name_buenos_contribuyentes} WHERE ruc = '{ruc}'")
                with engine.connect() as connection:
                    result = connection.execute(query).fetchone()
                if result:
                    fecha_buenos_contribuyentes = result[0]  # Se obtiene la fecha del buen contribuyente de la base de datos
                    df.at[index, 'Buenos Contribuyentes'] = "Si"
                    df.at[index, 'Fecha Buenos Contribuyentes'] = fecha_buenos_contribuyentes


            # Estado contribuyente
            if pd.notna(ruc):  # Revisar que RUC no sea nulo
                # Query para verificar que RUC se encuentre en tabla de sunat_actividades
                query = text(f"SELECT estado_contribuyente FROM {table_name_sunat} WHERE ruc = '{ruc}'")
                with engine.connect() as connection:
                    result = connection.execute(query).fetchone()
                if result:
                    estado_contribuyente = result[0]  # Se obtiene el valor del estado_contribuyente
                    df.at[index, 'Estado Contribuyente'] = estado_contribuyente

            # Condición domicilio
            if pd.notna(ruc):  # Revisar que RUC no sea nulo
                # Query para verificar que RUC se encuentre en tabla de sunat_actividades
                query = text(f"SELECT condicion_domicilio FROM {table_name_sunat} WHERE ruc = '{ruc}'")
                with engine.connect() as connection:
                    result = connection.execute(query).fetchone()
                if result:
                    condicion_domicilio = result[0]  # Se obtiene el valor de condicion_domicilio
                    df.at[index, 'Condición Domicilio'] = condicion_domicilio

        # Se guardan los datos modificados en el bucket de bdprovmid en GCP
        output_file = nombre_bd.split(".")[0] + "_mid.xlsx"
        guardar_datos_gcp(df, output_file)
    
        # Resultados finales
        resultado = f"Procesado: {nombre_bd}, {sheet_name}"
        return jsonify({"resultado": resultado}), 200

    except Exception as e:
        return jsonify({"message": f"Error en la función procesar: {e}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
