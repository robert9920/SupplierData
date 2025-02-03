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


def obtener_datos_linkedin(nombreprov):

    renew_tor_ip()

    # URL de Linkedin
    url = "https://www.linkedin.com/feed/"

    # Datos de inicio de sesión
    email = "drone123robert@outlook.com"
    password = "Greciatechpruebas123@"

    # Configuración de opciones de Chrome
    chrome_options = Options()
    # Configurar Tor como proxy SOCKS
    chrome_options.add_argument("--proxy-server=socks5://127.0.0.1:9150")
    #chrome_options.add_argument("--headless")  # Ejecutar en modo sin cabeza (sin interfaz gráfica)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Evitar detección de automatización

    # Driver de Google Chrome
    driver = webdriver.Chrome(options=chrome_options)

    # Se accede a LinkedIn
    driver.maximize_window()
    driver.get(url)

    time.sleep(3)

    ### Inicio de Sesión ###
    
    # Se imprime el valor del email y password en la barra de texto
    email_field = driver.find_element(By.ID, value="username")
    email_field.send_keys(email)
    password_field = driver.find_element(By.ID, value="password")
    password_field.send_keys(password)

    # Se clickea el botón de iniciar sesión
    iniciar_sesion_button = driver.find_element(By.XPATH, value="//button[normalize-space()='Iniciar sesión']")
    iniciar_sesion_button.click()

    time.sleep(10)

    ### Búsqueda de Empresa ###

    # Escribir nombre de empresa en barra
    search_field = driver.find_element(By.XPATH, value="//input[@placeholder='Buscar']")
    search_field.send_keys(nombreprov)
    search_field.send_keys(Keys.RETURN)

    time.sleep(2)

    # Ir a la sección de empresas #
    business_button = driver.find_element(By.XPATH, value="//button[normalize-space()='Empresas']")
    business_button.click()

    # Seleccionar primera opción #
    business_name_1 = driver.find_element(By.CLASS_NAME, value = "authentication-outlet")
    business_name_2 = business_name_1.find_element(By.CLASS_NAME, value = "kJPEILoQETreaDNshOhvmpgILCViDGXGc")
    #business_name_3 = business_name_2.find_element(By.XPATH, value = "//main[contains(@class,'kJPEILoQETreaDNshOhvmpgILCViDGXGc')]")
    #business_name_4 = business_name_3.find_element(By.XPATH, value = "//body[1]/div[5]/div[3]/div[2]/div[1]/div[1]/main[1]/div[1]/div[1]/div[2]/div[1]/ul[1]")


    print(business_name_1)
    print(business_name_2)
    #print(business_name_3)
    #print(business_name_4)

    time.sleep(10)
  
 
    # try:
    #     # Nombre de empresa / RUC
    #     driver_nombre_empresa_ruc = driver.find_elements(By.CLASS_NAME, "list-group-item-heading")
    #     nombre_empresa_ruc = driver_nombre_empresa_ruc[1].text
    #     nombre_empresa = nombre_empresa_ruc[14:]
    #     nombre_ruc = nombre_empresa_ruc[0:11]

    #     # Fecha Inicio Actividades / Estado Contribuyente / Condicion Contribuyente / Domicilio Fiscal
    #     driver_datos = driver.find_elements(By.CLASS_NAME, "list-group-item-text")
    #     estado_contribuyente = driver_datos[4].text
    #     condicion_contribuyente = driver_datos[5].text
    #     domicilio_fiscal = driver_datos[6].text
    #     domicilio_fiscal = domicilio_fiscal.split(" - ", 2)[-1].strip()

    #     # Actividades Económicas
    #     driver_tabla_actividades = driver.find_element(By.XPATH, "//div[10]//div[1]//div[2]//table[1]")
    #     driver_actividades = driver_tabla_actividades.find_elements(By.TAG_NAME, "tr")
    #     actividades_economicas = [actividad.text.split(" - ", 2)[-1].strip() for actividad in driver_actividades]

    #     # Cerrar el navegador
    #     driver.quit()

    #     return nombre_empresa, nombre_ruc, estado_contribuyente, condicion_contribuyente, domicilio_fiscal, actividades_economicas

    # except Exception as e:
    #     print("Número de RUC no válido o error en la extracción de datos:", e)
    #     driver.quit()
    #     return None, None, None, None, None, None


if __name__ == "__main__":
    obtener_datos_linkedin("ASCENSORES SCHINDLER DEL PERU S A")