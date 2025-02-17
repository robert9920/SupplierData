from google_extract_data import extract_data_links_openAI
from google_extract_data import normalize_data_IA_web
from google_extract_data import upload_key_data_web
from google_extract_data import export_csv_web
from evaluate_news import evaluate_news
from evaluate_news import normalize_data_IA_news
from evaluate_news import upload_key_data_news
from evaluate_news import export_csv_news
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text

# Valores para conexión a Postgresql
db_user = "postgres"
db_password = "greciatech"
db_host = "127.0.0.1"
db_port = "5432"
db_name = "ProvData"
table_name_web = "googleweb_datos" # tabla donde se encuentran los datos extraidos de la web
table_name_news = "googlenews_evaluation" # tabla donde se encuentran las evaluaciones realizadas en base a noticias
table_name_sunat = "sunat_ruc" # tabla donde se encuentran datos genéricos

# Lectura de datos
def read_data(BD_name, n_row, sheet_name):
    file_path = "./BD_corregidas/" + BD_name # Ruta base de datos
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

if __name__ == "__main__":
    # Solicitud de datos
    BD_name = input("Por favor, escriba el nombre de la Base de Datos (junto con su extensión .csv, .xls o .xlsx): ") # Nombre Base Datos
    sheet_name = input("Por favor, escriba el nombre de la hoja donde se encuentra la BD: ") # Nombre Hoja de la tabla de la BD
    n_row = int(input("Escriba el número de fila para empezar a leer el archivo: ")) # Número de fila donde inician los datos
    n_row = n_row - 1

    # Lectura de datos
    df = read_data(BD_name, n_row, sheet_name)

    # Número de columna donde está el RUC y razón social
    n_ruc = int(input("Escriba el número de la columna donde se encuentran los datos del RUC: ")) 
    n_razonsocial = int(input("Escriba el número de la columna donde se encuentra los datos de la Razón Social: ")) 

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
                    else:
                        print(f"Ya se tiene información sobre {provname} en tabla de datos web")
                # Se verifica que no existan datos del proveedor ya subidos a la tabla google news
                query = text(f"SELECT * FROM {table_name_news} WHERE proveedor = '{provname}'")
                with engine.connect() as connection:
                    result = connection.execute(query).fetchone()
                    if not result:
                        # Proceso para datos google news
                        result_news, links_used = evaluate_news(provname) # Se extrae data de la web del proveedor y ChatGPT la ordena por campos
                        key_data_news = normalize_data_IA_news(result_news, provname, links_used) # Se normaliza la data provista por ChatGPT y se retorna un df con los valores clave
                        upload_key_data_news(key_data_news) # Se suben datos de la web a PostgreSQL
                    else:
                        print(f"Ya se tiene información sobre {provname} en tabla de google news")

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
                        upload_key_data_web(key_data_web) # Se suben datos de la web a PostgreSQL
                    else:
                        print(f"Ya se tiene información sobre {provname} en tabla de datos web")
                # Se verifica que no existan datos del proveedor ya subidos a la tabla google news
                query = text(f"SELECT * FROM {table_name_news} WHERE proveedor = '{provname}'")
                with engine.connect() as connection:
                    result = connection.execute(query).fetchone()
                    if not result:
                        # Proceso para datos google news
                        result_news, links_used = evaluate_news(provname) # Se extrae data de la web del proveedor y ChatGPT la ordena por campos
                        key_data_news = normalize_data_IA_news(result_news, provname, links_used) # Se normaliza la data provista por ChatGPT y se retorna un df con los valores clave
                        upload_key_data_news(key_data_news) # Se suben datos de la web a PostgreSQL
                    else:
                        print(f"Ya se tiene información sobre {provname} en tabla de google news")


    
    print("Proceso de subida de datos finalizado a tablas web y google news")