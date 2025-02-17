import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def obtener_datos_sunat(RUC):
    # URL del buscador de SUNAT
    url = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp"

    # Driver de Google Chrome
    driver = webdriver.Chrome()
    driver.maximize_window()

    # Se accede a la página deseada
    driver.get(url)

    # Se imprime el valor del RUC en la barra de texto
    RUC_field = driver.find_element(By.ID, value="txtRuc")
    RUC_field.send_keys(RUC)

    # Se clickea el botón de aceptar para buscar el RUC
    RUC_button = driver.find_element(By.ID, value="btnAceptar")
    RUC_button.click()

    try:
        # Nombre de empresa / RUC
        driver_nombre_empresa_ruc = driver.find_elements(By.CLASS_NAME, "list-group-item-heading")
        nombre_empresa_ruc = driver_nombre_empresa_ruc[1].text
        nombre_empresa = nombre_empresa_ruc[14:]
        nombre_ruc = nombre_empresa_ruc[0:11]

        # Fecha Inicio Actividades / Estado Contribuyente / Condicion Contribuyente / Domicilio Fiscal
        driver_datos = driver.find_elements(By.CLASS_NAME, "list-group-item-text")
        estado_contribuyente = driver_datos[4].text
        condicion_contribuyente = driver_datos[5].text
        domicilio_fiscal = driver_datos[6].text
        domicilio_fiscal = domicilio_fiscal.split(" - ", 2)[-1].strip()

        # Actividades Económicas
        driver_tabla_actividades = driver.find_element(By.XPATH, "//div[10]//div[1]//div[2]//table[1]")
        driver_actividades = driver_tabla_actividades.find_elements(By.TAG_NAME, "tr")
        actividades_economicas = [actividad.text.split(" - ", 2)[-1].strip() for actividad in driver_actividades]

        # Cerrar el navegador
        driver.quit()

        return nombre_empresa, nombre_ruc, estado_contribuyente, condicion_contribuyente, domicilio_fiscal, actividades_economicas

    except Exception as e:
        print("Número de RUC no válido o error en la extracción de datos:", e)
        driver.quit()
        return None, None, None, None, None, None