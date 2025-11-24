"""
==============================================================================
MODULO DE RUTAS - GESTION DE DOCUMENTOS
==============================================================================

Descripcion:
    Blueprint de Flask que define los endpoints para la gestion de documentos
    escaneados. Permite consultar, descargar y unificar documentos procesados
    mediante OCR.

Endpoints:
    GET    /api/documents/<job_id>              - Listar documentos de un trabajo
    GET    /api/documents/<doc_id>/fields       - Obtener campos de un documento
    GET    /api/documents/download/<doc_id>     - Descargar PDF generado
    POST   /api/documents/unify/<job_id>        - Unificar PDFs de un trabajo
    GET    /api/documents/problematic/<job_id>  - Listar documentos problematicos
    GET    /api/documents/export-excel/<job_id> - Exportar datos a Excel consolidado

Autor: EMPROSERVIS
Version: 1.1.0
==============================================================================
"""

from flask import Blueprint, jsonify, send_file
from models.scanned_document import ScannedDocument
from controllers.unifier_controller import UnifierController
from controllers.excel_exporter import ExcelExporter


document_bp = Blueprint('documents', __name__, url_prefix='/api/documents')


@document_bp.route('/<int:job_id>', methods=['GET'])
def obtener_documentos(job_id):
    """
    ---
    tags:
      - Documentos
    summary: Listar documentos de un trabajo
    description: Obtiene todos los documentos procesados de un trabajo de escaneo
    parameters:
      - name: job_id
        in: path
        type: integer
        required: true
        description: ID del trabajo de escaneo
        example: 123
    responses:
      200:
        description: Lista de documentos obtenida correctamente
        schema:
          type: object
          properties:
            success:
              type: boolean
            count:
              type: integer
            data:
              type: array
      500:
        description: Error interno del servidor
    """
    try:
        documentos = ScannedDocument.query.filter_by(scan_job_id=job_id).all()
        
        return jsonify({
            'success': True,
            'count': len(documentos),
            'data': [doc.to_dict() for doc in documentos]
        }), 200
    
    except Exception as error:
        return jsonify({
            'success': False,
            'message': f'Error al obtener documentos: {str(error)}',
            'error': 'ERROR_CONSULTA'
        }), 500


@document_bp.route('/<int:doc_id>/fields', methods=['GET'])
def obtener_campos(doc_id):
    """
    ---
    tags:
      - Documentos
    summary: Obtener campos de un documento
    description: Recupera todos los campos extraidos de un documento especifico
    parameters:
      - name: doc_id
        in: path
        type: integer
        required: true
        description: ID del documento
        example: 456
    responses:
      200:
        description: Campos obtenidos correctamente
        schema:
          type: object
          properties:
            success:
              type: boolean
            document:
              type: object
            fields:
              type: array
      404:
        description: Documento no encontrado
      500:
        description: Error interno del servidor
    """
    try:
        documento = ScannedDocument.query.get(doc_id)
        
        if not documento:
            return jsonify({
                'success': False,
                'message': f'Documento con ID {doc_id} no encontrado',
                'error': 'DOCUMENTO_NO_ENCONTRADO'
            }), 404
        
        return jsonify({
            'success': True,
            'document': documento.to_dict(),
            'fields': [campo.to_dict() for campo in documento.fields]
        }), 200
    
    except Exception as error:
        return jsonify({
            'success': False,
            'message': f'Error al obtener campos: {str(error)}',
            'error': 'ERROR_CONSULTA'
        }), 500


@document_bp.route('/download/<int:doc_id>', methods=['GET'])
def descargar_documento(doc_id):
    """
    ---
    tags:
      - Documentos
    summary: Descargar PDF generado
    description: Descarga el archivo PDF procesado de un documento
    parameters:
      - name: doc_id
        in: path
        type: integer
        required: true
        description: ID del documento
        example: 456
    produces:
      - application/pdf
    responses:
      200:
        description: Archivo PDF descargado
        content:
          application/pdf:
            schema:
              type: string
              format: binary
      404:
        description: PDF no encontrado
      500:
        description: Error al descargar archivo
    """
    try:
        documento = ScannedDocument.query.get(doc_id)
        
        if not documento or not documento.output_pdf_path:
            return jsonify({
                'success': False,
                'message': 'PDF no encontrado o no generado',
                'error': 'PDF_NO_DISPONIBLE'
            }), 404
        
        return send_file(
            documento.output_pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'documento_{doc_id}.pdf'
        )
    
    except FileNotFoundError:
        return jsonify({
            'success': False,
            'message': 'Archivo PDF no existe en el sistema',
            'error': 'ARCHIVO_NO_EXISTE'
        }), 404
    
    except Exception as error:
        return jsonify({
            'success': False,
            'message': f'Error al descargar documento: {str(error)}',
            'error': 'ERROR_DESCARGA'
        }), 500


