# # procesar.py
# import json
# import re
# import requests
# from io import BytesIO
# from PyPDF2 import PdfReader
# from playwright.sync_api import sync_playwright
# from bs4 import BeautifulSoup
# import google.generativeai as genai

# def extraer_texto_pdf(pdf_url):
#     try:
#         response = requests.get(pdf_url, timeout=10)
#         response.raise_for_status()
#         with BytesIO(response.content) as pdf_file:
#             reader = PdfReader(pdf_file)
#             texto = ""
#             for page in reader.pages:
#                 texto += page.extract_text() or ""
#             return texto.strip()
#     except Exception as e:
#         print(f"❌ Error leyendo PDF {pdf_url}: {e}")
#         return ""

# def ejecutar_proceso(url: str, output_path: str, estado: dict):
#     try:
#         with sync_playwright() as p:
#             browser = p.webkit.launch(headless=True)
#             page = browser.new_page()
#             page.goto(url)
#             page.wait_for_timeout(10000)
#             html = page.content()
#             browser.close()

#         soup = BeautifulSoup(html, 'html.parser')
#         wrap_div = soup.find("div", class_="wrapsection")
#         tbody = wrap_div.find("table").find("tbody") if wrap_div else None

#         results = []
#         start_collecting = False
#         for tr in tbody.find_all("tr"):
#             tds = tr.find_all("td")
#             if not tds:
#                 continue
#             text = tds[0].get_text(strip=True)
#             if "Solicitudes de Cambios de Nombre" in text:
#                 start_collecting = True
#                 continue
#             if start_collecting and len(tds) >= 2:
#                 nombre = tds[0].get_text(strip=True)
#                 a_tag = tds[1].find("a")
#                 pdf = a_tag["href"] if a_tag else None
#                 results.append({"nombre": nombre, "pdf": pdf})
#         results = results[:100]

#         genai.configure(api_key='AIzaSyAl4sGdg1dbVHwEIhEsBLzv6O7qtRKonVw')
#         model = genai.GenerativeModel(model_name="gemini-2.5-flash-preview-05-20")
#         prompt = f"""
#         A continuación te proporciono un JSON generado por scraping web de publicaciones judiciales:

#         {json.dumps(results, ensure_ascii=False)}

#         Quiero que analices directamente este JSON y me devuelvas como salida únicamente un nuevo JSON que contenga:

#         - Solo los objetos válidos donde el campo "nombre" sea claramente un nombre completo de persona.
#         - Cada objeto debe mantener el campo "nombre" y "pdf".
#         - El JSON debe empezar por `[` y terminar en `]`, y ser válido.
#         """
#         response = model.generate_content(prompt, stream=True)
#         full_response = "".join([chunk.text for chunk in response])

#         json_match = re.search(r"\[\s*{.*?}\s*\]", full_response, re.DOTALL)
#         if not json_match:
#             estado["status"] = "error"
#             return
#         json_data = json.loads(json_match.group(0))

#         resultado_final = []
#         for entry in json_data:
#             texto_pdf = extraer_texto_pdf(entry["pdf"])[:3000]
#             prompt_cambio = f"""
#             \"\"\"{texto_pdf}\"\"\"
#             ¿Es una solicitud de cambio de nombre? Si sí, responde con:
#             {{
#               "nombre_original": "...",
#               "nombre_nuevo": "...",
#               "pdf": "{entry['pdf']}"
#             }}
#             Si no, responde solo con null.
#             """
#             sub_resp = model.generate_content(prompt_cambio)
#             content = sub_resp.text
#             match = re.search(r"{\\s*\"nombre_original\".*?}", content, re.DOTALL)
#             if match:
#                 try:
#                     parsed = json.loads(match.group(0))
#                     resultado_final.append(parsed)
#                 except:
#                     continue

#         with open(output_path, "w", encoding="utf-8") as f:
#             json.dump(resultado_final, f, ensure_ascii=False, indent=2)

#         estado["status"] = "listo"
#     except Exception as e:
#         estado["status"] = "error"
#         estado["error"] = str(e)

# import json
# import re
# import os
# import requests
# from io import BytesIO
# from PyPDF2 import PdfReader
# from playwright.sync_api import sync_playwright
# from bs4 import BeautifulSoup
# import google.generativeai as genai

