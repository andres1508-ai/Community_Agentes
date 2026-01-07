"""
Analizador de Resultados de Pruebas de Usabilidad con IA
=========================================================
Script para analizar respuestas de pruebas de usabilidad con diferentes
tipos de formato: Likert, texto, card sorting, diferencia semántica, etc.
Incluye análisis automático de contenido multimedia con Gemini AI.
"""

import pandas as pd
import numpy as np
import json
import requests
import time
import base64
import gc
import tempfile
import os
from collections import Counter
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Configuración de Gemini AI
import google.generativeai as genai

GEMINI_API_KEY = "AIzaSyD0_KViAJpkH4VIbRoomIq_TLu0KwpZkR4"
genai.configure(api_key=GEMINI_API_KEY)

# Modelo de Gemini para análisis multimedia (usando gemini-2.5-flash por estabilidad)
modelo_gemini = genai.GenerativeModel('gemini-2.5-flash')

# Configuración de reintentos
MAX_REINTENTOS = 5
ESPERA_BASE = 20  # segundos


class AgenteMultimedia:
    """Agente de IA para analizar contenido multimedia usando Gemini."""
    
    def __init__(self):
        self.modelo = modelo_gemini
        self.cache_analisis = {}
    
    def enfriamiento(self, segundos=10):
        """Realiza una pausa para enfriamiento de la API."""
        print(f"    ❄️ Enfriamiento: Pausando {segundos}s para evitar saturación...")
        time.sleep(segundos)

    def limpieza(self):
        """Limpia caché y memoria."""
        print("    🧹 Limpieza: Liberando memoria y caché...")
        self.cache_analisis.clear()
        gc.collect()

    def descargar_contenido(self, url: str) -> tuple:
        """Descarga contenido de una URL y retorna los bytes y el tipo MIME."""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '')
            
            # Determinar tipo MIME
            if 'image' in content_type or url.endswith('.png') or url.endswith('.jpg'):
                mime_type = 'image/png'
            elif 'video' in content_type or url.endswith('.webm') or url.endswith('.mp4'):
                mime_type = 'video/webm'
            elif 'audio' in content_type or url.endswith('.webm') or url.endswith('.mp3'):
                mime_type = 'audio/webm'
            else:
                mime_type = content_type.split(';')[0] if content_type else 'application/octet-stream'
            
            return response.content, mime_type
        except Exception as e:
            print(f"    ⚠️ Error descargando {url[:50]}...: {e}")
            return None, None
    
    def _llamar_gemini_con_reintentos(self, prompt, media_part):
        """Llama a Gemini con reintentos automáticos para manejar límites de cuota y errores del servidor."""
        ultimo_error = None
        for intento in range(MAX_REINTENTOS):
            try:
                response = self.modelo.generate_content([prompt, media_part])
                return response.text.strip()
            except Exception as e:
                error_str = str(e)
                ultimo_error = error_str
                # Reintentar para errores de cuota (429) y errores internos del servidor (500)
                if '429' in error_str or 'quota' in error_str.lower():
                    espera = ESPERA_BASE * (intento + 1)
                    print(f"    ⏳ Límite de cuota alcanzado. Esperando {espera}s antes de reintentar...")
                    time.sleep(espera)
                elif '500' in error_str or 'internal' in error_str.lower():
                    espera = ESPERA_BASE * (intento + 1)
                    print(f"    ⏳ Error interno del servidor (500). Esperando {espera}s antes de reintentar ({intento+1}/{MAX_REINTENTOS})...")
                    time.sleep(espera)
                else:
                    raise e
        return f"Error: Se agotaron los reintentos. Último error: {ultimo_error}"
    
    def analizar_imagen(self, url: str, contexto: str) -> str:
        """Analiza una imagen (heatmap) usando Gemini Vision."""
        if url in self.cache_analisis:
            return self.cache_analisis[url]
        
        try:
            contenido, mime_type = self.descargar_contenido(url)
            if contenido is None:
                return "No se pudo descargar la imagen para análisis."
            
            # Crear prompt para análisis de heatmap
            prompt = f"""Analiza esta imagen de un heatmap de clicks de una prueba de usabilidad.
            
Contexto de la pregunta: {contexto}

Por favor proporciona:
1. ¿Dónde se concentran los clicks principales?
2. ¿Qué elementos de la interfaz parecen atraer más atención?
3. ¿Hay patrones interesantes en el comportamiento del usuario?

Responde de forma concisa en español (máximo 3-4 oraciones)."""

            # Subir imagen a Gemini
            imagen_part = {
                "inline_data": {
                    "mime_type": mime_type,
                    "data": base64.b64encode(contenido).decode('utf-8')
                }
            }
            
            analisis = self._llamar_gemini_con_reintentos(prompt, imagen_part)
            
            self.cache_analisis[url] = analisis
            time.sleep(3)  # Rate limiting más conservador
            return analisis
            
        except Exception as e:
            return f"Error en análisis: {str(e)}"
    
    def analizar_video(self, url: str, contexto: str) -> str:
        """Analiza un video de grabación de pantalla usando Gemini."""
        if url in self.cache_analisis:
            return self.cache_analisis[url]
        
        try:
            contenido, mime_type = self.descargar_contenido(url)
            if contenido is None:
                return "No se pudo descargar el video para análisis."
            
            # Para videos grandes, usamos File API de Gemini
            prompt = f"""Analiza este video de grabación de pantalla de una prueba de usabilidad.

Contexto de la tarea: {contexto}

Por favor identifica:
1. ¿Qué pasos siguió el usuario para completar la tarea?
2. ¿Hubo momentos de confusión, hesitación o errores?
3. ¿El usuario completó la tarea exitosamente?
4. ¿Qué aspectos de la interfaz podrían mejorarse basado en este comportamiento?

Responde de forma estructurada y concisa en español."""

            # Usar File API para videos
            temp_file_path = None
            gemini_file = None
            
            try:
                # Guardar temporalmente
                ext = '.mp4' if 'mp4' in mime_type else '.webm'
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                    temp_file.write(contenido)
                    temp_file_path = temp_file.name
                
                print(f"      📤 Subiendo video a Gemini (File API)...")
                gemini_file = genai.upload_file(path=temp_file_path, mime_type=mime_type)
                
                # Esperar a que el video se procese
                while gemini_file.state.name == "PROCESSING":
                    print("      ⏳ Procesando video en Gemini...")
                    time.sleep(2)
                    gemini_file = genai.get_file(gemini_file.name)
                
                if gemini_file.state.name == "FAILED":
                    raise ValueError("El procesamiento del video falló en Gemini.")

                analisis = self._llamar_gemini_con_reintentos(prompt, gemini_file)
                self.cache_analisis[url] = analisis
                
            finally:
                # Limpieza de recursos
                if temp_file_path and os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                if gemini_file:
                    try:
                        gemini_file.delete()
                    except:
                        pass
            
            time.sleep(5)
            return analisis
            
        except Exception as e:
            return f"Error en análisis de video: {str(e)}"
    
    def analizar_audio(self, url: str, contexto: str) -> str:
        """Analiza un audio y transcribe/resume el contenido usando Gemini."""
        if url in self.cache_analisis:
            return self.cache_analisis[url]
        
        try:
            contenido, mime_type = self.descargar_contenido(url)
            if contenido is None:
                return "No se pudo descargar el audio para análisis."
            
            # CORRECCIÓN: Forzar tipo MIME de audio si es webm (evita que Gemini lo trate como video sin pista de video)
            if mime_type == 'video/webm' or url.endswith('.webm'):
                mime_type = 'audio/webm'
            
            prompt = f"""Escucha este audio de una prueba de usabilidad donde el usuario responde verbalmente.

Pregunta que se le hizo: {contexto}

Por favor:
1. Transcribe los puntos principales de lo que dice el usuario
2. Resume la opinión o respuesta del usuario en 2-3 oraciones
3. Identifica cualquier insight relevante para mejorar la usabilidad

Responde en español de forma estructurada."""

            # Usar File API para mayor estabilidad con audios
            temp_file_path = None
            gemini_file = None
            
            try:
                # Guardar temporalmente
                ext = '.mp3' if 'mp3' in mime_type else '.webm'
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                    temp_file.write(contenido)
                    temp_file_path = temp_file.name
                
                print(f"      📤 Subiendo audio a Gemini (File API) como {mime_type}...")
                gemini_file = genai.upload_file(path=temp_file_path, mime_type=mime_type)
                
                # Esperar a que el audio se procese (CRÍTICO para evitar error 400)
                while gemini_file.state.name == "PROCESSING":
                    print("      ⏳ Procesando audio en Gemini...")
                    time.sleep(1)
                    gemini_file = genai.get_file(gemini_file.name)
                
                if gemini_file.state.name == "FAILED":
                    print("      ⚠️ File API falló, intentando con inline_data...")
                    # Fallback a inline_data si File API falla
                    audio_part = {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": base64.b64encode(contenido).decode('utf-8')
                        }
                    }
                    analisis = self._llamar_gemini_con_reintentos(prompt, audio_part)
                    self.cache_analisis[url] = analisis
                    return analisis

                analisis = self._llamar_gemini_con_reintentos(prompt, gemini_file)
                self.cache_analisis[url] = analisis
                
            finally:
                # Limpieza de recursos
                if temp_file_path and os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                if gemini_file:
                    try:
                        gemini_file.delete()
                    except:
                        pass

            time.sleep(2)
            return analisis
            
        except Exception as e:
            return f"Error en análisis de audio: {str(e)}"
    
    def generar_sintesis_pregunta(self, analisis_individuales: list, tipo: str, contexto: str) -> str:
        """Genera una síntesis de todos los análisis individuales para una pregunta."""
        if not analisis_individuales:
            return ""
        
        try:
            prompt = f"""Basándote en los siguientes análisis individuales de {len(analisis_individuales)} usuarios para una pregunta de {tipo}:

Pregunta: {contexto}

Análisis individuales:
{chr(10).join([f"- Usuario {i+1}: {a}" for i, a in enumerate(analisis_individuales)])}

Por favor genera:
1. **Patrones comunes**: ¿Qué comportamientos o respuestas se repiten?
2. **Hallazgos clave**: ¿Cuáles son los insights más importantes?
3. **Recomendaciones**: ¿Qué mejoras se sugieren basándose en estos datos?

Responde de forma estructurada y concisa en español."""

            # Reintentos para síntesis también
            for intento in range(MAX_REINTENTOS):
                try:
                    response = self.modelo.generate_content(prompt)
                    time.sleep(3)
                    return response.text.strip()
                except Exception as e:
                    error_str = str(e)
                    if '429' in error_str or 'quota' in error_str.lower():
                        espera = ESPERA_BASE * (intento + 1)
                        print(f"    ⏳ Límite de cuota en síntesis. Esperando {espera}s...")
                        time.sleep(espera)
                    else:
                        raise e
            return "Error: Se agotaron los reintentos por límite de cuota."
            
        except Exception as e:
            return f"Error generando síntesis: {str(e)}"


