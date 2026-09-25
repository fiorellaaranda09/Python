import re
from urllib import request
from urllib.error import URLError

lpo = ["coño", "bobo", "culiao", "pinche", "estupido", "estupida"]


def quitar_acentos(texto):
    # Reemplaza vocales con tilde por vocales normales
    mapa = str.maketrans("áéíóúÁÉÍÓÚ", "aeiouAEIOU")
    return texto.translate(mapa)


def verificar_web(url):
    try:
        req = request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        f = request.urlopen(req)
    except URLError:
        return "¡La url " + url + " no existe!"
    else:
        # Decodificamos y pasamos todo a minúsculas y sin acentos
        aux = f.read().decode("utf-8")
        texto_limpio = quitar_acentos(aux.lower())

        palabras_encontradas = []

        for palabra in lpo:
            palabra_limpia = quitar_acentos(palabra.lower())
            # Busca la palabra completa ignorando signos de puntuación
            if re.search(r"\b" + palabra_limpia + r"\b", texto_limpio):
                palabras_encontradas.append(palabra)

        return palabras_encontradas


url = "https://es.wiktionary.org/wiki/Wikcionario:Insultos_regionales"
print("\n------------------------------------\n")
print("\nInforme de sitio:")
print(verificar_web(url))