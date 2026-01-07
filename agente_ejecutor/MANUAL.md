# Manual de uso y entendimiento del agente

## 1. Proposito
Agente automatizado para completar formularios web de pruebas de usabilidad en la plataforma Community Tester. Usa Playwright para controlar el navegador y Gemini para generar respuestas coherentes.

## 2. Archivos clave
- [agente_ejecutor.py](agente_ejecutor.py): logica completa del agente (clase `AgenteEjecutor` y `main()`).
- [run_test.py](run_test.py): punto de entrada sencillo que llama a `main()`.
- `.env` (en el directorio padre): debe contener `GEMINI_API_KEY` y, si se desea, variables de configuracion de la plataforma.

## 3. Requisitos previos
- Python 3.10+ instalado.
- Dependencias: `playwright`, `google-generativeai`, `python-dotenv`. Instalar con `pip install playwright google-generativeai python-dotenv`.
- Instalar navegadores de Playwright (una sola vez): `python -m playwright install chromium`.
- Chrome de escritorio opcional: el agente lo usa si esta disponible; si no, cae a Chromium de Playwright.
- Archivo `.env` en el directorio padre de esta carpeta con la clave de Gemini (`GEMINI_API_KEY`).

## 4. Como se ejecuta
1) Abrir una terminal en esta carpeta.
2) Ejecutar: `python run_test.py`.
3) El script:
   - Configura el encoding en Windows.
   - Importa y ejecuta `main()` desde el agente.

## 5. Flujo interno del agente (resumen)
1) Inicializacion: carga variables de entorno con `dotenv`, configura Gemini con `GEMINI_API_KEY`, prepara Playwright.
2) Login: abre el navegador (prioriza Chrome del sistema), navega a la URL de la plataforma y busca campos de email/clave y boton de login.
3) Busqueda de pruebas: localiza botones como "Comenzar" y extrae la URL de la prueba activa.
4) Ejecucion de la prueba: navega a la URL del formulario, analiza campos (texto, textarea, radio, checkbox, select, escalas), y genera respuestas con Gemini usando un contexto por defecto.
5) Relleno: completa los campos detectados y, opcionalmente, envia el formulario buscando botones de envio comunes.
6) Resultados: imprime en consola el estado de cada paso (login, pruebas encontradas, preguntas completadas, envio).

## 6. Componentes principales (en agente_ejecutor.py)
- Clase `AgenteEjecutor`: agrupa todo el flujo. Metodos destacados:
  - `iniciar_navegador()`: lanza Chrome del sistema o Chromium de Playwright.
  - `login_plataforma()`: realiza login automatico.
  - `buscar_pruebas_activas()`: detecta pruebas disponibles en la plataforma.
  - `ejecutar_prueba_plataforma()`: orquesta el flujo completo de inicio a fin.
  - `analizar_formulario()`, `generar_respuestas()`, `completar_formulario()`, `enviar_formulario()`: pipeline de interaccion con formularios.
- `main()`: interfaz automatica que crea el agente, ejecuta el flujo y cierra el navegador.

## 7. Por que Python
- Playwright tiene una API madura y estable en Python para automatizacion de navegadores.
- Ecosistema de IA accesible: el SDK oficial de Gemini esta disponible en Python y se integra facilmente con `google-generativeai`.
- Rapidez de desarrollo y legibilidad para scripts de automatizacion y glue code.
- Portabilidad: mismo script funciona en Windows, macOS y Linux con cambios minimos.

## 8. Configuracion y ajustes rapidos
Las credenciales y opciones (headless, idioma, timeouts) se pueden fijar en variables de entorno o directamente en la inicializacion del agente dentro de [agente_ejecutor.py](agente_ejecutor.py) (atributos `platform_url`, `platform_email`, `platform_password`, flags de headless y tiempo de espera).

## 9. Troubleshooting basico
- Si Playwright no abre, reinstalar navegadores: `python -m playwright install chromium`.
- Si falta la clave de Gemini, el agente lanza `ValueError`: crear `.env` con `GEMINI_API_KEY`.
- Si Chrome corporativo no esta instalado, el agente automaticamente usa Chromium.

## 10. Como se creo (vision general)
- Se desarrollo como script de automatizacion de pruebas para la plataforma Community Tester.
- Se eligio Playwright para robustez en deteccion de elementos y compatibilidad con Chrome/Chromium.
- Se integro Gemini para generar respuestas textuales coherentes y contextuales al formulario.
- Se estructuro en una unica clase (`AgenteEjecutor`) con funciones separadas para login, deteccion de pruebas, analisis de formularios y completado de campos, buscando mantener el flujo compacto y mantenible.