@document_bp.route('/unify/<int:job_id>', methods=['POST'])
def unificar_documentos(job_id):
    """
    ---
    tags:
      - Documentos
    summary: Unificar PDFs de un trabajo
    description: Combina todos los PDFs generados de un trabajo en un unico archivo
    parameters:
      - name: job_id
        in: path
        type: integer
        required: true
        description: ID del trabajo de escaneo
        example: 123
    responses:
      200:
        description: PDFs unificados correctamente
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            unified_pdf_path:
              type: string
      404:
        description: Trabajo no encontrado o sin documentos
      500:
        description: Error al unificar documentos
    """
    try:
        unificador = UnifierController.get_instance()
        ruta_unificada = unificador.unify_pdfs(job_id)
        
        return jsonify({
            'success': True,
            'message': 'Documentos unificados correctamente',
            'unified_pdf_path': ruta_unificada
        }), 200
    
    except ValueError as error_validacion:
        return jsonify({
            'success': False,
            'message': str(error_validacion),
            'error': 'ERROR_VALIDACION'
        }), 404
    
    except Exception as error:
        return jsonify({
            'success': False,
            'message': f'Error al unificar documentos: {str(error)}',
            'error': 'ERROR_UNIFICACION'
        }), 500


@document_bp.route('/problematic/<int:job_id>', methods=['GET'])
def obtener_problematicos(job_id):
    """
    ---
    tags:
      - Documentos
    summary: Obtener documentos problematicos
    description: Lista documentos que presentaron errores durante el procesamiento
    parameters:
      - name: job_id
        in: path
        type: integer
        required: true
        description: ID del trabajo de escaneo
        example: 123
    responses:
      200:
        description: Lista de documentos problematicos
        schema:
          type: object
          properties:
            success:
              type: boolean
            count:
              type: integer
            data:
              type: array
              items:
                type: object
      500:
        description: Error interno del servidor
    """
    try:
        unificador = UnifierController.get_instance()
        problematicos = unificador.get_problematic_documents(job_id)
        
        return jsonify({
            'success': True,
            'count': len(problematicos),
            'data': problematicos
        }), 200
    
    except Exception as error:
        return jsonify({
            'success': False,
            'message': f'Error al obtener documentos problematicos: {str(error)}',
            'error': 'ERROR_CONSULTA'
        }), 500


@document_bp.route('/export-excel/<int:job_id>', methods=['GET'])
def export_to_excel(job_id):
    """
    ---
    tags:
      - Documentos
    summary: Exportar datos a Excel consolidado
    description: Genera y descarga un archivo Excel con todos los campos extraidos estructurados en tabla
    parameters:
      - name: job_id
        in: path
        type: integer
        required: true
        description: ID del trabajo de escaneo
        example: 123
    produces:
      - application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
    responses:
      200:
        description: Excel descargado correctamente
        content:
          application/vnd.openxmlformats-officedocument.spreadsheetml.sheet:
            schema:
              type: string
              format: binary
      404:
        description: Trabajo no encontrado
      500:
        description: Error al generar Excel
    """
    try:
        exporter = ExcelExporter.get_instance()
        ruta_excel = exporter.export_to_excel(job_id)
        
        return send_file(
            ruta_excel,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'datos_consolidados_job_{job_id}.xlsx'
        )
    
    except ValueError as error_validacion:
        return jsonify({
            'success': False,
            'message': str(error_validacion),
            'error': 'ERROR_VALIDACION'
        }), 404
    
    except Exception as error:
        return jsonify({
            'success': False,
            'message': f'Error al exportar Excel: {str(error)}',
            'error': 'ERROR_EXPORTACION'
        }), 500