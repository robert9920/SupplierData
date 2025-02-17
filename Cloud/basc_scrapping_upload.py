import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from sqlalchemy import create_engine
from sqlalchemy import text
import unicodedata

# Valores para conexión a Postgresql
db_user = "postgres"
db_password = "greciatech"
db_host = "127.0.0.1"
db_port = "5432"
db_name = "ProvData"
table_name = "basc"

# Función para eliminar tildes de palabras en mayusculas
def eliminar_tildes_mayusculas(cadena):
    # Lista de caracteres especiales a preservar (en este caso, la "Ñ")
    caracteres_especiales = {'Ñ', 'ñ'}
    
    # Recorre cada carácter de la cadena
    cadena_sin_tildes = []
    for c in cadena:
        # Si el carácter es una "Ñ" o "ñ", lo preservamos
        if c in caracteres_especiales:
            cadena_sin_tildes.append(c)
        else:
            # Normaliza el carácter y elimina las tildes
            c_normalizado = unicodedata.normalize('NFD', c)
            c_sin_tilde = ''.join(
                letra for letra in c_normalizado
                if unicodedata.category(letra) != 'Mn'
            )
            cadena_sin_tildes.append(c_sin_tilde)
    
    # Une la lista en una cadena y convierte a mayúsculas
    cadena_final = ''.join(cadena_sin_tildes).upper()
    return cadena_final


# Función para obtener los datos de BASC PERÚ - Empresas Certificadas por PERÚ CERTIFICATION Vigentes
def get_data_basc():
    # URL del buscador de BASC PERU
    url = "https://www.bascperu.org/iso6.php"

    # Inicializar WebDriver de Chrome
    driver = webdriver.Chrome()
    driver.maximize_window()
    driver.get(url)

    # Crear un DataFrame vacío con las columnas requeridas
    df = pd.DataFrame(columns=["proveedor", "normas"])

    while (True):
        try:
            time.sleep(2)  # Esperar a que la página cargue completamente

            # Intentar cerrar ventana emergente si existe
            try:
                ventana_emergente = driver.find_element(By.XPATH, "//span[@aria-hidden='true']")
                ventana_emergente.click()
            except:
                print("No se encontró ventana emergente.")
            
            # Buscar los elementos con la clase correspondiente
            lista_elementos = driver.find_elements(By.CLASS_NAME, "lista-pdf-item")
            
            # Se seleccionan los elementos que sean correctos
            for elemento in lista_elementos:
                elemento_campos = elemento.text # Se obtiene el campo de empresa certificada, norma y "más información"
                for (num,letra) in enumerate(['A','E','I','O','U']): # Verificación porque hay elementos externos que no son empresas, son filas vacías
                    if letra in elemento_campos:
                        proveedor = elemento_campos.split("\n")[0].strip() # Se ubica el campo proveedor
                        proveedor = eliminar_tildes_mayusculas(proveedor)
                        norma = elemento_campos.split("\n")[1].strip() # Se ubica el campo norma
                        if proveedor in df["proveedor"].values: # verificamos que no sea un valor repetido
                            pass
                        else:
                            df.loc[len(df)] = [proveedor, norma] # Agregar los datos al DataFrame
                        break    
                    elif num < 5:
                        pass
                    else:
                        break
            
            # Se cambia a la siguiente página
            boton_siguiente_pagina = driver.find_element(By.CSS_SELECTOR, ".flecha-paginador-siguiente")
            boton_siguiente_pagina.click() # Cambio de página


        except Exception as e:
            print(f"Error durante la extracción o extracción finalizada: {e}")
            driver.quit()
            return df

# Función para subir el DF a una tabla en Postgresql
def upload_basc_sql(df):
    
    engine = create_engine(f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}") # Conexión a Postgresql

    if not df.empty: # Verificamos que data frame no esté vacío
        try: 
            with engine.begin() as conn: # Utiliza `begin` para manejar automáticamente transacciones
                for index, row in df.iterrows(): # Se eliminan los datos de proveedores ya existentes en la tabla
                    proveedor = row["proveedor"]  # Acceder al valor del proveedor en el DataFrame
                    print(f"Eliminando proveedor: {proveedor}")
                    delete_query = f"DELETE FROM {table_name} WHERE proveedor = '{proveedor}';"  # Consulta directa
                    conn.execute(text(delete_query))  # Envía la consulta como texto
        except Exception as e:
            print(f"Hubo un error al limpiar la tabla: {e}")
        # Se insertan datos en PostgreSQL
        df.to_sql(table_name, engine, if_exists="append", index=False)
        print(f"Datos BASC subidos a PostgreSQL en la tabla: {table_name}")
    else:
        print("No hay datos para subir a PostgreSQL")

if __name__ == "__main__":
    df = get_data_basc()
    upload_basc_sql(df)

