"""
==============================================================================
APLICACIÓN PRINCIPAL - SISTEMA DE ESCANEO INTELIGENTE DE DOCUMENTOS
==============================================================================

Descripción:
    Sistema Flask para procesamiento de documentos mediante OCR (Reconocimiento
    Óptico de Caracteres) con múltiples motores de extracción.

Características:
    - API RESTful con Flask
    - Soporte CORS para peticiones cross-origin
    - Documentación automática con Swagger
    - Conexión a base de datos MySQL
    - Manejo centralizado de errores
    - Múltiples rutas de escaneo y documentos

Autor: OctavoSMG
Versión: 1.0.0
Fecha: 2025
==============================================================================
"""

from flask import Flask
from flask_cors import CORS
from flasgger import Swagger

from db.config import DatabaseConfig
from db.connection import DatabaseConnection
from middlewares.error_handler import register_error_handlers
from routes.scan_routes import scan_bp
from routes.document_routes import document_bp


def crear_aplicacion():
    """
    Factory Pattern para crear y configurar la aplicación Flask.
    
    Este patrón permite:
    - Crear múltiples instancias de la app (útil para testing)
    - Configuración modular y reutilizable
    - Mejor separación de responsabilidades
    
    Returns:
        Flask: Instancia configurada de la aplicación Flask
        
    Example:
        >>> app = crear_aplicacion()
        >>> app.run(debug=True)
    """
    
    # =========================================================================
    # 1. INICIALIZACIÓN DE LA APLICACIÓN
    # =========================================================================
    aplicacion = Flask(__name__)
    
    
    # =========================================================================
    # 2. CONFIGURACIÓN DE BASE DE DATOS
    # =========================================================================
    configuracion_bd = DatabaseConfig.get_instance()
    
    # URI de conexión a MySQL
    aplicacion.config['SQLALCHEMY_DATABASE_URI'] = configuracion_bd.SQLALCHEMY_DATABASE_URI
    
    # Deshabilitar tracking de modificaciones (mejora rendimiento)
    aplicacion.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = configuracion_bd.SQLALCHEMY_TRACK_MODIFICATIONS
    
    
    # =========================================================================
    # 3. CONFIGURACIÓN DE CORS (Cross-Origin Resource Sharing)
    # =========================================================================
    # Permite peticiones desde cualquier origen (frontend React, Angular, etc.)
    CORS(aplicacion)
    
    
    # =========================================================================
    # 4. INICIALIZACIÓN DE BASE DE DATOS
    # =========================================================================
    conexion_bd = DatabaseConnection.get_instance()
    conexion_bd.init_app(aplicacion)
    
    
    # =========================================================================
    # 5. CONFIGURACIÓN DE SWAGGER (Documentación Automática)
    # =========================================================================
    configuracion_swagger = Swagger(aplicacion, template={
        "info": {
            "title": "API de Escaneo Inteligente de Documentos",
            "description": (
                "Sistema automatizado de procesamiento de documentos con OCR. "
                "Soporta extracción de texto mediante Tesseract, EasyOCR y PaddleOCR. "
                "Incluye detección automática de campos y validación de datos."
            ),
            "version": "1.0.0",
            "contact": {
                "name": "AlfaDinamita",
                "email": "soporte@alfadinamita.com"
            }
        },
        "schemes": ["http", "https"],
        "tags": [
            {
                "name": "Escaneo",
                "description": "Endpoints para procesamiento OCR de documentos"
            },
            {
                "name": "Documentos",
                "description": "Gestión y consulta de documentos escaneados"
            }
        ]
    })
    
    
    # =========================================================================
    # 6. REGISTRO DE MIDDLEWARES
    # =========================================================================
    # Manejo centralizado de errores (404, 500, validaciones, etc.)
    register_error_handlers(aplicacion)
    
    
    # =========================================================================
    # 7. REGISTRO DE BLUEPRINTS (RUTAS)
    # =========================================================================
    # Blueprint de rutas de escaneo (/api/scan/*)
    aplicacion.register_blueprint(scan_bp)
    
    # Blueprint de rutas de documentos (/api/documents/*)
    aplicacion.register_blueprint(document_bp)
    
    
    # =========================================================================
    # 8. RUTA RAÍZ (Información del Sistema)
    # =========================================================================
    @aplicacion.route('/')
    def ruta_principal():
        """
        Endpoint de bienvenida con información del sistema.
        
        Returns:
            dict: Información general de la API
            
        Swagger:
            ---
            tags:
              - Sistema
            responses:
              200:
                description: Información del sistema
                schema:
                  type: object
                  properties:
                    mensaje:
                      type: string
                    version:
                      type: string
                    documentacion:
                      type: string
                    estado:
                      type: string
        """
        return {
            'mensaje': 'API de Escaneo Inteligente de Documentos',
            'version': '1.0.0',
            'documentacion': '/apidocs',
            'estado': 'activo',
            'endpoints_disponibles': {
                'escaneo': '/api/scan',
                'documentos': '/api/documents',
                'swagger': '/apidocs'
            }
        }
    
    return aplicacion


# =============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# =============================================================================
if __name__ == '__main__':
    # Banner de inicio
    print("=" * 80)
    print(" " * 15 + "SISTEMA DE ESCANEO INTELIGENTE DE DOCUMENTOS")
    print("=" * 80)
    print()
    print("INFORMACIÓN DEL SERVIDOR:")
    print("   Host: http://localhost:5000")
    print("   Modo: Desarrollo (Debug activado)")
    print()
    print("DOCUMENTACIÓN Y ENDPOINTS:")
    print("   Swagger UI:    http://localhost:5000/apidocs")
    print("   API Escaneo:   http://localhost:5000/api/scan")
    print("   API Docs:      http://localhost:5000/api/documents")
    print()
    print("CARACTERÍSTICAS:")
    print("   - OCR Multi-Motor (Tesseract, EasyOCR, PaddleOCR)")
    print("   - Procesamiento de PDF e Imágenes")
    print("   - Extracción automática de campos")
    print("   - Validación de datos")
    print("   - API RESTful documentada")
    print()
    print("=" * 80)
    print("Servidor iniciando...")
    print("=" * 80)
    print()
    
    # Crear y ejecutar aplicación
    aplicacion = crear_aplicacion()
    aplicacion.run(
        host='0.0.0.0',      # Accesible desde cualquier IP
        port=5000,           # Puerto estándar
        debug=True,          # Modo desarrollo con auto-reload
        threaded=True        # Soporte para múltiples peticiones simultáneas
    )