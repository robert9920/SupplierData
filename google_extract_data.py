import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random

# Función para extraer todo el texto de las páginas webs 
def extract_text(url):
    try:
        # Enviar una solicitud GET a través de Tor
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
    ## Se extraen 3 resultados de esta página

    # Se imprime el nombre del proveedor en la barra de búsqueda de Google Web
    prov_field = driver.find_element(By.XPATH, value="//textarea[@id='APjFqb']")
    prov_field.send_keys(provname)
    prov_field.send_keys(Keys.RETURN)

    time.sleep(2) # Tiempo de espera

    # Se buscan las páginas web obtenidas
    search_results = driver.find_elements(By.CSS_SELECTOR, "div.g")
  
    # Existen páginas que se van a ignorar
    webs_ignore = ["linkedin", "universidadperu","facebook", "indeed"]
    n_web = 0 # Número de páginas web que se van considerando

    # Se itera sobre cada resultado obtenido
    for result in search_results:
        title_element = result.find_element(By.CSS_SELECTOR, "h3")
        title = title_element.text # Título del link obtenido
        link_element = result.find_element(By.CSS_SELECTOR, "a")
        link = link_element.get_attribute("href") # Link obtenido
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

    print(links_web)

    # # Se crea una lista para almacenar los links encontrados
    # news_link = list()

    # for new in news_found:
    #     try:
    #         # Se obtiene el link de la noticia
    #         news_link.append(new.get_attribute("href")) 
    #     except Exception as e:
    #         print(f"Error al obtener el enlace original: {e}")
    #         return None

    # # Cerrar el navegador
    # driver.quit()

    # print(news_link)
    # return(news_link)

get_links_googleweb("Lima Analytics")