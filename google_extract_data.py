import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import openai
from sqlalchemy import create_engine
from sqlalchemy import text
import pandas as pd
import os
from openai import OpenAI

# Valores para conexión a Postgresql
db_user = "postgres"
db_password = "greciatech"
db_host = "127.0.0.1"
db_port = "5432"
db_name = "padron_ruc"
table_name = "googleweb_datos"

# Función para extraer todo el texto de las páginas webs 
def extract_text(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    
    try:
        # Enviar una solicitud GET
        response = requests.get(url, headers=headers)
        # Verificar si la solicitud fue exitosa
        if response.status_code == 200:
            # Obtener el contenido HTML y usar BeautifulSoup para analizar el HTML
            soup = BeautifulSoup(response.text, "html.parser")
            # Extraer y devolver solo el contenido de texto, ignorando las etiquetas HTML
            return soup.get_text(separator=" ", strip=True)
        else:
            print(f"Error {response.status_code}: Acceso denegado a {url}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión: {e}")
        return False

# Función para obtener 5 links de google del proveedor que se indique
def get_links_googleweb(provname):

    # Lista final de links a considerar
    links_web = list()  

    # URL de Google Web
    url = "https://www.google.com.pe/?hl=es"

    # Configuración de opciones de Chrome
    chrome_options = Options()
    #chrome_options.add_argument("--headless")  # Ejecutar en modo sin cabeza (sin interfaz gráfica)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Evitar detección de automatización

    # Driver de Google Chrome
    driver = webdriver.Chrome(options=chrome_options)

    # Se accede a Google Web
    driver.maximize_window()
    driver.get(url)

    time.sleep(2)

    ##### Primera busqueda ###########
    ## Keyword: Nombre del proveedor
    ## Se extraen 3 resultados de esta búsqueda

    # Se imprime el nombre del proveedor en la barra de búsqueda de Google Web
    prov_field = driver.find_element(By.XPATH, value="//textarea[@id='APjFqb']")
    prov_field.send_keys(provname)
    prov_field.send_keys(Keys.RETURN)

    time.sleep(2) # Tiempo de espera

    # Se buscan las páginas web obtenidas
    search_results = driver.find_elements(By.CSS_SELECTOR, "div.g")
  
    # Existen páginas que se van a ignorar en esta búsqueda
    webs_ignore = ["computrabajo","twitter","pdf","linkedin", "universidadperu","facebook", "indeed", "bumeran","repositorio","ulima","glassdoor","bnamericas","aai"]
    n_web = 0 # Número de páginas web que se van considerando

    # Se itera sobre cada resultado obtenido
    for result in search_results:
        title_element = result.find_element(By.CSS_SELECTOR, "h3")
        title = title_element.text # Título del link obtenido
        link_element = result.find_element(By.CSS_SELECTOR, "a")
        link = link_element.get_attribute("href") # Link obtenido
        if link in links_web: # Se verifica si el link ya se encuentra en la lista de links
            pass # Se ignora la evaluación del link
        else: # Se evalua si no se encuentra agregado
            for count, web  in enumerate(webs_ignore, start = 1): # Se verifica que los links obtenidos no pertenezcan a las webs a ignorar
                if web in link:
                    break
                elif count < len(webs_ignore): # Se deben evaluar todos las webs ignore
                    pass
                else:
                    links_web.append(link) # Si no pertenecen, se agregan
                    n_web = n_web + 1
                    print(f"Title: {title}\nLink: {link}\n")

        if n_web == 3: # Se consideran 3 páginas web para esta búsqueda
            break

    ##### Segunda busqueda ###########
    ## Keyword: Nombre del proveedor + "contacto"
    ## Se extraen 2 resultados de esta búsqueda
    # Se imprime el nombre del proveedor más la palabra "contacto" en la barra de búsqueda de Google Web

    prov_field = driver.find_element(By.XPATH, value="//textarea[@id='APjFqb']")
    prov_field.send_keys(" contacto")
    prov_field.send_keys(Keys.RETURN)

    time.sleep(5) # Tiempo de espera

    # Se buscan las páginas web obtenidas
    search_results = driver.find_elements(By.CSS_SELECTOR, "div.g")
  
    # Existen páginas que se van a ignorar en esta búsqueda
    webs_ignore = ["computrabajo","twitter","pdf","linkedin", "universidadperu","facebook", "indeed", "bumeran","repositorio","ulima","glassdoor","bnamericas","aai"]

    # Se itera sobre cada resultado obtenido
    for result in search_results:
        title_element = result.find_element(By.CSS_SELECTOR, "h3")
        title = title_element.text # Título del link obtenido
        link_element = result.find_element(By.CSS_SELECTOR, "a")
        link = link_element.get_attribute("href") # Link obtenido
        if link in links_web: # Se verifica si el link ya se encuentra en la lista de links
            pass # se ignora la evaluación del link
        else: # se evalua si no se encuentra agregado
            for count, web  in enumerate(webs_ignore, start = 1): 
                if web in link: # Se verifica que los links obtenidos no pertenezcan a las webs a ignorar
                    break
                elif count < len(webs_ignore): # Se deben evaluar todos las webs ignore
                    pass
                else:
                    links_web.append(link) # Si no pertenecen, se agregan
                    n_web = n_web + 1
                    print(f"Title: {title}\nLink: {link}\n")

        if n_web == 5: # Se consideran 3 páginas web para esta búsqueda
            break

    return links_web

# Función final para extraer los datos de los links a evaluar - OpenAI
def extract_data_links_openAI(provname):

    # Cliente de OpenAI
    MODEL = "gpt-4o-mini"
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    # Obtener 5 enlaces de proveedores
    links_found = get_links_googleweb(provname)

    # Utilizar los enlaces para obtener los textos respectivos
    text_found = []
    for link in links_found:
        data_extracted = extract_text(link)
        if data_extracted:
            text_found.append(data_extracted)

    if len(text_found) >= 1:

        # Preparar los mensajes para la API de OpenAI
        messages = [
            {"role": "system", "content": f"Necesito recopilar información de empresas para enriquecer una base de datos de proveedores. Voy a estar enviándote textos pertenecientes a las páginas webs de las empresas, y debes buscar por la siguiente información: Ubicación de la empresa, datos de contacto (teléfonos, emails), redes sociales, productos y servicios ofrecidos, certificaciones, casos de éxito o clientes destacados, además de otra información destacable que consideres pertinente añadir. Cuando termine de enviarte todos los textos de las páginas web disponibles de la empresa, voy a enviar la palabra 'Finalizar', una vez que te envíe esa palabra, tú debes de enviarme todos los datos recopilados en una sola linea, es decir, en una única linea solo se escriben los datos de un campo, en la siguiente linea todo el siguiente campo, no saltes de linea a menos que hayas terminado con toda la información del campo, y así hasta finalizar con todos los datos solicitados. Importante, si en caso se detecta información contradictoria, igualmente indicar ambos datos en la misma linea, y en una última linea agregar un comentario como observación. Entonces, tu resultado final debe ser un texto con diversas lineas, donde en una unica linea se encuentre todo el campo solicitado, y al inicio de cada linea colocar el nombre del campo correspondiente (usar el nombre exacto de estos campos, sin tildes y no poner en negrita ni añadir otro simbolo especial como '*'): 'Ubicacion', 'Datos de Contacto', 'Redes Sociales', 'Productos/Servicios', 'Certificaciones', 'Clientes/Casos de Exito', 'Otra Informacion', 'Observaciones/Contradicciones'. Debes de asegurarte de que los textos sean sobre la empresa deseada, ahora, la empresa objetivo es: {provname}."}
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
        print("No se encontró data disponible de la empresa")
        return False

# Función final para extraer los datos de los links a evaluar - DeepSeek
def extract_data_links_DS(provname):

    # API Key de cuenta de DeepSeek
    client = openai.OpenAI(api_key="", base_url = "https://api.deepseek.com")

    # Obtener 5 enlaces de proveedores
    links_found = get_links_googleweb(provname)

    # Utilizar los enlaces para obtener los textos respectivos
    text_found = []
    for link in links_found:
        data_extracted = extract_text(link)
        if data_extracted:
            text_found.append(data_extracted)

    # Preparar los mensajes para la API de DeepSeek
    if text_found:
        messages = [
            {"role": "system", "content": f"Necesito recopilar información de empresas para enriquecer una base de datos de proveedores. Voy a estar enviándote textos pertenecientes a las páginas webs de las empresas, y debes buscar por la siguiente información: Ubicación de la empresa, datos de contacto (teléfonos, emails), redes sociales, productos y servicios ofrecidos, certificaciones, casos de éxito o clientes destacados, además de otra información destacable que consideres pertinente añadir. Cuando termine de enviarte todos los textos de las páginas web disponibles de la empresa, voy a enviar la palabra 'Finalizar', una vez que te envíe esa palabra, tú debes de enviarme una tabla con toda la información recopilada. Importante, si en caso se detecta información contradictoria, igualmente indicar ambos datos en la tabla, y en una última fila agregar un comentario como observación. Entonces, tu resultado final debe ser una tabla con las siguientes filas (usar el nombre exacto de estos campos, sin tildes): 'Ubicacion', 'Datos de Contacto', 'Redes Sociales', 'Productos/Servicios', 'Certificaciones', 'Clientes/Casos de Exito', 'Otra Informacion', 'Observaciones/Contradicciones'. Debes de asegurarte de que los textos sean sobre la empresa deseada, ahora, la empresa objetivo es: {provname}."}
        ]

        # Añadir cada texto como un mensaje de usuario
        for text in text_found:
            messages.append({"role": "user", "content": text})

        # Añadir el mensaje de finalización
        messages.append({"role": "user", "content": "Finalizar"})

        # Llamar a la API de DeepSeek
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages
        )

        # Obtener la respuesta del modelo
        result = response['choices'][0]['message']['content']
        print(result)
    
    else:
        print("No se encontró data de la empresa")
        return False


# Función final para extraer los datos de los links a evaluar - DeepSeek (OpenRouter)
def extract_data_links_DSOpen(provname):

    # API Key de cuenta de DeepSeek (OpenRouter)
    client = openai.OpenAI(api_key="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", base_url = "https://openrouter.ai/api/v1")

    # Obtener 5 enlaces de proveedores
    links_found = get_links_googleweb(provname)

    # Utilizar los enlaces para obtener los textos respectivos
    text_found = []
    for link in links_found:
        data_extracted = extract_text(link)
        if data_extracted:
            text_found.append(data_extracted)

    if len(text_found) >= 1:
        # Preparar los mensajes para la API de DeepSeek (OpenRouter)
        messages = [
            {"role": "system", "content": f"Necesito recopilar información de empresas para enriquecer una base de datos de proveedores. Voy a estar enviándote textos pertenecientes a las páginas webs de las empresas, y debes buscar por la siguiente información: Ubicación de la empresa, datos de contacto (teléfonos, emails), redes sociales, productos y servicios ofrecidos, certificaciones, casos de éxito o clientes destacados, además de otra información destacable que consideres pertinente añadir. Cuando termine de enviarte todos los textos de las páginas web disponibles de la empresa, voy a enviar la palabra 'Finalizar', una vez que te envíe esa palabra, tú debes de enviarme todos los datos recopilados fila por fila, es decir, en una fila solo se escriben los datos de un campo, en otra fila todo el siguiente campo, y así hasta finalizar con todos los datos solicitados. Importante, si en caso se detecta información contradictoria, igualmente indicar ambos datos en la linea, y en una última linea agregar un comentario como observación. Entonces, tu resultado final debe ser un texto con diversas lineas, y al inicio de cada linea colocar el nombre del campo correspondiente (usar el nombre exacto de estos campos, sin tildes y no poner en negrita ni añadir otro simbolo especial como '*'): 'Ubicacion', 'Datos de Contacto', 'Redes Sociales', 'Productos/Servicios', 'Certificaciones', 'Clientes/Casos de Exito', 'Otra Informacion', 'Observaciones/Contradicciones'. Debes de asegurarte de que los textos sean sobre la empresa deseada, ahora, la empresa objetivo es: {provname}."}
        ]

        # Añadir cada texto como un mensaje de usuario
        for text in text_found:
            messages.append({"role": "user", "content": text})

        # Añadir el mensaje de finalización
        messages.append({"role": "user", "content": "Finalizar"})

        try:
            # Llamar a la API de DeepSeek (Open Router)
            response = client.chat.completions.create(
                model="deepseek/deepseek-r1:free",
                messages=messages
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
        print("No se encontró data disponible de la empresa")
        return False

# Función para normalizar el output obtenido por la IA Gen
def normalize_data_IA(output_text, provname):
    try:
        # Diccionario donde se guardaran los datos
        data = {
            'proveedor': provname,
            'ubicacion': '',
            'datos_contacto': '',
            'redes_sociales': '',
            'productos_servicios': '',
            'certificaciones': '',
            'clientes_casos_exito': '',
            'otra_informacion': '',
            'observaciones_contradicciones': ''
        }
            
        # Dividir el texto en lineas
        lines = output_text.split('\n')

        # Iterar sobre cada linea para extraer los datos
        for line in lines:
            try:
                line = line.replace(":","")
            except:
                pass
            if 'Ubicacion' in line:
                data['ubicacion'] = line.split('Ubicacion')[1].strip()
            elif 'Datos de Contacto' in line:
                data['datos_contacto'] = line.split('Datos de Contacto')[1].strip()
            elif 'Redes Sociales' in line:
                data['redes_sociales'] = line.split('Redes Sociales')[1].strip()
            elif 'Productos/Servicios' in line:
                data['productos_servicios'] = line.split('Productos/Servicios')[1].strip()
            elif 'Certificaciones' in line:
                data['certificaciones'] = line.split('Certificaciones')[1].strip()
            elif 'Clientes/Casos de Exito' in line:
                data['clientes_casos_exito'] = line.split('Clientes/Casos de Exito')[1].strip()
            elif 'Otra Informacion' in line:
                data['otra_informacion'] = line.split('Otra Informacion')[1].strip()
            elif 'Observaciones/Contradicciones' in line:
                data['observaciones_contradicciones'] = line.split('Observaciones/Contradicciones')[1].strip()

        # Convertir diccionario a un dataframe
        df = pd.DataFrame([data])

        print(df) # Imprimir el dataframe
        return df
    
    except:
        print("No hay un resultado valido para normalizar")
        return pd.DataFrame()


# Función para subir la data normalizada a una tabla en Postgresql
def upload_key_data (key_data):
    
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
def export_csv ():

    engine = create_engine(f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}") # Conexión a Postgresql

    # Leer la tabla en un DataFrame
    df = pd.read_sql(f"SELECT * FROM {table_name}", engine)

    # Guardar como CSV
    df.to_csv("./PostgreSQL/datos_exportados.csv", index=True, encoding="utf-8-sig")

    print("✅ Exportación completada: datos_exportados.csv")

if __name__ == "__main__":
    provname = input("Indicar nombre del proveedor para extrar datos de la web: ")
    # Se obtiene la extracción de datos por la IA Gen
    result = extract_data_links_openAI(provname)
    # Se normalizan esos datos y se retorna un dataframe con los valores clave
    key_data = normalize_data_IA(result, provname)
    # Se suben esos datos a Postgresql
    upload_key_data(key_data)
    # Exportación de datos
    # export_csv()
