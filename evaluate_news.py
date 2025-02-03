from googlenews_getdata import extract_text
from googlenews_getdata import get_links_googlenews
import deepseek

def evaluate_news(provname, api_key):
    # Inicializar la API de DeepSeek
    ds = deepseek.DeepSeek(api_key)

    # Se obtienen los links de todas las noticias encontradas del proveedor a evaluar
    links_found = get_links_googlenews(provname)

    # Se utilizan los links para obtener el texto de cada noticia
    text_found = []
    for link in links_found:
        data_extracted = extract_text(link)
        text_found.append(data_extracted)

    # Enviar el prompt inicial solo para la primera noticia
    if text_found:
        initial_prompt = f"Quiero que te comportes como un analista senior experto en evaluación de empresas. A continuación, voy a pasarte textos de noticias online de diferentes empresas, quiero que evalúes ese contenido en los siguientes puntos: Eventos Corporativos (Fusiones, adquisiciones, nuevas alianzas), Cambios en la dirección (Nuevos CEO, cambios en la junta directiva), Expansión o reducción (Apertura/cierre de sucursales, expansión de operaciones), Problemas legales (Demandas, sanciones, auditorías.), Sanciones y cumplimiento (Relacionadas con normativas ISO, ESG, cumplimiento), Innovaciones y lanzamientos (Nuevos productos o servicios), Situación financiera (Reportes de crecimiento o crisis financieras), Impacto en la reputación (Opiniones del mercado, quejas o comentarios negativos). Cuando termine de enviarte todas las noticias disponibles de la empresa, voy a enviar la palabra 'Finalizar', una vez que te envíe esa palabra, tú debes de enviarme un valor numérico por cada campo de evaluación (Eventos Corporativos, Cambios en la dirección, Expansión o reducción, Problemas legales, Sanciones y cumplimiento, Innovaciones y lanzamientos, Situación financiera, Impacto en la reputación), en base a la información enviada (-3: Extremadamente negativo, -2: Muy Negativo, -1: Negativo, 0: No hay información o no es influyente, 1: Positivo, 2: Muy Positivo, 3: Extremadamente Positivo). Debes de asegurarte de que la noticia sea sobre la empresa deseada, ahora, la empresa a evaluar es {provname}.\n\n{text_found[0]}"
        ds.send_prompt(initial_prompt)

        # Enviar las noticias restantes sin el prompt inicial
        if len(text_found) > 1:
            for text in text_found[1:]:
                ds.send_prompt(text)

        # Finalizar la evaluación
        final_response = ds.send_prompt("Finalizar")
        print(f"Evaluación final de DeepSeek: {final_response}")
        return final_response
    else:
        print("No se encontraron noticias para evaluar.")
        return None

if __name__ == "__main__":
    provname = input("Indicar nombre del proveedor a evaluar: ")
    api_key = input("Indicar tu API Key de DeepSeek: ")
    result = evaluate_news(provname, api_key)
