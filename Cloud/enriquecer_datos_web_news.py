from google_extract_data import extract_data_links_openAI
from google_extract_data import normalize_data_IA_web
from google_extract_data import upload_key_data_web
# from evaluate_news import evaluate_news
# from evaluate_news import normalize_data_IA_news
# from evaluate_news import upload_key_data_news
# from evaluate_news import export_csv_news
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text
import os
from google.cloud import storage
from flask import Flask, request, jsonify

# App Flask
app = Flask(__name__)

# Valores para conexión a Postgresql
db_user = "provdata_user"
db_password = os.getenv("db_password")
db_host = "dpg-cupo701u0jms73bq5ng0-a.virginia-postgres.render.com"
db_port = "5432"
db_name = "provdata_db"
table_name_web = "googleweb_datos" # tabla donde se encuentran los datos extraidos de la web
table_name_news = "googlenews_evaluation" # tabla donde se encuentran las evaluaciones realizadas en base a noticias
table_name_sunat = "sunat_ruc_reducida" # tabla donde se encuentran datos genéricos

# Lectura de datos de la nube
def leer_datos_cloud(nombre_BD, n_row, sheet_name, bucket_name="bdprovmid"):
    # Inicializa el cliente de GCS
    client = storage.Client()

    # Obtiene el bucket
    bucket = client.bucket(bucket_name)

    # Obtiene el archivo (blob) desde el bucket
    blob = bucket.blob(nombre_BD)

    # Crea un archivo temporal para descargar el archivo
    #temp_file = "/tmp/temp_file"  # Ruta temporal
    temp_file = os.path.join(os.getcwd(), "temp_file")  # Ruta temporal en el directorio actual

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

################ Fin de funciones ######################

@app.route('/enriquecer_datos_web_news', methods=['POST'])
def enriquecer_datos_web_news():

    # Contador de cuantos datos no se han subido a base de datos
    missing_web = 0
    # Obtener los parámetros de la solicitud JSON
    data = request.json
    print("Datos recibidos:", data) # Depuración
    # Solicitud de datos
    nombre_bd = data.get("nombre_bd")
    sheet_name = data.get("sheet_name")
    n_row = data.get("n_row")
    n_row = n_row - 1
    n_ruc = data.get("n_ruc")
    n_razonsocial = data.get("n_razonsocial")

    try:
        # Lectura de datos
        df = leer_datos_cloud(nombre_bd, n_row, sheet_name)

        # Conexión a Postgresql
        engine = create_engine(f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}") 

        # Se itera sobre todo el pandas dataframe
        for index, row in df.iterrows():

            ruc = row[n_ruc-1]
            razon_social = row[n_razonsocial-1]

            if pd.notna(ruc): # RUC no es nulo
                # Query para obtener la razón social usando el RUC
                query = text(f"SELECT nombre_razonsocial FROM {table_name_sunat} WHERE ruc = '{ruc}'")
                with engine.connect() as connection:
                    result = connection.execute(query).fetchone()
                
                # Proceso si se tienen datos del ruc en Postgre
                if result: # RUC registrado en Base de Datos
                    provname = result[0] # Se obtiene la razón social de la base de datos de SUNAT
                    # Se verifica que no existan datos del proveedor ya subidos a la tabla web
                    query = text(f"SELECT * FROM {table_name_web} WHERE proveedor = '{provname}'")
                    with engine.connect() as connection:
                        result = connection.execute(query).fetchone()
                        if not result:
                            # Proceso para datos Web
                            result_web = extract_data_links_openAI(provname) # Se extrae data de la web del proveedor y ChatGPT la ordena por campos
                            key_data_web = normalize_data_IA_web(result_web, provname) # Se normaliza la data provista por ChatGPT y se retorna un df con los valores clave
                            upload_key_data_web(key_data_web) # Se suben datos de la web a PostgreSQL
                            if success:
                                missing_web += 1
                        else:
                            print(f"Ya se tiene información sobre {provname} en tabla de datos web")
                    # Se verifica que no existan datos del proveedor ya subidos a la tabla google news
                    # query = text(f"SELECT * FROM {table_name_news} WHERE proveedor = '{provname}'")
                    # with engine.connect() as connection:
                    #     result = connection.execute(query).fetchone()
                    #     if not result:
                    #         # Proceso para datos google news
                    #         result_news, links_used = evaluate_news(provname) # Se extrae data de la web del proveedor y ChatGPT la ordena por campos
                    #         key_data_news = normalize_data_IA_news(result_news, provname, links_used) # Se normaliza la data provista por ChatGPT y se retorna un df con los valores clave
                    #         upload_key_data_news(key_data_news) # Se suben datos de la web a PostgreSQL
                    #     else:
                    #         print(f"Ya se tiene información sobre {provname} en tabla de google news")

                else: # RUC no registrado en Base de Datos
                    provname = razon_social
                    # Se verifica que no existan datos del proveedor ya subidos a la tabla web
                    query = text(f"SELECT * FROM {table_name_web} WHERE proveedor = '{provname}'")
                    with engine.connect() as connection:
                        result = connection.execute(query).fetchone()
                        if not result:
                            # Proceso para datos Web
                            result_web = extract_data_links_openAI(provname) # Se extrae data de la web del proveedor y ChatGPT la ordena por campos
                            key_data_web = normalize_data_IA_web(result_web, provname) # Se normaliza la data provista por ChatGPT y se retorna un df con los valores clave
                            success = upload_key_data_web(key_data_web) # Se suben datos de la web a PostgreSQL
                            if success:
                                missing_web += 1
                        else:
                            print(f"Ya se tiene información sobre {provname} en tabla de datos web")
                    # Se verifica que no existan datos del proveedor ya subidos a la tabla google news
                    # query = text(f"SELECT * FROM {table_name_news} WHERE proveedor = '{provname}'")
                    # with engine.connect() as connection:
                    #     result = connection.execute(query).fetchone()
                    #     if not result:
                    #         # Proceso para datos google news
                    #         result_news, links_used = evaluate_news(provname) # Se extrae data de la web del proveedor y ChatGPT la ordena por campos
                    #         key_data_news = normalize_data_IA_news(result_news, provname, links_used) # Se normaliza la data provista por ChatGPT y se retorna un df con los valores clave
                    #         upload_key_data_news(key_data_news) # Se suben datos de la web a PostgreSQL
                    #     else:
                    #         print(f"Ya se tiene información sobre {provname} en tabla de google news")

        print(f"Falta evaluar {missing_web} proveedores en tabla google web")
        return jsonify({"resultado": f"Proceso de subida de datos finalizado. Faltan {missing_web} proveedores en tabla google web."}), 200

    except Exception as e:
        print(f"Error en la función enriquecer_datos_web_news: {e}")
        return jsonify({"resultado": "Error en la función enriquecer_datos_web_news"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
    