# def extraer_texto_pdf(pdf_url):
#     try:
#         response = requests.get(pdf_url, timeout=10)
#         response.raise_for_status()
#         with BytesIO(response.content) as pdf_file:
#             reader = PdfReader(pdf_file)
#             texto = ""
#             for page in reader.pages:
#                 texto += page.extract_text() or ""
#             return texto.strip()
#     except Exception as e:
#         print(f"❌ Error leyendo PDF {pdf_url}: {e}")
#         return ""

# def ejecutar_proceso(url: str, output_path: str, estado: dict):
#     try:
#         print("🚀 Iniciando proceso de scraping")
#         with sync_playwright() as p:
#             print("🧭 Lanzando navegador...")
#             browser = p.webkit.launch(headless=True)
#             page = browser.new_page()
#             print(f"🌐 Navegando a {url}")
#             page.goto(url)
#             page.wait_for_timeout(10000)
#             html = page.content()
#             browser.close()
#             print("✅ HTML obtenido")

#         print("🔍 Parseando HTML...")
#         soup = BeautifulSoup(html, 'html.parser')
#         wrap_div = soup.find("div", class_="wrapsection")
#         tbody = wrap_div.find("table").find("tbody") if wrap_div else None

#         print("📋 Extrayendo filas...")
#         results = []
#         start_collecting = False
#         for tr in tbody.find_all("tr"):
#             tds = tr.find_all("td")
#             if not tds:
#                 continue
#             text = tds[0].get_text(strip=True)
#             if "Solicitudes de Cambios de Nombre" in text:
#                 start_collecting = True
#                 continue
#             if start_collecting and len(tds) >= 2:
#                 nombre = tds[0].get_text(strip=True)
#                 a_tag = tds[1].find("a")
#                 pdf = a_tag["href"] if a_tag else None
#                 results.append({"nombre": nombre, "pdf": pdf})
#         print(f"🧾 Se encontraron {len(results)} registros")
#         results = results[:100]

#         print("🤖 Enviando a Gemini...")
#         genai.configure(api_key='AIzaSyAl4sGdg1dbVHwEIhEsBLzv6O7qtRKonVw')
#         model = genai.GenerativeModel(model_name="gemini-2.5-flash-preview-05-20")

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

#         json_match = re.search(r"\[\s*{.*?}\s*\]", full_response, re.DOTALL)
#         if not json_match:
#             print("⚠️ No se encontró JSON válido en la respuesta de Gemini")
#             estado["status"] = "error"
#             return
#         json_data = json.loads(json_match.group(0))
#         print(f"✅ Gemini devolvió {len(json_data)} resultados válidos")

#         resultado_final = []
#         for entry in json_data:
#             print(f"📄 Procesando PDF: {entry['pdf']}")
#             texto_pdf = extraer_texto_pdf(entry["pdf"])[:3000]
#             prompt_cambio = f"""
#             \"\"\"{texto_pdf}\"\"\"
#             ¿Es una solicitud de cambio de nombre? Si sí, responde con:
#             {{
#               "nombre_original": "...",
#               "nombre_nuevo": "...",
#               "pdf": "{entry['pdf']}"
#             }}
#             Si no, responde solo con null.
#             """
#             sub_resp = model.generate_content(prompt_cambio)
#             content = sub_resp.text
#             match = re.search(r"{\\s*\"nombre_original\".*?}", content, re.DOTALL)
#             if match:
#                 try:
#                     parsed = json.loads(match.group(0))
#                     resultado_final.append(parsed)
#                     print(f"✅ Agregado: {parsed}")
#                 except Exception as e:
#                     print(f"❌ Error parseando respuesta: {e}")
#                     continue

#         print(f"💾 Guardando {len(resultado_final)} resultados en {output_path}")
#         with open(output_path, "w", encoding="utf-8") as f:
#             json.dump(resultado_final, f, ensure_ascii=False, indent=2)

#         estado["status"] = "listo"
#         print("🎉 Proceso finalizado correctamente")

#     except Exception as e:
#         estado["status"] = "error"
#         estado["error"] = str(e)
#         print(f"💥 Error inesperado: {e}")

# import json
# import re
# import os
# import requests
# from io import BytesIO
# from PyPDF2 import PdfReader
# from playwright.sync_api import sync_playwright
# from bs4 import BeautifulSoup
# import google.generativeai as genai

