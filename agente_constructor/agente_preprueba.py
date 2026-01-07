"""
================================================================================
AGENTE ESTRUCTURADOR INTEGRAL - Community Tester
================================================================================
Genera Planes de Prueba de Usabilidad completos basados en:
- Brief del proyecto
- Prototipo de Figma
- Conocimiento de Ergonomía Física y Cognitiva
- Técnicas de Innovación SIT

Autor: Community Tester
Versión: 1.0
================================================================================
"""

import os
import re
import json
import warnings
import logging
from datetime import datetime
from typing import List, Dict, Optional

# Suprimir warnings
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GLOG_minloglevel'] = '2'
warnings.filterwarnings('ignore')
logging.getLogger('absl').setLevel(logging.ERROR)

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# BASE DE CONOCIMIENTO: ERGONOMÍA FÍSICA
# =============================================================================
CONOCIMIENTO_ERGONOMIA_FISICA = """
ERGONOMÍA FÍSICA - Criterios de Evaluación

1. PERCEPTIBILIDAD
   - ¿Los elementos visuales son fácilmente distinguibles?
   - ¿El contraste es adecuado para lectura?
   - ¿Los tamaños de texto son legibles?
   - ¿Los iconos son reconocibles?
   - ¿Hay feedback visual claro en las interacciones?

2. OPERABILIDAD (Ley de Fitts)
   - ¿Los botones tienen tamaño táctil adecuado (mínimo 44x44px)?
   - ¿Los elementos clickeables están bien espaciados?
   - ¿Las zonas de toque son accesibles con el pulgar?
   - ¿Los gestos requeridos son naturales?
   - ¿La navegación es alcanzable sin reposicionar el dispositivo?

3. CONSISTENCIA VISUAL
   - ¿Los elementos similares lucen similares?
   - ¿Los colores tienen significado consistente?
   - ¿La tipografía es uniforme?
   - ¿Los espaciados siguen un patrón?
   - ¿Los íconos mantienen el mismo estilo?

4. ACCESIBILIDAD FÍSICA
   - ¿Funciona con una sola mano?
   - ¿Los elementos críticos están en zonas de fácil acceso?
   - ¿Hay alternativas para usuarios con limitaciones motrices?
   - ¿El tiempo de respuesta es adecuado?

PREGUNTAS TIPO PARA ERGONOMÍA FÍSICA:
- "¿Qué tan fácil fue para usted localizar el botón de [acción]?"
- "¿Pudo usted leer claramente toda la información presentada?"
- "¿Los elementos en pantalla le parecieron del tamaño adecuado?"
- "¿Tuvo que hacer algún esfuerzo para alcanzar algún botón?"
"""

# =============================================================================
# BASE DE CONOCIMIENTO: ERGONOMÍA COGNITIVA
# =============================================================================
CONOCIMIENTO_ERGONOMIA_COGNITIVA = """
ERGONOMÍA COGNITIVA - Criterios de Evaluación

1. CARGA COGNITIVA
   - ¿La cantidad de información es manejable?
   - ¿Se requiere memorizar información entre pantallas?
   - ¿Las instrucciones son claras y concisas?
   - ¿Hay sobrecarga de opciones (paradoja de la elección)?
   - ¿Los formularios piden solo información necesaria?

2. MODELO MENTAL
   - ¿El flujo coincide con las expectativas del usuario?
   - ¿La navegación es predecible?
   - ¿Los términos usados son familiares?
   - ¿La estructura de información es lógica?
   - ¿El usuario sabe dónde está y hacia dónde puede ir?

3. CLARIDAD Y COMPRENSIÓN
   - ¿Los mensajes son entendibles sin conocimiento técnico?
   - ¿Los errores explican qué pasó y cómo solucionarlo?
   - ¿Las confirmaciones son claras?
   - ¿El progreso es visible en procesos largos?
   - ¿Los llamados a la acción son evidentes?

4. EFICIENCIA COGNITIVA
   - ¿Se puede completar la tarea sin ayuda externa?
   - ¿El número de pasos es el mínimo necesario?
   - ¿Hay atajos para usuarios frecuentes?
   - ¿La información se presenta en el momento adecuado?

PREGUNTAS TIPO PARA ERGONOMÍA COGNITIVA:
- "¿Le quedó claro a usted qué debía hacer en esta pantalla?"
- "¿La cantidad de información presentada le pareció adecuada?"
- "¿En algún momento se sintió usted confundido o perdido?"
- "¿Pudo usted anticipar qué pasaría al presionar este botón?"
"""

