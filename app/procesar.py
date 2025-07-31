
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

# def ejecutar_proceso(url: str, output_path: str, estado: dict):
#     try:
#         print("🚀 Iniciando proceso de scraping")
#         with sync_playwright() as p:
#             browser = p.chromium.launch(headless=True)
#             page = browser.new_page()
#             print(f"🌐 Navegando a {url}")
#             page.goto(url)
#             page.wait_for_timeout(10000)
#             html = page.content()
#             browser.close()

#         soup = BeautifulSoup(html, 'html.parser')
#         wrap_div = soup.find("div", class_="wrapsection")
#         tbody = wrap_div.find("table").find("tbody") if wrap_div else None

#         if not tbody:
#             print("❌ No se encontró la tabla en el HTML")
#             estado["status"] = "error"
#             return

#         results = []
#         start_collecting = False
#         for tr in tbody.find_all("tr"):
#             tds = tr.find_all("td")
#             if not tds:
#                 continue
#             text = tds[0].get_text(strip=True)
#             if "Solicitudes de Cambios de Nombre" in text:
#                 start_collecting = True
#                 print("🔍 Se encontró el encabezado de la sección de cambios de nombre")
#                 continue
#             if start_collecting and len(tds) >= 2:
#                 nombre = tds[0].get_text(strip=True)
#                 a_tag = tds[1].find("a")
#                 pdf = a_tag["href"] if a_tag else None
#                 results.append({"nombre": nombre, "pdf": pdf})

#         print(f"📄 Total de posibles PDFs encontrados: {len(results)}")
#         results = results[:100]  # Limite de seguridad

#         estado["total"] = len(results)
#         estado["procesados"] = 0
#         estado["progreso"] = 0

#         genai.configure(api_key="AIzaSyAl4sGdg1dbVHwEIhEsBLzv6O7qtRKonVw")
#         model = genai.GenerativeModel(model_name="gemini-2.5-flash-preview-05-20")

#         print("🤖 Solicitando filtrado inicial a Gemini...")
#         prompt = f"""
#         A continuación te proporciono un JSON generado por scraping web de publicaciones judiciales:

#         {json.dumps(results, ensure_ascii=False)}

#         Quiero que analices directamente este JSON y me devuelvas como salida únicamente un nuevo JSON que contenga:

#         - Solo los objetos válidos donde el campo "nombre" sea claramente un nombre completo de persona.
#         - Cada objeto debe mantener el campo "nombre" y "pdf".
#         - El JSON debe comenzar con [ y terminar con ]
#         """

#         response = model.generate_content(prompt, stream=True)
#         full_response = "".join([chunk.text for chunk in response])
#         print("📝 Respuesta recibida de Gemini (filtrado inicial):")
#         print(full_response[:1000])  # Fragmento

#         json_match = re.search(r"\[\s*{.*?}\s*\]", full_response, re.DOTALL)
#         if not json_match:
#             print("❌ No se pudo extraer JSON válido del resultado de Gemini")
#             estado["status"] = "error"
#             return

#         json_data = json.loads(json_match.group(0))
#         print(f"✅ Total de elementos validados por Gemini: {len(json_data)}")

#         # Ordena por campo "nombre"
#         json_data.sort(key=lambda x: x.get("nombre", ""))

#         base_name, _ = os.path.splitext(output_path)
#         csv_path = f"{base_name}.csv"

#         with open(output_path, "w", encoding="utf-8") as json_file, \
#              open(csv_path, "w", encoding="utf-8", newline="") as csv_file:

#             json_file.write("[\n")
#             writer = csv.DictWriter(csv_file, fieldnames=["nombre_original", "nombre_nuevo", "rut", "pdf"])
#             writer.writeheader()

#             first = True
#             guardados = 0

