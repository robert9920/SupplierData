import pandas as pd

# Función para reemplazar caracteres especiales
def reemplazar_caracteres(texto):
    # Diccionario de reemplazos
    reemplazos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'ñ': 'n', 'Ñ': 'N'
    }
    # Reemplazar cada carácter según el diccionario
    for original, reemplazo in reemplazos.items():
        texto = texto.replace(original, reemplazo)
    return texto

# Leer el archivo CSV
df = pd.read_csv('C:/Trabajo/Lima-Analytics-GreciaTech/Product Data Proveedores/Piloto/Fuentes de Datos/CONOSCE_2019_completo.csv', encoding='utf-8')

# Iterar sobre todas las columnas y aplicar el reemplazo
for columna in df.columns:
    df[columna] = df[columna].apply(lambda x: reemplazar_caracteres(str(x)))

# Guardar el nuevo archivo CSV con codificación UTF-8
df.to_csv('C:/Trabajo/Lima-Analytics-GreciaTech/Product Data Proveedores/Piloto/Fuentes de Datos/CONOSCE_2019_completo_utf8.csv', index=False, encoding='utf-8')

print("El archivo CSV ha sido procesado y guardado correctamente.")
