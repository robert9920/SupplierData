import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text
import unicodedata

# Valores para conexión a Postgresql
db_user = "postgres"
db_password = "greciatech"
db_host = "127.0.0.1"
db_port = "5432"
db_name = "padron_ruc"
table_name = "bid_completo"

# Función para eliminar tildes de palabras en mayúsculas
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

# Función para poner toda una string en mayúscula y reemplazar el simbolo "'"
def a_mayusculas_replace_symbol(cadena):
    cadena = cadena.upper()
    cadena = cadena.replace("'","")
    return cadena

# Función para subir el DF a una tabla en Postgresql
def upload_bid_sql(df):
    
    engine = create_engine(f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}") # Conexión a Postgresql

    if not df.empty: # Verificamos que data frame no esté vacío
        try: 
            with engine.begin() as conn: # Utiliza `begin` para manejar automáticamente transacciones
                for index, row in df.iterrows(): # Se eliminan los datos de proveedores ya existentes en la tabla
                    proveedor = row["proveedor"]  # Acceder al valor del proveedor en el DataFrame
                    print(f"Eliminando proveedor: {proveedor}")
                    delete_query = f"DELETE FROM {table_name} WHERE proveedor = '''{proveedor}''';"  # Consulta directa
                    conn.execute(text(delete_query))  # Envía la consulta como texto
        except Exception as e:
            print(f"Hubo un error al limpiar la tabla: {e}")
        # Se insertan datos en PostgreSQL
        df.to_sql(table_name, engine, if_exists="append", index=False)
        print(f"Datos BID subidos a PostgreSQL en la tabla: {table_name}")
    else:
        print("No hay datos para subir a PostgreSQL")

if __name__ == "__main__":
    try:
        # Cargar el DataFrame desde un archivo CSV
        df = pd.read_csv("../Fuentes de Datos/BID/data.csv", encoding = "latin1")

        # Aplicar las funciones a la columna "proveedor"
        df["proveedor"] = df["proveedor"].apply(a_mayusculas_replace_symbol)  # Primero, convertir a mayúsculas
        df["proveedor"] = df["proveedor"].apply(eliminar_tildes_mayusculas)  # Luego, eliminar tildes

        # Subir datos a postgresql
        upload_bid_sql(df)
        
        print("Proceso completado. El archivo 'data.csv' de BID ha sido subido a PostgreSQL")
    except Exception as e:
        print(f"Error al momento de subir archivo data BID: {e}")