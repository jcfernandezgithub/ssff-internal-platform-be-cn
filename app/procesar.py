
import json
import os
import csv
import json
import re
import requests
from io import BytesIO
from PyPDF2 import PdfReader
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import google.generativeai as genai
from app.utils import extraer_texto_pdf  # Asegúrate de tener esta función

def ejecutar_proceso(url: str, output_path: str, estado: dict):
    try:
        print("🚀 Iniciando proceso de scraping")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            print(f"🌐 Navegando a {url}")
            page.goto(url)
            page.wait_for_timeout(10000)
            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, 'html.parser')
        wrap_div = soup.find("div", class_="wrapsection")
        tbody = wrap_div.find("table").find("tbody") if wrap_div else None

        results = []
        start_collecting = False
        for tr in tbody.find_all("tr"):
            tds = tr.find_all("td")
            if not tds:
                continue
            text = tds[0].get_text(strip=True)
            if "Solicitudes de Cambios de Nombre" in text:
                start_collecting = True
                continue
            if start_collecting and len(tds) >= 2:
                nombre = tds[0].get_text(strip=True)
                a_tag = tds[1].find("a")
                pdf = a_tag["href"] if a_tag else None
                results.append({"nombre": nombre, "pdf": pdf})

        results = results[:100]
        estado["total"] = len(results)
        estado["procesados"] = 0
        estado["progreso"] = 0

        genai.configure(api_key="AIzaSyAl4sGdg1dbVHwEIhEsBLzv6O7qtRKonVw")
        model = genai.GenerativeModel(model_name="gemini-2.5-flash-preview-05-20")

        # ✅ Prompt actualizado
        prompt = f"""
        A continuación te proporciono un JSON generado por scraping web de publicaciones judiciales:

        {json.dumps(results, ensure_ascii=False)}

        Quiero que analices directamente este JSON y me devuelvas como salida únicamente un nuevo JSON que contenga:

        - Solo los objetos válidos donde el campo "nombre" sea claramente un nombre completo de persona.
        - Cada objeto debe mantener el campo "nombre" y "pdf".
        - El JSON debe comenzar con [ y terminar con ]
        """

        response = model.generate_content(prompt, stream=True)
        full_response = "".join([chunk.text for chunk in response])
        json_match = re.search(r"\[\s*{.*?}\s*\]", full_response, re.DOTALL)
        if not json_match:
            estado["status"] = "error"
            return

        json_data = json.loads(json_match.group(0))

        # Rutas de salida
        base_name, _ = os.path.splitext(output_path)
        csv_path = f"{base_name}.csv"

        with open(output_path, "w", encoding="utf-8") as json_file, \
             open(csv_path, "w", encoding="utf-8", newline="") as csv_file:

            json_file.write("[\n")
            writer = csv.DictWriter(csv_file, fieldnames=["nombre_original", "nombre_nuevo", "rut", "pdf"])
            writer.writeheader()

            first = True
            for entry in json_data:
            # for i, entry in enumerate(json_data):
            #     if i >= 10:
            #         break

                texto_pdf = extraer_texto_pdf(entry["pdf"])[:3000]
                prompt_cambio = f"""
                \"\"\"{texto_pdf}\"\"\"
                ¿Es una solicitud de cambio de nombre? Si sí, responde con:
                {{
                "nombre_original": "...",
                "nombre_nuevo": "...",
                "rut": "...",
                "pdf": "{entry['pdf']}"
                }}
                Si no, responde solo con null.
                """
                sub_resp = model.generate_content(prompt_cambio)
                content = sub_resp.text.strip()

                parsed = None
                match = re.search(r"{\s*\"nombre_original\".*?}", content, re.DOTALL)
                if match:
                    try:
                        parsed = json.loads(match.group(0))
                    except:
                        pass
                else:
                    try:
                        maybe_json = json.loads(content)
                        if isinstance(maybe_json, dict) and "nombre_original" in maybe_json:
                            parsed = maybe_json
                    except:
                        pass

                if parsed:
                    if not first:
                        json_file.write(",\n")
                    json.dump(parsed, json_file, ensure_ascii=False, indent=2)
                    writer.writerow(parsed)
                    first = False

                estado["procesados"] += 1
                estado["progreso"] = round(estado["procesados"] * 100 / min(10, estado["total"]))

            json_file.write("\n]\n")

        estado["status"] = "listo"
        print(f"✅ Procesamiento finalizado. Archivos guardados en:\n📄 JSON: {output_path}\n📑 CSV: {csv_path}")

    except Exception as e:
        print(f"❌ Error en ejecutar_proceso: {e}")
        estado["status"] = "error"