# Instancia global del agente
agente_ia = AgenteMultimedia()


def cargar_y_procesar_datos(ruta_respuestas: str, ruta_usuarios: str) -> pd.DataFrame:
    """
    Carga los CSVs y procesa la estructura anidada de respuestas.
    """
    respuestas_raw = pd.read_csv(ruta_respuestas)
    usuarios = pd.read_csv(ruta_usuarios)
    
    filas_expandidas = []
    
    for _, row in respuestas_raw.iterrows():
        id_usuario = row['id_usuario']
        tiempo_total = row['tiempo_respuesta']
        
        try:
            respuesta_json = json.loads(row['respuesta'])
            respuestas_lista = respuesta_json.get('respuestas', [])
            
            for resp in respuestas_lista:
                fila = {
                    'id_usuario': id_usuario,
                    'id_pregunta': resp.get('id_pregunta'),
                    'tipo_formato': resp.get('tipo_formato'),
                    'texto_pregunta': resp.get('texto_pregunta'),
                    'respuesta': resp.get('respuesta'),
                    'tiempo_respuesta': resp.get('tiempo_respuesta')
                }
                filas_expandidas.append(fila)
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            print(f"⚠️ Error procesando respuesta de usuario {id_usuario}: {e}")
            continue
    
    df_respuestas = pd.DataFrame(filas_expandidas)
    df = pd.merge(df_respuestas, usuarios, on='id_usuario', how='left')
    
    return df


