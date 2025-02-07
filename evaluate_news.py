from googlenews_getdata import extract_text
from googlenews_getdata import get_links_googlenews
from sqlalchemy import create_engine
from sqlalchemy import text
import pandas as pd
import os
from openai import OpenAI
import json

# Valores para conexión a Postgresql
db_user = "postgres"
db_password = "greciatech"
db_host = "127.0.0.1"
db_port = "5432"
db_name = "padron_ruc"
table_name = "googlenews_evaluation"

# Función para evaluar las noticias obtenida por cada proveedor
def evaluate_news(provname):

    # Cliente de OpenAI
    MODEL = "gpt-4o-mini"
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    # Se obtienen los links de todas las noticias encontradas del proveedor a evaluar
    links_found = get_links_googlenews(provname)

    # Verificamos si no hubo error en el proceso de web scrapping
    if links_found == None:
        print("Hubo un error en el proceso de web scrapping al intentar ubicar las noticias")
        return False

    if len(links_found) >= 1:
        # Se utilizan los links para obtener el texto de cada noticia
        text_found = []
        for link in links_found:
            data_extracted = extract_text(link)
            if data_extracted:
                text_found.append(data_extracted)

        # Verificamos que por lo menos haya 1 texto disponible para evaluar
        if len(text_found) >= 1:

            # Preparar los mensajes para la API de OpenAI
            messages = [
                {"role": "system", "content": f"Quiero que te comportes como un analista senior experto en evaluación de empresas. A continuación, voy a pasarte textos de noticias online de diferentes empresas, quiero que evalúes ese contenido en los siguientes puntos: Eventos Corporativos (Fusiones, adquisiciones, nuevas alianzas), Cambios en la dirección (Nuevos CEO, cambios en la junta directiva), Expansión o reducción (Apertura/cierre de sucursales, expansión de operaciones), Problemas legales (Demandas, sanciones, auditorías.), Sanciones y cumplimiento (Relacionadas con normativas ISO, ESG, cumplimiento), Innovaciones y lanzamientos (Nuevos productos o servicios), Situación financiera (Reportes de crecimiento o crisis financieras), Impacto en la reputación (Opiniones del mercado, quejas o comentarios negativos). Cuando termine de enviarte todas las noticias disponibles de la empresa, voy a enviar la palabra 'Finalizar', una vez que te envíe esa palabra, tú debes de enviarme un valor numérico por cada campo de evaluación, en base a la información enviada (-3: Extremadamente negativo, -2: Muy Negativo, -1: Negativo, 0: No hay información o no es influyente, 1: Positivo, 2: Muy Positivo, 3: Extremadamente Positivo). Tu respuesta debe ser un texto con diversas lineas, donde en una unica linea se encuentre únicamente el nombre del campo solicitado, y su puntuación, al inicio de cada linea colocar el nombre del campo correspondiente (usar el nombre exacto de estos campos, y poner ':' después del nombre del campo, por ejemplo: 'Campo A:', no usar tildes y no poner en negrita ni añadir otro simbolo especial como '*'): 'Eventos Corporativos', 'Cambios en la direccion', 'Expansion/reduccion', 'Problemas legales', 'Sanciones/cumplimiento', 'Innovaciones/lanzamientos', 'Situacion financiera', 'Impacto Reputacion' y 'Comentarios' (en este ultimo campo indicas cualquier comentario u observacion importante sobre la evaluacion). Debes de asegurarte de que la noticia sea sobre la empresa deseada, ahora, la empresa a objetivo es: {provname}."}
            ]

            # Añadir cada texto como un mensaje de usuario
            for text in text_found:
                messages.append({"role": "user", "content": text})

            # Añadir el mensaje de finalización
            messages.append({"role": "user", "content": "Finalizar"})

            try:
                # Llamar a la API de OpenAI
                response = client.chat.completions.create(
                    model= MODEL,
                    messages = messages
                )
                
                # Obtener la respuesta del modelo
                result = response.choices[0].message.content
                print(result)
                return result

            except json.decoder.JSONDecodeError as e:
                print(f"Error al decodificar la respuesta JSON: {e}")
                return False
        
            except Exception as e: # Cuando se envian muchos tokens como input, dependiendo del modelo, podría dar error
                print(f"Error inesperado: {e}")
                return False

        else:
            print("No se encontraron texto de noticias para evaluar")
            return ("Eventos Corporativos: 0\nCambios en la direccion: 0\nExpansion/reduccion: 0\nProblemas legales: 0\nSanciones/cumplimiento: 0\nInnovaciones/lanzamientos: 0\nSituacion financiera: 0\nImpacto Reputacion: 0\nComentarios: No se encontró información para evaluar al proveedor")
        
    else:
        print("No se encontraron links de noticias para evaluar")
        return ("Eventos Corporativos: 0\nCambios en la direccion: 0\nExpansion/reduccion: 0\nProblemas legales: 0\nSanciones/cumplimiento: 0\nInnovaciones/lanzamientos: 0\nSituacion financiera: 0\nImpacto Reputacion: 0\nComentarios: No se encontró información para evaluar al proveedor")
    
