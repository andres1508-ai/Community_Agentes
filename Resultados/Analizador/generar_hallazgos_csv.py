import os
import re
import json
import pandas as pd
from supabase import create_client, Client

# Configuración de Supabase
SUPABASE_URL = "https://fnpcclnzbdrzzbcoeqhm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZucGNjbG56YmRyenpiY29lcWhtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTcyNzAyNDUsImV4cCI6MjA3Mjg0NjI0NX0.0qzERgm-Nf_wiHMuijnf7X2vMX0k3oz4wyszKoo2sN0"

def leer_reporte(ruta_reporte):
    if not os.path.exists(ruta_reporte):
        return None
    with open(ruta_reporte, 'r', encoding='utf-8') as f:
        return f.read()

def extraer_id_ficha(texto):
    match = re.search(r"/respuestas/(\d+)/", texto)
    if match:
        return int(match.group(1))
    return 20

def limpiar_markdown(texto):
    if not texto: return ""
    # Eliminar negritas, cursivas, links, etc.
    texto = re.sub(r"\*\*(.*?)\*\*", r"\1", texto) # Negrita
    texto = re.sub(r"\*(.*?)\*", r"\1", texto)     # Cursiva
    texto = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", texto) # Links
    texto = re.sub(r"> ", "", texto) # Blockquotes
    texto = re.sub(r"🤖 \*\*Análisis IA:\*\*", "", texto) # Header IA
    texto = texto.strip()
    return texto

