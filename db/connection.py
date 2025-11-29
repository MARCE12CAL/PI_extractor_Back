"""
Gestor de Conexión de Base de Datos (Singleton)
"""
import time
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError

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
        """Inicializar BD con Flask app - Con reintentos"""
        db.init_app(app)
        
        # Intentar conectar con reintentos (para esperar a PostgreSQL)
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                with app.app_context():
                    # Probar conexión
                    db.engine.connect()
                    # Crear tablas
                    db.create_all()
                    print(" Base de datos inicializada correctamente")
                    return
            except OperationalError as e:
                if attempt < max_retries - 1:
                    print(f" Intento {attempt + 1}/{max_retries} - Esperando a PostgreSQL...")
                    time.sleep(retry_delay)
                else:
                    print(f" Error al conectar con la base de datos: {e}")
                    raise
    
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