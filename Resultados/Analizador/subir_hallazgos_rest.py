import os
import json
import pandas as pd
import requests

# --- CONFIGURACIÓN ---
SUPABASE_URL = "https://fnpcclnzbdrzzbcoeqhm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZucGNjbG56YmRyenpiY29lcWhtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTcyNzAyNDUsImV4cCI6MjA3Mjg0NjI0NX0.0qzERgm-Nf_wiHMuijnf7X2vMX0k3oz4wyszKoo2sN0"

def main():
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_csv = os.path.join(directorio_actual, 'Hallazgo.rows.csv')

    print("🔍 Leyendo CSV generado...")
    if not os.path.exists(ruta_csv):
        print("❌ No se encontró el archivo CSV.")
        return

    df = pd.read_csv(ruta_csv)
    
    if df.empty:
        print("❌ El CSV está vacío.")
        return

    # Obtener la primera fila (asumimos que es un solo registro por ejecución)
    fila = df.iloc[0]
    
    # Preparar datos para la API REST
    # Nota: Pandas lee los JSON strings como strings, necesitamos parsearlos si la API espera JSON objects,
    # pero si la columna en Supabase es JSONB, podemos enviar el objeto parseado.
    
    try:
        datos_api = {
            'id_ficha': int(fila['id_ficha']),
            'hallazgo_general': json.loads(fila['hallazgo_general']),
            'hallazgo_pregunta': json.loads(fila['hallazgo_pregunta']),
            'hallazgo_tester': json.loads(fila['hallazgo_tester'])
        }
    except json.JSONDecodeError as e:
        print(f"❌ Error al decodificar JSON del CSV: {e}")
        return

    print("☁️ Subiendo a Supabase (vía REST)...")
    
    url = f"{SUPABASE_URL}/rest/v1/Hallazgo"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    try:
        # Usamos verify=False para evitar errores de SSL en entornos corporativos
        response = requests.post(url, json=datos_api, headers=headers, verify=False)
        
        if response.status_code in [200, 201]:
            data = response.json()
            print("✅ Datos subidos exitosamente a Supabase.")
            if data:
                print(f"   ID Hallazgo creado: {data[0]['id_hallazgo']}")
        else:
            print(f"❌ Error al subir: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

if __name__ == "__main__":
    # Suprimir advertencias de SSL inseguro
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    main()
