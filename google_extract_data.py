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

# Función para extraer todo el texto de las noticias 
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
    
print(extract_text("https://pe.linkedin.com/company/agersa-srl"))
print("\n")
print("\n")
print(extract_text("https://www.universidadperu.com/empresas/agersa.php#google_vignette"))
print("\n")
print("\n")
print(extract_text("https://www.facebook.com/people/Agersa-SRL/100063484756028/"))
print("\n")
print("\n")
print(extract_text("https://www.facebook.com/people/Agersa-SRL/100063484756028/"))
print("\n")
print("\n")
print(extract_text("https://pe.linkedin.com/company/agersa-srl"))
