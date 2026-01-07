# Manual de Usuario - Agente Preprueba
## Community Tester - Generador de Planes de Prueba de Usabilidad

---

## 📋 Índice

1. [Descripción General](#1-descripción-general)
2. [Requisitos Previos](#2-requisitos-previos)
3. [Instalación y Configuración](#3-instalación-y-configuración)
4. [Cómo Ejecutar el Agente](#4-cómo-ejecutar-el-agente)
5. [Opciones del Menú](#5-opciones-del-menú)
6. [Preparar el Brief de Entrada](#6-preparar-el-brief-de-entrada)
7. [Integración con Figma](#7-integración-con-figma)
8. [Estructura del Plan de Prueba Generado](#8-estructura-del-plan-de-prueba-generado)
9. [Formatos de Preguntas Disponibles](#9-formatos-de-preguntas-disponibles)
10. [Conocimiento Base del Agente](#10-conocimiento-base-del-agente)
11. [Ejemplos de Uso](#11-ejemplos-de-uso)
12. [Solución de Problemas](#12-solución-de-problemas)

---

## 1. Descripción General

El **Agente Preprueba** es una herramienta automatizada que genera **Planes de Prueba de Usabilidad** completos y profesionales. Utiliza inteligencia artificial (Google Gemini) para analizar un brief de proyecto y, opcionalmente, las pantallas de un prototipo de Figma.

### ¿Qué hace el agente?

- Lee y analiza el brief del proyecto
- Extrae metadatos automáticamente (título, hipótesis, objetivos, dolores, etc.)
- Conecta con Figma para obtener las pantallas del prototipo (opcional)
- Genera un Plan de Prueba estructurado con preguntas basadas en:
  - Ergonomía Física
  - Ergonomía Cognitiva
  - Técnicas de Innovación SIT
- Guarda el plan en un archivo `.txt` con marca de tiempo

---

## 2. Requisitos Previos

### Software necesario

| Requisito | Descripción |
|-----------|-------------|
| Python 3.8+ | Lenguaje de programación |
| pip | Gestor de paquetes de Python |

### Librerías de Python requeridas

```
google-generativeai
python-dotenv
requests
```

### APIs necesarias

| API | Variable de entorno | Obligatoria |
|-----|---------------------|-------------|
| Google Gemini | `GEMINI_API_KEY` | ✅ Sí |
| Figma | `FIGMA_TOKEN` | ❌ No (opcional) |

---

## 3. Instalación y Configuración

### Paso 1: Instalar dependencias

```bash
pip install google-generativeai python-dotenv requests
```

### Paso 2: Crear archivo `.env`

Crea un archivo llamado `.env` en la misma carpeta del agente con el siguiente contenido:

```env
GEMINI_API_KEY=tu_api_key_de_gemini
FIGMA_TOKEN=tu_token_de_figma
```

### Paso 3: Obtener las API Keys

#### Google Gemini API Key:
1. Ve a [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Crea una cuenta o inicia sesión
3. Genera una nueva API Key
4. Copia la clave en el archivo `.env`

#### Figma Token (opcional):
1. Ve a [Figma Account Settings](https://www.figma.com/settings)
2. En la sección "Personal access tokens", genera un nuevo token
3. Copia el token en el archivo `.env`

---

## 4. Cómo Ejecutar el Agente

### Desde la línea de comandos

```bash
cd c:\Users\andres.machado\Desktop\IA_Tester\agente_constructor
python agente_preprueba.py
```

### Lo que verás al iniciar

```
======================================================================
🧪 AGENTE ESTRUCTURADOR INTEGRAL
   Community Tester - Generador de Planes de Prueba
======================================================================

Opciones:
  1. Generar Plan de Prueba (Brief + Figma)
  2. Generar Plan de Prueba (Solo Brief)
  3. Salir
----------------------------------------------------------------------

👉 Selecciona opción (1-3):
```

---

## 5. Opciones del Menú

### Opción 1: Generar Plan de Prueba (Brief + Figma)

Usa esta opción cuando tengas:
- ✅ Un archivo de brief (.txt)
- ✅ Un enlace a un prototipo de Figma

**Flujo:**
1. Ingresa la ruta del archivo brief
2. Pega el enlace de Figma
3. El agente procesa y genera el plan

### Opción 2: Generar Plan de Prueba (Solo Brief)

Usa esta opción cuando tengas:
- ✅ Un archivo de brief (.txt)
- ❌ Sin prototipo de Figma disponible

**Flujo:**
1. Ingresa la ruta del archivo brief
2. El agente genera el plan basándose solo en el brief

### Opción 3: Salir

Cierra el programa.

---

## 6. Preparar el Brief de Entrada

El brief es el documento de entrada principal. Debe ser un archivo `.txt` con la información del proyecto.

### Información recomendada en el brief

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| Título | Nombre de la prueba | "Prueba de Usabilidad - App Voluntariado" |
| Descripción | Objetivo general | "Evaluar la experiencia del usuario..." |
| Hipótesis | Lo que se quiere validar | "Los usuarios pueden completar el registro en menos de 3 minutos" |
| Flujo Digital | Producto o flujo a evaluar | "App Móvil de Voluntariado" |
| Autor | Quién diseña la prueba | "Juan Pérez" |
| Compañía | Organización | "Community Tester" |
| Línea de Negocio | Área del negocio | "Impacto Social" |
| Tipo de Prueba | Moderada o no moderada | "No moderada" |
| Fecha Inicio/Fin | Período de la prueba | "2026-01-15 a 2026-01-22" |
| Objetivos | Lista de objetivos | "1. Evaluar registro, 2. Medir navegación" |
| Dolores | Problemas identificados | "Alta tasa de abandono en registro" |
| Contexto Usuario | Perfil del usuario | "Jóvenes entre 18-30 años interesados en voluntariado" |

### Ejemplo de brief

```
BRIEF DE PRUEBA DE USABILIDAD

Título: Prueba de Usabilidad - Plataforma de Voluntariado Digital
Descripción: Evaluar la experiencia de usuarios al registrarse y buscar actividades de voluntariado.

Hipótesis: Los usuarios pueden encontrar una actividad de voluntariado y completar su registro en menos de 5 minutos sin ayuda externa.

Flujo Digital: App Voluntariado Connect
Autor: María García
Compañía: ONG Solidaridad Digital
Línea de Negocio: Tecnología Social
Tipo de Prueba: No moderada

Fechas:
- Inicio: 2026-01-20
- Fin: 2026-01-27

Objetivos:
1. Evaluar la facilidad del proceso de registro
2. Medir la comprensión de las categorías de voluntariado
3. Identificar puntos de fricción en la navegación
4. Validar la claridad de los llamados a la acción

Dolores identificados:
1. Alta tasa de abandono en el formulario de registro
2. Usuarios no encuentran actividades de su interés
3. Confusión con las categorías de voluntariado

Pantallas a evaluar:
- Home
- Registro
- Búsqueda de actividades
- Detalle de actividad
- Confirmación de inscripción

Contexto del usuario:
Jóvenes universitarios entre 18-28 años, con interés en causas sociales, familiarizados con aplicaciones móviles y redes sociales.
```

---

## 7. Integración con Figma

### Formatos de URL soportados

El agente acepta los siguientes formatos de enlaces de Figma:

| Formato | Ejemplo |
|---------|---------|
| File | `https://www.figma.com/file/ABC123/Mi-Proyecto` |
| Proto | `https://www.figma.com/proto/ABC123/Mi-Proyecto` |
| Design | `https://www.figma.com/design/ABC123/Mi-Proyecto` |

### ¿Qué información extrae de Figma?

- Nombre del archivo
- Pantallas principales (frames de nivel superior)
- Nombres de las pantallas para contextualizar las preguntas

### Sin Figma Token

Si no tienes configurado el `FIGMA_TOKEN`, el agente funcionará en **modo simulado** y generará el plan basándose únicamente en la información del brief.

---

## 8. Estructura del Plan de Prueba Generado

El plan de prueba generado sigue esta estructura:

```
Título de la Prueba: [Nombre de la prueba]
Descripción General: [Resumen del objetivo]

===============================================
Metadatos de la Prueba
===============================================
Flujo Digital: [Nombre del producto]
Autor: [Nombre del autor]
Compañía: [Nombre de la compañía]
Línea de Negocio: [Área]
Tipo de Prueba: [Moderada/No moderada]
Tallaje Estimado: [S/M/L]
Fecha Inicio: [Fecha]
Fecha Fin: [Fecha]

===============================================
Contexto del Brief
===============================================
[Explicación de la hipótesis y contexto]

===============================================
Plan de Prueba Estructurado
===============================================

Etapa 1 – [Nombre Descriptivo]

P1:
Objetivo: [Objetivo técnico interno]
Pregunta: [Pregunta para el usuario]
Formato: [tipo de formato]
Justificación del Formato: [Explicación técnica]
```

### Sistema de Tallaje

El agente calcula automáticamente el tamaño de la prueba:

| Tallaje | Preguntas | Condición |
|---------|-----------|-----------|
| S (Small) | 5-8 preguntas | ≤3 objetivos + dolores |
| M (Medium) | 9-15 preguntas | 4-6 objetivos + dolores |
| L (Large) | 16+ preguntas | >6 objetivos + dolores |

---

## 9. Formatos de Preguntas Disponibles

| Formato | Uso | Ejemplo |
|---------|-----|---------|
| `texto` | Respuestas abiertas y opiniones detalladas | "¿Qué mejoraría usted de esta pantalla?" |
| `escala_likert` | Medir satisfacción o dificultad (1-5) | "Califique de 1 a 5, donde 1 es 'Muy difícil' y 5 es 'Muy fácil'" |
| `audio` | Capturar pensamientos en voz alta | "Por favor, describa en voz alta lo que está pensando" |
| `pantalla` | Grabar pantalla para observar comportamiento | "Esta pregunta grabará su pantalla para ver cómo navega" |
| `card_sorting` | Evaluar arquitectura de información | Incluye Categorías y Tarjetas |
| `diferencia_semantica` | Medir percepciones bipolares | Incluye par de opuestos (Fácil vs. Difícil) |
| `click` | Identificar zonas de interés | "¿Dónde haría clic usted para...?" |
| `contexto` | Introducciones y transiciones | No cuenta como pregunta para el tallaje |

---

## 10. Conocimiento Base del Agente

El agente utiliza conocimiento especializado en tres áreas:

### 10.1 Ergonomía Física

- **Perceptibilidad**: Contraste, legibilidad, iconos reconocibles
- **Operabilidad (Ley de Fitts)**: Tamaño táctil ≥44x44px, zonas accesibles
- **Consistencia Visual**: Elementos similares, colores con significado
- **Accesibilidad Física**: Uso con una mano, alternativas para limitaciones

### 10.2 Ergonomía Cognitiva

- **Carga Cognitiva**: Información manejable, instrucciones claras
- **Modelo Mental**: Flujo predecible, términos familiares
- **Claridad**: Mensajes entendibles, errores explicativos
- **Eficiencia**: Pasos mínimos, atajos para usuarios frecuentes

### 10.3 Innovación SIT (Systematic Inventive Thinking)

| Técnica | Descripción | Pregunta guía |
|---------|-------------|---------------|
| Sustracción | Eliminar componentes no esenciales | "¿Qué pasaría si eliminamos...?" |
| Multiplicación | Duplicar con variación | "¿Qué tal múltiples formas de...?" |
| División | Separar en partes | "¿Qué tal si dividimos en pasos?" |
| Unificación | Asignar nueva función a elemento existente | "¿Qué elemento podría también...?" |
| Dependencia de Atributos | Relacionar atributos independientes | "¿Qué si cambiara según...?" |

---

## 11. Ejemplos de Uso

### Ejemplo 1: Generar plan con Brief y Figma

```
👉 Selecciona opción (1-3): 1

📄 GENERAR PLAN DE PRUEBA (Brief + Figma)

📖 Ruta del brief: ejemplo preprueba.txt

----------------------------------------------------------------------
🎨 CONFIGURACIÓN DE FIGMA
----------------------------------------------------------------------

📋 Pega el link de Figma: https://www.figma.com/file/ABC123/Mi-App

======================================================================
🧪 AGENTE ESTRUCTURADOR INTEGRAL - Community Tester
======================================================================

📖 Leyendo brief: ejemplo preprueba.txt
   Analizando contenido del brief...

🎨 Conectando con Figma...
   File key: ABC123
   Archivo: Mi-App
   Pantallas encontradas: 12

📝 Generando Plan de Prueba...
   Procesando con IA (esto puede tomar un momento)...
   ✅ Plan generado exitosamente

✅ Plan guardado: PlanPrueba_2026-01-07_143022.txt

======================================================================
✅ PROCESO COMPLETADO
======================================================================
```

### Ejemplo 2: Generar plan solo con Brief

```
👉 Selecciona opción (1-3): 2

📄 GENERAR PLAN DE PRUEBA (Solo Brief)

📖 Ruta del brief: ejemplo preprueba.txt

======================================================================
🧪 AGENTE ESTRUCTURADOR INTEGRAL - Community Tester
======================================================================

📖 Leyendo brief: ejemplo preprueba.txt
   Analizando contenido del brief...

📝 Generando Plan de Prueba...
   Procesando con IA (esto puede tomar un momento)...
   ✅ Plan generado exitosamente

✅ Plan guardado: PlanPrueba_2026-01-07_143522.txt

======================================================================
✅ PROCESO COMPLETADO
======================================================================
```

---

## 12. Solución de Problemas

### Error: "GEMINI_API_KEY no encontrada en .env"

**Causa**: No existe el archivo `.env` o la variable no está definida.

**Solución**:
1. Crea un archivo `.env` en la carpeta del agente
2. Agrega la línea: `GEMINI_API_KEY=tu_api_key`

### Error: "Archivo no encontrado"

**Causa**: La ruta del brief es incorrecta.

**Solución**:
- Verifica que el archivo exista
- Usa rutas absolutas (ej: `C:\Users\...\mi_brief.txt`)
- O rutas relativas desde la carpeta del agente

### Error: "URL de Figma no válida"

**Causa**: El formato del enlace de Figma no es reconocido.

**Solución**: Usa uno de estos formatos:
- `https://www.figma.com/file/XXXXX/Nombre`
- `https://www.figma.com/proto/XXXXX/Nombre`
- `https://www.figma.com/design/XXXXX/Nombre`

### Error: "FIGMA_TOKEN no configurado"

**Causa**: No está definido el token de Figma en `.env`.

**Solución**:
- Agrega `FIGMA_TOKEN=tu_token` al archivo `.env`
- O continúa sin Figma (el plan se generará solo con el brief)

### Error de codificación al leer el brief

**Causa**: El archivo tiene una codificación no soportada.

**Solución**: 
- Guarda el archivo como UTF-8
- El agente intenta automáticamente: UTF-8, Latin-1, CP1252, ISO-8859-1

### El plan generado está incompleto

**Causa**: Error en la conexión con la IA.

**Solución**:
1. Verifica tu conexión a internet
2. Verifica que tu API Key de Gemini sea válida
3. Ejecuta el agente nuevamente

---

## 📁 Archivos de Salida

Los planes generados se guardan con el formato:

```
PlanPrueba_YYYY-MM-DD_HHMMSS.txt
```

Por ejemplo: `PlanPrueba_2026-01-07_143022.txt`

---

## 📞 Soporte

Para dudas o problemas adicionales, contacta al equipo de Community Tester.

---

**Versión del Manual**: 1.0  
**Última actualización**: Enero 2026  
**Autor**: Community Tester