# Función para normalizar el output obtenido por la IA Gen
def normalize_data_IA_news(output_text, provname):
    try:
        # Diccionario donde se guardaran los datos
        data = {
            'proveedor': provname,
            'eventos_corporativos': '',
            'cambios_direccion': '',
            'expansion_reduccion': '',
            'problemas_legales': '',
            'sanciones_cumplimiento': '',
            'innovaciones_lanzamientos': '',
            'situacion_financiera': '',
            'impacto_reputacion': '',
            'comentarios': ''
        }
            
        # Dividir el texto en lineas
        lines = output_text.split('\n')

        # Iterar sobre cada linea para extraer los datos
        for line in lines:
            try:
                line = line.replace(":","")
            except:
                pass
            if 'Eventos Corporativos' in line:
                data['eventos_corporativos'] = line.split('Eventos Corporativos')[1].strip()
            elif 'Cambios en la direccion' in line:
                data['cambios_direccion'] = line.split('Cambios en la direccion')[1].strip()
            elif 'Expansion/reduccion' in line:
                data['expansion_reduccion'] = line.split('Expansion/reduccion')[1].strip()
            elif 'Problemas legales' in line:
                data['problemas_legales'] = line.split('Problemas legales')[1].strip()
            elif 'Sanciones/cumplimiento' in line:
                data['sanciones_cumplimiento'] = line.split('Sanciones/cumplimiento')[1].strip()
            elif 'Innovaciones/lanzamientos' in line:
                data['innovaciones_lanzamientos'] = line.split('Innovaciones/lanzamientos')[1].strip()
            elif 'Situacion financiera' in line:
                data['situacion_financiera'] = line.split('Situacion financiera')[1].strip()
            elif 'Impacto Reputacion' in line:
                data['impacto_reputacion'] = line.split('Impacto Reputacion')[1].strip()
            elif 'Comentarios' in line:
                data['comentarios'] = line.split('Comentarios')[1].strip()


        # Convertir diccionario a un dataframe
        df = pd.DataFrame([data])

        print(df) # Imprimir el dataframe
        return df
    
    except:
        print("No hay un resultado valido para normalizar")
        return pd.DataFrame()
    
# Función para subir la data normalizada a una tabla en Postgresql
def upload_key_data_news (key_data):
    
    engine = create_engine(f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}") # Conexión a Postgresql

    if not key_data.empty: # Verificamos que data frame no esté vacío
        try: 
            with engine.begin() as conn: # Utiliza `begin` para manejar automáticamente transacciones
                proveedor = key_data['proveedor'].iloc[0]  # Acceder al valor del proveedor en el DataFrame
                # Se elimina valor en caso ya existe de la tabla antes de insertar nuevos datos
                delete_query = f"DELETE FROM {table_name} WHERE proveedor = '{proveedor}';"  # Consulta directa
                conn.execute(text(delete_query))  # Envía la consulta como texto
                print(f"Valor {proveedor} limpiado correctamente.")
        except Exception as e:
            print(f"No se ha limpiado el dato de {proveedor}: {e}")

        # Se insertan datos en PostgreSQL
        key_data.to_sql(table_name, engine, if_exists="append", index=False)
        print(f"Datos de {proveedor} subidos a PostgreSQL en la tabla: {table_name}")
    else:
        print("No hay data normalizada para subir a PostgreSQL")

# Función para exportar datos de tabla como csv
def export_csv_news ():

    engine = create_engine(f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}") # Conexión a Postgresql

    # Leer la tabla en un DataFrame
    df = pd.read_sql(f"SELECT * FROM {table_name}", engine)

    # Guardar como CSV
    df.to_csv("./PostgreSQL/datos_exportados_google_news.csv", index=True, encoding="utf-8-sig")

    print("✅ Exportación completada: datos_exportados_google_news.csv")

if __name__ == "__main__":
    provname = input("Indicar nombre del proveedor a evaluar: ")
    # Se evaluan los textos de las noticias obtenidas por webscrapping
    result = evaluate_news(provname) 
    # Se normalizan esos datos y se retorna un dataframe con los valores evaluados
    key_data = normalize_data_IA_news(result, provname)
    # Se suben esos datos a Postgresql
    upload_key_data_news(key_data)
    # # Exportación de datos
    # export_csv_news()