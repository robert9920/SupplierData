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
from stem import Signal
from stem.control import Controller

# Cambiar IP de Tor
def renew_tor_ip():
    try:
        # Conectar al controlador de Tor
        with Controller.from_port(port=9051) as controller:
            # Autenticación por cookie (si está habilitada en torrc)
            controller.authenticate()

            # Enviar la señal para cambiar la IP
            controller.signal(Signal.NEWNYM)

            print("IP de Tor cambiada.")
    except Exception as e:
        print(f"Error al cambiar la IP de Tor: {e}")


# Función para extraer todo el texto de las noticias 
def extract_text(url):

    renew_tor_ip()

    # Configurar el proxy SOCKS de Tor
    proxies = {
        "http": "socks5h://127.0.0.1:9150",  # Usar 'socks5h' para resolver DNS a través de Tor
        "https": "socks5h://127.0.0.1:9150",
    }

    try:
        # Enviar una solicitud GET a través de Tor
        response = requests.get(url, proxies=proxies)
        #response = requests.get(url)

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

# Función para extraer los links de las noticias de cada empresa 
def get_links_googlenews(provname, n_news_max = 10):

    renew_tor_ip()

    # URL de Google News
    url = "https://news.google.com/home?hl=es-419&gl=PE&ceid=PE:es-419"

    # Configuración de opciones de Chrome
    chrome_options = Options()
    # Configurar Tor como proxy SOCKS
    chrome_options.add_argument("--proxy-server=socks5://127.0.0.1:9150")
    #chrome_options.add_argument("--headless")  # Ejecutar en modo sin cabeza (sin interfaz gráfica)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Evitar detección de automatización

    # Driver de Google Chrome
    driver = webdriver.Chrome(options=chrome_options)

    # Se accede a Google News
    driver.maximize_window()
    driver.get(url)

    
    # En caso se tenga que aceptar permisos de Google
    time.sleep(2)
    try:
        container_aceptar = driver.find_element(By.CLASS_NAME, value = "jn2Duf")
        container_aceptar_2 = container_aceptar.find_element(By.CLASS_NAME, value = "AIC7ge")
        container_aceptar_3 = container_aceptar_2.find_element(By.CLASS_NAME, value = "CxJub")
        container_aceptar_4 = container_aceptar_3.find_element(By.CLASS_NAME, value = "VtwTSb")
        container_aceptar_5 = container_aceptar_4.find_element(By.XPATH, value = "//div[@class='VtwTSb']//form[2]")
        actions = ActionChains(driver)
        actions.move_to_element(container_aceptar_5).click().perform()
    except:
        pass

    time.sleep(3)

    # Se imprime el nombre del proveedor en la barra de búsqueda de Google News
    prov_field = driver.find_element(By.XPATH, value="//input[@aria-label='Busca temas, ubicaciones y fuentes']")
    prov_field.send_keys(provname)
    prov_field.send_keys(Keys.RETURN)

    time.sleep(4)

    # Se buscan las noticias obtenidas
    container_news = driver.find_element(By.CLASS_NAME, value = "UW0SDc")
    news_found = container_news.find_elements(By.CLASS_NAME, value = "JtKRv")

    # Se crea una lista para almacenar los links encontrados
    news_link = list()

    # Obtener el identificador de la pestaña original
    original_tab = driver.current_window_handle    

    # Número de links obtenidos 
    links_found = 0

    for new in news_found:

        try:
            # Se encontró 1 nuevo link
            links_found = links_found + 1

            # Desplazarse al elemento y hacer click
            actions = ActionChains(driver)
            actions.move_to_element(new).click().perform()

            # Esperar a que se abra la nueva pestaña
            time.sleep(random.uniform(8, 10))

            # Cambiar a la nueva pestaña
            new_tab = [tab for tab in driver.window_handles if tab != original_tab][0]
            driver.switch_to.window(new_tab)

            # En caso se tenga que aceptar permisos de Google
            try:
                container_aceptar = driver.find_element(By.CLASS_NAME, value = "jn2Duf")
                container_aceptar_2 = container_aceptar.find_element(By.CLASS_NAME, value = "AIC7ge")
                container_aceptar_3 = container_aceptar_2.find_element(By.CLASS_NAME, value = "CxJub")
                container_aceptar_4 = container_aceptar_3.find_element(By.CLASS_NAME, value = "VtwTSb")
                container_aceptar_5 = container_aceptar_4.find_element(By.XPATH, value = "//div[@class='VtwTSb']//form[2]")
                actions = ActionChains(driver)
                actions.move_to_element(container_aceptar_5).click().perform()
                # Esperar a que cargue la página completamente
                time.sleep(random.uniform(2, 3))
            except:
                pass

            # Se obtiene el link de la noticia
            news_link.append(driver.current_url) 

            # Se cierra la nueva pestaña
            driver.close() 

             # Se regresa a la pestaña original
            driver.switch_to.window(original_tab)     

            # Esperar a que la página cargue completamente  
            time.sleep(random.uniform(1, 2))

            if links_found >= n_news_max:
                break

        except Exception as e:
            print(f"Error al obtener el enlace original: {e}")
            return None

    # Cerrar el navegador
    driver.quit()

    print(news_link)
    return(news_link)

# Pruebas #################
# links = get_data_googlenews("SERVICIOS GENERALES PARDO MIGUEL S.R.L")
# for link in links:
#     texto = extract_text(link)
#     print(texto)



### Opción 2 - Leer los links sin ingresar a cada uno ###

# def get_data_googlenews(provname):

#     # URL de Google News
#     url = "https://news.google.com/home?hl=es-419&gl=PE&ceid=PE:es-419"

#     # Configuración de opciones de Chrome
#     chrome_options = Options()
#     # Configurar Tor como proxy SOCKS
#     chrome_options.add_argument("--proxy-server=socks5://127.0.0.1:9150")
#     #chrome_options.add_argument("--headless")  # Ejecutar en modo sin cabeza (sin interfaz gráfica)
#     chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Evitar detección de automatización

#     # Driver de Google Chrome
#     driver = webdriver.Chrome(options=chrome_options)

#     # Se accede a Google News
#     driver.maximize_window()
#     driver.get(url)

#     time.sleep(2)

#     # Se imprime el nombre del proveedor en la barra de búsqueda de Google News
#     prov_field = driver.find_element(By.XPATH, value="//input[@aria-label='Busca temas, ubicaciones y fuentes']")
#     prov_field.send_keys(provname)
#     prov_field.send_keys(Keys.RETURN)

#     time.sleep(2)

#     # Se buscan las noticias obtenidas
#     container_news = driver.find_element(By.CLASS_NAME, value = "UW0SDc")
#     news_found = container_news.find_elements(By.CLASS_NAME, value = "JtKRv")

#     # Se crea una lista para almacenar los links encontrados
#     news_link = list()

#     for new in news_found:
#         try:
#             # Se obtiene el link de la noticia
#             news_link.append(new.get_attribute("href")) 
#         except Exception as e:
#             print(f"Error al obtener el enlace original: {e}")
#             return None

#     # Cerrar el navegador
#     driver.quit()

#     print(news_link)
#     return(news_link)