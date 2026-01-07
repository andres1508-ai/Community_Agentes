#!/usr/bin/env python3
"""
Script de ejecución para el Agente Ejecutor.
Ejecuta automáticamente las pruebas en la plataforma Community Tester.
"""

import sys
import os

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Agregar el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar el agente
from agente_ejecutor import main

if __name__ == "__main__":
    print("\n" + "="*70)
    print("INICIANDO AGENTE EJECUTOR - MODO AUTOMATICO")
    print("="*70)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Ejecución cancelada por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
