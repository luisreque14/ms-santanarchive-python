import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURACIÓN PRINCIPAL ---
ANIO_INICIO = 2026
ANIO_FIN = 2026
MODO_HEADLESS = True


def limpiar_fecha(row_element):
    meses = {'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
             'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'}
    try:
        dia = row_element.find_element(By.CLASS_NAME, "day").text.strip().zfill(2)
        mes_raw = row_element.find_element(By.CLASS_NAME, "month").text.strip().lower()
        anio = row_element.find_element(By.CLASS_NAME, "year").text.strip()
        mes_num = meses.get(mes_raw, '01')
        return f"{anio}/{mes_num}/{dia}"
    except:
        return ""


def ejecutar_scraping_rango(inicio, fin, headless):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    all_final_data = []

    for anio in range(inicio, fin + 1):
        print(f"\n--- EXPLORANDO AÑO: {anio} ---")
        url_busqueda = f"https://www.setlist.fm/search?artist=5bd69ff4&query=santana&year={anio}"
        driver.get(url_busqueda)
        time.sleep(5)

        # --- DETECCIÓN HÍBRIDA DE PÁGINAS ---
        try:
            # Criterio 1: Elementos con clase .pageLink
            criterio_old = driver.find_elements(By.CSS_SELECTOR, ".listPagingNavigator .pageLink")
            # Criterio 2: Cualquier descendiente de la lista (para capturar el '14')
            criterio_new = driver.find_elements(By.CSS_SELECTOR, ".listPagingNavigator li *")

            todos_los_elementos = criterio_old + criterio_new
            numeros = []
            for e in todos_los_elementos:
                txt = e.text.strip()
                if txt.isdigit():
                    numeros.append(int(txt))

            total_paginas = max(numeros) if numeros else 1
            print(f" [SISTEMA] Detección híbrida exitosa: {total_paginas} páginas encontradas.")
        except:
            total_paginas = 1

        conciertos_info = []

        # FASE 1: RECOPILAR URLS
        for page in range(1, total_paginas + 1):
            print(f" Escaneando lista -> Página {page} de {total_paginas}...")
            driver.get(f"{url_busqueda}&page={page}")
            time.sleep(4)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            items = driver.find_elements(By.CLASS_NAME, "setlistPreview")
            for item in items:
                try:
                    link_elem = item.find_element(By.CSS_SELECTOR, "h2 a")
                    url_detalle = link_elem.get_attribute("href")
                    try:
                        tour_raw = item.find_element(By.XPATH, ".//*[contains(text(), 'Tour:')]").text
                        tour_text = tour_raw.split("Tour:")[1].strip()
                    except:
                        tour_text = ""

                    full_text = \
                    item.find_element(By.TAG_NAME, "h2").text.replace("Santana at", "").split("Edit setlist")[0].strip()
                    partes = [p.strip() for p in full_text.split(',')]
                    fecha = limpiar_fecha(item)
                    venue = partes[0] if partes else ""
                    es_festival = "SI" if "festival" in venue.lower() else "NO"

                    ciudad, estado, pais = "", "", ""
                    if len(partes) > 1:
                        raw_p = partes[-1]
                        pais = "United States" if raw_p == "USA" else ("United Kingdom" if raw_p == "UK" else raw_p)
                        if len(partes) >= 3:
                            ciudad = partes[1]
                            if len(partes) == 4: estado = partes[2]

                    conciertos_info.append({
                        "url": url_detalle, "fecha": fecha, "venue": venue, "tour": tour_text,
                        "ciudad": ciudad, "estado": estado, "pais": pais, "es_festival": es_festival
                    })
                except:
                    continue

        # FASE 2: PROCESAR DETALLES
        print(f" [INFO] Extrayendo datos de {len(conciertos_info)} conciertos...")
        for idx, c in enumerate(conciertos_info):
            print(f"   ({idx + 1}/{len(conciertos_info)}) {c['fecha']} - {c['venue']}")
            driver.get(c['url'])
            time.sleep(2.5)

            tour_final = c['tour']
            if not tour_final:
                try:
                    tour_final = \
                    driver.find_element(By.XPATH, "//*[contains(text(), 'Tour:')]").text.split("Tour:")[1].split(",")[
                        0].strip()
                except:
                    pass

            filas_canciones = driver.find_elements(By.CSS_SELECTOR, "li.setlistParts.song")

            # SI NO HAY CANCIONES, AGREGAR FILA VACÍA
            if not filas_canciones:
                all_final_data.append({
                    "Fecha": c['fecha'], "Venue": c['venue'], "Es Festival?": c['es_festival'],
                    "Tour": tour_final, "Ciudad": c['ciudad'], "Estado": c['estado'],
                    "País": c['pais'], "Canción": "", "Artista Invitado": "", "Artista Invitado Full Text": ""
                })
                continue

            for fila in filas_canciones:
                try:
                    cancion = fila.find_element(By.CLASS_NAME, "songLabel").text.strip()
                    invitado_full, invitado_limpio = "", ""
                    try:
                        info_part = fila.find_element(By.CLASS_NAME, "infoPart")
                        texto_small = info_part.find_element(By.TAG_NAME, "small").text.strip()
                        invitado_full = texto_small.replace("(", "").replace(")", "").strip()
                        texto_lower = invitado_full.lower()

                        if "with" in texto_lower:
                            parte_despues_with = invitado_full.split("with")[1].strip()
                            bloqueadores = ["snippet", "introduction", "band intro", "cover", "by ", "solo", "tease",
                                            "lyrics", "debut", "jam", "instrumental", "bass", "drum", "percussion",
                                            "guitar"]

                            if not (any(b in parte_despues_with.lower() for b in
                                        bloqueadores) or parte_despues_with.startswith('"')):
                                separadores = [" live", " debut", " on ", " snippet", " cover", " by "]
                                nombre_final = parte_despues_with
                                for sep in separadores:
                                    if sep in nombre_final.lower(): nombre_final = nombre_final.lower().split(sep)[
                                        0].strip()
                                if len(nombre_final) > 2: invitado_limpio = nombre_final.strip(' "').title()
                    except:
                        pass

                    all_final_data.append({
                        "Fecha": c['fecha'], "Venue": c['venue'], "Es Festival?": c['es_festival'],
                        "Tour": tour_final, "Ciudad": c['ciudad'], "Estado": c['estado'],
                        "País": c['pais'], "Canción": cancion,
                        "Artista Invitado": invitado_limpio,
                        "Artista Invitado Full Text": invitado_full
                    })
                except:
                    continue

    driver.quit()
    return all_final_data


if __name__ == "__main__":
    datos = ejecutar_scraping_rango(ANIO_INICIO, ANIO_FIN, MODO_HEADLESS)
    if datos:
        df = pd.DataFrame(datos)
        columnas = ["Fecha", "Venue", "Es Festival?", "Tour", "Ciudad", "Estado", "País", "Canción", "Artista Invitado",
                    "Artista Invitado Full Text"]
        df[columnas].to_excel(f"Santana_Setlists_{ANIO_INICIO}_{ANIO_FIN}.xlsx", index=False)
        print(f"\n¡ÉXITO! Proceso finalizado.")