"""
Gestor de Conexión de Base de Datos (Singleton)
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class DatabaseConnection:
    """Gestor único de conexión a BD"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance
    
    @staticmethod
    def init_app(app):
        """Inicializar BD con Flask app"""
        db.init_app(app)
        with app.app_context():
            db.create_all()
            print("✅ Base de datos inicializada")
    
    @staticmethod
    def get_db():
        """Obtener instancia de BD"""
        return db
    
    @staticmethod
    def get_session():
        """Obtener sesión de BD"""
        return db.session
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
