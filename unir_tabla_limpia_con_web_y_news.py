import pandas as pd
from sqlalchemy import create_engine

# Conexión a PostgreSQL
db_user = "postgres"
db_password = "greciatech"
db_host = "127.0.0.1"
db_port = "5432"
db_name = "padron_ruc"
table_name_web = "googleweb_datos" # tabla donde se encuentran los datos extraidos de la web
table_name_news = "googlenews_evaluation" # tabla donde se encuentran las evaluaciones realizadas en base a noticias
table_name_sunat = "sunat_ruc" # tabla donde se encuentran datos genéricos

# Lectura de datos
def leer_datos(nombre_BD, n_row, sheet_name):
    file_path = "./BD_corregidas/" + nombre_BD # Ruta base de datos
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

# Se une la tabla limpia y con datos de SUNAT (procesada por la función limpieza_enriquecimiento_datos.py) con tablas de news y web
if __name__ == "__main__":

    # Solicitud de datos
    nombre_BD = input("Por favor, escriba el nombre de la Base de Datos (junto con su extensión .csv, .xls o .xlsx): ") # Nombre Base Datos
    sheet_name = input("Por favor, escriba el nombre de la hoja donde se encuentra la BD: ") # Nombre Hoja de la tabla de la BD
    n_row = int(input("Escriba el número de fila para empezar a leer el archivo: ")) # Número de fila donde inician los datos
    n_row = n_row - 1

    # Lectura de datos
    df = leer_datos(nombre_BD, n_row, sheet_name)

    # Número de columna donde está el RUC y razón social
    n_ruc = int(input("Escriba el número de la columna donde se encuentran los datos del RUC: "))

    # Nombre de columna donde está el RUC
    nombre_ruc = df.columns[n_ruc-1]

    # Crear la conexión
    engine = create_engine(f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")

    # Cargar las tablas de PostgreSQL
    query_sunat_ruc = f"SELECT ruc, nombre_razonsocial FROM {table_name_sunat}"
    query_googlenews = f"SELECT proveedor as prov1, eventos_corporativos, cambios_direccion, expansion_reduccion, problemas_legales, sanciones_cumplimiento, innovaciones_lanzamientos, situacion_financiera, impacto_reputacion, comentarios FROM {table_name_news}"
    query_googleweb = f"SELECT proveedor as prov2, ubicacion, datos_contacto, redes_sociales, productos_servicios, certificaciones, clientes_casos_exito, otra_informacion, observaciones_contradicciones FROM {table_name_web}" 

    df_sunat_ruc = pd.read_sql(query_sunat_ruc, engine)
    df_googlenews = pd.read_sql(query_googlenews, engine)
    df_googleweb = pd.read_sql(query_googleweb, engine)

    # Conversión de tipo de datos
    df[nombre_ruc] = df[nombre_ruc].astype(str)

    # Unir las tablas

    # Unir el CSV con la tabla sunat_ruc usando el RUC
    df_merged = pd.merge(df, df_sunat_ruc, left_on = nombre_ruc, right_on="ruc", how="left")
    # Eliminar la columna "ruc" redundante después del merge
    df_merged.drop(columns=["ruc"], inplace=True)

    # Unir el resultado con googlenews_evaluation usando el nombre_razonsocial
    df_merged = pd.merge(df_merged, df_googlenews, left_on="nombre_razonsocial", right_on="prov1", how="left")
    # Eliminar la columna "prov1" redundante después del merge
    df_merged.drop(columns=["prov1"], inplace=True)

    # Unir el resultado con googleweb_datos usando el nombre_razonsocial
    df_merged = pd.merge(df_merged, df_googleweb, left_on="nombre_razonsocial", right_on="prov2", how="left")
    # Eliminar la columna "prov2" redundante después del merge
    df_merged.drop(columns=["prov2"], inplace=True)

    # Guardar tabla final
    output_file = nombre_BD.split(".")[0] + "_final.xlsx"
    print(output_file)
    df_merged.to_excel(output_file, index=False)  # Guardar como excel