# =============================================================================
# BASE DE CONOCIMIENTO: INNOVACIÓN SIT
# =============================================================================
CONOCIMIENTO_SIT = """
TÉCNICAS SIT (Systematic Inventive Thinking) - Para Innovación

1. SUSTRACCIÓN
   Eliminar un componente esencial y encontrar valor en su ausencia.
   Pregunta guía: "¿Qué pasaría si eliminamos [elemento]?"
   Ejemplo: "¿Qué pasaría si eliminamos el paso de confirmación?"
   Aplicación en pruebas: Identificar elementos que podrían simplificarse o eliminarse.

2. MULTIPLICACIÓN
   Duplicar un componente pero modificando algún atributo.
   Pregunta guía: "¿Qué pasaría si duplicamos [elemento] con una variación?"
   Ejemplo: "¿Qué tal múltiples formas de autenticación?"
   Aplicación en pruebas: Explorar variantes de funcionalidades existentes.

3. DIVISIÓN
   Separar un componente en partes o reorganizar sus elementos.
   Pregunta guía: "¿Qué pasaría si dividimos [elemento] en partes?"
   Ejemplo: "¿Qué tal si el registro se divide en pasos más pequeños?"
   Aplicación en pruebas: Evaluar si procesos largos se beneficiarían de fragmentación.

4. UNIFICACIÓN DE TAREAS
   Asignar una nueva función a un elemento existente.
   Pregunta guía: "¿Qué elemento existente podría cumplir también [otra función]?"
   Ejemplo: "¿El botón de ayuda podría también mostrar el progreso?"
   Aplicación en pruebas: Identificar oportunidades de consolidación.

5. DEPENDENCIA DE ATRIBUTOS
   Crear relaciones entre atributos que antes eran independientes.
   Pregunta guía: "¿Qué pasaría si [atributo A] cambiara según [atributo B]?"
   Ejemplo: "¿El nivel de detalle podría adaptarse al perfil del usuario?"
   Aplicación en pruebas: Explorar personalización y adaptabilidad.

PREGUNTAS TIPO PARA INNOVACIÓN SIT:
- "Si pudiera usted eliminar un paso de este proceso, ¿cuál sería?"
- "¿Qué funcionalidad le gustaría que se agregara a esta pantalla?"
- "¿Cómo mejoraría usted este flujo para hacerlo más rápido?"
- "¿Qué elemento de otras aplicaciones le gustaría ver aquí?"
"""

# =============================================================================
# FORMATOS PERMITIDOS
# =============================================================================
FORMATOS_PERMITIDOS = """
FORMATOS PERMITIDOS (usar EXACTAMENTE estos nombres):

1. texto
   - Para respuestas abiertas y opiniones detalladas
   - Usar cuando se necesita profundidad cualitativa

2. escala_likert
   - DEBE incluir leyenda numérica explicada
   - Ejemplo: "Califique de 1 a 5, donde 1 es 'Muy difícil' y 5 es 'Muy fácil'"
   - Usar para medir satisfacción, dificultad, acuerdo

3. audio
   - Para capturar pensamientos en voz alta
   - Usar cuando escribir interrumpiría la tarea

4. pantalla
   - DEBE especificar que se grabará y POR QUÉ
   - Ejemplo: "Esta pregunta grabará su pantalla para que podamos ver cómo navega..."
   - Usar para observar comportamiento real

5. card_sorting
   - DEBE incluir dos listas: "Categorías" y "Tarjetas"
   - Usar para evaluar arquitectura de información

6. diferencia_semantica
   - DEBE incluir UN SOLO par de opuestos por pregunta
   - Ejemplo: "(Fácil vs. Difícil)"
   - Usar para medir percepciones en escala bipolar

7. click
   - Para identificar zonas de interés
   - Usar cuando se necesita saber dónde haría click el usuario

8. contexto
   - Para introducciones y transiciones
   - NO cuenta como pregunta para el tallaje
   - Usar para situar al usuario sin revelar objetivos técnicos
"""

