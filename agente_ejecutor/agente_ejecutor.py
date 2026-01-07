"""
================================================================================
AGENTE EJECUTOR DE PRUEBAS - Community Tester
================================================================================
Agente que puede acceder a formularios web y completarlos con coherencia.
Usa Playwright para automatización y Gemini para generar respuestas inteligentes.

Autor: Community Tester
Versión: 2.0 (Playwright)
================================================================================
"""

import os
import sys
import time
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

# Agregar path del padre para acceder al .env
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import google.generativeai as genai

# Cargar .env desde el directorio padre
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)


class AgenteEjecutor:
    """
    Agente que ejecuta pruebas en formularios web.
    Puede acceder a URLs, identificar campos y completarlos inteligentemente.
    Usa Playwright para mayor compatibilidad y robustez.
    """
    
    def __init__(self):
        """Inicializa el agente con las APIs."""
        print("\n🤖 Inicializando Agente Ejecutor...")
        
        # Configurar Gemini para respuestas inteligentes
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.modelo = genai.GenerativeModel('gemini-2.0-flash')
            print("   ✅ Gemini configurado")
        else:
            raise ValueError("❌ GEMINI_API_KEY no encontrada en .env")
        
        # Playwright se inicializa cuando se necesita
        self.playwright = None
        self.browser = None
        self.page = None
        self.navegador_iniciado = False
        self.logged_in = False
        
       
       
        self.platform_url = "https://community-wheat-one.vercel.app/"
        self.platform_email = "tester@gmail.com"
        self.platform_password = "Prueba123"
    
    def iniciar_navegador(self, headless: bool = False):
        """
        Inicia el navegador priorizando Chrome del sistema (perfil corporativo).
        Si no se encuentra Chrome, cae a Chromium de Playwright.
        """
        try:
            from playwright.sync_api import sync_playwright
            import os

            print("\n🌐 Iniciando navegador (prioridad: Chrome del Sistema)...")

            self.playwright = sync_playwright().start()

            chrome_paths = [
                r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                r"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                os.path.expandvars(r"%ProgramFiles%\\Google\\Chrome\\Application\\chrome.exe"),
                os.path.expandvars(r"%ProgramFiles(x86)%\\Google\\Chrome\\Application\\chrome.exe"),
                os.path.expandvars(r"%LocalAppData%\\Google\\Chrome\\Application\\chrome.exe"),
            ]

            chrome_found = None
            for path in chrome_paths:
                if path and os.path.exists(path):
                    chrome_found = path
                    print(f"   ✅ Chrome del Sistema encontrado en: {path}")
                    break

            if chrome_found:
                print("   🔄 Lanzando Chrome del Sistema...")
                try:
                    self.browser = self.playwright.chromium.launch(
                        executable_path=chrome_found,
                        channel=None,  # usamos la ruta explícita
                        headless=headless,
                        args=[
                            '--no-default-browser-check',
                            '--no-first-run',
                            '--disable-sync',
                            '--disable-notifications',
                            '--disable-popup-blocking',
                            '--disable-infobars',
                            '--lang=es',
                        ],
                    )
                    print("   ✅ Chrome del Sistema iniciado correctamente")
                except Exception as chrome_error:
                    print(f"   ⚠️ Error lanzando Chrome: {str(chrome_error)[:120]}")
                    print("   🔄 Usando Chromium de Playwright como fallback...")
                    self.browser = self.playwright.chromium.launch(
                        headless=headless,
                        args=['--start-maximized', '--disable-notifications'],
                    )
                    print("   ✅ Chromium iniciado")
            else:
                print("   ⚠️ Chrome del Sistema no encontrado, usando Chromium...")
                self.browser = self.playwright.chromium.launch(
                    headless=headless,
                    args=['--start-maximized', '--disable-notifications'],
                )
                print("   ✅ Chromium iniciado")

            context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                locale='es-ES',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            )

            self.page = context.new_page()
            self.navegador_iniciado = True

            return True

        except Exception as e:
            print(f"   ❌ Error iniciando navegador: {e}")
            return False
    
    def cerrar_navegador(self):
        """Cierra el navegador."""
        try:
            if self.page:
                self.page.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            self.navegador_iniciado = False
            self.logged_in = False
            print("   🔒 Navegador cerrado")
        except Exception as e:
            print(f"   ⚠️ Error cerrando navegador: {e}")
    
    def login_plataforma(self) -> bool:
        """
        Realiza login en la plataforma Community Tester.
        Optimizado para manejar Figma embebido y navegación automática.
        
        Returns:
            True si el login fue exitoso
        """
        if not self.navegador_iniciado:
            # headless=False para ver la ventana y forzar perfil corporativo de Chrome
            if not self.iniciar_navegador(headless=False):
                return False
        
        if self.logged_in:
            print("   ✅ Ya está logueado")
            return True
        
        try:
            print(f"\n🔐 Iniciando sesión en la plataforma Community Tester...")
            print(f"   📍 URL: {self.platform_url}")
            
            # Navegar a la plataforma con más tiempo de espera
            self.page.goto(self.platform_url, wait_until='domcontentloaded', timeout=30000)
            time.sleep(3)
            
            # Esperar a que jQuery esté listo si existe
            try:
                self.page.wait_for_load_state("networkidle", timeout=5000)
            except:
                pass
            
            current_url = self.page.url
            print(f"   📍 URL actual: {current_url}")
            
            # PASO 1: Buscar campos de login
            email_field = None
            password_field = None
            
            # Selectores comunes para campos de email
            email_selectors = [
                'input[type="email"]',
                'input[name="email"]',
                'input[id*="email"]',
                'input[name="user_email"]',
                'input[name="username"]',
                'input[placeholder*="email" i]',
                'input[placeholder*="usuario" i]',
                '#email',
                '#user-email',
            ]
            
            for selector in email_selectors:
                try:
                    field = self.page.locator(selector).first
                    if field.is_visible(timeout=2000):
                        email_field = field
                        print(f"   ✅ Campo email encontrado: {selector}")
                        break
                except:
                    continue
            
            # Si no encontramos campo de email, verificar si ya estamos logueados
            if not email_field:
                print("   ⚠️ No se encontró campo de email - verificando sesión activa...")
                
                # Verificar si hay indicadores de sesión activa
                page_html = self.page.content().lower()
                logged_indicators = [
                    'logout', 'cerrar sesión', 'dashboard', 'mis pruebas',
                    'panel de control', 'mi cuenta', 'perfil'
                ]
                
                for indicator in logged_indicators:
                    if indicator in page_html:
                        print(f"   ✅ Sesión activa detectada ({indicator})")
                        self.logged_in = True
                        return True
                
                # Esperar a que cargue completamente
                time.sleep(3)
                email_field = self.page.locator('input[type="email"]').first
                if not email_field.is_visible(timeout=1000):
                    print("   ❌ No se encontraron campos de login")
                    return False
            
            # PASO 2: Buscar campo de contraseña
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[id*="password"]',
                '#password',
                '#user-password',
            ]
            
            for selector in password_selectors:
                try:
                    field = self.page.locator(selector).first
                    if field.is_visible(timeout=2000):
                        password_field = field
                        print(f"   ✅ Campo contraseña encontrado: {selector}")
                        break
                except:
                    continue
            
            if not password_field:
                print("   ❌ No se encontró campo de contraseña")
                return False
            
            # PASO 3: Llenar credenciales
            print(f"   📧 Ingresando email: {self.platform_email}")
            email_field.click()
            time.sleep(0.3)
            email_field.fill("")
            time.sleep(0.2)
            email_field.type(self.platform_email, delay=50)
            time.sleep(0.5)
            
            print("   🔑 Ingresando contraseña...")
            password_field.click()
            time.sleep(0.3)
            password_field.fill("")
            time.sleep(0.2)
            password_field.type(self.platform_password, delay=50)
            time.sleep(0.5)
            
            # PASO 4: Buscar y hacer clic en botón de login
            login_button = None
            login_selectors = [
                'button[type="submit"]',
                'button:has-text("Iniciar sesión")',
                'button:has-text("Ingresar")',
                'button:has-text("Iniciar")',
                'button:has-text("Login")',
                'button:has-text("Entrar")',
                'button:has-text("Sign in")',
                'input[type="submit"]',
            ]
            
            for selector in login_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if btn.is_visible(timeout=1000):
                        login_button = btn
                        print(f"   ✅ Botón de login encontrado: {selector}")
                        break
                except:
                    continue
            
            if login_button:
                print("   ▶️ Haciendo clic en botón de login...")
                login_button.scroll_into_view_if_needed()
                time.sleep(0.3)
                login_button.click()
                time.sleep(4)  # Esperar respuesta del servidor
                print("   ⏳ Esperando confirmación de login...")
            else:
                # Intentar presionar Enter como último recurso
                print("   ⏳ Intentando login con ENTER...")
                password_field.press('Enter')
                time.sleep(4)
            
            # PASO 5: Verificar login exitoso
            new_url = self.page.url
            print(f"   📍 URL después de login: {new_url}")
            
            # Verificar cambio de URL
            if new_url != self.platform_url and 'login' not in new_url.lower():
                print(f"   ✅ Login exitoso! Redirección detectada")
                self.logged_in = True
                return True
            
            # Verificar contenido de página
            page_content = self.page.content().lower()
            if any(text in page_content for text in ['dashboard', 'mis pruebas', 'panel', 'logout']):
                print(f"   ✅ Login exitoso! Contenido verificado")
                self.logged_in = True
                return True
            
            # Esperar un poco más y verificar de nuevo
            time.sleep(2)
            page_content = self.page.content().lower()
            if any(text in page_content for text in ['dashboard', 'mis pruebas', 'panel', 'logout']):
                print(f"   ✅ Login exitoso! (verificado en segundo intento)")
                self.logged_in = True
                return True
            
            # Verificar si hay errores visibles
            try:
                error_msg = self.page.locator('[role="alert"], .error, .alert-danger').first
                if error_msg.is_visible(timeout=1000):
                    error_text = error_msg.inner_text()
                    print(f"   ❌ Error en login: {error_text[:100]}")
                    return False
            except:
                pass
            
            print(f"   ⚠️ No se pudo confirmar login, continuando de todas formas...")
            self.logged_in = True
            return True
            
        except Exception as e:
            print(f"   ❌ Error en login: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def buscar_pruebas_activas(self) -> List[Dict]:
        """
        Busca las pruebas activas disponibles en la plataforma.
        Intenta múltiples estrategias para encontrar pruebas.
        
        Returns:
            Lista de pruebas encontradas con su información
        """
        if not self.logged_in:
            if not self.login_plataforma():
                return []
        
        print("\n🔍 Buscando pruebas activas...")
        pruebas = []
        
        try:
            time.sleep(2)  # Esperar carga de la página
            
            # Estrategia 1: Buscar botones "Comenzar"
            botones_comenzar = self.page.locator('button:has-text("Comenzar")').all()
            
            if botones_comenzar:
                print(f"   ✅ Encontrados {len(botones_comenzar)} botones 'Comenzar'")
            
            for i, btn in enumerate(botones_comenzar):
                if btn.is_visible():
                    try:
                        # Intentar obtener el contenedor padre (la card de la prueba)
                        card_text = btn.evaluate("""
                            el => {
                                let parent = el.parentElement;
                                for (let i = 0; i < 5; i++) {
                                    if (parent && parent.innerText && parent.innerText.length > 50) {
                                        return parent.innerText;
                                    }
                                    parent = parent?.parentElement;
                                }
                                return '';
                            }
                        """)
                        
                        # Extraer título (primera línea significativa)
                        lineas = [l.strip() for l in card_text.split('\n') if l.strip() and len(l.strip()) > 3]
                        titulo = lineas[0] if lineas else f'Prueba {i+1}'
                        
                        # Limpiar título
                        if titulo in ['Disponible', 'Comenzar', 'Continuar']:
                            titulo = lineas[1] if len(lineas) > 1 else f'Prueba {i+1}'
                        
                        prueba = {
                            'titulo': titulo[:60],
                            'descripcion': card_text[:200] if card_text else '',
                            'boton_comenzar': btn
                        }
                        pruebas.append(prueba)
                        print(f"   ✅ Prueba encontrada: {titulo[:50]}")
                    except Exception as e:
                        pruebas.append({
                            'titulo': f'Prueba {i+1}',
                            'descripcion': '',
                            'boton_comenzar': btn
                        })
                        print(f"   ✅ Botón Comenzar encontrado #{i+1}")
            
            # Estrategia 2: Si no hay pruebas, buscar cualquier botón que se vea "activo"
            if not pruebas:
                print("   ⚠️ No se encontraron botones 'Comenzar', buscando alternativas...")
                
                # Buscar otros botones comunes
                otros_selectores = [
                    'button:has-text("Continuar")',
                    'button:has-text("Comenzar Prueba")',
                    'button:has-text("Start")',
                    'button:has-text("Begin")',
                    'a:has-text("Comenzar")',
                    'a:has-text("Continuar")',
                ]
                
                for selector in otros_selectores:
                    botones = self.page.locator(selector).all()
                    if botones:
                        print(f"   ✅ Encontrados: {selector} ({len(botones)} elementos)")
                        for i, btn in enumerate(botones[:3]):
                            if btn.is_visible():
                                pruebas.append({
                                    'titulo': f'Prueba {len(pruebas)+1}',
                                    'descripcion': '',
                                    'boton_comenzar': btn
                                })
                        if len(pruebas) > 0:
                            break
            
            # Estrategia 3: Ver TODO el HTML para debug
            if not pruebas:
                print("   📄 Analizando HTML completo...")
                contenido = self.page.content().lower()
                
                if 'prueba' in contenido or 'test' in contenido or 'usabilidad' in contenido:
                    print("   ✓ Página contiene referencias a pruebas")
                else:
                    print("   ✗ No se detectan referencias a pruebas en el HTML")
                
                # Guardar screenshot para debug
                try:
                    self.page.screenshot(path="screenshot_pruebas.png")
                    print("   📸 Captura guardada: screenshot_pruebas.png")
                except:
                    pass
            
            print(f"\n   📋 Total pruebas activas: {len(pruebas)}")
            return pruebas
            
        except Exception as e:
            print(f"   ❌ Error buscando pruebas: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def comenzar_prueba(self, prueba: Dict = None) -> bool:
        """
        Hace clic en "Comenzar" -> "Continuar" -> "Comenzar prueba" -> maneja permisos.
        
        Args:
            prueba: Diccionario con info de la prueba (opcional, si no se da toma la primera)
        
        Returns:
            True si se inició la prueba correctamente
        """
        try:
            # Paso 1: Hacer clic en "Comenzar"
            if prueba and 'boton_comenzar' in prueba:
                boton = prueba['boton_comenzar']
            else:
                boton = self.page.locator('button:has-text("Comenzar"), a:has-text("Comenzar")').first
            
            if boton and boton.is_visible():
                print("\n▶️ Paso 1: Clic en Comenzar...")
                boton.scroll_into_view_if_needed()
                time.sleep(0.5)
                boton.click()
                time.sleep(2)
                print(f"   ✅ Página de detalles cargada")
            else:
                print("   ❌ No se encontró botón Comenzar")
                return False
            
            # Paso 2: Hacer clic en "Continuar"
            continuar_btn = self.page.locator('button:has-text("Continuar")').first
            if continuar_btn and continuar_btn.is_visible(timeout=3000):
                print("   ▶️ Paso 2: Clic en Continuar...")
                continuar_btn.scroll_into_view_if_needed()
                time.sleep(0.5)
                continuar_btn.click()
                time.sleep(2)
                print(f"   ✅ Página de recomendaciones cargada")
            
            # Paso 3: Hacer clic en "Comenzar prueba"
            comenzar_prueba_btn = self.page.locator('button:has-text("Comenzar prueba")').first
            if comenzar_prueba_btn and comenzar_prueba_btn.is_visible(timeout=3000):
                print("   ▶️ Paso 3: Clic en Comenzar prueba...")
                comenzar_prueba_btn.scroll_into_view_if_needed()
                time.sleep(0.5)
                comenzar_prueba_btn.click()
                time.sleep(2)
            
            # Paso 4: Manejar modales de permisos (micrófono, cámara, pantalla, etc.)
            self._manejar_permisos()
            
            print(f"   ✅ Formulario de prueba listo")
            print(f"   📍 URL actual: {self.page.url}")
            return True
                
        except Exception as e:
            print(f"   ❌ Error iniciando prueba: {e}")
            return False
    
    def _manejar_permisos(self):
        """Maneja los modales de permisos y configuración (micrófono, cámara, pantalla, etc.)"""
        print("   🔐 Verificando permisos y configuración...")
        
        # Lista de botones para avanzar en modales de configuración (en orden de prioridad)
        botones_avanzar = [
            ('button:has-text("Permitir acceso")', 'Permitir acceso'),
            ('button:has-text("Probar micrófono")', 'Probar micrófono'),
            ('button:has-text("Probar cámara")', 'Probar cámara'),
            ('button:has-text("Detener grabación")', 'Detener grabación'),
            ('button:has-text("Detener")', 'Detener'),
            ('button:has-text("Continuar")', 'Continuar'),
            ('button:has-text("Siguiente")', 'Siguiente'),
            ('button:has-text("Aceptar")', 'Aceptar'),
            ('button:has-text("OK")', 'OK'),
            ('button:has-text("Listo")', 'Listo'),
            ('button:has-text("Confirmar")', 'Confirmar'),
            ('button:has-text("Empezar")', 'Empezar'),
            ('button:has-text("Comenzar")', 'Comenzar'),
        ]
        
        # Intentar avanzar en hasta 15 modales/pasos de configuración
        pasos_completados = 0
        for intento in range(15):
            boton_encontrado = False
            time.sleep(1.5)  # Esperar que cargue el modal
            
            # Primero verificar si hay una prueba de audio/grabación activa
            try:
                grabando = self.page.locator('text=Grabando').first
                if grabando.is_visible(timeout=500):
                    print(f"      🎤 Grabación detectada, esperando 3 segundos...")
                    time.sleep(3)  # Simular que se grabó algo
            except:
                pass
            
            for selector, nombre in botones_avanzar:
                try:
                    btn = self.page.locator(selector).first
                    if btn.is_visible(timeout=1000):
                        # Verificar que no sea un botón de cancelar
                        btn_text = btn.inner_text().lower()
                        if 'cancelar' in btn_text or 'cancel' in btn_text:
                            continue
                        
                        print(f"      ✅ Clic en '{nombre}'...")
                        btn.scroll_into_view_if_needed()
                        time.sleep(0.3)
                        btn.click()
                        time.sleep(1.5)
                        pasos_completados += 1
                        boton_encontrado = True
                        break
                except:
                    continue
            
            if not boton_encontrado:
                # Verificar si hay campos de formulario (significa que llegamos a las preguntas)
                try:
                    tiene_preguntas = self.page.locator('input[type="text"], textarea, [role="radio"], [role="checkbox"], input[type="range"]').count() > 0
                    # También verificar si hay texto que parece pregunta
                    page_content = self.page.content().lower()
                    tiene_contenido_pregunta = any(p in page_content for p in ['pregunta', 'question', '¿', 'responda', 'seleccione'])
                    
                    if tiene_preguntas or tiene_contenido_pregunta:
                        print(f"      ✅ Formulario de preguntas detectado")
                        break
                except:
                    pass
                
                # No hay más modales después de 2 intentos sin encontrar botón
                if intento >= 2 and not boton_encontrado:
                    break
        
        if pasos_completados > 0:
            print(f"   ✅ {pasos_completados} paso(s) de configuración completado(s)")
        else:
            print(f"   ℹ️ No se encontraron modales de configuración")
    
    def ejecutar_prueba_plataforma(self) -> Dict:
        """
        Proceso completo: login -> buscar prueba -> comenzar -> completar prueba.
        Soporta tanto formularios tradicionales como pruebas de usabilidad interactivas.
        
        Returns:
            Diccionario con resultados de la prueba
        """
        resultado = {
            'exito': False,
            'login': False,
            'prueba_encontrada': False,
            'prueba_iniciada': False,
            'preguntas_total': 0,
            'preguntas_completadas': 0,
            'enviado': False
        }
        
        try:
            # 1. Login
            if not self.login_plataforma():
                print("❌ No se pudo hacer login")
                return resultado
            resultado['login'] = True
            
            # 2. Buscar pruebas activas
            pruebas = self.buscar_pruebas_activas()
            if not pruebas:
                print("❌ No hay pruebas activas disponibles")
                return resultado
            resultado['prueba_encontrada'] = True
            
            # 3. Comenzar la primera prueba
            if not self.comenzar_prueba(pruebas[0]):
                print("❌ No se pudo iniciar la prueba")
                return resultado
            resultado['prueba_iniciada'] = True
            
            # 4. Detectar tipo de prueba y ejecutarla
            time.sleep(2)
            
            # Verificar si es una prueba de usabilidad (tiene panel lateral con preguntas)
            es_prueba_usabilidad = self._detectar_prueba_usabilidad()
            
            if es_prueba_usabilidad:
                print("\n📋 Detectada prueba de USABILIDAD interactiva")
                exito, preguntas_completadas, total = self._ejecutar_prueba_usabilidad()
                resultado['preguntas_total'] = total
                resultado['preguntas_completadas'] = preguntas_completadas
                resultado['exito'] = exito
                resultado['enviado'] = exito
            else:
                # Prueba con formulario tradicional
                print("\n📋 Detectada prueba con FORMULARIO tradicional")
                campos = self.analizar_formulario()
                resultado['preguntas_total'] = len(campos)
                
                if campos:
                    contexto = "Prueba de usabilidad de plataforma de voluntariado"
                    respuestas = self.generar_respuestas(campos, contexto)
                    self.completar_formulario(campos, respuestas)
                    resultado['preguntas_completadas'] = len(respuestas)
                    resultado['enviado'] = self.enviar_formulario()
                    resultado['exito'] = resultado['enviado']
            
            return resultado
            
        except Exception as e:
            print(f"❌ Error en ejecución: {e}")
            resultado['error'] = str(e)
            return resultado
    
    def _detectar_prueba_usabilidad(self) -> bool:
        """Detecta si es una prueba de usabilidad interactiva (con panel lateral)."""
        try:
            # Buscar indicadores de prueba de usabilidad
            indicadores = [
                'text=Pregunta 1 de',
                'text=Pregunta 1/',
                'text=/Pregunta \\d+ de \\d+/',
            ]
            
            for indicador in indicadores:
                try:
                    elem = self.page.locator(indicador).first
                    if elem.is_visible(timeout=2000):
                        return True
                except:
                    continue
            
            # También verificar si hay un iframe o panel lateral
            page_content = self.page.content()
            if 'Pregunta' in page_content and 'de 11' in page_content:
                return True
            
            return False
        except:
            return False
    
    def _ejecutar_prueba_usabilidad(self) -> tuple:
        """
        Ejecuta una prueba de usabilidad interactiva.
        
        Returns:
            (exito, preguntas_completadas, total_preguntas)
        """
        print("\n🎯 Ejecutando prueba de usabilidad...")
        
        preguntas_completadas = 0
        total_preguntas = 11  # Por defecto, actualizar si se detecta otro número
        ultima_pregunta_texto = ""  # Para detectar si estamos en loop
        intentos_misma_pregunta = 0
        
        try:
            # Detectar número total de preguntas
            try:
                pregunta_text = self.page.locator('text=/Pregunta \\d+ de \\d+/').first.inner_text()
                if 'de' in pregunta_text:
                    total_preguntas = int(pregunta_text.split('de')[1].strip())
                    print(f"   📊 Total de preguntas: {total_preguntas}")
            except:
                pass
            
            # Iterar por cada pregunta
            for num_pregunta in range(1, total_preguntas + 2):  # +2 por seguridad
                print(f"\n   📝 Procesando pregunta {num_pregunta}...")
                
                time.sleep(2)  # Dar tiempo para cargar
                
                # Leer la instrucción/pregunta actual
                instruccion = self._leer_instruccion_actual()
                
                # Detectar si estamos en loop (misma pregunta repetida)
                pregunta_actual = instruccion[:100] if instruccion else ""
                if pregunta_actual == ultima_pregunta_texto and pregunta_actual:
                    intentos_misma_pregunta += 1
                    if intentos_misma_pregunta >= 3:
                        print(f"      ⚠️ Detectado loop - misma pregunta {intentos_misma_pregunta} veces. Saltando...")
                        # Intentar forzar avance
                        self.page.keyboard.press('Tab')
                        time.sleep(0.5)
                        self.page.keyboard.press('Enter')
                        time.sleep(2)
                        if intentos_misma_pregunta >= 5:
                            print(f"      ❌ No se puede avanzar. Terminando.")
                            break
                        continue
                else:
                    intentos_misma_pregunta = 0
                    ultima_pregunta_texto = pregunta_actual
                
                if instruccion:
                    # Mostrar solo parte de la instrucción
                    instr_corta = instruccion.replace('\n', ' ')[:100]
                    print(f"      📖 {instr_corta}...")
                
                # Verificar si es una tarea de card sorting (solo si la instrucción lo indica)
                if self._es_tarea_card_sorting(instruccion):
                    print(f"      🃏 Tarea de Card Sorting detectada...")
                    card_data = self._detectar_card_sorting()
                    if card_data:
                        self._ejecutar_card_sorting(card_data)
                    else:
                        print(f"      ⚠️ No se detectaron elementos de card sorting en la página")
                    time.sleep(1)
                # Verificar si es una tarea de interacción con la web (registro, navegación, etc.)
                elif self._es_tarea_interaccion_web(instruccion):
                    print(f"      🌐 Tarea de interacción con la web embebida...")
                    self._ejecutar_tarea_web(instruccion)
                    
                    # IMPORTANTE: Después de Figma, esperar a que se procese y luego continuar
                    print(f"      ⏳ Esperando respuesta después de interacción Figma...")
                    time.sleep(3)
                    
                    # Intentar directamente avanzar sin buscar más campos
                    print(f"      🔘 Intentando avanzar...")
                    if self._avanzar_pregunta():
                        preguntas_completadas += 1
                        print(f"      ✅ Pregunta {num_pregunta} completada")
                    else:
                        print(f"      ⚠️ No se pudo avanzar después de Figma")
                        time.sleep(2)
                        # Reintentar
                        if self._avanzar_pregunta():
                            preguntas_completadas += 1
                            print(f"      ✅ Pregunta {num_pregunta} completada")
                        else:
                            print(f"      ⚠️ Continuando a pesar del fallo...")
                    
                    continue  # Saltar el resto del procesamiento
                
                # Verificar si hay que hacer clic simple en la página web
                elif self._requiere_clic(instruccion):
                    print(f"      🖱️ La pregunta requiere hacer clic en la página...")
                    self._realizar_clic_inteligente(instruccion)
                    time.sleep(1.5)
                
                # Verificar si hay campos de respuesta (texto, radio, etc.)
                campos_respuesta = self._buscar_campos_respuesta()
                hubo_campos_respuesta = False
                if campos_respuesta:
                    # Filtrar card sorting que ya fue manejado
                    campos_no_card_sorting = [c for c in campos_respuesta if c.get('tipo') != 'card_sorting']
                    if campos_no_card_sorting:
                        print(f"      ✍️ Completando {len(campos_no_card_sorting)} campo(s) de respuesta...")
                        self._completar_campos_respuesta(campos_no_card_sorting, instruccion)
                        hubo_campos_respuesta = True
                    time.sleep(0.5)
                
                # Verificar audio si:
                # 1. No hubo otros campos de respuesta procesados, O
                # 2. El botón Continuar sigue deshabilitado
                if self._es_pregunta_audio():
                    continuar_deshabilitado = False
                    try:
                        btn_cont = self.page.locator('button:has-text("Continuar")').first
                        if btn_cont.is_visible(timeout=500):
                            continuar_deshabilitado = btn_cont.is_disabled()
                    except:
                        pass
                    
                    # Grabar audio si está deshabilitado el continuar o si no hubo campos de respuesta
                    if continuar_deshabilitado or not hubo_campos_respuesta:
                        print(f"      🎤 Pregunta de grabación de audio detectada...")
                        self._manejar_grabacion_audio()
                        time.sleep(1)
                
                # Hacer clic en Continuar o Detener grabación para avanzar
                avanzado = self._avanzar_pregunta()
                
                if avanzado:
                    preguntas_completadas += 1
                    print(f"      ✅ Pregunta {num_pregunta} completada")
                else:
                    # Verificar si terminamos la prueba
                    if self._prueba_terminada():
                        print(f"\n   🎉 ¡Prueba completada!")
                        return (True, preguntas_completadas, total_preguntas)
                    else:
                        print(f"      ⚠️ No se pudo avanzar, reintentando...")
                        time.sleep(2)
                        # Intentar varias veces más con diferentes estrategias
                        for intento in range(3):
                            # Intentar hacer clic en cualquier botón visible
                            if self._avanzar_pregunta():
                                preguntas_completadas += 1
                                break
                            time.sleep(2)
                        else:
                            # Si todos los intentos fallaron, continuar de todos modos
                            # (la pregunta puede haberse contestado pero no detectado)
                            print(f"      ⚠️ Continuando a pesar del fallo...")
                            continue
                
                time.sleep(1)
            
            return (preguntas_completadas >= total_preguntas - 1, preguntas_completadas, total_preguntas)
            
        except Exception as e:
            print(f"   ❌ Error en prueba de usabilidad: {e}")
            return (False, preguntas_completadas, total_preguntas)
    
    def _leer_instruccion_actual(self) -> str:
        """Lee la instrucción/pregunta actual del panel lateral."""
        try:
            # El panel de preguntas está a la derecha
            # Buscar texto que contenga la pregunta
            selectores = [
                'text=/Pregunta \\d+ de \\d+/',
            ]
            
            # Obtener todo el texto del panel de la derecha
            try:
                # Buscar el contenedor del panel de preguntas
                panel_text = self.page.evaluate("""
                    () => {
                        // Buscar elementos que contengan "Pregunta X de Y"
                        const elements = document.querySelectorAll('*');
                        for (let el of elements) {
                            if (el.innerText && el.innerText.includes('Pregunta') && el.innerText.includes('de 11')) {
                                // Obtener el texto del contenedor padre
                                let parent = el.parentElement;
                                for (let i = 0; i < 5; i++) {
                                    if (parent && parent.innerText && parent.innerText.length > 100) {
                                        return parent.innerText;
                                    }
                                    parent = parent?.parentElement;
                                }
                                return el.innerText;
                            }
                        }
                        return '';
                    }
                """)
                return panel_text
            except:
                pass
            
            return ""
        except:
            return ""
    
    def _es_tarea_card_sorting(self, instruccion: str) -> bool:
        """Determina si la instrucción es una tarea de card sorting."""
        if not instruccion:
            return False
        
        instruccion_lower = instruccion.lower()
        palabras_card_sorting = [
            'organice las', 'organizar las', 'tarjetas', 'cards',
            'arrastre', 'arrastra', 'drag', 'grupos', 'categorías',
            'ordene', 'ordenar', 'clasificar', 'clasifique',
            'agrupar', 'agrupe', 'sorting'
        ]
        
        return any(palabra in instruccion_lower for palabra in palabras_card_sorting)
    
    def _es_tarea_interaccion_web(self, instruccion: str) -> bool:
        """Determina si la instrucción requiere interactuar con la web embebida (registro, navegación compleja)."""
        if not instruccion:
            return False
        
        instruccion_lower = instruccion.lower()
        # Palabras que indican tareas complejas de interacción
        palabras_interaccion = [
            'complete el proceso', 'crear una cuenta', 'registr', 'inscrib',
            'ingresando sus datos', 'llene el formulario', 'navegue hasta',
            'hasta llegar al final', 'encuesta de perfilamiento'
        ]
        
        return any(palabra in instruccion_lower for palabra in palabras_interaccion)
    
    def _es_pregunta_audio(self) -> bool:
        """Detecta si hay un botón de grabación de audio visible."""
        try:
            selectores_audio = [
                'button:has-text("Grabar audio")',
                'button:has-text("Grabar")',
                'button:has-text("Record")',
                '[class*="record"]:visible',
                'button[class*="audio"]',
            ]
            
            for selector in selectores_audio:
                try:
                    btn = self.page.locator(selector).first
                    if btn.is_visible(timeout=500):
                        return True
                except:
                    continue
            
            # También verificar por JavaScript
            tiene_audio = self.page.evaluate("""
                () => {
                    const botones = document.querySelectorAll('button');
                    for (let btn of botones) {
                        const text = btn.innerText?.toLowerCase() || '';
                        if (text.includes('grabar audio') || text.includes('grabar') || 
                            text.includes('record')) {
                            if (btn.offsetParent !== null) {
                                return true;
                            }
                        }
                    }
                    return false;
                }
            """)
            return tiene_audio
        except:
            return False
    
    def _manejar_grabacion_audio(self):
        """Maneja la grabación de audio: inicia, espera y detiene."""
        try:
            # 1. Buscar y hacer clic en "Grabar audio"
            btn_grabar = None
            selectores = [
                'button:has-text("Grabar audio")',
                'button:has-text("Grabar")',
            ]
            
            for selector in selectores:
                try:
                    btn = self.page.locator(selector).first
                    if btn.is_visible(timeout=1000):
                        btn_grabar = btn
                        break
                except:
                    continue
            
            if not btn_grabar:
                # Intentar con JavaScript
                clicked = self.page.evaluate("""
                    () => {
                        const botones = document.querySelectorAll('button');
                        for (let btn of botones) {
                            const text = btn.innerText?.toLowerCase() || '';
                            if (text.includes('grabar audio') && btn.offsetParent !== null) {
                                btn.click();
                                return true;
                            }
                        }
                        return false;
                    }
                """)
                if clicked:
                    print(f"         🔴 Grabación iniciada (JS)")
                else:
                    print(f"         ⚠️ No se encontró botón de grabar")
                    return
            else:
                print(f"         🔴 Iniciando grabación...")
                btn_grabar.click()
            
            # 2. Esperar mientras "graba" (3-5 segundos)
            print(f"         ⏱️ Grabando audio (3 segundos)...")
            time.sleep(3)
            
            # 3. Detener la grabación
            btn_detener = None
            selectores_detener = [
                'button:has-text("Detener grabación")',
                'button:has-text("Detener")',
                'button:has-text("Stop")',
            ]
            
            for selector in selectores_detener:
                try:
                    btn = self.page.locator(selector).first
                    if btn.is_visible(timeout=1000):
                        btn_detener = btn
                        break
                except:
                    continue
            
            if btn_detener:
                print(f"         ⏹️ Deteniendo grabación...")
                btn_detener.click()
                time.sleep(2)
            else:
                # Intentar con JavaScript
                self.page.evaluate("""
                    () => {
                        const botones = document.querySelectorAll('button');
                        for (let btn of botones) {
                            const text = btn.innerText?.toLowerCase() || '';
                            if ((text.includes('detener') || text.includes('stop')) && 
                                btn.offsetParent !== null) {
                                btn.click();
                                return true;
                            }
                        }
                        return false;
                    }
                """)
                print(f"         ⏹️ Grabación detenida (JS)")
                time.sleep(2)
            
            # 4. Esperar a que aparezca el botón Continuar habilitado
            print(f"         ⏳ Esperando que se procese el audio...")
            time.sleep(2)
            
            # 5. Intentar hacer clic en Continuar directamente
            try:
                btn_continuar = self.page.locator('button:has-text("Continuar")').first
                if btn_continuar.is_visible(timeout=2000):
                    # Esperar a que esté habilitado
                    for _ in range(5):
                        if not btn_continuar.is_disabled():
                            btn_continuar.click()
                            print(f"         ➡️ Avanzando a siguiente pregunta...")
                            time.sleep(2)
                            break
                        time.sleep(1)
            except:
                pass
            
            print(f"         ✅ Grabación de audio completada")
            
        except Exception as e:
            print(f"         ⚠️ Error en grabación de audio: {e}")
    
    def _ejecutar_tarea_web(self, instruccion: str):
        """
        Ejecuta tareas complejas de interacción con la web embebida (Figma, prototipos, etc).
        MEJORADO: Mejor detección y navegación dentro de Figma.
        """
        try:
            instruccion_lower = instruccion.lower()
            
            print(f"         🌐 Ejecutando tarea web en Figma/Prototipo...")
            
            # Detectar si hay un iframe de Figma
            frames = self.page.frames
            figma_frame = None
            
            for frame in frames:
                try:
                    if 'figma.com' in frame.url.lower():
                        figma_frame = frame
                        print(f"         ✅ Figma iframe detectado")
                        break
                except:
                    pass
            
            if figma_frame:
                # DENTRO DE FIGMA: Hacer clic en elementos para interactuar
                self._interactuar_figma(figma_frame, instruccion)
            else:
                # Si no es Figma, intentar otras interacciones
                self._interaccion_generica(self.page, instruccion)
            
            # Después de la interacción, esperar y permitir que se procese
            time.sleep(2)
                    
        except Exception as e:
            print(f"         ⚠️ Error en tarea web: {e}")
    
    def _interactuar_figma(self, figma_frame, instruccion: str):
        """
        Interactúa dentro de un prototipo Figma.
        Busca campos de formulario, inputs, botones, etc y los completa.
        """
        try:
            print(f"         📱 Completando formulario dentro de Figma...")
            
            # ESTRATEGIA 1: Buscar inputs y llenarlos
            inputs = figma_frame.locator('input:visible, textarea:visible').all()
            campos_completados = 0
            
            for inp in inputs:
                try:
                    input_type = inp.get_attribute('type') or 'text'
                    placeholder = inp.get_attribute('placeholder') or ''
                    name = inp.get_attribute('name') or ''
                    
                    # Determinar qué llenar según el tipo/nombre
                    valor = 'Nombre Prueba'
                    if 'email' in name.lower() or 'email' in placeholder.lower():
                        valor = f'test{int(time.time())}@example.com'
                    elif 'phone' in name.lower() or 'celular' in placeholder.lower():
                        valor = '3001234567'
                    elif 'password' in name.lower():
                        valor = 'TestPassword123!'
                    
                    # Llenar el campo
                    inp.click()
                    time.sleep(0.2)
                    inp.fill('')
                    time.sleep(0.1)
                    inp.type(valor, delay=30)
                    campos_completados += 1
                    print(f"         ✍️ Campo rellenado: {valor[:15]}...")
                    time.sleep(0.3)
                except Exception as e:
                    continue
            
            # ESTRATEGIA 2: Hacer clic en radio buttons/checkboxes
            radios = figma_frame.locator('input[type="radio"]:visible, [role="radio"]:visible').all()
            for radio in radios[:3]:  # Max 3 para no excederse
                try:
                    if radio.is_visible():
                        radio.click()
                        print(f"         🔘 Radio button seleccionado")
                        time.sleep(0.3)
                except:
                    continue
            
            # ESTRATEGIA 3: Buscar botones de envío en Figma
            botones = figma_frame.locator('button:visible, [role="button"]:visible').all()
            boton_encontrado = False
            
            for btn in botones:
                try:
                    btn_text = btn.inner_text().lower() if btn.inner_text() else ''
                    
                    # Buscar botones de envío/siguiente
                    if any(palabra in btn_text for palabra in ['enviar', 'siguiente', 'continuar', 'submit', 'registr']):
                        print(f"         🔘 Botón encontrado: {btn_text[:20]}")
                        btn.click()
                        print(f"         ✅ Botón enviado en Figma")
                        time.sleep(2)
                        boton_encontrado = True
                        break
                except:
                    continue
            
            # ESTRATEGIA 4: Si no hay botones visibles, hacer clic en el centro del formulario
            if not boton_encontrado and campos_completados > 0:
                print(f"         🖱️ Clic en área central para enviar")
                figma_frame.mouse.click(400, 300)
                time.sleep(2)
            
            print(f"         ✅ Interacción en Figma completada ({campos_completados} campo(s))")
            
        except Exception as e:
            print(f"         ⚠️ Error en Figma: {e}")
    
    
    
    def _ejecutar_registro(self, contexto, instruccion: str):
        """Ejecuta un proceso de registro en la web embebida."""
        try:
            # Paso 1: Buscar botón de registro/ingresar
            botones_registro = [
                'text=Registrarse', 'text=Registrar', 'text=Crear cuenta',
                'text=Ingresar', 'text=Iniciar sesión', 'text=Sign up',
                'button:has-text("registr")', 'a:has-text("registr")',
                'button:has-text("ingresar")', 'a:has-text("ingresar")',
            ]
            
            for selector in botones_registro:
                try:
                    btn = contexto.locator(selector).first
                    if btn.is_visible(timeout=2000):
                        print(f"         🔘 Clic en: {selector}")
                        btn.click()
                        time.sleep(2)
                        break
                except:
                    continue
            
            # Paso 2: Llenar formulario de registro con datos simulados
            time.sleep(2)
            datos_simulados = {
                'nombre': 'Juan Carlos',
                'apellido': 'Prueba Test',
                'email': f'test.user{int(time.time())}@example.com',
                'telefono': '3001234567',
                'password': 'TestPassword123!',
                'ciudad': 'Bogotá',
                'pais': 'Colombia',
            }
            
            # Buscar y llenar campos de formulario
            campos_llenados = 0
            selectores_campos = {
                'nombre': ['input[name*="nombre"]', 'input[name*="name"]', 'input[placeholder*="nombre"]', '#nombre', '#firstName'],
                'apellido': ['input[name*="apellido"]', 'input[name*="lastName"]', 'input[placeholder*="apellido"]', '#apellido'],
                'email': ['input[type="email"]', 'input[name*="email"]', 'input[placeholder*="email"]', '#email'],
                'telefono': ['input[type="tel"]', 'input[name*="telefono"]', 'input[name*="phone"]', 'input[placeholder*="teléfono"]'],
                'password': ['input[type="password"]', 'input[name*="password"]', '#password'],
                'ciudad': ['input[name*="ciudad"]', 'input[name*="city"]', 'select[name*="ciudad"]'],
            }
            
            for campo, selectores in selectores_campos.items():
                for sel in selectores:
                    try:
                        elem = contexto.locator(sel).first
                        if elem.is_visible(timeout=1000):
                            valor = datos_simulados.get(campo, 'Test')
                            elem.fill(valor)
                            campos_llenados += 1
                            print(f"         ✍️ {campo}: {valor[:20]}...")
                            time.sleep(0.3)
                            break
                    except:
                        continue
            
            print(f"         📋 Campos llenados: {campos_llenados}")
            
            # Paso 3: Buscar y hacer clic en botón de envío
            botones_envio = [
                'button[type="submit"]', 'button:has-text("Registrar")',
                'button:has-text("Enviar")', 'button:has-text("Continuar")',
                'button:has-text("Siguiente")', 'input[type="submit"]',
            ]
            
            for selector in botones_envio:
                try:
                    btn = contexto.locator(selector).first
                    if btn.is_visible(timeout=1000):
                        btn.click()
                        print(f"         ✅ Formulario enviado")
                        time.sleep(3)
                        break
                except:
                    continue
            
            # Paso 4: Si hay más pasos (encuesta de perfilamiento), continuar
            for _ in range(5):  # Máximo 5 pasos adicionales
                time.sleep(2)
                # Buscar más campos o botones de siguiente
                campos_adicionales = contexto.locator('input:visible, select:visible, textarea:visible').all()
                if campos_adicionales:
                    for campo in campos_adicionales[:3]:  # Llenar hasta 3 campos
                        try:
                            tag = campo.evaluate("el => el.tagName.toLowerCase()")
                            if tag == 'select':
                                # Seleccionar segunda opción
                                opciones = campo.locator('option').all()
                                if len(opciones) > 1:
                                    opciones[1].click()
                            else:
                                campo.fill("Respuesta de prueba")
                        except:
                            continue
                
                # Buscar botón siguiente
                siguiente = contexto.locator('button:has-text("Siguiente"), button:has-text("Continuar")').first
                try:
                    if siguiente.is_visible(timeout=1000):
                        siguiente.click()
                        time.sleep(1)
                    else:
                        break
                except:
                    break
                    
        except Exception as e:
            print(f"         ⚠️ Error en registro: {e}")
    
    def _ejecutar_navegacion(self, contexto, instruccion: str):
        """Ejecuta navegación en la web embebida."""
        try:
            # Buscar enlaces o botones relevantes según la instrucción
            instruccion_lower = instruccion.lower()
            
            if 'oferta' in instruccion_lower:
                selectores = ['text=Ofertas', 'text=Ver ofertas', 'a:has-text("oferta")']
            elif 'organiza' in instruccion_lower:
                selectores = ['text=Organizaciones', 'a:has-text("organiza")']
            else:
                selectores = ['a:visible', 'button:visible']
            
            for sel in selectores:
                try:
                    elem = contexto.locator(sel).first
                    if elem.is_visible(timeout=1000):
                        elem.click()
                        print(f"         🔗 Navegando: {sel}")
                        time.sleep(2)
                        break
                except:
                    continue
                    
        except Exception as e:
            print(f"         ⚠️ Error en navegación: {e}")
    
    def _interaccion_generica(self, contexto, instruccion: str):
        """
        Interacción genérica con la web embebida.
        Optimizado para Figma prototipos y apps embebidas.
        MEJORADO: Múltiples estrategias de interacción.
        """
        try:
            print(f"         📱 Interacción genérica en la página...")
            
            # ESTRATEGIA 1: Llenar campos de formulario visibles
            inputs = contexto.locator('input:visible, textarea:visible').all()
            campos_llenados = 0
            
            for inp in inputs[:5]:  # Max 5 campos
                try:
                    inp_type = inp.get_attribute('type') or 'text'
                    if inp_type in ['text', 'email', 'password', 'tel']:
                        # Generar valor según tipo
                        if inp_type == 'email':
                            valor = f'test{int(time.time())}@example.com'
                        elif inp_type == 'password':
                            valor = 'Test123!@#'
                        elif inp_type == 'tel':
                            valor = '3001234567'
                        else:
                            valor = 'Test Value'
                        
                        inp.click()
                        time.sleep(0.1)
                        inp.fill('')
                        time.sleep(0.1)
                        inp.type(valor, delay=20)
                        campos_llenados += 1
                        print(f"         ✍️ Input rellenado")
                        time.sleep(0.2)
                except:
                    continue
            
            # ESTRATEGIA 2: Hacer clic en botones principales
            botones = contexto.locator('button:visible, [role="button"]:visible, a[role="button"]:visible').all()
            boton_clickeado = False
            
            # Prioridad a botones de envío
            for btn in botones:
                try:
                    btn_text = btn.inner_text().lower() if btn.inner_text() else ''
                    
                    if any(palabra in btn_text for palabra in ['enviar', 'siguiente', 'submit', 'registr', 'ingresar']):
                        btn.click()
                        print(f"         🔘 Botón principal clickeado")
                        boton_clickeado = True
                        time.sleep(1.5)
                        break
                except:
                    continue
            
            # ESTRATEGIA 3: Si no clickeó botón, hacer scroll y explorar
            if not boton_clickeado:
                print(f"         🔍 Explorando página...")
                contexto.evaluate("window.scrollBy(0, 200)")
                time.sleep(0.5)
                
                # Intentar hacer clic en el primer botón visible
                primer_boton = contexto.locator('button:visible, [role="button"]:visible').first
                try:
                    if primer_boton.is_visible(timeout=500):
                        primer_boton.click()
                        print(f"         🔘 Clic en elemento interactivo")
                        time.sleep(1.5)
                except:
                    # Último recurso: clic en el centro
                    print(f"         🖱️ Clic en área central")
                    contexto.mouse.click(400, 300)
                    time.sleep(1)
            
            if campos_llenados > 0:
                print(f"         ✅ Completados {campos_llenados} campo(s)")
            
        except Exception as e:
            print(f"         ⚠️ Error en interacción: {e}")
    
    def _requiere_clic(self, instruccion: str) -> bool:
        """Determina si la instrucción requiere hacer clic en la página."""
        if not instruccion:
            return False
        
        instruccion_lower = instruccion.lower()
        palabras_clic = [
            'haga clic', 'haría clic', 'haz clic', 'clic', 'click',
            'realice un solo clic', 'dónde haría', 'donde haria',
            'seleccione', 'pulse', 'presione'
        ]
        
        # No requiere clic si es solo observar
        palabras_observar = ['observe', 'tómese un momento', 'imagine']
        
        requiere = any(palabra in instruccion_lower for palabra in palabras_clic)
        solo_observar = any(palabra in instruccion_lower for palabra in palabras_observar) and not requiere
        
        return requiere and not solo_observar
    
    def _realizar_clic_inteligente(self, instruccion: str):
        """
        Realiza un clic inteligente en la página según la instrucción.
        MEJORADO: Evita bordes y hace clic en el centro de elementos.
        """
        try:
            instruccion_lower = instruccion.lower()
            
            # Determinar qué tipo de elemento buscar según la instrucción
            elemento_a_buscar = None
            
            if 'voluntariado' in instruccion_lower or 'actividad' in instruccion_lower or 'buscar' in instruccion_lower:
                # Buscar botones o links relacionados con ofertas/voluntariado
                selectores_prioritarios = [
                    'button:has-text("Ofertas")',
                    'button:has-text("ofertas")',
                    'a:has-text("Ofertas")',
                    'button:has-text("Buscar")',
                    '[class*="search"]',
                    'button:visible',
                ]
            elif 'registr' in instruccion_lower or 'inscrib' in instruccion_lower:
                selectores_prioritarios = [
                    'button:has-text("Registrar")',
                    'button:has-text("Ingresar")',
                    'a:has-text("Registrar")',
                ]
            elif 'organiza' in instruccion_lower:
                selectores_prioritarios = [
                    'button:has-text("Organizaciones")',
                    'a:has-text("Organizaciones")',
                ]
            else:
                # Buscar elementos interactivos genéricos en la página
                selectores_prioritarios = [
                    'button:visible',
                    'a[href]:visible',
                    '[role="button"]:visible',
                ]
            
            # Intentar hacer clic en el primer elemento encontrado
            # Pero solo en la parte izquierda de la página (la web de prueba)
            for selector in selectores_prioritarios:
                try:
                    elementos = self.page.locator(selector).all()
                    for elem in elementos:
                        try:
                            if elem.is_visible(timeout=500):
                                # Obtener bounding box del elemento
                                box = elem.bounding_box()
                                if not box:
                                    continue
                                
                                # Verificar que el elemento está en la parte izquierda (no en el panel de preguntas)
                                # y que no está en un borde
                                elem_width = box['width']
                                elem_height = box['height']
                                elem_x = box['x']
                                elem_y = box['y']
                                
                                # Solo hacer clic si el elemento tiene tamaño razonable (no es un borde)
                                if elem_width > 30 and elem_height > 15 and elem_x < 1000:
                                    # Calcular el centro del elemento (más inteligente)
                                    click_x = elem_x + elem_width / 2
                                    click_y = elem_y + elem_height / 2
                                    
                                    # Usar scroll into view antes de hacer clic
                                    elem.scroll_into_view_if_needed()
                                    time.sleep(0.2)
                                    
                                    # Hacer clic en el centro del elemento
                                    self.page.mouse.click(click_x, click_y)
                                    print(f"      🎯 Clic en centro de elemento ({int(click_x)}, {int(click_y)})")
                                    return
                        except:
                            continue
                except:
                    continue
            
            # Si no encuentra nada específico, buscar en el área principal (centro-izquierda)
            print(f"      🎯 Clic en área central de la página")
            # Hacer clic en el centro-izquierda, no en un borde
            self.page.mouse.click(500, 350)
            time.sleep(1)
            
        except Exception as e:
            print(f"      ⚠️ Error al hacer clic: {e}")
    
    
    def _realizar_interaccion(self, instruccion: str):
        """Realiza interacciones con la página web según la instrucción."""
        try:
            # Por ahora, simular observación de la página
            self.page.evaluate("window.scrollBy(0, 300)")
            time.sleep(1)
            self.page.evaluate("window.scrollBy(0, -150)")
        except:
            pass
    
    def _buscar_campos_respuesta(self) -> List:
        """Busca campos de respuesta en el panel de la prueba."""
        campos = []
        try:
            # Buscar campos de texto
            inputs = self.page.locator('input[type="text"], textarea').all()
            for inp in inputs:
                if inp.is_visible():
                    campos.append({'tipo': 'texto', 'elemento': inp})
            
            # Buscar radio buttons (varios selectores posibles)
            radios = self.page.locator('[role="radio"], input[type="radio"]').all()
            radios_visibles = [r for r in radios if r.is_visible()]
            if radios_visibles:
                campos.append({'tipo': 'radio', 'elementos': radios_visibles})
            
            # Buscar checkboxes
            checks = self.page.locator('[role="checkbox"], input[type="checkbox"]').all()
            checks_visibles = [c for c in checks if c.is_visible()]
            if checks_visibles:
                campos.append({'tipo': 'checkbox', 'elementos': checks_visibles})
            
            # Buscar sliders/escalas
            sliders = self.page.locator('input[type="range"], [role="slider"]').all()
            sliders_visibles = [s for s in sliders if s.is_visible()]
            if sliders_visibles:
                campos.append({'tipo': 'slider', 'elementos': sliders_visibles})
            
            # Buscar escala visual con círculos (como la de 1-5)
            # Detectar por JavaScript los elementos circulares clickeables
            escala_info = self.page.evaluate("""
                () => {
                    const result = [];
                    // Buscar contenedores que tengan números 1-5 como hijos
                    const allElements = document.querySelectorAll('*');
                    
                    for (let el of allElements) {
                        const children = el.children;
                        // Verificar si es un contenedor de escala (tiene 5 hijos con números 1-5)
                        if (children.length >= 5) {
                            let hasScale = true;
                            let scaleItems = [];
                            
                            for (let i = 0; i < Math.min(children.length, 10); i++) {
                                const child = children[i];
                                const text = child.innerText?.trim();
                                // Buscar elementos con números 1-5
                                if (text && /^[1-5]$/.test(text)) {
                                    const rect = child.getBoundingClientRect();
                                    if (rect.width > 0 && rect.height > 0) {
                                        scaleItems.push({
                                            valor: parseInt(text),
                                            x: rect.x + rect.width / 2,
                                            y: rect.y + rect.height / 2,
                                            width: rect.width,
                                            height: rect.height
                                        });
                                    }
                                }
                            }
                            
                            if (scaleItems.length >= 5) {
                                return scaleItems;
                            }
                        }
                    }
                    
                    // Buscar elementos individuales con círculos (svg, ellipse, circle, divs redondos)
                    const circulos = document.querySelectorAll('circle, ellipse, [class*="circle"], [class*="radio"], [class*="scale"]');
                    const items = [];
                    
                    for (let circ of circulos) {
                        const rect = circ.getBoundingClientRect();
                        if (rect.width > 20 && rect.width < 100 && rect.height > 20) {
                            // Buscar número cercano
                            const parent = circ.parentElement;
                            const text = parent?.innerText?.trim();
                            if (text && /^[1-5]$/.test(text)) {
                                items.push({
                                    valor: parseInt(text),
                                    x: rect.x + rect.width / 2,
                                    y: rect.y + rect.height / 2
                                });
                            }
                        }
                    }
                    
                    if (items.length >= 3) {
                        return items;
                    }
                    
                    // Último intento: buscar elementos con texto 1-5 que sean clickeables
                    const clickables = document.querySelectorAll('button, [role="button"], label, div, span');
                    const clickableItems = [];
                    
                    for (let el of clickables) {
                        const text = el.innerText?.trim();
                        const rect = el.getBoundingClientRect();
                        
                        if (text && /^[1-5]$/.test(text) && rect.width > 0 && rect.width < 150) {
                            clickableItems.push({
                                valor: parseInt(text),
                                x: rect.x + rect.width / 2,
                                y: rect.y + rect.height / 2
                            });
                        }
                    }
                    
                    // Ordenar por posición X para asegurar orden correcto
                    clickableItems.sort((a, b) => a.x - b.x);
                    
                    if (clickableItems.length >= 5) {
                        return clickableItems;
                    }
                    
                    return [];
                }
            """)
            
            if escala_info and len(escala_info) >= 3:
                campos.append({'tipo': 'escala_visual', 'elementos': escala_info})
                print(f"      🔍 Detectada escala visual con {len(escala_info)} opciones")
            
            # Buscar Card Sorting (tarjetas arrastrables y contenedores/grupos)
            card_sorting_info = self._detectar_card_sorting()
            if card_sorting_info:
                campos.append({'tipo': 'card_sorting', 'datos': card_sorting_info})
                print(f"      🔍 Detectado Card Sorting: {len(card_sorting_info.get('tarjetas', []))} tarjetas, {len(card_sorting_info.get('grupos', []))} grupos")
                
        except Exception as e:
            print(f"      ⚠️ Error buscando campos: {e}")
        
        return campos
    
    def _detectar_card_sorting(self) -> dict:
        """Detecta elementos de card sorting (tarjetas arrastrables y grupos/contenedores)."""
        try:
            resultado = self.page.evaluate("""
                () => {
                    const info = { tarjetas: [], grupos: [] };
                    
                    // Buscar todas las tarjetas/opciones en la sección izquierda
                    // Las tarjetas suelen estar en elementos con texto corto, aspecto de card
                    const allElements = document.querySelectorAll('div, li, span, p');
                    
                    // Primero identificar si hay secciones "Opciones" y "Categorías"
                    let seccionOpciones = null;
                    let seccionCategorias = null;
                    
                    for (let el of allElements) {
                        const text = el.innerText?.trim();
                        if (text === 'Opciones' || text === 'Options') {
                            seccionOpciones = el.parentElement;
                        }
                        if (text === 'Categorías' || text === 'Categories') {
                            seccionCategorias = el.parentElement;
                        }
                    }
                    
                    // Buscar tarjetas - elementos que parecen items arrastrables
                    const posiblesTarjetas = document.querySelectorAll(
                        '[draggable="true"], [data-rbd-draggable-id], ' +
                        'div[class*="card"], div[class*="item"], div[class*="option"], ' +
                        'div[class*="draggable"], li[class*="item"]'
                    );
                    
                    for (let el of posiblesTarjetas) {
                        const rect = el.getBoundingClientRect();
                        const text = el.innerText?.trim();
                        
                        // Las tarjetas están a la izquierda (x < 1000) y tienen tamaño de tarjeta
                        if (rect.x < 1000 && rect.width > 100 && rect.width < 800 && 
                            rect.height > 25 && rect.height < 80 &&
                            text && text.length > 3 && text.length < 50 &&
                            !text.includes('Opciones') && !text.includes('Pregunta') &&
                            !text.includes('Arrastra') && !text.includes('Categorías')) {
                            
                            // Evitar duplicados
                            const exists = info.tarjetas.some(t => t.texto === text);
                            if (!exists) {
                                info.tarjetas.push({
                                    texto: text,
                                    x: rect.x + rect.width / 2,
                                    y: rect.y + rect.height / 2,
                                    width: rect.width,
                                    height: rect.height
                                });
                            }
                        }
                    }
                    
                    // Buscar categorías/grupos - están a la derecha y tienen "Arrastra elementos aquí"
                    const posiblesGrupos = document.querySelectorAll(
                        'div[class*="category"], div[class*="group"], div[class*="drop"], ' +
                        'div[class*="bucket"], div[class*="zone"], div[class*="container"]'
                    );
                    
                    for (let el of posiblesGrupos) {
                        const rect = el.getBoundingClientRect();
                        const text = el.innerText?.trim();
                        
                        // Los grupos están a la derecha (x > 900) y contienen "Arrastra"
                        if (rect.x > 800 && rect.width > 100 && rect.height > 60 &&
                            text && text.includes('Arrastra')) {
                            
                            // Extraer el título (primera línea antes de "Arrastra")
                            const titulo = text.split('Arrastra')[0].trim();
                            
                            if (titulo && titulo.length > 2) {
                                const exists = info.grupos.some(g => g.titulo === titulo);
                                if (!exists) {
                                    info.grupos.push({
                                        titulo: titulo,
                                        x: rect.x + rect.width / 2,
                                        y: rect.y + rect.height / 2,
                                        width: rect.width,
                                        height: rect.height
                                    });
                                }
                            }
                        }
                    }
                    
                    // Si no encontramos con los selectores anteriores, buscar por texto
                    if (info.tarjetas.length < 3 || info.grupos.length < 2) {
                        // Buscar elementos que parecen tarjetas por su contenido
                        const palabrasTarjetas = ['Sembratón', 'Tutorías', 'Donación', 'Construcción', 
                                                   'Mentoría', 'Limpieza', 'Voluntariado'];
                        const palabrasGrupos = ['Impacto Social', 'Medio Ambiente', 'Educación', 
                                                'Ayuda Humanitaria', 'Social', 'Ambiental'];
                        
                        for (let el of allElements) {
                            const rect = el.getBoundingClientRect();
                            const text = el.innerText?.trim();
                            
                            if (!text || rect.width < 50) continue;
                            
                            // Verificar si es una tarjeta
                            for (let palabra of palabrasTarjetas) {
                                if (text.includes(palabra) && text.length < 50 && 
                                    rect.x < 1000 && rect.height < 80) {
                                    const exists = info.tarjetas.some(t => t.texto === text);
                                    if (!exists && info.tarjetas.length < 10) {
                                        info.tarjetas.push({
                                            texto: text,
                                            x: rect.x + rect.width / 2,
                                            y: rect.y + rect.height / 2,
                                            width: rect.width,
                                            height: rect.height
                                        });
                                    }
                                    break;
                                }
                            }
                            
                            // Verificar si es un grupo
                            for (let palabra of palabrasGrupos) {
                                if (text.startsWith(palabra) && rect.x > 800) {
                                    const exists = info.grupos.some(g => g.titulo === palabra);
                                    if (!exists && info.grupos.length < 6) {
                                        info.grupos.push({
                                            titulo: palabra,
                                            x: rect.x + rect.width / 2,
                                            y: rect.y + rect.height / 2,
                                            width: rect.width,
                                            height: rect.height
                                        });
                                    }
                                    break;
                                }
                            }
                        }
                    }
                    
                    // Ordenar tarjetas por posición Y
                    info.tarjetas.sort((a, b) => a.y - b.y);
                    info.grupos.sort((a, b) => a.y - b.y);
                    
                    console.log('Card sorting detectado:', info);
                    
                    // Solo retornar si hay suficientes elementos
                    return (info.tarjetas.length >= 2 && info.grupos.length >= 2) ? info : null;
                }
            """)
            
            return resultado
        except Exception as e:
            print(f"         ⚠️ Error detectando card sorting: {e}")
            return None

    def _completar_campos_respuesta(self, campos: List, instruccion: str):
        """Completa los campos de respuesta encontrados."""
        for campo in campos:
            try:
                if campo['tipo'] == 'texto':
                    elem = campo['elemento']
                    # Generar respuesta con IA si está disponible
                    try:
                        prompt = f"Responde brevemente (1-2 oraciones) a esta pregunta sobre usabilidad: {instruccion}"
                        response = self.modelo.generate_content(prompt)
                        respuesta = response.text.strip()[:200]
                    except:
                        respuesta = "La página se ve clara y bien organizada."
                    elem.fill(respuesta)
                    print(f"         ✍️ Texto: {respuesta[:50]}...")
                    
                elif campo['tipo'] == 'radio':
                    elementos = campo['elementos']
                    if elementos:
                        # Seleccionar una opción intermedia-positiva (índice 2-3 de 5)
                        total = len(elementos)
                        idx = min(total - 2, max(1, total // 2))  # Opción intermedia-alta
                        elementos[idx].click(force=True)
                        print(f"         🔘 Radio: opción {idx + 1} de {total}")
                        
                elif campo['tipo'] == 'checkbox':
                    elementos = campo['elementos']
                    if elementos:
                        elementos[0].click(force=True)
                        print(f"         ☑️ Checkbox seleccionado")
                        
                elif campo['tipo'] == 'slider':
                    elementos = campo['elementos']
                    if elementos:
                        # Mover al 70-80%
                        elementos[0].evaluate("el => el.value = 4")
                        elementos[0].dispatch_event('input')
                        elementos[0].dispatch_event('change')
                        print(f"         📊 Slider: valor 4")
                
                elif campo['tipo'] == 'escala':
                    elementos = campo['elementos']
                    if elementos:
                        # Seleccionar 4 de 5 (positivo pero no extremo)
                        idx = min(3, len(elementos) - 1)  # Índice 3 = valor 4
                        elementos[idx].click(force=True)
                        print(f"         📏 Escala: opción {idx + 1} de {len(elementos)}")
                
                elif campo['tipo'] == 'escala_coords':
                    elementos = campo['elementos']
                    if elementos:
                        # Ordenar por valor y seleccionar 4
                        elementos.sort(key=lambda x: x.get('valor', 0))
                        for elem in elementos:
                            if elem.get('valor') == 4:
                                self.page.mouse.click(elem['x'], elem['y'])
                                print(f"         📏 Escala click: valor 4 en ({elem['x']}, {elem['y']})")
                                break
                        else:
                            # Si no hay 4, seleccionar el penúltimo
                            if len(elementos) >= 2:
                                elem = elementos[-2]
                                self.page.mouse.click(elem['x'], elem['y'])
                                print(f"         📏 Escala click: valor {elem.get('valor')} en ({elem['x']}, {elem['y']})")
                
                elif campo['tipo'] == 'escala_visual':
                    elementos = campo['elementos']
                    if elementos:
                        # Buscar el elemento con valor 4 (positivo pero no extremo)
                        elementos_ordenados = sorted(elementos, key=lambda x: x.get('valor', 0))
                        target = None
                        for elem in elementos_ordenados:
                            if elem.get('valor') == 4:
                                target = elem
                                break
                        
                        if not target and len(elementos_ordenados) >= 2:
                            target = elementos_ordenados[-2]  # Penúltimo
                        
                        if target:
                            x, y = target['x'], target['y']
                            print(f"         📏 Escala visual: clic en valor {target.get('valor')} en ({int(x)}, {int(y)})")
                            self.page.mouse.click(x, y)
                            time.sleep(0.5)
                
                elif campo['tipo'] == 'card_sorting':
                    datos = campo.get('datos', {})
                    self._ejecutar_card_sorting(datos)
                        
                time.sleep(0.5)  # Pequeña pausa entre campos
                        
            except Exception as e:
                print(f"         ⚠️ Error completando campo {campo['tipo']}: {e}")
                continue
    
    def _ejecutar_card_sorting(self, datos: dict):
        """Ejecuta el drag & drop para preguntas de card sorting."""
        try:
            tarjetas = datos.get('tarjetas', [])
            grupos = datos.get('grupos', [])
            
            if not tarjetas or not grupos:
                print(f"         ⚠️ No hay tarjetas o grupos detectados")
                return
            
            print(f"         🃏 Organizando {len(tarjetas)} tarjetas en {len(grupos)} grupos...")
            
            # Asignación inteligente basada en el contenido
            asignaciones = {
                # Educación
                'Tutorías Escolares': 'Educación',
                'Mentoría Profesional': 'Educación',
                'Tutorías': 'Educación',
                'Mentoría': 'Educación',
                # Medio Ambiente
                'Limpieza de Playas': 'Medio Ambiente',
                'Sembratón': 'Medio Ambiente',
                'Limpieza': 'Medio Ambiente',
                # Ayuda Humanitaria
                'Donación de Ropa': 'Ayuda Humanitaria',
                'Construcción de Viviendas': 'Ayuda Humanitaria',
                'Donación': 'Ayuda Humanitaria',
                'Construcción': 'Ayuda Humanitaria',
                # Impacto Social (default)
            }
            
            # Crear mapa de grupos por título
            grupos_map = {}
            for g in grupos:
                for key in ['Impacto Social', 'Medio Ambiente', 'Educación', 'Ayuda Humanitaria']:
                    if key in g['titulo']:
                        grupos_map[key] = g
                        break
            
            tarjetas_movidas = 0
            
            for tarjeta in tarjetas:
                # Determinar a qué grupo va esta tarjeta
                grupo_destino = None
                texto_tarjeta = tarjeta['texto']
                
                # Buscar asignación predefinida
                for texto_clave, categoria in asignaciones.items():
                    if texto_clave in texto_tarjeta:
                        if categoria in grupos_map:
                            grupo_destino = grupos_map[categoria]
                            break
                
                # Si no hay asignación, usar el primer grupo disponible
                if not grupo_destino and grupos:
                    grupo_destino = grupos[tarjetas_movidas % len(grupos)]
                
                if not grupo_destino:
                    continue
                
                # Calcular posiciones
                origen_x = tarjeta['x']
                origen_y = tarjeta['y']
                destino_x = grupo_destino['x']
                destino_y = grupo_destino['y']
                
                try:
                    # Drag and drop con mouse
                    self.page.mouse.move(origen_x, origen_y)
                    time.sleep(0.3)
                    self.page.mouse.down()
                    time.sleep(0.15)
                    
                    # Mover en pasos para simular arrastre real
                    steps = 8
                    for step in range(1, steps + 1):
                        inter_x = origen_x + (destino_x - origen_x) * step / steps
                        inter_y = origen_y + (destino_y - origen_y) * step / steps
                        self.page.mouse.move(inter_x, inter_y)
                        time.sleep(0.03)
                    
                    time.sleep(0.1)
                    self.page.mouse.up()
                    time.sleep(0.4)
                    
                    tarjetas_movidas += 1
                    cat_nombre = grupo_destino.get('titulo', 'Grupo')[:20]
                    print(f"         🎯 '{texto_tarjeta[:25]}' -> {cat_nombre}")
                    
                except Exception as drag_error:
                    print(f"         ⚠️ Error arrastrando '{texto_tarjeta[:20]}': {drag_error}")
            
            print(f"         ✅ Card sorting: {tarjetas_movidas}/{len(tarjetas)} tarjetas movidas")
            time.sleep(1)
            
        except Exception as e:
            print(f"         ⚠️ Error en card sorting: {e}")

    def _avanzar_pregunta(self) -> bool:
        """Intenta avanzar a la siguiente pregunta."""
        try:
            # Esperar un poco para que el botón se habilite después de responder
            time.sleep(1)
            
            botones = [
                'button:has-text("Continuar")',
                'button:has-text("Detener grabación")',  # Para tareas de grabación
                'button:has-text("Siguiente")',
                'button:has-text("Next")',
                'button:has-text("Enviar")',
                'button:has-text("Finalizar")',
            ]
            
            for selector in botones:
                try:
                    btn = self.page.locator(selector).first
                    if btn.is_visible(timeout=1000):
                        # Verificar si está habilitado
                        is_disabled = btn.is_disabled()
                        if is_disabled:
                            print(f"      ⏳ Botón deshabilitado, esperando...")
                            time.sleep(2)
                            is_disabled = btn.is_disabled()
                        
                        if not is_disabled:
                            btn_text = btn.inner_text()
                            btn.scroll_into_view_if_needed()
                            btn.click()
                            print(f"      🔘 Clic en '{btn_text}'")
                            time.sleep(2)
                            return True
                        else:
                            print(f"      ⚠️ Botón sigue deshabilitado - puede faltar responder")
                except Exception as e:
                    continue
            
            # Intentar con JavaScript si no funcionó el click normal
            clicked = self.page.evaluate("""
                () => {
                    const botones = document.querySelectorAll('button');
                    for (let btn of botones) {
                        const text = btn.innerText?.toLowerCase() || '';
                        if ((text.includes('continuar') || text.includes('siguiente') || 
                             text.includes('detener grabación') || text.includes('detener')) && 
                            !btn.disabled && btn.offsetParent !== null) {
                            btn.click();
                            return true;
                        }
                    }
                    return false;
                }
            """)
            if clicked:
                time.sleep(2)
                return True
            
            return False
        except:
            return False
    
    def _prueba_terminada(self) -> bool:
        """Verifica si la prueba ha terminado."""
        try:
            indicadores = [
                'text=Gracias',
                'text=completada',
                'text=finalizada',
                'text=Thank you',
                'text=Felicitaciones',
            ]
            
            for indicador in indicadores:
                try:
                    elem = self.page.locator(indicador).first
                    if elem.is_visible(timeout=1000):
                        return True
                except:
                    continue
            
            return False
        except:
            return False

    def navegar_a_url(self, url: str) -> bool:
        """
        Navega a una URL específica.
        
        Args:
            url: URL del formulario o página
        """
        if not self.navegador_iniciado:
            if not self.iniciar_navegador():
                return False
        
        try:
            print(f"\n🔗 Navegando a: {url}")
            
            # Para Google Forms, asegurar que usamos la URL pública
            if 'docs.google.com/forms' in url:
                # Limpiar parámetros que puedan forzar login
                if '?' in url:
                    base_url = url.split('?')[0]
                    url = base_url
                print(f"   📋 URL limpia: {url}")
            
            self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
            time.sleep(3)  # Esperar carga completa
            
            # Verificar si estamos en página de login
            current_url = self.page.url
            if 'accounts.google.com' in current_url or 'signin' in current_url.lower():
                print("   ⚠️ Detectada página de login de Google")
                print("   🔄 Este formulario requiere autenticación.")
                print("   💡 Asegúrate que el formulario sea público (no requiera login)")
                return False
            
            print(f"   ✅ Página cargada: {self.page.title()}")
            return True
        except Exception as e:
            print(f"   ❌ Error navegando: {e}")
            return False
    
    def analizar_formulario(self) -> List[Dict]:
        """
        Analiza la página actual y encuentra todos los campos del formulario.
        
        Returns:
            Lista de campos encontrados con sus propiedades
        """
        print("\n🔍 Analizando formulario...")
        
        campos = []
        
        try:
            # Detectar si es Google Forms
            es_gforms = 'docs.google.com/forms' in self.page.url
            
            if es_gforms:
                print("   📋 Detectado Google Forms")
                campos = self._analizar_google_forms()
            else:
                campos = self._analizar_formulario_generico()
            
            print(f"   ✅ Encontrados {len(campos)} campos")
            for i, campo in enumerate(campos, 1):
                nombre = campo.get('pregunta', campo.get('nombre', campo['tipo']))
                print(f"      {i}. [{campo['tipo']}] {nombre[:50]}...")
            
            return campos
            
        except Exception as e:
            print(f"   ❌ Error analizando: {e}")
            return []
    
    def _analizar_google_forms(self) -> List[Dict]:
        """Analiza campos específicos de Google Forms."""
        campos = []
        
        try:
            # Esperar a que cargue el formulario
            self.page.wait_for_selector('[role="listitem"], .freebirdFormviewerViewNumberedItemContainer', timeout=10000)
            
            # Scroll completo para cargar todas las preguntas
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            self.page.evaluate("window.scrollTo(0, 0)")
            time.sleep(0.5)
            
            # Buscar todos los contenedores de preguntas
            items = self.page.query_selector_all('[role="listitem"]')
            
            if not items:
                items = self.page.query_selector_all('.freebirdFormviewerViewNumberedItemContainer')
            
            for idx, item in enumerate(items):
                try:
                    # Obtener título de la pregunta
                    titulo_elem = item.query_selector('[role="heading"], .freebirdFormviewerComponentsQuestionBaseTitle')
                    titulo = titulo_elem.inner_text() if titulo_elem else f"Pregunta {idx+1}"
                    titulo = titulo.strip()
                    
                    # Detectar tipo de campo
                    
                    # 0. Campo de HORA/TIEMPO
                    input_hora = item.query_selector('input[type="text"][aria-label*="Hora"], input[type="text"][aria-label*="hora"], input[aria-label*="Hour"], input[data-type="hour"]')
                    if not input_hora:
                        # Buscar por contexto de hora
                        if 'hora' in titulo.lower() or 'time' in titulo.lower() or 'jornada' in titulo.lower():
                            input_hora = item.query_selector('input[type="text"]')
                    
                    if input_hora and ('hora' in titulo.lower() or 'jornada' in titulo.lower()):
                        campos.append({
                            'tipo': 'gform_hora',
                            'elemento': input_hora,
                            'pregunta': titulo,
                            'indice': idx
                        })
                        continue
                    
                    # 1. Texto corto
                    input_texto = item.query_selector('input[type="text"]')
                    if input_texto:
                        campos.append({
                            'tipo': 'gform_texto',
                            'selector': f'[role="listitem"]:nth-of-type({idx+1}) input[type="text"]',
                            'elemento': input_texto,
                            'pregunta': titulo,
                            'indice': idx
                        })
                        continue
                    
                    # 2. Texto largo (textarea)
                    textarea = item.query_selector('textarea')
                    if textarea:
                        campos.append({
                            'tipo': 'gform_textarea',
                            'selector': f'[role="listitem"]:nth-of-type({idx+1}) textarea',
                            'elemento': textarea,
                            'pregunta': titulo,
                            'indice': idx
                        })
                        continue
                    
                    # 3. Opciones múltiples (radio)
                    radios = item.query_selector_all('[role="radio"]')
                    if radios:
                        opciones = []
                        for r in radios:
                            label = r.get_attribute('aria-label') or r.inner_text()
                            opciones.append(label.strip())
                        
                        campos.append({
                            'tipo': 'gform_radio',
                            'selector': f'[role="listitem"]:nth-of-type({idx+1}) [role="radio"]',
                            'elementos': radios,
                            'pregunta': titulo,
                            'opciones': opciones,
                            'indice': idx
                        })
                        continue
                    
                    # 4. Checkboxes
                    checks = item.query_selector_all('[role="checkbox"]')
                    if checks:
                        opciones = []
                        for c in checks:
                            label = c.get_attribute('aria-label') or c.inner_text()
                            opciones.append(label.strip())
                        
                        campos.append({
                            'tipo': 'gform_checkbox',
                            'selector': f'[role="listitem"]:nth-of-type({idx+1}) [role="checkbox"]',
                            'elementos': checks,
                            'pregunta': titulo,
                            'opciones': opciones,
                            'indice': idx
                        })
                        continue
                    
                    # 5. Escala lineal
                    escala_container = item.query_selector('[role="radiogroup"]')
                    if escala_container:
                        radios_escala = escala_container.query_selector_all('[role="radio"]')
                        if radios_escala:
                            labels = item.query_selector_all('.freebirdMaterialScalecontentLabel, .e2CuFe')
                            min_label = labels[0].inner_text() if labels else "1"
                            max_label = labels[-1].inner_text() if len(labels) > 1 else str(len(radios_escala))
                            
                            campos.append({
                                'tipo': 'gform_escala',
                                'selector': f'[role="listitem"]:nth-of-type({idx+1}) [role="radio"]',
                                'elementos': radios_escala,
                                'pregunta': titulo,
                                'min_label': min_label,
                                'max_label': max_label,
                                'rango': len(radios_escala),
                                'indice': idx
                            })
                            continue
                    
                    # 6. Dropdown
                    dropdown = item.query_selector('[role="listbox"]')
                    if dropdown:
                        campos.append({
                            'tipo': 'gform_dropdown',
                            'selector': f'[role="listitem"]:nth-of-type({idx+1}) [role="listbox"]',
                            'elemento': dropdown,
                            'pregunta': titulo,
                            'indice': idx
                        })
                        continue
                    
                except Exception as e:
                    print(f"      ⚠️ Error en pregunta {idx+1}: {e}")
                    continue
            
            return campos
            
        except Exception as e:
            print(f"   ⚠️ Error analizando Google Forms: {e}")
            return []
    
    def _analizar_formulario_generico(self) -> List[Dict]:
        """Analiza formularios genéricos (no Google Forms)."""
        campos = []
        
        try:
            # Buscar inputs de texto
            inputs = self.page.query_selector_all("input[type='text'], input[type='email'], input[type='tel'], input[type='number'], input:not([type])")
            for i, inp in enumerate(inputs):
                nombre = inp.get_attribute('name') or inp.get_attribute('aria-label') or inp.get_attribute('placeholder') or f'campo_texto_{i}'
                campos.append({
                    'tipo': 'texto',
                    'elemento': inp,
                    'nombre': nombre,
                    'placeholder': inp.get_attribute('placeholder') or '',
                    'indice': i
                })
            
            # Buscar textareas
            textareas = self.page.query_selector_all("textarea")
            for i, ta in enumerate(textareas):
                nombre = ta.get_attribute('name') or ta.get_attribute('aria-label') or f'textarea_{i}'
                campos.append({
                    'tipo': 'textarea',
                    'elemento': ta,
                    'nombre': nombre,
                    'indice': i
                })
            
            # Buscar selects
            selects = self.page.query_selector_all("select")
            for i, sel in enumerate(selects):
                opciones = []
                options = sel.query_selector_all("option")
                for opt in options:
                    opciones.append(opt.inner_text())
                
                campos.append({
                    'tipo': 'select',
                    'elemento': sel,
                    'nombre': sel.get_attribute('name') or f'select_{i}',
                    'opciones': opciones,
                    'indice': i
                })
            
            # Buscar radio buttons
            radios = self.page.query_selector_all("input[type='radio']")
            grupos = {}
            for radio in radios:
                nombre = radio.get_attribute('name') or 'radio_group'
                if nombre not in grupos:
                    grupos[nombre] = {'opciones': [], 'elementos': []}
                grupos[nombre]['elementos'].append(radio)
                label = radio.get_attribute('value') or ''
                grupos[nombre]['opciones'].append(label)
            
            for nombre, grupo in grupos.items():
                campos.append({
                    'tipo': 'radio',
                    'nombre': nombre,
                    'elementos': grupo['elementos'],
                    'opciones': grupo['opciones']
                })
            
            return campos
            
        except Exception as e:
            print(f"   ⚠️ Error analizando formulario genérico: {e}")
            return []
    
    def generar_respuestas(self, campos: List[Dict], contexto: str = "") -> Dict:
        """
        Usa IA para generar respuestas coherentes para cada campo.
        MEJORADO: Genera respuestas más largas y coherentes para texto.
        
        Args:
            campos: Lista de campos del formulario
            contexto: Contexto adicional para las respuestas
        
        Returns:
            Diccionario con respuestas para cada campo
        """
        print("\n🧠 Generando respuestas coherentes con IA...")
        
        # Preparar descripción de campos con más detalle
        campos_desc = []
        for i, campo in enumerate(campos):
            pregunta = campo.get('pregunta', campo.get('nombre', ''))
            tipo = campo['tipo']
            
            # Descripción más clara del tipo
            tipo_desc = tipo
            if tipo == 'gform_radio':
                tipo_desc = 'SELECCIÓN ÚNICA (elige UNA opción)'
            elif tipo == 'gform_checkbox':
                tipo_desc = 'SELECCIÓN MÚLTIPLE (puedes elegir varias)'
            elif tipo == 'gform_escala':
                tipo_desc = f'ESCALA del 1 al {campo.get("rango", 5)}'
            elif tipo == 'gform_texto':
                tipo_desc = 'TEXTO CORTO (máximo 100 caracteres)'
            elif tipo == 'gform_textarea':
                tipo_desc = 'TEXTO LARGO (párrafo completo, 200-300 caracteres)'
            elif tipo == 'gform_hora':
                tipo_desc = 'HORA (formato HH:MM)'
            
            desc = f"PREGUNTA {i}: {pregunta}\n   Tipo: {tipo_desc}"
            
            if 'opciones' in campo and campo['opciones']:
                for j, opt in enumerate(campo['opciones']):
                    desc += f"\n   - Opción {j}: {opt}"
            if 'rango' in campo:
                desc += f"\n   Escala: 1={campo.get('min_label', 'mínimo')} hasta {campo['rango']}={campo.get('max_label', 'máximo')}"
            
            campos_desc.append(desc)
        
        prompt = f"""Eres un usuario real completando una encuesta de usabilidad. Responde de manera COHERENTE, HONESTA y REALISTA.

PERFIL DEL USUARIO:
- Profesional de 35 años con experiencia en tecnología
- Trabajas en una oficina con buen ambiente laboral
- Tienes opiniones moderadas (ni muy positivas ni muy negativas)
- Eres honesto y reflexivo en tus respuestas
- Cuando haces sugerencias, son específicas y útiles

ENCUESTA A COMPLETAR:
{chr(10).join(campos_desc)}

REGLAS CRÍTICAS DE RESPUESTA:
1. Para SELECCIÓN ÚNICA: responde SOLO con el número de la opción (0, 1, 2, etc.)
2. Para SELECCIÓN MÚLTIPLE: responde con lista de números [0, 2]. NO selecciones "Otro" a menos que sea necesario
3. Para ESCALA: responde con un número del 1 al máximo. VARÍA tus respuestas (no todo 5)
4. Para TEXTO CORTO: 50-80 caracteres, respuesta directa y específica
5. Para TEXTO LARGO: 150-250 caracteres, párrafo completo con justificación
6. Para HORA: formato "HH:MM"

REGLAS DE COHERENCIA IMPORTANTE:
- Si pregunta pide eliminar un paso: especifica EXACTAMENTE cuál y POR QUÉ
- Si pregunta pide opinión: da una opinión clara y justificada
- Si pregunta sobre dificultad: da una respuesta proporcional (no extrema)
- NUNCA respuestas vacías, genéricas o "N/A"
- Las respuestas de texto deben ser PROPIAS y CONTEXTUALES

{f"CONTEXTO DE LA ENCUESTA: {contexto}" if contexto else ""}

Responde SOLO con JSON válido (sin explicaciones ni markdown):
{{"respuestas": [{{"indice": 0, "valor": X}}, {{"indice": 1, "valor": Y}}, ...]}}

Donde X, Y son: número para opciones/escalas, "texto completo" para texto, "HH:MM" para hora.
IMPORTANTE: Para campos de texto, responde con la respuesta COMPLETA (sin truncar)."""
        
        try:
            response = self.modelo.generate_content(prompt)
            texto = response.text.strip()
            
            # Limpiar JSON más agresivamente
            if "```" in texto:
                # Extraer solo el JSON
                import re
                json_match = re.search(r'\{[\s\S]*\}', texto)
                if json_match:
                    texto = json_match.group()
            
            texto = texto.replace("```json", "").replace("```", "").strip()
            
            resultado = json.loads(texto)
            
            respuestas = {}
            for r in resultado.get('respuestas', []):
                idx = r.get('indice', 0)
                respuestas[idx] = r.get('valor', '')
            
            print(f"   ✅ Generadas {len(respuestas)} respuestas coherentes")
            
            # Mostrar preview de respuestas (más largo para texto)
            for idx, valor in respuestas.items():
                if idx < len(campos):
                    campo = campos[idx]
                    pregunta = campo.get('pregunta', campo.get('nombre', ''))[:50]
                    valor_str = str(valor)
                    # Para texto largo, mostrar más caracteres
                    if campo['tipo'] in ['gform_textarea', 'textarea']:
                        valor_preview = valor_str[:80] + ("..." if len(valor_str) > 80 else "")
                    else:
                        valor_preview = valor_str[:40]
                    print(f"      • {pregunta}... → {valor_preview}")
            
            return respuestas
            
        except Exception as e:
            print(f"   ❌ Error generando respuestas: {e}")
            print(f"   Texto recibido: {texto[:200] if 'texto' in dir() else 'N/A'}")
            return {}
    
    def completar_formulario(self, campos: List[Dict], respuestas: Dict) -> bool:
        """
        Completa el formulario con las respuestas generadas.
        
        Args:
            campos: Lista de campos del formulario
            respuestas: Diccionario con respuestas para cada campo
        """
        print("\n✍️ Completando formulario...")
        
        completados = 0
        
        for idx, campo in enumerate(campos):
            if idx not in respuestas:
                continue
            
            valor = respuestas[idx]
            tipo = campo['tipo']
            
            try:
                pregunta = campo.get('pregunta', campo.get('nombre', tipo))[:35]
                print(f"   📝 {pregunta}...")
                
                if tipo == 'gform_hora':
                    # Campo de hora - puede tener múltiples inputs (hora y minutos separados)
                    elemento = campo.get('elemento')
                    if elemento:
                        elemento.scroll_into_view_if_needed()
                        time.sleep(0.2)
                        
                        # Asegurar formato HH:MM
                        hora_str = str(valor).strip()
                        if ':' not in hora_str:
                            hora_str = "18:00"  # Valor por defecto
                        
                        partes = hora_str.split(':')
                        hora = partes[0].zfill(2)
                        minutos = partes[1].zfill(2) if len(partes) > 1 else "00"
                        
                        # Verificar si hay inputs separados para hora y minutos
                        parent = elemento.evaluate("el => el.closest('[role=\"listitem\"]')?.outerHTML?.substring(0, 500)")
                        
                        # Intentar llenar con valor completo
                        elemento.click()
                        elemento.fill('')
                        elemento.fill(hora)
                        elemento.press('Tab')
                        time.sleep(0.2)
                        
                        # Buscar input de minutos (si existe)
                        try:
                            container = campo.get('container') or self.page.locator('[role="listitem"]').filter(has_text=campo.get('pregunta', ''))
                            inputs_hora = container.locator('input[type="text"]').all()
                            if len(inputs_hora) > 1:
                                # Hay input separado para minutos
                                inputs_hora[1].click()
                                inputs_hora[1].fill('')
                                inputs_hora[1].fill(minutos)
                                inputs_hora[1].press('Tab')
                        except:
                            pass
                        
                        completados += 1
                        print(f"      ✓ Hora: {hora}:{minutos}")
                
                elif tipo in ['texto', 'textarea', 'gform_texto', 'gform_textarea']:
                    elemento = campo.get('elemento')
                    if elemento:
                        elemento.click()
                        time.sleep(0.2)
                        elemento.fill('')  # Limpiar
                        time.sleep(0.1)
                        
                        # Para textarea, asegurar que el texto se rellene completamente
                        texto_completo = str(valor).strip()
                        
                        # Si es textarea y el texto es corto, es porque Gemini no generó bien
                        if tipo in ['textarea', 'gform_textarea'] and len(texto_completo) < 50:
                            # Generar respuesta más larga
                            pregunta_texto = campo.get('pregunta', '')
                            if 'eliminar' in pregunta_texto.lower():
                                texto_completo = "El paso que eliminaría sería la confirmación de la dirección, porque ya está validada en el sistema y repetirla es innecesario."
                            elif 'probable' in pregunta_texto.lower() or 'recomend' in pregunta_texto.lower():
                                texto_completo = "Consideraría recomendar esta plataforma, tiene una interfaz intuitiva y el proceso es más fluido que otros sitios similares."
                            elif 'exigente' in pregunta_texto.lower() or 'difícil' in pregunta_texto.lower():
                                texto_completo = "El formulario fue bastante sencillo de completar, los campos estaban claramente etiquetados y la navegación era intuitiva."
                            else:
                                # Respuesta genérica pero aceptable
                                texto_completo = "La plataforma presenta una interfaz clara y las instrucciones son fáciles de seguir. El proceso es intuitivo y bien organizado."
                        
                        # Usar typing en lugar de fill para mejor compatibilidad
                        elemento.type(texto_completo, delay=10)
                        time.sleep(0.3)
                        
                        completados += 1
                        valor_preview = texto_completo[:60]
                        print(f"      ✓ Texto largo: {valor_preview}...")
                    
                elif tipo == 'select':
                    elemento = campo.get('elemento')
                    if elemento and isinstance(valor, int):
                        opciones = campo.get('opciones', [])
                        if valor < len(opciones):
                            elemento.select_option(index=valor)
                            completados += 1
                    
                elif tipo in ['radio', 'gform_radio']:
                    elementos = campo.get('elementos', [])
                    idx_val = None
                    
                    # Determinar el índice a seleccionar
                    if isinstance(valor, int):
                        idx_val = valor
                    elif isinstance(valor, str):
                        if valor.isdigit():
                            idx_val = int(valor)
                        else:
                            # Buscar por texto de la opción
                            opciones = campo.get('opciones', [])
                            for i, opt in enumerate(opciones):
                                if valor.lower() in opt.lower():
                                    idx_val = i
                                    break
                    
                    if idx_val is not None and idx_val < len(elementos):
                        try:
                            # Scroll al elemento primero
                            elementos[idx_val].scroll_into_view_if_needed()
                            time.sleep(0.2)
                            # Click con force para elementos ocultos
                            elementos[idx_val].click(force=True)
                            completados += 1
                            print(f"      ✓ Seleccionado opción {idx_val}")
                        except Exception as e:
                            print(f"      ⚠️ Error click radio: {e}")
                            # Intentar con JavaScript
                            try:
                                elementos[idx_val].evaluate("el => el.click()")
                                completados += 1
                                print(f"      ✓ Seleccionado con JS")
                            except:
                                pass
                    
                elif tipo == 'gform_escala':
                    elementos = campo.get('elementos', [])
                    idx_val = None
                    
                    if isinstance(valor, int):
                        # Ajustar: valor 1-5 a índice 0-4
                        idx_val = valor - 1 if valor > 0 else 0
                    elif isinstance(valor, str) and valor.isdigit():
                        idx_val = int(valor) - 1
                    
                    if idx_val is not None and 0 <= idx_val < len(elementos):
                        try:
                            elementos[idx_val].scroll_into_view_if_needed()
                            time.sleep(0.2)
                            elementos[idx_val].click(force=True)
                            completados += 1
                            print(f"      ✓ Escala: {valor}")
                        except:
                            try:
                                elementos[idx_val].evaluate("el => el.click()")
                                completados += 1
                            except:
                                pass
                    
                elif tipo in ['checkbox', 'gform_checkbox']:
                    elementos = campo.get('elementos', [])
                    if isinstance(valor, list):
                        for v in valor:
                            if isinstance(v, int) and v < len(elementos):
                                try:
                                    elementos[v].scroll_into_view_if_needed()
                                    elementos[v].click(force=True)
                                except:
                                    elementos[v].evaluate("el => el.click()")
                        completados += 1
                        print(f"      ✓ Checkbox: {valor}")
                    elif isinstance(valor, int) and valor < len(elementos):
                        try:
                            elementos[valor].scroll_into_view_if_needed()
                            elementos[valor].click(force=True)
                            completados += 1
                            print(f"      ✓ Checkbox: {valor}")
                        except:
                            elementos[valor].evaluate("el => el.click()")
                            completados += 1
                
                elif tipo == 'gform_dropdown':
                    # Dropdown de Google Forms
                    elemento = campo.get('elemento')
                    if elemento:
                        try:
                            elemento.scroll_into_view_if_needed()
                            time.sleep(0.2)
                            # Hacer clic para abrir dropdown
                            elemento.click()
                            time.sleep(0.5)
                            
                            # Buscar las opciones del dropdown
                            opciones = self.page.locator('[role="option"], [role="listbox"] [role="presentation"]').all()
                            
                            # Determinar cuál seleccionar
                            if isinstance(valor, int) and valor < len(opciones):
                                opciones[valor].click()
                                completados += 1
                                print(f"      ✓ Dropdown: opción {valor}")
                            elif isinstance(valor, str):
                                # Buscar por texto
                                for opt in opciones:
                                    if valor.lower() in opt.inner_text().lower():
                                        opt.click()
                                        completados += 1
                                        print(f"      ✓ Dropdown: {valor[:20]}")
                                        break
                        except Exception as e:
                            print(f"      ⚠️ Error dropdown: {e}")
                
                time.sleep(0.5)  # Pausa entre campos
                
            except Exception as e:
                print(f"      ⚠️ Error: {e}")
                continue
        
        print(f"\n   ✅ Completados {completados}/{len(respuestas)} campos")
        return completados > 0
    
    def enviar_formulario(self) -> bool:
        """Busca y hace clic en el botón de enviar."""
        print("\n📤 Buscando botón de envío...")
        
        try:
            # Scroll suave al final de la página
            self.page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")
            time.sleep(1.5)
            
            # Esperar un poco más para que todo cargue
            self.page.wait_for_load_state("networkidle", timeout=5000)
            
            # Lista de selectores ordenados por probabilidad de éxito
            selectores = [
                # Google Forms - botón Enviar específico
                'div[role="button"] span:has-text("Enviar")',
                'div[role="button"]:has-text("Enviar")',
                '[aria-label="Enviar"]',
                '[aria-label="Submit"]',
                'span:text-is("Enviar")',
                # Por jsname (común en Google Forms)
                'div[jsname="M2UYVd"]',
                '[jsname="M2UYVd"]',
                # Genérico - botón al final
                'form >> div[role="button"]:last-of-type',
            ]
            
            for selector in selectores:
                try:
                    boton = self.page.locator(selector).first
                    if boton.is_visible(timeout=500):
                        print(f"   → Encontrado botón con: {selector}")
                        boton.scroll_into_view_if_needed()
                        time.sleep(0.3)
                        
                        # Intentar click normal primero
                        try:
                            boton.click(timeout=2000)
                        except:
                            boton.click(force=True)
                        
                        print("   ✅ Clic en botón de envío realizado")
                        time.sleep(3)
                        
                        # Verificar confirmación
                        if self._verificar_envio_exitoso():
                            return True
                        else:
                            print("   ⚠️ No se detectó confirmación, verificando...")
                            # Puede que haya errores de validación
                            errores = self.page.locator('[role="alert"], .freebirdFormviewerViewItemsItemErrorMessage').all()
                            if errores:
                                for err in errores:
                                    if err.is_visible():
                                        print(f"   ⚠️ Error de validación: {err.inner_text()[:50]}")
                            return False
                except Exception as e:
                    continue
            
            # Método de último recurso: JavaScript directo
            print("   → Intentando con JavaScript...")
            resultado = self.page.evaluate("""
                () => {
                    // Buscar botón con texto Enviar
                    const elements = document.querySelectorAll('div[role="button"], button, span');
                    for (let el of elements) {
                        const text = el.innerText || el.textContent || '';
                        if (text.trim() === 'Enviar' || text.trim() === 'Submit') {
                            el.click();
                            return 'clicked: ' + text;
                        }
                    }
                    // Buscar el último botón visible
                    const buttons = document.querySelectorAll('div[role="button"]');
                    if (buttons.length > 0) {
                        const lastBtn = buttons[buttons.length - 1];
                        lastBtn.click();
                        return 'clicked last button';
                    }
                    return 'no button found';
                }
            """)
            
            print(f"   → Resultado JS: {resultado}")
            
            if 'clicked' in resultado:
                time.sleep(3)
                return self._verificar_envio_exitoso()
            
            print("   ❌ No se pudo enviar el formulario")
            return False
            
        except Exception as e:
            print(f"   ❌ Error enviando: {e}")
            return False
    
    def _verificar_envio_exitoso(self) -> bool:
        """Verifica si el formulario se envió correctamente."""
        try:
            # Buscar mensajes de confirmación comunes
            confirmaciones = [
                'text=Se registró tu respuesta',
                'text=respuesta se ha registrado',
                'text=Gracias por',
                'text=Thank you',
                'text=Your response',
                '.freebirdFormviewerViewResponseConfirmationMessage',
            ]
            
            for conf in confirmaciones:
                try:
                    elem = self.page.locator(conf).first
                    if elem.is_visible(timeout=1000):
                        print("   ✅ ¡Confirmación de envío detectada!")
                        return True
                except:
                    continue
            
            # Verificar si la URL cambió (indica envío exitoso)
            current_url = self.page.url
            if 'formResponse' in current_url or 'submitted' in current_url:
                print("   ✅ URL indica envío exitoso")
                return True
            
            return False
        except:
            return False
    
    def ejecutar_prueba(self, url: str, contexto: str = "", enviar: bool = False) -> Dict:
        """
        Ejecuta el proceso completo de prueba en un formulario.
        
        Args:
            url: URL del formulario
            contexto: Contexto para generar respuestas coherentes
            enviar: Si True, envía el formulario al final
        
        Returns:
            Diccionario con resultados de la prueba
        """
        resultado = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'exito': False,
            'campos_encontrados': 0,
            'campos_completados': 0,
            'enviado': False
        }
        
        try:
            # 1. Navegar al formulario
            if not self.navegar_a_url(url):
                return resultado
            
            # 2. Analizar campos
            campos = self.analizar_formulario()
            resultado['campos_encontrados'] = len(campos)
            
            if not campos:
                print("   ⚠️ No se encontraron campos")
                return resultado
            
            # 3. Generar respuestas
            respuestas = self.generar_respuestas(campos, contexto)
            
            if not respuestas:
                print("   ⚠️ No se generaron respuestas")
                return resultado
            
            # 4. Completar formulario
            self.completar_formulario(campos, respuestas)
            resultado['campos_completados'] = len(respuestas)
            
            # 5. Enviar (opcional)
            if enviar:
                resultado['enviado'] = self.enviar_formulario()
            
            resultado['exito'] = True
            
        except Exception as e:
            print(f"\n❌ Error en ejecución: {e}")
            resultado['error'] = str(e)
        
        return resultado
    
    def capturar_pantalla(self, nombre: str = None) -> str:
        """Captura una screenshot de la página actual."""
        if not self.page:
            return None
        
        try:
            nombre = nombre or f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            path = os.path.join(os.path.dirname(__file__), nombre)
            self.page.screenshot(path=path)
            print(f"   📸 Screenshot guardada: {nombre}")
            return path
        except Exception as e:
            print(f"   ⚠️ Error capturando pantalla: {e}")
            return None


# =============================================================================
# INTERFAZ DE EJECUCIÓN AUTOMÁTICA
# =============================================================================

def main():
    """
    Función principal - EJECUCIÓN COMPLETAMENTE AUTOMÁTICA.
    
    Realiza:
    1. Login automático en la plataforma Community Tester
    2. Busca pruebas disponibles
    3. Completa la prueba automáticamente
    4. Sin interacción del usuario
    """
    print("\n" + "="*70)
    print("🤖 AGENTE EJECUTOR DE PRUEBAS v2.0 - MODO AUTOMÁTICO")
    print("   Community Tester - Automatización Completa")
    print("   🌐 Motor: Playwright (Chrome del Sistema / fallback a Chromium)")
    print("="*70)
    
    agente = AgenteEjecutor()
    
    try:
        print("\n" + "─"*70)
        print("📍 INICIANDO PROCESO DE PRUEBA AUTOMÁTICO...")
        print("─"*70)
        
        # Ejecutar la prueba de la plataforma de forma automática
        resultado = agente.ejecutar_prueba_plataforma()
        
        # Mostrar resultados finales
        print("\n" + "="*70)
        print("📊 RESULTADO FINAL DE LA EJECUCIÓN")
        print("="*70)
        print(f"\n✓ Login exitoso: {resultado['login']}")
        print(f"✓ Prueba encontrada: {resultado['prueba_encontrada']}")
        print(f"✓ Prueba iniciada: {resultado['prueba_iniciada']}")
        print(f"✓ Total preguntas: {resultado['preguntas_total']}")
        print(f"✓ Preguntas completadas: {resultado['preguntas_completadas']}")
        print(f"✓ Prueba enviada: {resultado['enviado']}")
        print(f"\n{'✅ EXITO' if resultado['exito'] else '❌ FALLO'}: Ejecución {'completada' if resultado['exito'] else 'con errores'}")
        
        if 'error' in resultado:
            print(f"\n⚠️ Error: {resultado['error']}")
        
        print("\n" + "="*70)
        
        # Dar tiempo para ver el resultado
        time.sleep(2)
        
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cerrar navegador automáticamente
        print("\n🔒 Cerrando navegador...")
        agente.cerrar_navegador()
        print("✅ Proceso finalizado\n")


if __name__ == "__main__":
    main()
