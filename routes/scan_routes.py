"""
==============================================================================
MODULO DE RUTAS - ESCANEO DE DOCUMENTOS
==============================================================================

Descripcion:
    Blueprint de Flask que define los endpoints para el procesamiento OCR
    de documentos. Gestiona el inicio, procesamiento y seguimiento de 
    trabajos de escaneo.

Endpoints:
    POST   /api/scan/start          - Iniciar nuevo trabajo de escaneo
    POST   /api/scan/process/<id>   - Procesar trabajo de escaneo
    GET    /api/scan/status/<id>    - Consultar estado del trabajo

Autor: EMPROSERVIS
Version: 1.0.0
==============================================================================
"""

from flask import Blueprint, request, jsonify
from controllers.scanner_controller import ScannerController
from models.scan_job import ScanJob


scan_bp = Blueprint('scan', __name__, url_prefix='/api/scan')


@scan_bp.route('/start', methods=['POST'])
def iniciar_escaneo():
    """
    ---
    tags:
      - Escaneo
    summary: Iniciar trabajo de escaneo OCR
    description: Crea un nuevo trabajo de escaneo para procesar documentos en una carpeta
    parameters:
      - name: body
        in: body
        required: true
        description: Ruta de la carpeta a escanear
        schema:
          type: object
          required:
            - folder_path
          properties:
            folder_path:
              type: string
              description: Ruta absoluta de la carpeta con documentos
              example: "C:/Documentos/Facturas"
    responses:
      200:
        description: Escaneo iniciado correctamente
        schema:
          type: object
          properties:
            success:
              type: boolean
            job_id:
              type: integer
            message:
              type: string
            data:
              type: object
      400:
        description: Parametros invalidos
      500:
        description: Error interno del servidor
    """
    try:
        datos_request = request.get_json()
        ruta_carpeta = datos_request.get('folder_path')
        
        if not ruta_carpeta:
            return jsonify({
                'success': False,
                'message': 'Debe proporcionar una ruta de carpeta valida',
                'error': 'PARAMETRO_FALTANTE'
            }), 400
        
        controlador_escaneo = ScannerController.get_instance()
        resultado = controlador_escaneo.start_scan(ruta_carpeta)
        
        return jsonify({
            'success': True,
            'job_id': resultado['id'],
            'message': 'Escaneo iniciado correctamente',
            'data': resultado
        }), 200
    
    except ValueError as error_validacion:
        return jsonify({
            'success': False,
            'message': str(error_validacion),
            'error': 'ERROR_VALIDACION'
        }), 400
    
    except Exception as error:
        return jsonify({
            'success': False,
            'message': f'Error al iniciar escaneo: {str(error)}',
            'error': 'ERROR_INTERNO'
        }), 500


@scan_bp.route('/process/<int:job_id>', methods=['POST'])
def procesar_escaneo(job_id):
    """
    ---
    tags:
      - Escaneo
    summary: Procesar trabajo de escaneo
    description: Ejecuta el procesamiento OCR de documentos de un trabajo
    parameters:
      - name: job_id
        in: path
        type: integer
        required: true
        description: ID del trabajo de escaneo
        example: 123
    responses:
      200:
        description: Procesamiento completado
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            data:
              type: object
      404:
        description: Trabajo no encontrado
      500:
        description: Error en procesamiento
    """
    try:
        controlador_escaneo = ScannerController.get_instance()
        resultado = controlador_escaneo.process_scan(job_id)
        
        return jsonify({
            'success': True,
            'message': 'Escaneo completado correctamente',
            'data': resultado
        }), 200
    
    except ValueError as error_validacion:
        return jsonify({
            'success': False,
            'message': str(error_validacion),
            'error': 'TRABAJO_NO_ENCONTRADO'
        }), 404
    
    except Exception as error:
        return jsonify({
            'success': False,
            'message': f'Error al procesar escaneo: {str(error)}',
            'error': 'ERROR_PROCESAMIENTO'
        }), 500


@scan_bp.route('/status/<int:job_id>', methods=['GET'])
def obtener_estado(job_id):
    """
    ---
    tags:
      - Escaneo
    summary: Consultar estado del trabajo
    description: Obtiene informacion detallada del estado de un trabajo de escaneo
    parameters:
      - name: job_id
        in: path
        type: integer
        required: true
        description: ID del trabajo de escaneo
        example: 123
    responses:
      200:
        description: Estado obtenido correctamente
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: object
              properties:
                id:
                  type: integer
                status:
                  type: string
                  enum: [pending, processing, completed, failed, cancelled]
                progress_percentage:
                  type: number
      404:
        description: Trabajo no encontrado
      500:
        description: Error interno
    """
    try:
        trabajo_escaneo = ScanJob.query.get(job_id)
        
        if not trabajo_escaneo:
            return jsonify({
                'success': False,
                'message': f'Trabajo de escaneo con ID {job_id} no encontrado',
                'error': 'TRABAJO_NO_ENCONTRADO'
            }), 404
        
        datos_trabajo = trabajo_escaneo.to_dict()
        
        return jsonify({
            'success': True,
            'data': datos_trabajo
        }), 200
    
    except Exception as error:
        return jsonify({
            'success': False,
            'message': f'Error al consultar estado: {str(error)}',
            'error': 'ERROR_CONSULTA'
        }), 500