#             for entry in json_data:
#                 print(f"📄 Procesando: {entry['nombre']}")
#                 texto_pdf = extraer_texto_pdf(entry["pdf"])[:3000]
#                 prompt_cambio = f"""
#                 \"\"\"{texto_pdf}\"\"\"
#                 ¿Es una solicitud de cambio de nombre? Si sí, responde con:
#                 {{
#                   "nombre_original": "...",
#                   "nombre_nuevo": "...",
#                   "rut": "...",
#                   "pdf": "{entry['pdf']}"
#                 }}
#                 Si no, responde solo con null.
#                 """
#                 sub_resp = model.generate_content(prompt_cambio)
#                 content = sub_resp.text.strip()

#                 parsed = None
#                 try:
#                     match = re.search(r"{\s*\"nombre_original\".*?}", content, re.DOTALL)
#                     if match:
#                         parsed = json.loads(match.group(0))
#                     else:
#                         maybe_json = json.loads(content)
#                         if isinstance(maybe_json, dict) and "nombre_original" in maybe_json:
#                             parsed = maybe_json
#                 except Exception as e:
#                     print(f"⚠️ Error al interpretar respuesta Gemini: {e}")
#                     print(f"📬 Contenido devuelto:\n{content}")
#                     continue

#                 if parsed:
#                     print(f"🔄 {parsed['nombre_original']} ➜ {parsed['nombre_nuevo']}")
#                     if not first:
#                         json_file.write(",\n")
#                     json.dump(parsed, json_file, ensure_ascii=False, indent=2)
#                     writer.writerow(parsed)
#                     guardados += 1
#                     first = False
#                 else:
#                     print("⛔ No se detectó un cambio válido.")

#                 estado["procesados"] += 1
#                 estado["progreso"] = round(estado["procesados"] * 100 / estado["total"])

#             json_file.write("\n]\n")

#         estado["status"] = "listo"
#         print(f"✅ Finalizado. Cambios guardados: {guardados}")
#         print(f"📄 JSON: {output_path}")
#         print(f"📑 CSV: {csv_path}")

#     except Exception as e:
#         print(f"❌ Error general en ejecutar_proceso: {e}")
#         estado["status"] = "error"