def analizar_escala_likert(df_pregunta: pd.DataFrame, id_pregunta: str, texto_pregunta: str) -> str:
    """Analiza respuestas tipo escala Likert."""
    resultado = []
    resultado.append(f"### Pregunta {id_pregunta} - Escala Likert\n")
    resultado.append(f"**{texto_pregunta}**\n")
    
    respuestas_num = pd.to_numeric(df_pregunta['respuesta'], errors='coerce')
    respuestas_validas = respuestas_num.dropna()
    
    if len(respuestas_validas) == 0:
        resultado.append("⚠️ No hay respuestas numéricas válidas.\n")
        return '\n'.join(resultado)
    
    promedio = respuestas_validas.mean()
    mediana = respuestas_validas.median()
    moda_result = stats.mode(respuestas_validas, keepdims=True)
    moda = moda_result.mode[0] if len(moda_result.mode) > 0 else np.nan
    desv_std = respuestas_validas.std()
    
    resultado.append("#### Estadísticas Generales\n")
    resultado.append("| Métrica | Valor |")
    resultado.append("|---------|-------|")
    resultado.append(f"| **Promedio** | {promedio:.2f} |")
    resultado.append(f"| **Mediana** | {mediana:.2f} |")
    resultado.append(f"| **Moda** | {moda:.2f} |")
    resultado.append(f"| **Desviación Estándar** | {desv_std:.2f} |")
    resultado.append(f"| **N (respuestas)** | {len(respuestas_validas)} |")
    resultado.append("")
    
    resultado.append("#### Distribución de Respuestas\n")
    distribucion = respuestas_validas.value_counts().sort_index()
    resultado.append("| Valor | Frecuencia | Porcentaje | Visual |")
    resultado.append("|-------|------------|------------|--------|")
    for valor, freq in distribucion.items():
        porcentaje = (freq / len(respuestas_validas)) * 100
        barra = "█" * int(porcentaje / 10)
        resultado.append(f"| {int(valor)} | {freq} | {porcentaje:.1f}% | {barra} |")
    resultado.append("")
    
    resultado.append("#### Promedio por Empresa\n")
    df_temp = df_pregunta.copy()
    df_temp['respuesta_num'] = pd.to_numeric(df_temp['respuesta'], errors='coerce')
    promedio_empresa = df_temp.groupby('empresa')['respuesta_num'].agg(['mean', 'count']).round(2)
    
    resultado.append("| Empresa | Promedio | N |")
    resultado.append("|---------|----------|---|")
    for empresa, row in promedio_empresa.iterrows():
        resultado.append(f"| {empresa} | {row['mean']:.2f} | {int(row['count'])} |")
    resultado.append("")
    
    return '\n'.join(resultado)


