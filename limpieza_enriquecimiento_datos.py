import pandas as pd
from request_RUC import obtener_datos_sunat
import warnings
import re
from sqlalchemy import create_engine
from sqlalchemy import text 

# Ignorar todas las advertencias
warnings.filterwarnings("ignore")

######## Configuraciones conexión a base de datos #######

db_user = "postgres"
db_password = "greciatech"
db_host = "127.0.0.1"
db_port = "5432"
db_name = "padron_ruc"
table_name_sunat = "sunat_ruc"
table_name_buenos_contribuyentes = "sunat_buenos_contribuyentes"
table_name_agente_retencion = "sunat_agente_retencion"

######## Funciones #############

# Lectura de datos
def leer_datos(nombre_BD, n_row, sheet_name):
    file_path = "../BDProv/" + nombre_BD # Ruta base de datos
    print(file_path)
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, skiprows=n_row, header=0, sheet_name = sheet_name) # Se empieza con la lectura del csv desde la fila n_row
        elif file_path.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path, skiprows=n_row, header=0, sheet_name = sheet_name) # Se empieza con la lectura del excel desde la fila n_row
        else:
            raise ValueError("El archivo debe ser de tipo .csv, .xls o .xlsx")
        
        print("Archivo leído exitosamente")
        return df

    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return None
    

# Función para capitalizar la primera letra de cada nombre o apellido
def format_name(name):
    if pd.notna(name):
        return True, name.strip().title()  # Primra letra mayuscula, el resto minúscula
    else:
        return False, "Falta nombre/apellido"

# Función para validar correos electrónicos
def validate_email(email):
    regex = r'^[A-Za-z0-9áéíóúÁÉÍÓÚ._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}$'
    if pd.notna(email):
        separators = r"[ /;,]"
        emails = re.split(separators, email.strip())
        for e in emails:
            # Se revisa que no haya ningún "_" al inicio
            if e.startswith("_"):
                return False, "Formato de correo inválido: inicia con '_'"
            # Se revisa el formato del correo
            if not (re.fullmatch(regex, email.strip())):
                return False, "Formato de correo inválido"
        else:
            return True, None  # Todos los correos son válidos
    return False, "Falta correo"  

# Función para validar números de Perú
def validate_phone(phone):
    if pd.notna(phone):
        # Limpieza del número
        phone_str = str(phone).strip()
        phone_str = phone_str.replace(" ","")
        phone_str = phone_str.replace("+","")
        phone_str = phone_str.replace("-","")
        phone_str = phone_str.replace("(","")
        phone_str = phone_str.replace(")","")
        # Verficaciones del número, presenta diversos formatos
        if phone_str.isdigit():
            if len(phone_str) < 7:
                return False, "Longitud de número de teléfono no válida"
            if phone_str[0:3] == "051" and phone_str[3] == "9" and len(phone_str) == 12:
                num_real = phone_str[3:]
                return False, f"El número telefónico móvil presenta código de Perú y es el siguiente: {num_real}"
            elif phone_str[0:2] == "51" and phone_str[2] == "9" and len(phone_str) == 11:
                num_real = phone_str[2:]
                return False, f"El número telefónico móvil presenta código de Perú y es el siguiente: {num_real}"
            elif phone_str[2] == "9" and len(phone_str) == 11:
                num_real = phone_str[2:]
                cod_num = phone_str[0:2]
                return False, f"El número telefónico móvil identificado es el siguiente: {num_real}, con código: {cod_num}"
            elif phone_str[3] == "9" and len(phone_str) == 12:
                num_real = phone_str[3:]
                cod_num = phone_str[0:3]
                return False, f"El número telefónico móvil identificado es el siguiente: {num_real}, con código: {cod_num}"  
            elif len(phone_str) == 9 and phone_str.startswith("9"):  # Teléfono Móvil
                return True, None
            elif len(phone_str) == 7:  # Teléfono Fijo
                return True, None
            else:
                return False, "Longitud de número de teléfono no válida"
        else:
            return False, "El número telefónico contiene caracteres no numéricos"
    return False, "Falta numero telefónico"

