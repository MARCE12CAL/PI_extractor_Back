"""
==============================================================================
MODULO DE RUTAS - MACHINE LEARNING OCR
==============================================================================

Descripcion:
    Blueprint de Flask para endpoints de aprendizaje automático.
    Permite entrenar, corregir y mejorar el sistema OCR con el tiempo.

Endpoints:
    POST   /api/ml/learn              - Registrar corrección manual
    GET    /api/ml/suggest/<field_id> - Obtener sugerencias
    POST   /api/ml/auto-correct/<doc_id> - Auto-corregir documento
    GET    /api/ml/status             - Estado del aprendizaje
    POST   /api/ml/export             - Exportar conocimiento
    POST   /api/ml/import             - Importar conocimiento

Autor: EMPROSERVIS
Version: 1.0.0
==============================================================================
"""

from flask import Blueprint, jsonify, request, send_file
from controllers.ml_ocr_learner import MLOCRLearner
from models.document_field import DocumentField


ml_bp = Blueprint('ml', __name__, url_prefix='/api/ml')


@ml_bp.route('/learn', methods=['POST'])
def learn_correction():
    """
    ---
    tags:
      - Machine Learning
    summary: Registrar corrección manual
    description: Aprende de una corrección manual del usuario para mejorar futuras predicciones
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - field_id
            - original_value
            - corrected_value
            - field_name
          properties:
            field_id:
              type: integer
              example: 123
            original_value:
              type: string
              example: "Marcela Garcia"
            corrected_value:
              type: string
              example: "Marcela García"
            field_name:
              type: string
              example: "nombre"
    responses:
      200:
        description: Corrección aprendida correctamente
      400:
        description: Datos inválidos
      500:
        description: Error en aprendizaje
    """
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['field_id', 'original_value', 'corrected_value', 'field_name']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'message': 'Faltan campos requeridos',
                'required': required_fields
            }), 400
        
        learner = MLOCRLearner.get_instance()
        
        resultado = learner.learn_from_correction(
            field_id=data['field_id'],
            original_value=data['original_value'],
            corrected_value=data['corrected_value'],
            field_name=data['field_name']
        )
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 500
    
    except Exception as error:
        return jsonify({
            'success': False,
            'message': f'Error al procesar corrección: {str(error)}'
        }), 500


@ml_bp.route('/suggest/<int:field_id>', methods=['GET'])
def get_suggestions(field_id):
    """
    ---
    tags:
      - Machine Learning
    summary: Obtener sugerencias de corrección
    description: Sugiere correcciones basadas en aprendizaje previo
    parameters:
      - name: field_id
        in: path
        type: integer
        required: true
        description: ID del campo
        example: 123
    responses:
      200:
        description: Sugerencias obtenidas
      404:
        description: Campo no encontrado
      500:
        description: Error al generar sugerencias
    """
    try:
        campo = DocumentField.query.get(field_id)
        
        if not campo:
            return jsonify({
                'success': False,
                'message': f'Campo {field_id} no encontrado'
            }), 404
        
        learner = MLOCRLearner.get_instance()
        
        sugerencias = learner.suggest_correction(
            field_value=campo.field_value,
            field_name=campo.field_name.lower()
        )
        
        return jsonify({
            'success': True,
            'field_id': field_id,
            'current_value': campo.field_value,
            'field_name': campo.field_name,
            **sugerencias
        }), 200
    
    except Exception as error:
        return jsonify({
            'success': False,
            'message': f'Error al obtener sugerencias: {str(error)}'
        }), 500


@ml_bp.route('/auto-correct/<int:doc_id>', methods=['POST'])
def auto_correct_document(doc_id):
    """
    ---
    tags:
      - Machine Learning
    summary: Auto-corregir documento
    description: Aplica correcciones automáticas a todos los campos del documento
    parameters:
      - name: doc_id
        in: path
        type: integer
        required: true
        description: ID del documento
        example: 456
    responses:
      200:
        description: Documento mejorado correctamente
      404:
        description: Documento no encontrado
      500:
        description: Error al mejorar documento
    """
    try:
        learner = MLOCRLearner.get_instance()
        
        resultado = learner.batch_improve_document(doc_id)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 404
    
    except Exception as error:
        return jsonify({
            'success': False,
            'message': f'Error al mejorar documento: {str(error)}'
        }), 500