def analizar_texto(df_pregunta: pd.DataFrame, id_pregunta: str, texto_pregunta: str) -> str:
    """Analiza respuestas tipo texto."""
    resultado = []
    resultado.append(f"### Pregunta {id_pregunta} - Texto\n")
    resultado.append(f"**{texto_pregunta}**\n")
    resultado.append("#### Respuestas por Usuario\n")
    
    for _, row in df_pregunta.iterrows():
        usuario = row.get('nombre', row['id_usuario'])
        empresa = row.get('empresa', 'N/A')
        respuesta = row['respuesta']
        
        resultado.append(f"**{usuario}** ({empresa}):")
        resultado.append(f"> {respuesta}\n")
    
    resultado.append(f"*Total de respuestas: {len(df_pregunta)}*\n")
    return '\n'.join(resultado)


def analizar_audio_con_ia(df_pregunta: pd.DataFrame, id_pregunta: str, texto_pregunta: str) -> str:
    """Analiza respuestas tipo audio con transcripción y análisis de IA."""
    resultado = []
    resultado.append(f"### Pregunta {id_pregunta} - Audio\n")
    resultado.append(f"**{texto_pregunta}**\n")
    resultado.append("#### Grabaciones de Audio por Usuario\n")
    
    analisis_individuales = []
    
    for _, row in df_pregunta.iterrows():
        usuario = row.get('nombre', row['id_usuario'])
        empresa = row.get('empresa', 'N/A')
        respuesta = row['respuesta']
        
        # Extraer URL del audio
        if isinstance(respuesta, dict):
            audio_url = respuesta.get('audio_url', 'URL no disponible')
        elif isinstance(respuesta, str):
            try:
                resp_dict = json.loads(respuesta)
                audio_url = resp_dict.get('audio_url', respuesta)
            except:
                audio_url = respuesta
        else:
            audio_url = str(respuesta)
        
        resultado.append(f"**{usuario}** ({empresa}): [🎵 Audio]({audio_url})")
        
        # Analizar con IA
        if audio_url and audio_url != 'URL no disponible':
            print(f"    🎵 Analizando audio de {usuario}...")
            analisis = agente_ia.analizar_audio(audio_url, texto_pregunta)
            resultado.append(f"> 🤖 **Análisis IA:** {analisis}\n")
            analisis_individuales.append(analisis)
        else:
            resultado.append("")
    
    resultado.append(f"*Total de grabaciones: {len(df_pregunta)}*\n")
    
    # Síntesis general
    if len(analisis_individuales) > 1:
        print(f"    📊 Generando síntesis de audios...")
        sintesis = agente_ia.generar_sintesis_pregunta(analisis_individuales, "audio", texto_pregunta)
        resultado.append("#### 🎯 Síntesis de Respuestas de Audio\n")
        resultado.append(sintesis)
        resultado.append("")
    
    return '\n'.join(resultado)


def analizar_card_sorting(df_pregunta: pd.DataFrame, id_pregunta: str, texto_pregunta: str) -> str:
    """Analiza respuestas tipo card sorting generando matriz de frecuencia."""
    resultado = []
    resultado.append(f"### Pregunta {id_pregunta} - Card Sorting\n")
    resultado.append(f"**{texto_pregunta}**\n")
    
    todas_asignaciones = []
    errores_parse = 0
    
    for _, row in df_pregunta.iterrows():
        try:
            respuesta = row['respuesta']
            
            if isinstance(respuesta, str):
                datos = json.loads(respuesta)
            elif isinstance(respuesta, dict):
                datos = respuesta
            else:
                errores_parse += 1
                continue
            
            if isinstance(datos, dict):
                for categoria, tarjetas in datos.items():
                    if isinstance(tarjetas, list):
                        for tarjeta in tarjetas:
                            todas_asignaciones.append({
                                'tarjeta': str(tarjeta),
                                'categoria': str(categoria)
                            })
        except (json.JSONDecodeError, TypeError, AttributeError) as e:
            errores_parse += 1
            continue
    
    if not todas_asignaciones:
        resultado.append("⚠️ No se pudieron parsear las respuestas de card sorting.\n")
        if errores_parse > 0:
            resultado.append(f"*Errores de parseo: {errores_parse}*\n")
        return '\n'.join(resultado)
    
    df_asignaciones = pd.DataFrame(todas_asignaciones)
    matriz = pd.crosstab(df_asignaciones['tarjeta'], df_asignaciones['categoria'])
    
    resultado.append("#### Matriz de Frecuencia (Tarjeta × Categoría)\n")
    resultado.append("*Muestra cuántas veces cada tarjeta fue asignada a cada categoría*\n")
    
    categorias = sorted(matriz.columns.tolist())
    header = "| Tarjeta | " + " | ".join(str(c) for c in categorias) + " | **Total** |"
    separator = "|---------|" + "|".join([":--------:"] * len(categorias)) + "|:--------:|"
    
    resultado.append(header)
    resultado.append(separator)
    
    for tarjeta in sorted(matriz.index):
        fila_valores = [str(matriz.loc[tarjeta, cat]) if cat in matriz.columns else "0" for cat in categorias]
        total_fila = matriz.loc[tarjeta].sum()
        resultado.append(f"| {tarjeta} | " + " | ".join(fila_valores) + f" | **{total_fila}** |")
    
    totales = [str(matriz[cat].sum()) for cat in categorias]
    total_general = matriz.values.sum()
    resultado.append(f"| **Total** | " + " | ".join(totales) + f" | **{total_general}** |")
    resultado.append("")
    
    resultado.append("#### Análisis de Consenso\n")
    resultado.append("*Categoría más frecuente para cada tarjeta:*\n")
    
    for tarjeta in sorted(matriz.index):
        cat_max = matriz.loc[tarjeta].idxmax()
        freq_max = matriz.loc[tarjeta].max()
        total = matriz.loc[tarjeta].sum()
        porcentaje = (freq_max / total) * 100 if total > 0 else 0
        
        if porcentaje >= 80:
            consenso = "🟢 Alto"
        elif porcentaje >= 50:
            consenso = "🟡 Medio"
        else:
            consenso = "🔴 Bajo"
        
        resultado.append(f"- **{tarjeta}** → {cat_max} ({freq_max}/{total} = {porcentaje:.0f}%) - {consenso}")
    
    resultado.append("")
    
    if errores_parse > 0:
        resultado.append(f"*⚠️ {errores_parse} respuesta(s) no pudieron ser parseadas.*\n")
    
    return '\n'.join(resultado)