# =============================================================================
# REGLAS DE REDACCIÓN
# =============================================================================
REGLAS_REDACCION = """
REGLAS DE REDACCIÓN (OBLIGATORIAS):

1. ENFOQUE EN LA PERSONA ("USTEDEO"):
   - Todas las preguntas en segunda persona formal ("usted")
   - Incorrecto: "¿Qué tan fácil fue encontrar el botón?"
   - Correcto: "¿Qué tan fácil fue para usted encontrar el botón?"

2. INTRODUCCIONES AMIGABLES:
   - Los contextos NO revelan objetivos técnicos
   - NO usar jerga (carga cognitiva, ley de Fitts, etc.)
   - Deben ser guiones naturales para situar al usuario
   - Incorrecto: "Evaluaremos la carga mental del formulario"
   - Correcto: "A continuación, interactúe con el formulario como lo haría normalmente"

3. REGLA DEL TIEMPO LÍMITE:
   - Si una pregunta tiene límite de tiempo, DEBE ir precedida por un contexto:
   - "Para la siguiente tarea, usted tendrá un límite de [X] minutos. Por favor, prepárese."

4. EVALUACIÓN ÚNICA:
   - Cada pregunta evalúa UN solo aspecto
   - No mezclar conceptos en una misma pregunta

5. JUSTIFICACIÓN OBLIGATORIA:
   - Después de cada pregunta: "Justificacion del Formato: [explicación técnica]"
"""