# Función para validar el número de RUC
def validate_id_number(id_number):
    if pd.notna(id_number):
        id_str = str(id_number).strip()
        if id_str.isdigit() and len(id_str) == 11:
            return True, None
        else:
            return False, "RUC inválido (debe poseer 11 dígitos numéricos)"
    return False, "Falta el número de RUC"


################ Fin de funciones ######################

# Solicitud de datos
nombre_BD = input("Por favor, escriba el nombre de la Base de Datos (junto con su extensión .csv, .xls o .xlsx): ") # Nombre Base Datos
sheet_name = input("Por favor, escriba el nombre de la hoja donde se encuentra la BD: ") # Nombre Hoja de la tabla de la BD
n_row = int(input("Escriba el número de fila para empezar a leer el archivo: ")) # Número de fila donde inician los datos
n_row = n_row - 1

# Lectura de datos
df = leer_datos(nombre_BD, n_row, sheet_name)
#df.fillna("NA", inplace=True) # Se pone NA en los valores nulos

# Datos columnas
# Se solicitan los numeros de columnas de los valores a verificar
n_razonsocial = int(input("Escriba el número de la columna donde se encuentra los datos de la Razón Social: ")) 
n_name = int(input("Escriba el número de la columna donde se encuentra los datos de Nombre: ")) 
n_lastname = int(input("Escriba el número de la columna donde se encuentran los datos del Apellido: ")) 
n_email = int(input("Escriba el número de la columna donde se encuentran los datos del Email: ")) 
n_phone = int(input("Escriba el número de la columna donde se encuentran los datos del Teléfono: ")) 
n_ruc = int(input("Escriba el número de la columna donde se encuentran los datos del RUC: ")) 


# Se inicializa nueva columna para descripción de errores
df['Descripción del error'] = ""
# Se inicializan nuevas columnas para identificar el estado contribuyente y la condición de domicilio
df['Estado Contribuyente'] = ""
df["Condición Domicilio"] = ""
# Se inicializan nuevas columnas para identificar agentes de retención y su fecha
df['Agente Retención'] = ""
df["Fecha Agente Retención"] = ""
# Se inicializan nuevas columnas para identificar buenos contribuyentes y su fecha
df['Buenos Contribuyentes'] = ""
df["Fecha Buenos Contribuyentes"] = ""