def analizar_diferencia_semantica(df_pregunta: pd.DataFrame, id_pregunta: str, texto_pregunta: str) -> str:
    """Analiza respuestas tipo diferencia semántica."""
    resultado = []
    resultado.append(f"### Pregunta {id_pregunta} - Diferencia Semántica\n")
    resultado.append(f"**{texto_pregunta}**\n")
    
    frecuencias = df_pregunta['respuesta'].value_counts()
    total = len(df_pregunta)
    
    resultado.append("#### Frecuencia de Opciones\n")
    resultado.append("| Opción | Frecuencia | Porcentaje | Visual |")
    resultado.append("|--------|------------|------------|--------|")
    
    for opcion, freq in frecuencias.items():
        porcentaje = (freq / total) * 100
        barra = "█" * int(porcentaje / 5)
        resultado.append(f"| {opcion} | {freq} | {porcentaje:.1f}% | {barra} |")
    
    resultado.append("")
    resultado.append(f"*Total de respuestas: {total}*\n")
    
    return '\n'.join(resultado)


def analizar_click_con_ia(df_pregunta: pd.DataFrame, id_pregunta: str, texto_pregunta: str) -> str:
    """Analiza respuestas tipo click (heatmaps) con análisis de IA."""
    resultado = []
    resultado.append(f"### Pregunta {id_pregunta} - Click / Heatmap\n")
    resultado.append(f"**{texto_pregunta}**\n")
    resultado.append("#### Heatmaps por Usuario\n")
    
    analisis_individuales = []
    
    for _, row in df_pregunta.iterrows():
        usuario = row.get('nombre', row['id_usuario'])
        empresa = row.get('empresa', 'N/A')
        respuesta = row['respuesta']
        
        if isinstance(respuesta, dict):
            heatmap_url = respuesta.get('heatmap_url', 'URL no disponible')
        elif isinstance(respuesta, str):
            try:
                resp_dict = json.loads(respuesta)
                heatmap_url = resp_dict.get('heatmap_url', respuesta)
            except:
                heatmap_url = respuesta
        else:
            heatmap_url = str(respuesta)
        
        resultado.append(f"**{usuario}** ({empresa}): [🖼️ Ver Heatmap]({heatmap_url})")
        
        # Analizar con IA
        if heatmap_url and heatmap_url != 'URL no disponible':
            print(f"    🖼️ Analizando heatmap de {usuario}...")
            analisis = agente_ia.analizar_imagen(heatmap_url, texto_pregunta)
            resultado.append(f"> 🤖 **Análisis IA:** {analisis}\n")
            analisis_individuales.append(analisis)
        else:
            resultado.append("")
    
    resultado.append(f"*Total de clicks registrados: {len(df_pregunta)}*\n")
    
    # Síntesis general
    if len(analisis_individuales) > 1:
        print(f"    📊 Generando síntesis de heatmaps...")
        sintesis = agente_ia.generar_sintesis_pregunta(analisis_individuales, "heatmap/click", texto_pregunta)
        resultado.append("#### 🎯 Síntesis de Análisis de Heatmaps\n")
        resultado.append(sintesis)
        resultado.append("")
    
    return '\n'.join(resultado)