def extraer_datos(texto):
    hallazgos_pregunta = []
    hallazgos_tester = []
    
    # Acumuladores para el hallazgo general
    todos_patrones = []
    todos_hallazgos = []
    todas_recomendaciones = []

    # Dividir por preguntas
    secciones = re.split(r"### Pregunta (\d+)", texto)
    
    # La sección 0 es el resumen general antes de las preguntas
    
    for i in range(1, len(secciones), 2):
        id_pregunta = secciones[i]
        contenido = secciones[i+1]
        
        # --- 1. Hallazgos por Pregunta ---
        sintesis_texto = ""
        titulo_hallazgo = f"Análisis Pregunta {id_pregunta}"
        
        # Prioridad 1: Síntesis de IA
        match_sintesis = re.search(r"#### 🎯 Síntesis.*?\n(.*?)(?=### Pregunta|---|$)", contenido, re.DOTALL)
        if match_sintesis:
            raw_sintesis = match_sintesis.group(1).strip()
            sintesis_texto = limpiar_markdown(raw_sintesis)
            
            # Extraer partes para el General
            patrones = re.search(r"Patrones Comunes(.*?)(?=Hallazgos Clave|$)", raw_sintesis, re.DOTALL | re.IGNORECASE)
            hallazgos = re.search(r"Hallazgos Clave(.*?)(?=Recomendaciones|$)", raw_sintesis, re.DOTALL | re.IGNORECASE)
            recomendaciones = re.search(r"Recomendaciones(.*?)(?=$)", raw_sintesis, re.DOTALL | re.IGNORECASE)
            
            if patrones: todos_patrones.append(f"P{id_pregunta}: {limpiar_markdown(patrones.group(1))}")
            if hallazgos: todos_hallazgos.append(f"P{id_pregunta}: {limpiar_markdown(hallazgos.group(1))}")
            if recomendaciones: todas_recomendaciones.append(f"P{id_pregunta}: {limpiar_markdown(recomendaciones.group(1))}")

        # Prioridad 2: Estadísticas Generales (Likert)
        elif "Estadísticas Generales" in contenido:
            match_stats = re.search(r"#### Estadísticas Generales(.*?)(?=####|$)", contenido, re.DOTALL)
            if match_stats:
                sintesis_texto = "Estadísticas: " + limpiar_markdown(match_stats.group(1))
        
        # Prioridad 2.1: Frecuencia de Opciones (Diferencia Semántica)
        elif "Frecuencia de Opciones" in contenido:
            match_freq = re.search(r"#### Frecuencia de Opciones(.*?)(?=####|$)", contenido, re.DOTALL)
            if match_freq:
                sintesis_texto = "Frecuencias: " + limpiar_markdown(match_freq.group(1))

        # Prioridad 3: Matriz de Frecuencia (Card Sorting)
        elif "Matriz de Frecuencia" in contenido:
            match_matrix = re.search(r"#### Análisis de Consenso(.*?)(?=---|$)", contenido, re.DOTALL)
            if match_matrix:
                sintesis_texto = "Consenso: " + limpiar_markdown(match_matrix.group(1))
            else:
                match_matrix_raw = re.search(r"#### Matriz de Frecuencia(.*?)(?=####|$)", contenido, re.DOTALL)
                if match_matrix_raw:
                    sintesis_texto = "Frecuencias: " + limpiar_markdown(match_matrix_raw.group(1))

        # Prioridad 4: Respuestas de Texto (si no hay síntesis)
        elif "#### Respuestas por Usuario" in contenido:
             sintesis_texto = "Ver respuestas individuales de los usuarios."

        if sintesis_texto:
            hallazgos_pregunta.append({
                'pregunta': id_pregunta,
                'titulo': titulo_hallazgo,
                'hallazgo': sintesis_texto[:1000] # Limitar longitud
            })

        # --- 2. Hallazgos por Tester ---
        # Buscar bloques de usuario: **Nombre** (Empresa)...
        # Regex para capturar nombre, empresa y el contenido siguiente
        # El contenido puede ser un bloque de cita (> ...) o texto plano hasta el siguiente usuario o fin de sección
        
        # Iteramos por líneas para ser más robustos
        lines = contenido.split('\n')
        current_tester = None
        current_empresa = None
        current_text = []
        
        for line in lines:
            # Detectar inicio de usuario: **Nombre** (Empresa)
            match_user = re.match(r"\*\*(.*?)\*\* \((.*?)\)", line)
            if match_user:
                # Guardar el anterior si existe
                if current_tester:
                    texto_tester = "\n".join(current_text).strip()
                    # Limpieza específica para IA
                    if "> 🤖" in texto_tester:
                        match_ia = re.search(r"> 🤖 \*\*Análisis IA:\*\* (.*)", texto_tester, re.DOTALL)
                        if match_ia:
                            texto_tester = match_ia.group(1)
                    
                    texto_tester = limpiar_markdown(texto_tester)
                    if texto_tester:
                        hallazgos_tester.append({
                            'pregunta': id_pregunta,
                            'nombre': current_tester,
                            'empresa': current_empresa,
                            'hallazgo': texto_tester[:500],
                            'idUsuario': 'simulado'
                        })
                
                # Iniciar nuevo usuario
                current_tester = match_user.group(1)
                current_empresa = match_user.group(2)
                current_text = []
                # Si hay texto en la misma línea después del paréntesis (ej: links), agregarlo?
                # A veces hay links: [Ver Video](...)
                # A veces hay duración: - Duración: ...
                # Ignoramos la línea del encabezado para el texto del hallazgo, a menos que sea texto directo
            
            elif current_tester:
                # Acumular texto si estamos dentro de un usuario
                # Detenerse si encontramos un encabezado de sección (####)
                if line.strip().startswith("####"):
                    # Fin de la lista de usuarios para esta pregunta
                    texto_tester = "\n".join(current_text).strip()
                    if "> 🤖" in texto_tester:
                        match_ia = re.search(r"> 🤖 \*\*Análisis IA:\*\* (.*)", texto_tester, re.DOTALL)
                        if match_ia:
                            texto_tester = match_ia.group(1)
                    
                    texto_tester = limpiar_markdown(texto_tester)
                    if texto_tester:
                        hallazgos_tester.append({
                            'pregunta': id_pregunta,
                            'nombre': current_tester,
                            'empresa': current_empresa,
                            'hallazgo': texto_tester[:500],
                            'idUsuario': 'simulado'
                        })
                    current_tester = None
                    current_text = []
                else:
                    current_text.append(line)
        
        # Procesar el último usuario si quedó pendiente al final del bloque
        if current_tester:
            texto_tester = "\n".join(current_text).strip()
            if "> 🤖" in texto_tester:
                match_ia = re.search(r"> 🤖 \*\*Análisis IA:\*\* (.*)", texto_tester, re.DOTALL)
                if match_ia:
                    texto_tester = match_ia.group(1)
            
            texto_tester = limpiar_markdown(texto_tester)
            if texto_tester:
                hallazgos_tester.append({
                    'pregunta': id_pregunta,
                    'nombre': current_tester,
                    'empresa': current_empresa,
                    'hallazgo': texto_tester[:500],
                    'idUsuario': 'simulado'
                })

    # --- 3. Construir Hallazgo General Agregado ---
    hallazgo_general = {
        'analisis_experiencia_actual': {
            'fortalezas_clave': [{'descripcion': p} for p in todos_patrones] if todos_patrones else [{'descripcion': "No se detectaron patrones globales."}],
            'fricciones_criticas': [{'descripcion': h} for h in todos_hallazgos] if todos_hallazgos else [{'descripcion': "No se detectaron fricciones globales."}],
            'recomendaciones': [{'descripcion': r} for r in todas_recomendaciones] if todas_recomendaciones else [{'descripcion': "No se generaron recomendaciones globales."}]
        }
    }

    return hallazgo_general, hallazgos_pregunta, hallazgos_tester

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

    print("🧠 Procesando hallazgos...")
    hallazgo_general, hallazgo_pregunta, hallazgo_tester = extraer_datos(texto_reporte)

    # Crear la fila única
    fila = {
        'id_ficha': id_ficha,
        'hallazgo_general': json.dumps(hallazgo_general, ensure_ascii=False),
        'hallazgo_pregunta': json.dumps(hallazgo_pregunta, ensure_ascii=False),
        'hallazgo_tester': json.dumps(hallazgo_tester, ensure_ascii=False)
    }

    df = pd.DataFrame([fila])
    
    print(f"💾 Guardando CSV en {ruta_csv}...")
    df.to_csv(ruta_csv, index=False, encoding='utf-8')

    print("☁️ Subiendo a Supabase...")
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        datos_api = {
            'id_ficha': id_ficha,
            'hallazgo_general': hallazgo_general,
            'hallazgo_pregunta': hallazgo_pregunta,
            'hallazgo_tester': hallazgo_tester
        }
        
        response = supabase.table('Hallazgo').insert(datos_api).execute()
        print("✅ Datos subidos exitosamente a Supabase.")
        print(f"   ID Hallazgo creado: {response.data[0]['id_hallazgo']}")
        
    except Exception as e:
        print(f"❌ Error al subir a Supabase: {e}")

if __name__ == "__main__":
    main()