# def extraer_texto_pdf(pdf_url):
#     try:
#         response = requests.get(pdf_url, timeout=10)
#         response.raise_for_status()
#         with BytesIO(response.content) as pdf_file:
#             reader = PdfReader(pdf_file)
#             texto = ""
#             for page in reader.pages:
#                 texto += page.extract_text() or ""
#             return texto.strip()
#     except Exception as e:
#         print(f"❌ Error leyendo PDF {pdf_url}: {e}")
#         return ""

# def ejecutar_proceso(url: str, output_path: str, estado: dict):
#     try:
#         print("🚀 Iniciando proceso de scraping")
#         with sync_playwright() as p:
#             print("🧭 Lanzando navegador...")
#             browser = p.webkit.launch(headless=True)
#             page = browser.new_page()
#             print(f"🌐 Navegando a {url}")
#             page.goto(url)
#             page.wait_for_timeout(10000)
#             html = page.content()
#             browser.close()
#             print("✅ HTML obtenido")

#         print("🔍 Parseando HTML...")
#         soup = BeautifulSoup(html, 'html.parser')
#         wrap_div = soup.find("div", class_="wrapsection")
#         tbody = wrap_div.find("table").find("tbody") if wrap_div else None

#         print("📋 Extrayendo filas...")
#         results = []
#         start_collecting = False
#         for tr in tbody.find_all("tr"):
#             tds = tr.find_all("td")
#             if not tds:
#                 continue
#             text = tds[0].get_text(strip=True)
#             if "Solicitudes de Cambios de Nombre" in text:
#                 start_collecting = True
#                 continue
#             if start_collecting and len(tds) >= 2:
#                 nombre = tds[0].get_text(strip=True)
#                 a_tag = tds[1].find("a")
#                 pdf = a_tag["href"] if a_tag else None
#                 results.append({"nombre": nombre, "pdf": pdf})
#         print(f"🧾 Se encontraron {len(results)} registros")
#         results = results[:100]

#         print("🤖 Enviando a Gemini...")
#         genai.configure(api_key='AIzaSyAl4sGdg1dbVHwEIhEsBLzv6O7qtRKonVw')
#         model = genai.GenerativeModel(model_name="gemini-2.5-flash-preview-05-20")

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

#         json_match = re.search(r"\[\s*{.*?}\s*\]", full_response, re.DOTALL)
#         if not json_match:
#             print("⚠️ No se encontró JSON válido en la respuesta de Gemini")
#             estado["status"] = "error"
#             return
#         json_data = json.loads(json_match.group(0))
#         print(f"✅ Gemini devolvió {len(json_data)} resultados válidos")

#         print(f"💾 Guardando progresivamente en {output_path}")
#         with open(output_path, "w", encoding="utf-8") as f:
#             f.write("[\n")
#             first = True

#             for entry in json_data:
#                 print(f"📄 Procesando PDF: {entry['pdf']}")
#                 texto_pdf = extraer_texto_pdf(entry["pdf"])[:3000]
#                 prompt_cambio = f"""
#                 \"\"\"{texto_pdf}\"\"\"
#                 ¿Es una solicitud de cambio de nombre? Si sí, responde con:
#                 {{
#                   "nombre_original": "...",
#                   "nombre_nuevo": "...",
#                   "pdf": "{entry['pdf']}"
#                 }}
#                 Si no, responde solo con null.
#                 """
#                 sub_resp = model.generate_content(prompt_cambio)
#                 content = sub_resp.text
#                 match = re.search(r"{\\s*\"nombre_original\".*?}", content, re.DOTALL)
#                 if match:
#                     try:
#                         parsed = json.loads(match.group(0))
#                         if not first:
#                             f.write(",\n")
#                         json.dump(parsed, f, ensure_ascii=False, indent=2)
#                         f.flush()
#                         first = False
#                         print(f"✅ Agregado y escrito: {parsed}")
#                     except Exception as e:
#                         print(f"❌ Error parseando respuesta: {e}")
#                         continue

#             f.write("\n]")

#         estado["status"] = "listo"
#         print("🎉 Proceso finalizado correctamente")