def analizar_pantalla_con_ia(df_pregunta: pd.DataFrame, id_pregunta: str, texto_pregunta: str) -> str:
    """Analiza respuestas tipo pantalla (grabaciones de video) con IA."""
    resultado = []
    resultado.append(f"### Pregunta {id_pregunta} - Grabación de Pantalla\n")
    resultado.append(f"**{texto_pregunta}**\n")
    resultado.append("#### Videos por Usuario\n")
    
    analisis_individuales = []
    
    for _, row in df_pregunta.iterrows():
        usuario = row.get('nombre', row['id_usuario'])
        empresa = row.get('empresa', 'N/A')
        tiempo = row.get('tiempo_respuesta', 'N/A')
        respuesta = row['respuesta']
        
        if isinstance(respuesta, dict):
            video_url = respuesta.get('video_url', 'URL no disponible')
        elif isinstance(respuesta, str):
            try:
                resp_dict = json.loads(respuesta)
                video_url = resp_dict.get('video_url', respuesta)
            except:
                video_url = respuesta
        else:
            video_url = str(respuesta)
        
        resultado.append(f"**{usuario}** ({empresa}) - Duración: {tiempo}s: [🎬 Ver Video]({video_url})")
        
        # Analizar con IA
        if video_url and video_url != 'URL no disponible':
            print(f"    🎬 Analizando video de {usuario}...")
            analisis = agente_ia.analizar_video(video_url, texto_pregunta)
            resultado.append(f"> 🤖 **Análisis IA:** {analisis}\n")
            analisis_individuales.append(analisis)
        else:
            resultado.append("")
    
    resultado.append(f"*Total de grabaciones: {len(df_pregunta)}*\n")
    
    # Síntesis general
    if len(analisis_individuales) > 1:
        print(f"    📊 Generando síntesis de videos...")
        sintesis = agente_ia.generar_sintesis_pregunta(analisis_individuales, "grabación de pantalla", texto_pregunta)
        resultado.append("#### 🎯 Síntesis de Análisis de Videos\n")
        resultado.append(sintesis)
        resultado.append("")
    
    return '\n'.join(resultado)


def analizar_contexto(df_pregunta: pd.DataFrame, id_pregunta: str, texto_pregunta: str) -> str:
    """Analiza preguntas de contexto (instrucciones)."""
    resultado = []
    resultado.append(f"### Pregunta {id_pregunta} - Contexto/Instrucción\n")
    resultado.append(f"**{texto_pregunta}**\n")
    
    tiempos = pd.to_numeric(df_pregunta['tiempo_respuesta'], errors='coerce').dropna()
    if len(tiempos) > 0:
        resultado.append(f"*Tiempo promedio de lectura: {tiempos.mean():.1f} segundos*\n")
    
    return '\n'.join(resultado)


def analizar_tiempos(df: pd.DataFrame) -> str:
    """Analiza tiempos de respuesta y detecta outliers."""
    resultado = []
    resultado.append("## ⏱️ Análisis de Tiempos de Respuesta\n")
    
    df['tiempo_respuesta'] = pd.to_numeric(df['tiempo_respuesta'], errors='coerce')
    df_filtrado = df[df['tipo_formato'] != 'contexto'].copy()
    
    resultado.append("### Tiempo Promedio por Pregunta\n")
    tiempo_por_pregunta = df_filtrado.groupby(['id_pregunta', 'tipo_formato'])['tiempo_respuesta'].agg(['mean', 'std', 'min', 'max', 'count'])
    tiempo_por_pregunta = tiempo_por_pregunta.round(2)
    
    resultado.append("| Pregunta | Tipo | Promedio (s) | Desv. Std | Mín | Máx | N |")
    resultado.append("|----------|------|--------------|-----------|-----|-----|---|")
    
    for (pregunta, tipo), row in tiempo_por_pregunta.iterrows():
        std_val = row['std'] if not pd.isna(row['std']) else 0
        resultado.append(f"| {pregunta} | {tipo} | {row['mean']:.1f} | {std_val:.1f} | {row['min']:.1f} | {row['max']:.1f} | {int(row['count'])} |")
    
    resultado.append("")
    
    resultado.append("### 🚨 Detección de Outliers (> 2σ)\n")
    resultado.append("*Usuarios que tardaron significativamente más que el promedio:*\n")
    
    outliers_encontrados = []
    
    for pregunta in df_filtrado['id_pregunta'].unique():
        df_pregunta = df_filtrado[df_filtrado['id_pregunta'] == pregunta]
        tiempos = df_pregunta['tiempo_respuesta'].dropna()
        
        if len(tiempos) < 3:
            continue
        
        promedio = tiempos.mean()
        std = tiempos.std()
        
        if std == 0:
            continue
            
        umbral = promedio + (2 * std)
        outliers = df_pregunta[df_pregunta['tiempo_respuesta'] > umbral]
        
        for _, row in outliers.iterrows():
            usuario = row.get('nombre', row['id_usuario'])
            tiempo = row['tiempo_respuesta']
            desv_sobre_media = (tiempo - promedio) / std if std > 0 else 0
            outliers_encontrados.append({
                'pregunta': pregunta,
                'usuario': usuario,
                'tiempo': tiempo,
                'promedio': promedio,
                'desviaciones': desv_sobre_media
            })
    
    if outliers_encontrados:
        resultado.append("| Pregunta | Usuario | Tiempo (s) | Promedio (s) | Desviaciones σ |")
        resultado.append("|----------|---------|------------|--------------|----------------|")
        for o in outliers_encontrados:
            resultado.append(f"| {o['pregunta']} | {o['usuario']} | {o['tiempo']:.1f} | {o['promedio']:.1f} | +{o['desviaciones']:.1f}σ |")
    else:
        resultado.append("✅ No se detectaron outliers significativos.\n")
    
    resultado.append("")
    
    resultado.append("### Tiempo Total por Usuario\n")
    tiempo_por_usuario = df_filtrado.groupby(['id_usuario', 'nombre', 'empresa'])['tiempo_respuesta'].agg(['sum', 'mean', 'count'])
    tiempo_por_usuario = tiempo_por_usuario.round(2).sort_values('sum', ascending=False)
    
    resultado.append("| Usuario | Empresa | Tiempo Total (s) | Promedio/Pregunta (s) | Preguntas |")
    resultado.append("|---------|---------|------------------|----------------------|-----------|")
    
    for (id_usr, nombre, empresa), row in tiempo_por_usuario.iterrows():
        minutos = row['sum'] / 60
        resultado.append(f"| {nombre} | {empresa} | {row['sum']:.1f} ({minutos:.1f} min) | {row['mean']:.1f} | {int(row['count'])} |")
    
    resultado.append("")
    
    return '\n'.join(resultado)


