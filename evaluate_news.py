from googlenews_getdata import extract_text
from googlenews_getdata import get_links_googlenews


def evaluate_news(provname):

    # Se obtienen los links de todas las noticias encontradas del proveedor a evaluar
    links_found = list()
    links_found = get_links_googlenews(provname)

    # Se utilizan los links para obtener el texto de cada noticia
    text_found = list()
    for link in links_found:
        data_extracted = extract_text(link)
        text_found.append(data_extracted)


    return text_found


if __name__ == "__main__":
    provname = input("Indicar nombre del proveedor a evaluar: ")
    result = evaluate_news(provname)
    print(f"Se han encontrado {len(result)} noticias.")
    print(result)