class AgentePreprueba:
    """
    Agente Estructurador Integral para generar Planes de Prueba de Usabilidad.
    """
    
    def __init__(self):
        """Inicializa el agente con las APIs necesarias."""
        # Configurar Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.modelo = genai.GenerativeModel('gemini-2.0-flash')
        else:
            raise ValueError("GEMINI_API_KEY no encontrada en .env")
        
        # Configurar Figma
        self.figma_token = os.getenv("FIGMA_TOKEN")
        self.figma_api_url = "https://api.figma.com/v1"
    
    def leer_brief(self, ruta_brief: str) -> Dict:
        """
        Lee y analiza el brief del proyecto.
        """
        print(f"\n📖 Leyendo brief: {ruta_brief}")
        
        contenido = None
        codificaciones = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in codificaciones:
            try:
                with open(ruta_brief, 'r', encoding=encoding) as f:
                    contenido = f.read()
                break
            except UnicodeDecodeError:
                continue
            except FileNotFoundError:
                print(f"❌ Archivo no encontrado: {ruta_brief}")
                return {}
        
        if not contenido:
            print("❌ No se pudo leer el archivo")
            return {}
        
        # Extraer metadatos del brief usando IA
        print("   Analizando contenido del brief...")
        metadatos = self._extraer_metadatos_brief(contenido)
        
        return {
            'contenido': contenido,
            'metadatos': metadatos
        }
    
    def _extraer_metadatos_brief(self, contenido: str) -> Dict:
        """Extrae metadatos estructurados del brief usando IA."""
        prompt = f"""Analiza este brief de prueba de usabilidad y extrae la información clave.

BRIEF:
{contenido}

Extrae y responde SOLO con JSON válido (sin marcadores de código):
{{
    "titulo": "Título de la prueba",
    "descripcion": "Descripción general del objetivo",
    "hipotesis": "Hipótesis principal a validar",
    "flujo_digital": "Nombre del flujo o producto",
    "autor": "Autor del brief",
    "compania": "Compañía",
    "linea_negocio": "Línea de negocio",
    "tipo_prueba": "Tipo de prueba (moderada/no moderada)",
    "fecha_inicio": "Fecha inicio si está especificada",
    "fecha_fin": "Fecha fin si está especificada",
    "objetivos": ["objetivo 1", "objetivo 2"],
    "dolores": ["dolor/problema 1", "dolor/problema 2"],
    "pantallas_mencionadas": ["pantalla 1", "pantalla 2"],
    "contexto_usuario": "Descripción del usuario objetivo"
}}
"""
        try:
            response = self.modelo.generate_content(prompt)
            texto = self._limpiar_respuesta_json(response.text)
            return json.loads(texto)
        except Exception as e:
            print(f"   ⚠️ Error extrayendo metadatos: {e}")
            return {}
    
    def obtener_pantallas_figma(self, figma_url: str) -> List[Dict]:
        """
        Obtiene las pantallas del prototipo de Figma.
        """
        print(f"\n🎨 Conectando con Figma...")
        
        # Extraer file_key del URL
        file_key = self._extraer_file_key(figma_url)
        if not file_key:
            print("   ⚠️ URL de Figma no válida, usando modo simulado")
            return []
        
        print(f"   File key: {file_key}")
        
        if not self.figma_token:
            print("   ⚠️ FIGMA_TOKEN no configurado, usando modo simulado")
            return []
        
        try:
            import requests
            headers = {"X-FIGMA-TOKEN": self.figma_token}
            url = f"{self.figma_api_url}/files/{file_key}"
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            datos = response.json()
            nombre_archivo = datos.get('name', 'Sin nombre')
            print(f"   Archivo: {nombre_archivo}")
            
            # Extraer pantallas principales
            pantallas = self._extraer_pantallas(datos.get('document', {}))
            print(f"   Pantallas encontradas: {len(pantallas)}")
            
            return pantallas
            
        except Exception as e:
            print(f"   ⚠️ Error conectando con Figma: {e}")
            return []
    
    def _extraer_file_key(self, url: str) -> Optional[str]:
        """Extrae el file_key de una URL de Figma."""
        if not url:
            return None
        
        patterns = ['/file/', '/proto/', '/design/']
        for pattern in patterns:
            if pattern in url:
                try:
                    key = url.split(pattern)[1].split('/')[0].split('?')[0]
                    return key
                except:
                    continue
        return None
    
    def _extraer_pantallas(self, nodo: Dict, nivel: int = 0) -> List[Dict]:
        """Extrae pantallas principales del árbol de Figma."""
        pantallas = []
        
        # Solo extraer frames de niveles superiores (pantallas principales)
        if nivel <= 3 and nodo.get('type') == 'FRAME':
            nombre = nodo.get('name', '')
            # Filtrar elementos internos
            excluir = ['icon', 'button', 'input', 'card', 'vector', 'rectangle', 
                      'ellipse', 'line', 'group', 'component', 'instance']
            if not any(ex in nombre.lower() for ex in excluir) and len(nombre) > 2:
                pantallas.append({
                    'nombre': nombre,
                    'id': nodo.get('id', ''),
                    'tipo': nodo.get('type', '')
                })
        
        # Recursión controlada
        if nivel < 4:
            for hijo in nodo.get('children', []):
                pantallas.extend(self._extraer_pantallas(hijo, nivel + 1))
        
        return pantallas
    
    def generar_plan_prueba(self, brief: Dict, pantallas: List[Dict]) -> str:
        """
        Genera el Plan de Prueba completo usando IA con todo el conocimiento.
        """
        print("\n📝 Generando Plan de Prueba...")
        
        metadatos = brief.get('metadatos', {})
        contenido_brief = brief.get('contenido', '')
        
        # Preparar lista de pantallas
        if pantallas:
            pantallas_texto = "\n".join([f"- {p['nombre']}" for p in pantallas[:50]])
        else:
            pantallas_texto = "No se obtuvieron pantallas de Figma"
        
        # Calcular tallaje estimado basado en objetivos
        num_objetivos = len(metadatos.get('objetivos', []))
        num_dolores = len(metadatos.get('dolores', []))
        total_items = num_objetivos + num_dolores
        
        if total_items <= 3:
            tallaje = "S (Small - 5-8 preguntas)"
        elif total_items <= 6:
            tallaje = "M (Medium - 9-15 preguntas)"
        else:
            tallaje = "L (Large - 16+ preguntas)"
        
        # EJEMPLO DE FORMATO CORRECTO
        ejemplo_formato = '''
Etapa 1 – Primera Impresión y Conexión Cultural

P1:
Objetivo: Situar al usuario en el escenario de uso (Home) sin sesgos técnicos.
Pregunta: Imagine que usted tiene interés en apoyar una causa social y ha llegado a esta página principal. Por favor, tómese un momento para observar lo que se presenta en pantalla.
Formato: contexto
Justificación del Formato: Necesario para que el usuario explore la interfaz visual antes de realizar tareas.

P2:
Objetivo: Evaluar la ergonomía cognitiva (perceptibilidad) y la jerarquía visual del CTA principal.
Pregunta: Basado en su primera impresión, ¿dónde haría clic usted para comenzar a buscar una actividad de voluntariado? Realice un solo clic.
Formato: click
Justificación del Formato: Permite identificar si el llamado a la acción es intuitivo y visible según el mapa de calor.

P3:
Objetivo: Validar la hipótesis de "Diseño Contextual-Cultural" y la conexión emocional.
Pregunta: ¿Cómo percibe usted el lenguaje y las imágenes de esta pantalla inicial en relación con su entorno cultural o regional?
Formato: diferencia_semantica
Justificación del Formato: Mide la percepción subjetiva de pertenencia, clave para la hipótesis del brief.
Categoría: (Ajeno a mi cultura vs. Cercano a mi cultura)

P4:
Objetivo: Evaluar la ergonomía física (confort visual) de los elementos gráficos.
Pregunta: Califique de 1 a 5 qué tan cómoda es para usted la lectura de los textos y la visualización de los iconos, donde 1 es "Muy incómodo/difícil de leer" y 5 es "Muy cómodo/fácil de leer".
Formato: escala_likert
Justificación del Formato: Cuantifica el esfuerzo visual requerido, alineado con el estudio de aspectos visibles y táctiles.

Etapa 2 – El Reto del Registro (Evaluación de Fricción)

P5:
Objetivo: Preparar al usuario para una tarea crítica con medición de eficiencia.
Pregunta: A continuación, usted deberá crear una cuenta nueva en la plataforma. Para la siguiente tarea, usted tendrá un límite de 3 minutos para completar el formulario. Por favor, prepárese antes de continuar.
Formato: contexto
Justificación del Formato: Establece el escenario y la restricción de tiempo para medir la fluidez del flujo crítico.

P6:
Objetivo: Medir la operabilidad y detectar errores en el flujo de registro (Ergonomía Física y Cognitiva).
Pregunta: Por favor, complete el proceso de registro ingresando sus datos simulados hasta llegar a la confirmación de la cuenta. Esta pregunta grabará su pantalla para que podamos ver cómo navega y si encuentra algún obstáculo.
Formato: pantalla
Justificación del Formato: Es vital observar dónde se detiene el usuario o si comete errores en el formulario, dado que es un punto de abandono alto.

P7:
Objetivo: Validar el modelo mental de las categorías (Ergonomía Cognitiva).
Pregunta: Organice las siguientes tarjetas dentro de los grupos que usted considere más lógicos según su criterio personal.
Formato: card_sorting
Justificación del Formato: Verifica si la arquitectura de información coincide con cómo el usuario las entiende.
Categorías: [Impacto Social, Medio Ambiente, Educación, Ayuda Humanitaria]
Tarjetas: [Sembratón, Tutorías Escolares, Donación de Ropa, Construcción de Viviendas]

P8:
Objetivo: Aplicar Innovación SIT (Técnica de Sustracción) para optimizar el flujo.
Pregunta: Si usted pudiera eliminar un paso o dato solicitado durante todo el proceso que acaba de realizar para hacerlo más ágil sin perder seguridad, ¿cuál sería?
Formato: texto
Justificación del Formato: Busca insights para aplicar la técnica de sustracción (eliminar componentes no esenciales) y reducir la fricción.
'''
        
        # Construir el prompt maestro
        prompt = f"""Eres el Agente Estructurador Integral de Community Tester. 
Tu misión es diseñar un Plan de Prueba de Usabilidad COMPLETO y PROFESIONAL.

================================================================================
CONOCIMIENTO BASE
================================================================================

{CONOCIMIENTO_ERGONOMIA_FISICA}

{CONOCIMIENTO_ERGONOMIA_COGNITIVA}

{CONOCIMIENTO_SIT}

{FORMATOS_PERMITIDOS}

{REGLAS_REDACCION}

================================================================================
EJEMPLO DE FORMATO CORRECTO (SIGUE ESTA ESTRUCTURA EXACTAMENTE)
================================================================================
{ejemplo_formato}

================================================================================
INFORMACIÓN DEL PROYECTO A EVALUAR
================================================================================

BRIEF COMPLETO:
{contenido_brief}

METADATOS EXTRAÍDOS:
- Título: {metadatos.get('titulo', 'Por definir')}
- Hipótesis: {metadatos.get('hipotesis', 'Por definir')}
- Objetivos: {metadatos.get('objetivos', [])}
- Dolores identificados: {metadatos.get('dolores', [])}
- Contexto usuario: {metadatos.get('contexto_usuario', 'Por definir')}

PANTALLAS DISPONIBLES EN FIGMA:
{pantallas_texto}

TALLAJE ESTIMADO: {tallaje}

================================================================================
INSTRUCCIONES DE GENERACIÓN (OBLIGATORIAS)
================================================================================

GENERA UN PLAN DE PRUEBA COMPLETO EN TEXTO PLANO.

ESTRUCTURA OBLIGATORIA DEL DOCUMENTO:

Título de la Prueba: [Extraer del brief]
Descripción General: [Resumen del objetivo de la prueba]

===============================================
Metadatos de la Prueba
===============================================
Flujo Digital: {metadatos.get('flujo_digital', 'Por definir')}
Autor: {metadatos.get('autor', 'Por definir')}
Compañía: {metadatos.get('compania', 'Por definir')}
Línea de Negocio: {metadatos.get('linea_negocio', 'Por definir')}
Tipo de Prueba: {metadatos.get('tipo_prueba', 'Usabilidad')}
Tallaje Estimado: {tallaje}
Fecha Inicio: {metadatos.get('fecha_inicio', 'Por definir')}
Fecha Fin: {metadatos.get('fecha_fin', 'Por definir')}

===============================================
Contexto del Brief
===============================================
[2-3 párrafos explicando la hipótesis y el contexto del proyecto]

===============================================
Plan de Prueba Estructurado
===============================================

FORMATO OBLIGATORIO PARA CADA PREGUNTA:

P[número]:
Objetivo: [Objetivo técnico/interno - NO visible al usuario]
Pregunta: [Texto de la pregunta usando "usted" - visible al usuario]
Formato: [uno de: texto, escala_likert, audio, pantalla, card_sorting, diferencia_semantica, click, contexto]
Justificación del Formato: [Explicación técnica de por qué este formato]
(Si es escala_likert: incluir "de 1 a 5, donde 1 es X y 5 es Y" EN la pregunta)
(Si es card_sorting: agregar líneas Categorías: [...] y Tarjetas: [...])
(Si es diferencia_semantica: agregar línea Categoría: (X vs. Y))
(Si es pantalla: explicar en la pregunta que se grabará y por qué)

REGLAS PARA LA GENERACIÓN:

1. ETAPAS: Nombrar cada etapa descriptivamente (Etapa 1 – Nombre Descriptivo)
2. CONTEXTOS: Cada etapa INICIA con una pregunta formato "contexto" para situar al usuario
3. USTEDEO: TODAS las preguntas usan "usted" (¿Qué tan fácil fue para usted...?)
4. NO JERGA: Los contextos NO mencionan términos técnicos (carga cognitiva, Fitts, etc.)
5. TIEMPO LÍMITE: Si una tarea tiene tiempo, el contexto ANTERIOR debe avisar
6. VARIEDAD: Usar AL MENOS 5 formatos diferentes
7. ERGONOMÍA: Mezclar preguntas de ergonomía física Y cognitiva
8. SIT: Incluir 2-3 preguntas de innovación SIT (sustracción, multiplicación, etc.) al final
9. CARD SORTING: Incluir al menos 1 pregunta de card_sorting con categorías y tarjetas relevantes
10. DIFERENCIA SEMÁNTICA: Incluir al menos 1 pregunta con par de opuestos

GENERA EL PLAN COMPLETO AHORA (texto plano, sin markdown):
"""

        try:
            print("   Procesando con IA (esto puede tomar un momento)...")
            response = self.modelo.generate_content(prompt)
            plan = response.text
            
            # Limpiar formato markdown si lo hay
            plan = self._limpiar_formato(plan)
            
            print("   ✅ Plan generado exitosamente")
            return plan
            
        except Exception as e:
            print(f"   ❌ Error generando plan: {e}")
            return self._generar_plan_fallback(metadatos)
    
    def _limpiar_respuesta_json(self, texto: str) -> str:
        """Limpia la respuesta de la IA para obtener JSON válido."""
        texto = texto.strip()
        if texto.startswith("```"):
            lineas = texto.split("\n")
            lineas = [l for l in lineas if not l.strip().startswith("```")]
            texto = "\n".join(lineas)
        return texto
    
    def _limpiar_formato(self, texto: str) -> str:
        """Elimina formato markdown del texto."""
        # Eliminar negritas
        texto = re.sub(r'\*\*([^*]+)\*\*', r'\1', texto)
        # Eliminar cursivas
        texto = re.sub(r'\*([^*]+)\*', r'\1', texto)
        # Eliminar headers markdown
        texto = re.sub(r'^#+\s*', '', texto, flags=re.MULTILINE)
        # Eliminar bloques de código
        texto = re.sub(r'```[^`]*```', '', texto)
        return texto
    
    def _generar_plan_fallback(self, metadatos: Dict) -> str:
        """Genera un plan básico si falla la IA."""
        return f"""
Titulo de la Prueba: {metadatos.get('titulo', 'Plan de Prueba')}
Descripcion General: Plan de prueba generado con información limitada.

===============================================
Metadatos de la Prueba
===============================================
(Error al generar - revisar conexión con IA)

===============================================
Plan de Prueba Estructurado
===============================================

Etapa 1 - Introduccion

P1:
    Objetivo: Dar la bienvenida al participante
    Pregunta: Bienvenido/a a esta prueba de usabilidad. A continuacion le pediremos que realice algunas tareas sencillas.
    Formato: contexto
    Justificacion del Formato: Necesario para situar al usuario.

(Plan incompleto - ejecutar nuevamente)
"""
    
    def guardar_plan(self, plan: str, nombre_archivo: str = None) -> str:
        """Guarda el plan de prueba en un archivo."""
        if not nombre_archivo:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            nombre_archivo = f"PlanPrueba_{timestamp}.txt"
        
        try:
            with open(nombre_archivo, 'w', encoding='utf-8') as f:
                f.write(plan)
            print(f"\n✅ Plan guardado: {nombre_archivo}")
            return nombre_archivo
        except Exception as e:
            print(f"❌ Error guardando: {e}")
            return None
    
    def ejecutar(self, ruta_brief: str, figma_url: str = None) -> str:
        """
        Ejecuta el proceso completo de generación del Plan de Prueba.
        """
        print("\n" + "="*70)
        print("🧪 AGENTE ESTRUCTURADOR INTEGRAL - Community Tester")
        print("="*70)
        
        # 1. Leer y analizar brief
        brief = self.leer_brief(ruta_brief)
        if not brief:
            return None
        
        # 2. Obtener pantallas de Figma (opcional)
        pantallas = []
        if figma_url:
            pantallas = self.obtener_pantallas_figma(figma_url)
        
        # 3. Generar plan de prueba
        plan = self.generar_plan_prueba(brief, pantallas)
        
        # 4. Guardar plan
        archivo = self.guardar_plan(plan)
        
        print("\n" + "="*70)
        print("✅ PROCESO COMPLETADO")
        print("="*70)
        
        return archivo