def generar_reporte(df: pd.DataFrame, usar_ia: bool = True) -> str:
    """Genera el reporte completo en formato Markdown."""
    reporte = []
    
    reporte.append("# 📊 Reporte de Análisis de Prueba de Usabilidad\n")
    if usar_ia:
        reporte.append("*📌 Incluye análisis automático con Gemini AI*\n")
    reporte.append("---\n")
    
    reporte.append("## 📋 Resumen General\n")
    n_usuarios = df['id_usuario'].nunique()
    n_preguntas = df['id_pregunta'].nunique()
    n_respuestas = len(df)
    empresas = df['empresa'].dropna().unique()
    
    reporte.append(f"- **Total de usuarios:** {n_usuarios}")
    reporte.append(f"- **Total de preguntas analizadas:** {n_preguntas}")
    reporte.append(f"- **Total de respuestas:** {n_respuestas}")
    reporte.append(f"- **Empresas participantes:** {', '.join(str(e) for e in empresas)}")
    reporte.append("")
    
    reporte.append("### Participantes\n")
    reporte.append("| Nombre | Empresa | Especialidad |")
    reporte.append("|--------|---------|--------------|")
    participantes = df[['nombre', 'empresa', 'especialidad']].drop_duplicates()
    for _, p in participantes.iterrows():
        reporte.append(f"| {p['nombre']} | {p['empresa']} | {p.get('especialidad', 'N/A')} |")
    reporte.append("")
    
    tipos = df['tipo_formato'].value_counts()
    reporte.append("### Distribución por Tipo de Formato\n")
    reporte.append("| Tipo | Cantidad |")
    reporte.append("|------|----------|")
    for tipo, cantidad in tipos.items():
        reporte.append(f"| {tipo} | {cantidad} |")
    reporte.append("")
    
    reporte.append("---\n")
    reporte.append("## 📝 Análisis por Pregunta\n")
    
    preguntas_unicas = sorted(df['id_pregunta'].unique())
    
    for id_pregunta in preguntas_unicas:
        df_pregunta = df[df['id_pregunta'] == id_pregunta]
        tipo_formato = df_pregunta['tipo_formato'].iloc[0].lower().strip()
        texto_pregunta = df_pregunta['texto_pregunta'].iloc[0] if 'texto_pregunta' in df_pregunta.columns else ""
        
        print(f"📝 Procesando pregunta {id_pregunta} ({tipo_formato})...")
        
        if tipo_formato == 'escala_likert':
            reporte.append(analizar_escala_likert(df_pregunta, id_pregunta, texto_pregunta))
        elif tipo_formato == 'texto':
            reporte.append(analizar_texto(df_pregunta, id_pregunta, texto_pregunta))
        elif tipo_formato == 'audio':
            if usar_ia:
                reporte.append(analizar_audio_con_ia(df_pregunta, id_pregunta, texto_pregunta))
            else:
                reporte.append(analizar_audio_sin_ia(df_pregunta, id_pregunta, texto_pregunta))
        elif tipo_formato == 'card_sorting':
            reporte.append(analizar_card_sorting(df_pregunta, id_pregunta, texto_pregunta))
        elif tipo_formato == 'diferencia_semantica':
            reporte.append(analizar_diferencia_semantica(df_pregunta, id_pregunta, texto_pregunta))
        elif tipo_formato == 'click':
            if usar_ia:
                reporte.append(analizar_click_con_ia(df_pregunta, id_pregunta, texto_pregunta))
            else:
                reporte.append(analizar_click_sin_ia(df_pregunta, id_pregunta, texto_pregunta))
        elif tipo_formato == 'pantalla':
            if usar_ia:
                reporte.append(analizar_pantalla_con_ia(df_pregunta, id_pregunta, texto_pregunta))
            else:
                reporte.append(analizar_pantalla_sin_ia(df_pregunta, id_pregunta, texto_pregunta))
        elif tipo_formato == 'contexto':
            reporte.append(analizar_contexto(df_pregunta, id_pregunta, texto_pregunta))
        else:
            reporte.append(f"### Pregunta {id_pregunta} - {tipo_formato}\n")
            reporte.append(f"**{texto_pregunta}**\n")
            reporte.append("#### Respuestas\n")
            for _, row in df_pregunta.iterrows():
                usuario = row.get('nombre', row['id_usuario'])
                reporte.append(f"- **{usuario}:** {row['respuesta']}")
            reporte.append("")
        
        # Enfriamiento y limpieza si se usó IA
        if usar_ia and tipo_formato in ['audio', 'click', 'pantalla']:
            agente_ia.enfriamiento()
            agente_ia.limpieza()
            
        reporte.append("---\n")
    
    reporte.append(analizar_tiempos(df))
    
    reporte.append("---\n")
    reporte.append("*Reporte generado automáticamente por Analizador de Usabilidad con IA*\n")
    
    return '\n'.join(reporte)


