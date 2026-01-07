# Manual de uso y entendimiento del agente de análisis de usabilidad

## 1. Propósito general
El agente automatiza el análisis de respuestas de pruebas de usabilidad, generando hallazgos estructurados a partir de datos cuantitativos (Likert), cualitativos (texto), y contenido multimedia (imágenes, audio, video) usando Gemini y exporta los resultados listos para cargarse en Supabase.

## 2. Flujo de extremo a extremo
1) Fuente de datos: los CSV `Respuesta_rows.csv` y `Usuario_rows.csv` contienen las respuestas brutas y el perfil de cada participante.
2) Normalización: `analizador_usabilidad.py` transforma las respuestas anidadas en un DataFrame plano y separa cada pregunta por usuario.
3) Análisis por tipo de pregunta:
   - Likert: calcula métricas (media, mediana, moda, desviación) y distribuciones.
   - Texto libre: agrupa y lista respuestas; puede resumir con IA (no incluido en el fragmento leído).
   - Card sorting / matrices: computa consensos y frecuencias.
   - Multimedia: descarga heatmaps, videos o audios y los envía a Gemini para describir comportamientos.
4) Síntesis: genera resúmenes por pregunta y patrones generales con Gemini (gestiona reintentos y rate limiting).
5) Serialización: guarda un reporte en Markdown y construye JSON con hallazgos generales, por pregunta y por tester.
6) Exportación: `generar_hallazgos_csv.py` o `procesar_hallazgos_ia.py` producen `Hallazgo.rows.csv` y pueden publicar en Supabase. `subir_hallazgos_rest.py` ofrece una vía REST alternativa para evitar problemas de SSL del cliente oficial.

## 3. Archivos clave y responsabilidades
- `analizador_usabilidad.py`: núcleo analítico. Limpia, tabula y analiza cada tipo de pregunta; integra el agente multimedia (Gemini) con reintentos y control de cuota.
- `generar_hallazgos_csv.py`: lee el reporte Markdown, pregunta a Gemini para estructurar hallazgos y escribe el CSV listo para cargar; dejó comentada la subida directa a Supabase para evitar errores SSL.
- `procesar_hallazgos_ia.py`: alternativa sin IA generativa: parsea el Markdown con regex, arma los hallazgos y sí sube a Supabase con el cliente oficial.
- `subir_hallazgos_rest.py`: publica el CSV a Supabase vía REST (útil en entornos corporativos con certificados problemáticos).
- `reporte_usabilidad.md`: salida principal del análisis (insumos para los scripts de exportación).

## 4. Configuración sensible
- Claves expuestas en código:
  - `GEMINI_API_KEY` en `analizador_usabilidad.py` y `generar_hallazgos_csv.py`.
  - `SUPABASE_URL` y `SUPABASE_KEY` en `generar_hallazgos_csv.py`, `procesar_hallazgos_ia.py`, `subir_hallazgos_rest.py`.
- Recomendado: moverlas a variables de entorno y leerlas con `os.getenv` para evitar filtrados y permitir rotación.

## 5. Cómo ejecutar (local)
1) Crear entorno: `python -m venv .venv` y activar (`.venv\Scripts\activate` en Windows).
2) Instalar dependencias mínimas: `pip install pandas numpy scipy requests google-generativeai supabase`. Ajusta versiones según tu política.
3) Ubicarte en la carpeta `Analizador`.
4) Flujo típico:
   - Generar reporte: `python analizador_usabilidad.py` (requiere los CSV de entrada en la raíz del proyecto o ajustar rutas en el script).
   - Estructurar hallazgos con IA: `python generar_hallazgos_csv.py` (lee `reporte_usabilidad.md`).
   - O bien parsear sin IA y subir: `python procesar_hallazgos_ia.py`.
   - Publicar vía REST: `python subir_hallazgos_rest.py` (usa `Hallazgo.rows.csv`).
5) Validar la salida: abre `Hallazgo.rows.csv` y revisa que los campos `hallazgo_general`, `hallazgo_pregunta` y `hallazgo_tester` contengan JSON válido.

## 6. Decisiones de diseño y por qué
- Reintentos y enfriamiento en Gemini: se manejan códigos 429/500 con backoff incremental para no romper el flujo por cuotas o errores transitorios.
- Cache de análisis multimedia: evita repetir llamadas a la misma URL y reduce costos/tiempo.
- Descarga local + File API para video/audio: mejora estabilidad con archivos grandes y formatos mixtos (ej. .webm sin pista de video).
- Limpieza de Markdown con regex (`procesar_hallazgos_ia.py`): permite generar hallazgos deterministas sin depender de IA generativa, útil en entornos sin cuota.
- Separación de exportes (cliente Supabase vs REST): hay dos caminos para sortear limitaciones de certificados o del cliente oficial.
- Limitación de longitud de hallazgos por tester/pregunta: se recorta a ~500-1000 caracteres para que el JSON sea manejable y aceptado por la API.

## 7. Extensiones y pruebas sugeridas
- Externalizar todas las claves a variables de entorno y añadir validaciones al inicio de cada script.
- Añadir pruebas unitarias para las funciones de parsing y de estadísticos (Likert/card sorting) para evitar regresiones.
- Incluir validación de esquemas (pydantic o jsonschema) antes de escribir o subir a Supabase.
- Registrar logs estructurados (nivel INFO/ERROR) en vez de `print` para facilitar observabilidad.
- Añadir un dry-run que genere sólo el CSV sin subir nada (o confirmar antes de subir).

## 8. Preguntas rápidas de operación
- ¿Dónde veo el resultado? En `Analizador/reporte_usabilidad.md` y el CSV `Analizador/Hallazgo.rows.csv`.
- ¿Qué pasa si Gemini falla? El flujo intenta reintentos; si agota, devuelve un mensaje de error en el campo de hallazgo. Considera re-ejecutar o usar el parser determinista (`procesar_hallazgos_ia.py`).
- ¿Cómo cambio el ID de ficha? Se detecta del Markdown (`/respuestas/<id>/`); si no existe, usa 20. Ajusta `extraer_id_ficha` si necesitas otro patrón.

## 9. Seguridad y cumplimiento
- Sustituye las claves hardcodeadas inmediatamente.
- Habilita `verify=True` en `requests` cuando dispongas de certificados válidos.
- Revisa políticas de datos: los medios (audio/video/imágenes) se suben a Gemini; asegúrate de tener consentimiento y de cumplir con retención/privacidad.

## 10. Referencias rápidas
- Flujo completo: `analizador_usabilidad.py`
- Estructuración con IA y CSV: `generar_hallazgos_csv.py`
- Parsing sin IA + subida cliente: `procesar_hallazgos_ia.py`
- Subida REST: `subir_hallazgos_rest.py`
