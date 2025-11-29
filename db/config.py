"""
Configuración de Base de Datos (Singleton)
"""
import os


class DatabaseConfig:
    """Configuración única de base de datos"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConfig, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # PostgreSQL - Usar variable de entorno o fallback local
        self.SQLALCHEMY_DATABASE_URI = os.getenv(
            'DATABASE_URL',
            'postgresql://scanner_user:scanner_pass@localhost:5432/document_scanner_db'
        )
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,  # Verifica conexiones antes de usarlas
            'pool_recycle': 300,     # Recicla conexiones cada 5 minutos
            'connect_args': {
                'connect_timeout': 10
            }
        }
        
        self._initialized = True
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance