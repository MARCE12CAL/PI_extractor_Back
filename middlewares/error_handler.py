"""
Middleware: Manejo de Errores
"""
from flask import jsonify


def register_error_handlers(app):
    """Registrar manejadores de errores"""
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'message': 'Recurso no encontrado',
            'error': str(error)
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor',
            'error': str(error)
        }), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        return jsonify({
            'success': False,
            'message': 'Error inesperado',
            'error': str(error)
        }), 500