@ml_bp.route('/status', methods=['GET'])
def get_learning_status():
    """
    ---
    tags:
      - Machine Learning
    summary: Estado del aprendizaje
    description: Obtiene estadísticas del sistema de aprendizaje automático
    responses:
      200:
        description: Estado obtenido correctamente
    """
    try:
        learner = MLOCRLearner.get_instance()
        
        status = learner._get_learning_status()
        
        return jsonify({
            'success': True,
            'status': status,
            'message': f'Sistema en nivel: {status["learning_level"]}'
        }), 200
    
    except Exception as error:
        return jsonify({
            'success': False,
            'message': f'Error al obtener estado: {str(error)}'
        }), 500


@ml_bp.route('/export', methods=['POST'])
def export_knowledge():
    """
    ---
    tags:
      - Machine Learning
    summary: Exportar conocimiento
    description: Exporta todo el conocimiento aprendido a un archivo JSON
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            filename:
              type: string
              example: "knowledge_backup.json"
    responses:
      200:
        description: Conocimiento exportado
    """
    try:
        data = request.get_json() or {}
        filename = data.get('filename', 'knowledge_export.json')
        
        output_path = f'exports/{filename}'
        
        learner = MLOCRLearner.get_instance()
        resultado = learner.export_knowledge(output_path)
        
        if resultado['success']:
            return send_file(
                output_path,
                mimetype='application/json',
                as_attachment=True,
                download_name=filename
            )
        else:
            return jsonify(resultado), 500
    
    except Exception as error:
        return jsonify({
            'success': False,
            'message': f'Error al exportar: {str(error)}'
        }), 500


@ml_bp.route('/import', methods=['POST'])
def import_knowledge():
    """
    ---
    tags:
      - Machine Learning
    summary: Importar conocimiento
    description: Importa conocimiento previamente exportado
    parameters:
      - in: formData
        name: file
        type: file
        required: true
        description: Archivo JSON con conocimiento
    responses:
      200:
        description: Conocimiento importado
      400:
        description: Archivo inválido
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No se proporcionó archivo'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'Nombre de archivo vacío'
            }), 400
        
        # Guardar archivo temporalmente
        import_path = f'temp/{file.filename}'
        file.save(import_path)
        
        # Importar
        learner = MLOCRLearner.get_instance()
        resultado = learner.import_knowledge(import_path)
        
        return jsonify(resultado), 200 if resultado['success'] else 500
    
    except Exception as error:
        return jsonify({
            'success': False,
            'message': f'Error al importar: {str(error)}'
        }), 500


@ml_bp.route('/batch-correct', methods=['POST'])
def batch_correct_job():
    """
    ---
    tags:
      - Machine Learning
    summary: Mejorar todos los documentos de un trabajo
    description: Aplica correcciones automáticas a todos los documentos de un trabajo
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - job_id
          properties:
            job_id:
              type: integer
              example: 1
            confidence_threshold:
              type: number
              example: 0.80
    responses:
      200:
        description: Documentos mejorados
    """
    try:
        data = request.get_json()
        
        if 'job_id' not in data:
            return jsonify({
                'success': False,
                'message': 'job_id requerido'
            }), 400
        
        from models.scanned_document import ScannedDocument
        
        documentos = ScannedDocument.query.filter_by(
            scan_job_id=data['job_id']
        ).all()
        
        learner = MLOCRLearner.get_instance()
        
        resultados = []
        total_mejorados = 0
        
        for doc in documentos:
            resultado = learner.batch_improve_document(doc.id)
            if resultado['success'] and resultado['fields_improved'] > 0:
                total_mejorados += 1
                resultados.append({
                    'document_id': doc.id,
                    'fields_improved': resultado['fields_improved']
                })
        
        return jsonify({
            'success': True,
            'job_id': data['job_id'],
            'total_documents': len(documentos),
            'documents_improved': total_mejorados,
            'details': resultados
        }), 200
    
    except Exception as error:
        return jsonify({
            'success': False,
            'message': f'Error en mejora masiva: {str(error)}'
        }), 500