# =============================================================================
# INTERFAZ DE LÍNEA DE COMANDOS
# =============================================================================

def obtener_link_figma() -> str:
    """Solicita el link de Figma al usuario."""
    print("\n" + "-"*70)
    print("🎨 CONFIGURACIÓN DE FIGMA")
    print("-"*70)
    print("\nFormatos soportados:")
    print("  - https://www.figma.com/file/ABC123/Mi-Proyecto")
    print("  - https://www.figma.com/proto/ABC123/Mi-Proyecto")
    print("  - https://www.figma.com/design/ABC123/Mi-Proyecto")
    print("\n(Presiona ENTER para omitir Figma)")
    
    link = input("\n📋 Pega el link de Figma: ").strip()
    return link if link else None


def menu_principal():
    """Muestra el menú principal."""
    print("\n" + "="*70)
    print("🧪 AGENTE ESTRUCTURADOR INTEGRAL")
    print("   Community Tester - Generador de Planes de Prueba")
    print("="*70)
    print("\nOpciones:")
    print("  1. Generar Plan de Prueba (Brief + Figma)")
    print("  2. Generar Plan de Prueba (Solo Brief)")
    print("  3. Salir")
    print("-"*70)
    
    return input("\n👉 Selecciona opción (1-3): ").strip()


def main():
    """Función principal."""
    agente = AgentePreprueba()
    
    while True:
        opcion = menu_principal()
        
        if opcion == "1":
            # Con Figma
            print("\n📄 GENERAR PLAN DE PRUEBA (Brief + Figma)")
            brief_path = input("\n📖 Ruta del brief: ").strip()
            
            if not brief_path or not os.path.exists(brief_path):
                print("❌ Archivo no encontrado")
                continue
            
            figma_url = obtener_link_figma()
            agente.ejecutar(brief_path, figma_url)
            
        elif opcion == "2":
            # Solo Brief
            print("\n📄 GENERAR PLAN DE PRUEBA (Solo Brief)")
            brief_path = input("\n📖 Ruta del brief: ").strip()
            
            if not brief_path or not os.path.exists(brief_path):
                print("❌ Archivo no encontrado")
                continue
            
            agente.ejecutar(brief_path)
            
        elif opcion == "3":
            print("\n👋 ¡Hasta luego!")
            break
        
        else:
            print("\n❌ Opción no válida")
        
        input("\n📌 Presiona ENTER para continuar...")


if __name__ == "__main__":
    main()