# Conexión a PostgreSQL
engine = create_engine(f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")

# Diccionario de reemplazos para limpiar strings con tilde y puntos no deseados
reemplazos = {
    'á': 'a',
    'é': 'e',
    'í': 'i',
    'ó': 'o',
    'ú': 'u',
    'Á': 'A',
    'É': 'E',
    'Í': 'I',
    'Ó': 'O',
    'Ú': 'U',
    '.': ''
}
tabla = str.maketrans(reemplazos)


# Se realizan validaciones, correcciones y enriquecimiento de datos
for index, row in df.iterrows():
    errors = []

    # Validar razón social con base de datos postgresql

    ruc = row[n_ruc - 1]
    razon_social = row[n_razonsocial - 1]

    if pd.notna(ruc):  # Revisar que RUC no sea nulo
        # Query para obtener la razon social utilizando el RUC
        query = text(f"SELECT nombre_razonsocial FROM {table_name_sunat} WHERE ruc = '{ruc}'")
        with engine.connect() as connection:
            result = connection.execute(query).fetchone()
        
        if result:
            correct_name = result[0]  # Se obtiene la razón social de la base de datos
            if razon_social.strip().lower().translate(tabla) != correct_name.strip().lower().replace('.',''):
                # Si los nombres no coinciden
                error_message = f"Nombre de razón social incorrecto. Nombre correcto: {correct_name}"
                errors.append(error_message)
        else:
            # RUC no encontrado en la base de datos
            error_message = "RUC no se encontró en la base de datos"
            errors.append(error_message)

    # Validar / formatear "Nombre"
    name_valid, name_error_corrected = format_name(row[n_name-1])
    if  name_valid:
        df.iloc[index, n_name-1] = name_error_corrected
    else:
        errors.append(name_error_corrected)

    # Validar / formatear "Apellido"
    lastname_valid, lastname_error_corrected = format_name(row[n_lastname-1])
    if  lastname_valid:
        df.iloc[index, n_lastname-1] = lastname_error_corrected
    else:
        errors.append(lastname_error_corrected)

    # Validar "E-mail"
    email_valid, email_error = validate_email(row[n_email-1])
    if not email_valid:
        errors.append(email_error)

    # Validar "Teléfono"
    phone_valid, phone_error = validate_phone(row[n_phone-1])
    if not phone_valid:
        errors.append(phone_error)

    # Validar "Número de identificación (RUC)"
    id_valid, id_error = validate_id_number(row[n_ruc-1])
    if not id_valid:
        errors.append(id_error)

    # Añadir errores encontrados a la columna "Descripción del error" 
    df.at[index, 'Descripción del error'] = "; ".join(errors)

    ###### Enriquecimiento de datos ######

    # Agentes de retención
    if pd.notna(ruc):  # Revisar que RUC no sea nulo
        # Query para verificar que RUC se encuentre en tabla de agentes de renteción
        query = text(f"SELECT a_partir_de FROM {table_name_agente_retencion} WHERE ruc = '{ruc}'")
        with engine.connect() as connection:
            result = connection.execute(query).fetchone()
        if result:
            fecha_agente_retencion = result[0]  # Se obtiene la fecha del agente de retención de la base de datos
            df.at[index, 'Agente Retención'] = "Si"
            df.at[index, 'Fecha Agente Retención'] = fecha_agente_retencion


    # Buenos Contribuyentes
    if pd.notna(ruc):  # Revisar que RUC no sea nulo
        # Query para verificar que RUC se encuentre en tabla de buenos contribuyentes
        query = text(f"SELECT a_partir_de FROM {table_name_buenos_contribuyentes} WHERE ruc = '{ruc}'")
        with engine.connect() as connection:
            result = connection.execute(query).fetchone()
        if result:
            fecha_buenos_contribuyentes = result[0]  # Se obtiene la fecha del buen contribuyente de la base de datos
            df.at[index, 'Buenos Contribuyentes'] = "Si"
            df.at[index, 'Fecha Buenos Contribuyentes'] = fecha_buenos_contribuyentes


    # Estado contribuyente
    if pd.notna(ruc):  # Revisar que RUC no sea nulo
        # Query para verificar que RUC se encuentre en tabla de sunat_actividades
        query = text(f"SELECT estado_contribuyente FROM {table_name_sunat} WHERE ruc = '{ruc}'")
        with engine.connect() as connection:
            result = connection.execute(query).fetchone()
        if result:
            estado_contribuyente = result[0]  # Se obtiene el valor del estado_contribuyente
            df.at[index, 'Estado Contribuyente'] = estado_contribuyente

    # Condición domicilio
    if pd.notna(ruc):  # Revisar que RUC no sea nulo
        # Query para verificar que RUC se encuentre en tabla de sunat_actividades
        query = text(f"SELECT condicion_domicilio FROM {table_name_sunat} WHERE ruc = '{ruc}'")
        with engine.connect() as connection:
            result = connection.execute(query).fetchone()
        if result:
            condicion_domicilio = result[0]  # Se obtiene el valor de condicion_domicilio
            df.at[index, 'Condición Domicilio'] = condicion_domicilio



# Se guardan los datos modificados en un nuevo archivo 
output_file = nombre_BD.split(".")[0] + "_corrected.xlsx"
print(output_file)
df.to_excel(output_file, index=False)

print(f"Nuevo archivo {output_file} generado")


# if __name__ == "__main__":
#     RUC = input("Digite el número de RUC que desea buscar: ")
#     nombre_empresa, nombre_ruc, estado_contribuyente, condicion_contribuyente, domicilio_fiscal, actividades_economicas = obtener_datos_sunat(RUC)
    
#     if nombre_empresa:
#         print("Nombre de empresa:", nombre_empresa)
#         print("RUC de la empresa:", nombre_ruc)
#         print("Estado Contribuyente:", estado_contribuyente)
#         print("Condición Contribuyente:", condicion_contribuyente)
#         print("Domicilio Fiscal:", domicilio_fiscal)
#         print("Actividades Económicas:", actividades_economicas)