# Funciones sin IA (fallback)
def analizar_audio_sin_ia(df_pregunta: pd.DataFrame, id_pregunta: str, texto_pregunta: str) -> str:
    resultado = []
    resultado.append(f"### Pregunta {id_pregunta} - Audio\n")
    resultado.append(f"**{texto_pregunta}**\n")
    resultado.append("#### Grabaciones de Audio por Usuario\n")
    
    for _, row in df_pregunta.iterrows():
        usuario = row.get('nombre', row['id_usuario'])
        empresa = row.get('empresa', 'N/A')
        respuesta = row['respuesta']
        
        if isinstance(respuesta, dict):
            audio_url = respuesta.get('audio_url', 'URL no disponible')
        else:
            audio_url = str(respuesta)
        
        resultado.append(f"- **{usuario}** ({empresa}): [Audio]({audio_url})")
    
    resultado.append(f"\n*Total de grabaciones: {len(df_pregunta)}*\n")
    return '\n'.join(resultado)


def analizar_click_sin_ia(df_pregunta: pd.DataFrame, id_pregunta: str, texto_pregunta: str) -> str:
    resultado = []
    resultado.append(f"### Pregunta {id_pregunta} - Click / Heatmap\n")
    resultado.append(f"**{texto_pregunta}**\n")
    resultado.append("#### Heatmaps por Usuario\n")
    
    for _, row in df_pregunta.iterrows():
        usuario = row.get('nombre', row['id_usuario'])
        empresa = row.get('empresa', 'N/A')
        respuesta = row['respuesta']
        
        if isinstance(respuesta, dict):
            heatmap_url = respuesta.get('heatmap_url', 'URL no disponible')
        else:
            heatmap_url = str(respuesta)
        
        resultado.append(f"- **{usuario}** ({empresa}): [Ver Heatmap]({heatmap_url})")
    
    resultado.append(f"\n*Total de clicks registrados: {len(df_pregunta)}*\n")
    return '\n'.join(resultado)


def analizar_pantalla_sin_ia(df_pregunta: pd.DataFrame, id_pregunta: str, texto_pregunta: str) -> str:
    resultado = []
    resultado.append(f"### Pregunta {id_pregunta} - Grabación de Pantalla\n")
    resultado.append(f"**{texto_pregunta}**\n")
    resultado.append("#### Videos por Usuario\n")
    
    for _, row in df_pregunta.iterrows():
        usuario = row.get('nombre', row['id_usuario'])
        empresa = row.get('empresa', 'N/A')
        tiempo = row.get('tiempo_respuesta', 'N/A')
        respuesta = row['respuesta']
        
        if isinstance(respuesta, dict):
            video_url = respuesta.get('video_url', 'URL no disponible')
        else:
            video_url = str(respuesta)
        
        resultado.append(f"- **{usuario}** ({empresa}) - Duración: {tiempo}s: [Ver Video]({video_url})")
    
    resultado.append(f"\n*Total de grabaciones: {len(df_pregunta)}*\n")
    return '\n'.join(resultado)


def main():
    """Función principal del script."""
    import os
    
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    directorio_padre = os.path.dirname(directorio_actual)
    
    ruta_respuestas = os.path.join(directorio_padre, 'Respuesta_rows.csv')
    ruta_usuarios = os.path.join(directorio_padre, 'Usuario_rows.csv')
    
    if not os.path.exists(ruta_respuestas):
        print(f"❌ Error: No se encontró el archivo '{ruta_respuestas}'")
        return
    
    if not os.path.exists(ruta_usuarios):
        print(f"❌ Error: No se encontró el archivo '{ruta_usuarios}'")
        return
    
    print("📂 Cargando y procesando datos...")
    df = cargar_y_procesar_datos(ruta_respuestas, ruta_usuarios)
    
    print(f"✅ Datos procesados: {len(df)} respuestas de {df['id_usuario'].nunique()} usuarios")
    print("🤖 Iniciando análisis con Gemini AI...")
    print("   (Esto puede tomar varios minutos para contenido multimedia)\n")
    
    # Generar reporte con IA
    reporte = generar_reporte(df, usar_ia=True)
    
    print("\n" + "="*60)
    print(reporte)
    
    ruta_salida = os.path.join(directorio_actual, 'reporte_usabilidad.md')
    with open(ruta_salida, 'w', encoding='utf-8') as f:
        f.write(reporte)
    
    print(f"\n💾 Reporte guardado en: {ruta_salida}")


if __name__ == "__main__":
    main()
