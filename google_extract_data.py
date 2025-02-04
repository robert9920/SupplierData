import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import deepseek

# Función para extraer todo el texto de las páginas webs 
def extract_text(url):
    try:
        # Enviar una solicitud GET
        response = requests.get(url)
        # Verificar si la solicitud fue exitosa
        if response.status_code == 200:
            # Obtener el contenido HTML
            html_content = response.text

            # Usar BeautifulSoup para analizar el HTML
            soup = BeautifulSoup(html_content, "html.parser")

            # Extraer y devolver solo el contenido de texto, ignorando las etiquetas HTML
            text_content = soup.get_text(separator=" ", strip=True)

            return text_content
        else:
            print(f"Error al recuperar la página {url}. Código de estado: {response.status_code}")
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
    webs_ignore = ["linkedin", "universidadperu","facebook", "indeed"]
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
    webs_ignore = ["linkedin", "universidadperu","facebook", "indeed"]

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

# Función final para extraer los datos de los links a evaluar
def extract_data_links(provname, api_key):
    # Inicializar la API de DeepSeek
    ds = deepseek.DeepSeek(api_key)

    # Se obtienen 5 links de proveedores 
    links_found = get_links_googleweb(provname)

    # Se utilizan los links para obtener los textos respectivos
    text_found = []
    for link in links_found:
        data_extracted = extract_text(link)
        if data_extracted:
            text_found.append(data_extracted)

    # Enviar el prompt inicial solo para el primer texto
    if text_found:
        initial_prompt = f"Necesito recopilar información de empresas para enriquecer una base de datos de proveedores. Voy a estar enviándote textos pertenecientes a las páginas webs de las empresas, y debes buscar por la siguiente información: Ubicación de la empresa, datos de contacto (teléfonos, emails), redes sociales, productos y servicios ofrecidos, certificaciones, casos de éxito o clientes destacados, además de otra información destacable que consideres pertinente añadir. Cuando termine de enviarte todos los textos de las páginas web disponibles de la empresa, voy enviar la palabra “Finalizar”, una vez que te envíe esa palabra, tú debes de enviarme una tabla con toda la información recopilada. Importante, si en caso se detecta información contradictoria, igualmente indicar ambos datos en la tabla, y en una última fila agregar un comentario como observación. Debes de asegurarte de que los textos sean sobre la empresa deseada, ahora, la empresa objetivo es: {provname}.\n\n Empezamos con el primer texto: {text_found[0]}"
        ds.send_prompt(initial_prompt)

        # Enviar las noticias restantes sin el prompt inicial
        if len(text_found) > 1:
            for text in text_found[1:]:
                ds.send_prompt(text)

        # Finalizar la evaluación
        final_response = ds.send_prompt("Finalizar")
        print(f"Evaluación final de DeepSeek: {final_response}")
        return final_response
    else:
        print("No se encontraron links para evaluar.")
        return None


if __name__ == "__main__":
    provname = input("Indicar nombre del proveedor para extrar datos de la web: ")
    api_key = input("Indicar tu API Key de DeepSeek: ")
    result = extract_data_links(provname, api_key)

