import os
import json
import pandas as pd
import google.generativeai as genai
from supabase import create_client, Client
import re
import time

# --- CONFIGURACIÓN ---
GEMINI_API_KEY = "AIzaSyD0_KViAJpkH4VIbRoomIq_TLu0KwpZkR4"
SUPABASE_URL = "https://fnpcclnzbdrzzbcoeqhm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZucGNjbG56YmRyenpiY29lcWhtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTcyNzAyNDUsImV4cCI6MjA3Mjg0NjI0NX0.0qzERgm-Nf_wiHMuijnf7X2vMX0k3oz4wyszKoo2sN0"

genai.configure(api_key=GEMINI_API_KEY)
modelo = genai.GenerativeModel('gemini-flash-latest')

def leer_reporte(ruta):
    if not os.path.exists(ruta):
        return None
    with open(ruta, 'r', encoding='utf-8') as f:
        return f.read()

def extraer_id_ficha(texto):
    match = re.search(r"/respuestas/(\d+)/", texto)
    if match:
        return int(match.group(1))
    return 20

def generar_hallazgos_con_ia(texto_reporte):
    print("🤖 Consultando a Gemini para estructurar hallazgos...")
    
    prompt = f"""
    Actúa como un experto analista de UX. Tu tarea es procesar el siguiente "Reporte de Usabilidad" (en Markdown) y extraer información estructurada en formato JSON.
    
    Necesito que generes un objeto JSON con EXACTAMENTE estas 3 claves principales:
    
    1. "hallazgo_general": Un objeto con la estructura:
       {{
         "analisis_experiencia_actual": {{
           "fortalezas_clave": [ {{"descripcion": "..."}}, ... ],
           "fricciones_criticas": [ {{"descripcion": "..."}}, ... ],
           "recomendaciones": [ {{"descripcion": "..."}}, ... ]
         }}
       }}
       *Basado en TODO el reporte, sintetiza los puntos más importantes.*

    2. "hallazgo_pregunta": Una lista de objetos para CADA pregunta del test (314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324). Estructura:
       [
         {{
           "pregunta": "315",
           "titulo": "Análisis Heatmap",
           "hallazgo": "Resumen del hallazgo para esta pregunta..."
         }},
         ...
       ]
       *Si la pregunta tiene una "Síntesis" en el reporte, úsala. Si solo tiene tablas/estadísticas (como Likert o Card Sorting), genera un breve resumen textual interpretando los datos.*

    3. "hallazgo_tester": Una lista de objetos con los hallazgos GENERALES por usuario (consolidando su comportamiento en todas las preguntas). Estructura:
       [
         {{
           "nombre": "Nombre del Usuario",
           "empresa": "Empresa del Usuario",
           "hallazgo": "Resumen consolidado del comportamiento, opiniones y fricciones de este usuario a lo largo de toda la prueba (Heatmaps, Videos, Audios, etc.)...",
           "idUsuario": "simulado"
         }},
         ...
       ]
       *No desgloses por pregunta. Genera UN solo objeto por cada usuario participante (Daniel Salazar, Luis Fernando Lee, Maria Paz Hernandez, Isabella Florez, Valeria Lozano, Paula Cuellar).*

    --- REPORTE DE USABILIDAD ---
    {texto_reporte}
    -----------------------------
    
    IMPORTANTE:
    - Responde SOLO con el JSON válido.
    - No uses bloques de código markdown (```json).
    - Asegúrate de que el JSON esté bien formado.
    """

    try:
        respuesta = modelo.generate_content(prompt)
        texto_respuesta = respuesta.text.strip()
        # Limpiar posibles bloques de código si el modelo los pone
        if texto_respuesta.startswith("```"):
            texto_respuesta = texto_respuesta.replace("```json", "").replace("```", "")
        
        datos = json.loads(texto_respuesta)
        return datos
    except Exception as e:
        print(f"❌ Error al procesar con IA: {e}")
        return None

def main():
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_reporte = os.path.join(directorio_actual, 'reporte_usabilidad.md')
    ruta_csv = os.path.join(directorio_actual, 'Hallazgo.rows.csv')

    print("🔍 Leyendo reporte...")
    texto_reporte = leer_reporte(ruta_reporte)
    if not texto_reporte:
        print("❌ No se pudo leer el reporte.")
        return

    id_ficha = extraer_id_ficha(texto_reporte)
    print(f"🆔 ID Ficha detectado: {id_ficha}")

    datos_ia = generar_hallazgos_con_ia(texto_reporte)
    
    if not datos_ia:
        print("❌ No se pudieron generar los datos con IA.")
        return

    # Preparar datos para CSV y Supabase
    hallazgo_general = datos_ia.get('hallazgo_general', {})
    hallazgo_pregunta = datos_ia.get('hallazgo_pregunta', [])
    hallazgo_tester = datos_ia.get('hallazgo_tester', [])

    # Crear fila para CSV
    fila = {
        'id_ficha': id_ficha,
        'hallazgo_general': json.dumps(hallazgo_general, ensure_ascii=False),
        'hallazgo_pregunta': json.dumps(hallazgo_pregunta, ensure_ascii=False),
        'hallazgo_tester': json.dumps(hallazgo_tester, ensure_ascii=False)
    }

    df = pd.DataFrame([fila])
    print(f"💾 Guardando CSV en {ruta_csv}...")
    df.to_csv(ruta_csv, index=False, encoding='utf-8')

    print("⚠️ La subida a Supabase se realizará con el script 'subir_hallazgos_rest.py' para evitar errores SSL.")
    # print("☁️ Subiendo a Supabase...")
    # try:
    #     supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
    #     datos_api = {
    #         'id_ficha': id_ficha,
    #         'hallazgo_general': hallazgo_general,
    #         'hallazgo_pregunta': hallazgo_pregunta,
    #         'hallazgo_tester': hallazgo_tester
    #     }
        
    #     response = supabase.table('Hallazgo').insert(datos_api).execute()
    #     print("✅ Datos subidos exitosamente a Supabase.")
    #     if response.data:
    #         print(f"   ID Hallazgo creado: {response.data[0]['id_hallazgo']}")
        
    # except Exception as e:
    #     print(f"❌ Error al subir a Supabase: {e}")

if __name__ == "__main__":
    main()
