"""
Configuración de Base de Datos (Singleton)
"""
import os
from pathlib import Path


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
        
        # PostgreSQL
        self.SQLALCHEMY_DATABASE_URI = os.getenv(
            'DATABASE_URL',
            'postgresql://scanner_user:scanner_pass@localhost:5432/document_scanner_db'
        )
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        
        self._initialized = True
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
