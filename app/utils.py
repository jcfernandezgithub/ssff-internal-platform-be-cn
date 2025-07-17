import requests
from PyPDF2 import PdfReader
from io import BytesIO

def extraer_texto_pdf(pdf_url: str) -> str:
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
        print(f"❌ Error extrayendo texto del PDF {pdf_url}: {e}")
        return ""