#     except Exception as e:
#         estado["status"] = "error"
#         estado["error"] = str(e)
#         print(f"💥 Error inesperado: {e}")
# import json
# import re
# import os
# import requests
# from io import BytesIO
# from PyPDF2 import PdfReader
# from playwright.sync_api import sync_playwright
# from bs4 import BeautifulSoup
# import google.generativeai as genai

# def extraer_texto_pdf(pdf_url):
#     try:
#         response = requests.get(pdf_url, timeout=10)
#         response.raise_for_status()
#         with BytesIO(response.content) as pdf_file:
#             reader = PdfReader(pdf_file)
#             texto = ""
#             for page in reader.pages:
#                 texto += page.extract_text() or ""
#             return texto.strip()
#     except Exception as e:
#         print(f"❌ Error leyendo PDF {pdf_url}: {e}")
#         return ""

# def ejecutar_proceso(url: str, output_path: str, estado: dict):
#     try:
#         print("🚀 Iniciando proceso de scraping")
#         with sync_playwright() as p:
#             print("🧭 Lanzando navegador...")
#             browser = p.webkit.launch(headless=True)
#             page = browser.new_page()
#             print(f"🌐 Navegando a {url}")
#             page.goto(url)
#             page.wait_for_timeout(10000)
#             html = page.content()
#             browser.close()
#             print("✅ HTML obtenido")

#         print("🔍 Parseando HTML...")
#         soup = BeautifulSoup(html, 'html.parser')
#         wrap_div = soup.find("div", class_="wrapsection")
#         tbody = wrap_div.find("table").find("tbody") if wrap_div else None

#         print("📋 Extrayendo filas...")
#         results = []
#         start_collecting = False
#         for tr in tbody.find_all("tr"):
#             tds = tr.find_all("td")
#             if not tds:
#                 continue
#             text = tds[0].get_text(strip=True)
#             if "Solicitudes de Cambios de Nombre" in text:
#                 start_collecting = True
#                 continue
#             if start_collecting and len(tds) >= 2:
#                 nombre = tds[0].get_text(strip=True)
#                 a_tag = tds[1].find("a")
#                 pdf = a_tag["href"] if a_tag else None
#                 results.append({"nombre": nombre, "pdf": pdf})
#         print(f"🧾 Se encontraron {len(results)} registros")
#         results = results[:100]

#         estado["total"] = len(results)
#         estado["procesados"] = 0
#         estado["progreso"] = 0

#         print("🤖 Enviando a Gemini...")
#         genai.configure(api_key="AIzaSyAl4sGdg1dbVHwEIhEsBLzv6O7qtRKonVw")
#         model = genai.GenerativeModel(model_name="gemini-2.5-flash-preview-05-20")

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

#         json_match = re.search(r"\[\s*{.*?}\s*\]", full_response, re.DOTALL)
#         if not json_match:
#             print("⚠️ No se encontró JSON válido en la respuesta de Gemini")
#             estado["status"] = "error"
#             return
#         json_data = json.loads(json_match.group(0))
#         print(f"✅ Gemini devolvió {len(json_data)} resultados válidos")

#         print(f"💾 Guardando progresivamente en {output_path}")
#         with open(output_path, "w", encoding="utf-8") as f:
#             f.write("[\n")
#             first = True

#             for entry in json_data:
#                 print(f"📄 Procesando PDF: {entry['pdf']}")
#                 texto_pdf = extraer_texto_pdf(entry["pdf"])[:3000]
#                 prompt_cambio = f"""
#                 \"\"\"{texto_pdf}\"\"\"
#                 ¿Es una solicitud de cambio de nombre? Si sí, responde con:
#                 {{
#                   "nombre_original": "...",
#                   "nombre_nuevo": "...",
#                   "pdf": "{entry['pdf']}"
#                 }}
#                 Si no, responde solo con null.
#                 """
#                 sub_resp = model.generate_content(prompt_cambio)
#                 content = sub_resp.text
#                 match = re.search(r"{\\s*\"nombre_original\".*?}", content, re.DOTALL)
#                 if match:
#                     try:
#                         parsed = json.loads(match.group(0))
#                         if not first:
#                             f.write(",\n")
#                         json.dump(parsed, f, ensure_ascii=False, indent=2)
#                         f.flush()
#                         first = False
#                         print(f"✅ Agregado y escrito: {parsed}")
#                     except Exception as e:
#                         print(f"❌ Error parseando respuesta: {e}")
#                         continue