def ejecutar_proceso(url: str, output_path: str, estado: dict, estado_path: str):
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

        if not tbody:
            print("❌ No se encontró la tabla en el HTML")
            estado["status"] = "error"
            with open(estado_path, "w") as f:
                json.dump(estado, f)
            return

        results = []
        start_collecting = False
        for tr in tbody.find_all("tr"):
            tds = tr.find_all("td")
            if not tds:
                continue

            text = tds[0].get_text(strip=True)

            if "Solicitudes de Cambios de Nombre" in text:
                start_collecting = True
                print("🔍 Se encontró el encabezado de la sección de cambios de nombre")
                continue

            # 🔴 Corte al detectar nuevo encabezado fuera de la sección deseada
            if start_collecting and (
                "Reconstituciones Inscripción de Dominio" in text or
                "Rectificaciones" in text or
                text.startswith("Reconstituciones") or
                text.startswith("Rectificaciones")
            ):
                print("🛑 Sección de cambios de nombre finalizada")
                break

            if start_collecting and len(tds) >= 2:
                nombre = tds[0].get_text(strip=True)
                a_tag = tds[1].find("a")
                pdf = a_tag["href"] if a_tag else None
                results.append({"nombre": nombre, "pdf": pdf})

        print(f"📄 Total de posibles PDFs encontrados: {len(results)}")
        results.sort(key=lambda x: x.get("nombre", ""))

        estado["total"] = len(results)
        estado["procesados"] = 0
        estado["progreso"] = 0
        with open(estado_path, "w") as f:
            json.dump(estado, f)

        # 🔐 Configurar Gemini
        genai.configure(api_key="AIzaSyAl4sGdg1dbVHwEIhEsBLzv6O7qtRKonVw")
        model = genai.GenerativeModel(model_name="gemini-2.5-flash-preview-05-20")

        base_name, _ = os.path.splitext(output_path)
        csv_path = f"{base_name}.csv"

        with open(output_path, "w", encoding="utf-8") as json_file, \
             open(csv_path, "w", encoding="utf-8", newline="") as csv_file:

            json_file.write("[\n")
            writer = csv.DictWriter(csv_file, fieldnames=["nombre_original", "nombre_nuevo", "rut", "pdf"])
            writer.writeheader()

            first = True
            guardados = 0

            for entry in results:
                print(f"📄 Procesando: {entry['nombre']}")
                texto_pdf = extraer_texto_pdf(entry["pdf"])[:3000]

                prompt_cambio = f"""
                \"\"\"{texto_pdf}\"\"\"

                ¿Este texto corresponde a una solicitud de cambio de nombre?

                Si la respuesta es sí, extraé exclusivamente la información de la persona cuyo nombre será cambiado (ya sea menor o adulto), y devolvé el siguiente JSON:

                {{
                "nombre_original": "...",
                "nombre_nuevo": "...",
                "rut": "...",
                "pdf": "{entry['pdf']}"
                }}

                Instrucciones clave:
                - "nombre_original": debe ser el nombre de la persona a la que se le cambiará el nombre.
                - "nombre_nuevo": el nuevo nombre que se solicita para esa persona.
                - "rut": debe ser **el número de cédula o RUT de la persona cuyo nombre será cambiado**, si aparece.
                    - Si aparece más de un RUT, sólo se debe usar el que corresponde a esa persona.
                    - Si **la persona que cambia su nombre es menor y su RUT no aparece**, colocar `"rut": "null"`.
                    - Nunca coloques el RUT de quien representa al menor.

                Consejo: si hay una persona actuando "en representación de su hijo/hija", el RUT suele estar asociado al adulto. Asegurate de que el RUT **coincida con la persona cuyo nombre cambiará**, no con quien presenta la solicitud.

                No inventes datos. Si no hay suficiente información para completar algún campo, colocá "null".

                Si el texto **no** corresponde a una solicitud de cambio de nombre, respondé solo con: null
                """


                try:
                    sub_resp = model.generate_content(prompt_cambio)
                    content = sub_resp.text.strip()

                    parsed = None
                    match = re.search(r"{\s*\"nombre_original\".*?}", content, re.DOTALL)
                    if match:
                        parsed = json.loads(match.group(0))
                    else:
                        maybe_json = json.loads(content)
                        if isinstance(maybe_json, dict) and "nombre_original" in maybe_json:
                            parsed = maybe_json

                    if parsed:
                        print(f"🔄 {parsed['nombre_original']} ➜ {parsed['nombre_nuevo']}")
                        if not first:
                            json_file.write(",\n")
                        json.dump(parsed, json_file, ensure_ascii=False, indent=2)
                        writer.writerow(parsed)
                        guardados += 1
                        first = False
                    else:
                        print("⛔ No se detectó un cambio válido.")
                except Exception as e:
                    print(f"⚠️ Error al procesar PDF: {entry['pdf']}")
                    print(f"💬 Gemini devolvió:\n{content}")
                    print(f"🧨 Error: {e}")

                estado["procesados"] += 1
                estado["progreso"] = round(estado["procesados"] * 100 / estado["total"])
                with open(estado_path, "w") as f:
                    json.dump(estado, f)

            json_file.write("\n]\n")

        estado["status"] = "listo"
        with open(estado_path, "w") as f:
            json.dump(estado, f)

        print(f"✅ Finalizado. Cambios guardados: {guardados}")
        print(f"📄 JSON: {output_path}")
        print(f"📑 CSV: {csv_path}")

    except Exception as e:
        print(f"❌ Error general en ejecutar_proceso: {e}")
        estado["status"] = "error"
        with open(estado_path, "w") as f:
            json.dump(estado, f)