#                 estado["procesados"] += 1
#                 estado["progreso"] = round(estado["procesados"] * 100 / estado["total"])
#                 print(f"📊 Progreso: {estado['progreso']}%")

#             f.write("\n]")

#         estado["status"] = "listo"
#         print("🎉 Proceso finalizado correctamente")

#     except Exception as e:
#         estado["status"] = "error"
#         estado["error"] = str(e)
#         print(f"💥 Error inesperado: {e}")

import json
import re
import os
import requests
from io import BytesIO
from PyPDF2 import PdfReader
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import google.generativeai as genai

def extraer_texto_pdf(pdf_url):
    try:
        response = requests.get(pdf_url, timeout=10)
        response.raise_for_status()
        with BytesIO(response.content) as pdf_file:
            reader = PdfReader(pdf_file)
            texto = ""
            for page in reader.pages:
                texto += page.extract_text() or ""
            return texto.strip()
    except Exception as e:
        print(f"❌ Error leyendo PDF {pdf_url}: {e}")
        return ""

def ejecutar_proceso(url: str, output_path: str, estado: dict):
    try:
        print("🚀 Iniciando proceso de scraping")
        with sync_playwright() as p:
            print("🧭 Lanzando navegador...")
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            print(f"🌐 Navegando a {url}")
            page.goto(url)
            page.wait_for_timeout(10000)
            html = page.content()
            browser.close()
            print("✅ HTML obtenido")

        print("🔍 Parseando HTML...")
        soup = BeautifulSoup(html, 'html.parser')
        wrap_div = soup.find("div", class_="wrapsection")
        tbody = wrap_div.find("table").find("tbody") if wrap_div else None

        print("📋 Extrayendo filas...")
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
        print(f"🧾 Se encontraron {len(results)} registros")
        results = results[:100]

        estado["total"] = len(results)
        estado["procesados"] = 0
        estado["progreso"] = 0

        print("🤖 Enviando a Gemini...")
        genai.configure(api_key=os.getenv("GEMINI_API_KEY", "AIzaSyAl4sGdg1dbVHwEIhEsBLzv6O7qtRKonVw"))
        model = genai.GenerativeModel(model_name="gemini-2.5-flash-preview-05-20")

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

        print("🔍 Respuesta completa de Gemini:")
        print(full_response[:1000])  # mostrar parte del contenido completo

        json_match = re.search(r"\[\s*{.*?}\s*\]", full_response, re.DOTALL)
        if not json_match:
            print("⚠️ No se encontró JSON válido en la respuesta de Gemini")
            estado["status"] = "error"
            return

        json_data = json.loads(json_match.group(0))
        print(f"✅ Gemini devolvió {len(json_data)} resultados válidos")

        print(f"💾 Guardando progresivamente en {output_path}")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("[\n")
            first = True
            try:
                for i, entry in enumerate(json_data):
                    if i >= 10:
                        print("🔚 Límite de 10 PDFs alcanzado. Finalizando procesamiento.")
                        break

                    print(f"📄 Procesando PDF {i + 1}: {entry['pdf']}")
                    texto_pdf = extraer_texto_pdf(entry["pdf"])[:3000]
                    prompt_cambio = f"""
                        \"\"\"{texto_pdf}\"\"\"
                        ¿Es una solicitud de cambio de nombre? Si sí, responde con:
                        {{
                        "nombre_original": "...",
                        "nombre_nuevo": "...",
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
                            f.write(",\n")
                        json.dump(parsed, f, ensure_ascii=False, indent=2)
                        f.flush()
                        first = False
                        print(f"✅ Agregado y escrito: {parsed}")
                    else:
                        print("⚠️ No se encontró JSON válido o Gemini respondió null. Se omite esta entrada.")

                    estado["procesados"] += 1
                    estado["progreso"] = round(estado["procesados"] * 100 / min(10, estado["total"]))
                    print(f"📊 Progreso: {estado['progreso']}%")
            finally:
                f.write("\n]\n")
                estado["status"] = "listo"
                print("🎉 Proceso finalizado correctamente")

    except Exception as e:
        estado["status"] = "error"
        estado["error"] = str(e)
        print(f"💥 Error inesperado: {e}")

