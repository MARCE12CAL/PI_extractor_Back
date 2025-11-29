"""
==============================================================================
MIGRACIÓN DE BASE DE DATOS - MACHINE LEARNING
==============================================================================

Script para agregar campos necesarios para el sistema de ML.

Ejecutar:
    python -m db.migrations.add_ml_fields

==============================================================================
"""

import sys
import os

# Agregar el directorio raíz al path de Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


def add_ml_fields():
    """Agrega campos para ML a la tabla document_field"""
    
    print("Iniciando migración para Machine Learning...")
    
    try:
        from flask import Flask
        from db.config import DatabaseConfig
        from db.connection import db
        from sqlalchemy import text
        
        # Crear aplicación Flask
        app = Flask(__name__)
        
        # Cargar configuración
        db_config = DatabaseConfig.get_instance()
        app.config['SQLALCHEMY_DATABASE_URI'] = db_config.SQLALCHEMY_DATABASE_URI
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = db_config.SQLALCHEMY_TRACK_MODIFICATIONS
        
        # Inicializar base de datos
        db.init_app(app)
        
        print(f" Conectando a: {db_config.SQLALCHEMY_DATABASE_URI.split('@')[1] if '@' in db_config.SQLALCHEMY_DATABASE_URI else 'base de datos'}")
        
    except ImportError as e:
        print(f" Error al importar módulos: {e}")
        print("Asegúrate de ejecutar desde la raíz del proyecto:")
        print("  python -m db.migrations.add_ml_fields")
        return
    except Exception as e:
        print(f" Error al configurar la aplicación: {e}")
        return
    
    with app.app_context():
        try:
            # Campos a agregar (tipos de datos para PostgreSQL)
            campos = [
                ("manually_corrected", "BOOLEAN DEFAULT FALSE"),
                ("auto_corrected", "BOOLEAN DEFAULT FALSE"),
                ("correction_date", "TIMESTAMP NULL"),
                ("correction_confidence", "FLOAT DEFAULT 0.0")
            ]
            
            # Detectar nombre de la tabla (plural o singular)
            inspector = db.inspect(db.engine)
            table_names = inspector.get_table_names()
            
            table_name = None
            if 'document_fields' in table_names:
                table_name = 'document_fields'
            elif 'document_field' in table_names:
                table_name = 'document_field'
            else:
                print(" No se encontró la tabla document_field(s)")
                return
            
            print(f" Usando tabla: {table_name}\n")
            
            campos_agregados = 0
            
            for campo_nombre, campo_tipo in campos:
                try:
                    query = text(f"""
                        ALTER TABLE {table_name} 
                        ADD COLUMN {campo_nombre} {campo_tipo}
                    """)
                    
                    db.session.execute(query)
                    db.session.commit()
                    
                    print(f"✓ Campo '{campo_nombre}' agregado correctamente")
                    campos_agregados += 1
                
                except Exception as e:
                    error_msg = str(e).lower()
                    if "duplicate column" in error_msg or "already exists" in error_msg:
                        print(f"⚠  Campo '{campo_nombre}' ya existe, saltando...")
                        db.session.rollback()
                    else:
                        print(f"⚠  Error con campo '{campo_nombre}': {str(e)}")
                        db.session.rollback()
            
            if campos_agregados > 0:
                print(f"\n Migración completada exitosamente ({campos_agregados} campos agregados)")
                print("\nNuevos campos agregados:")
                print("  - manually_corrected: Indica si fue corregido manualmente")
                print("  - auto_corrected: Indica si fue corregido automáticamente")
                print("  - correction_date: Fecha de la corrección")
                print("  - correction_confidence: Confianza de la corrección")
            else:
                print("\n Todos los campos ya existían en la base de datos")
        
        except Exception as error:
            print(f"\n Error en migración: {str(error)}")
            db.session.rollback()
            import traceback
            traceback.print_exc()


def rollback_ml_fields():
    """Revierte la migración (opcional)"""
    
    print("Revirtiendo migración de Machine Learning...")
    
    try:
        from flask import Flask
        from db.config import DatabaseConfig
        from db.connection import db
        from sqlalchemy import text
        
        # Crear aplicación Flask
        app = Flask(__name__)
        
        # Cargar configuración
        db_config = DatabaseConfig.get_instance()
        app.config['SQLALCHEMY_DATABASE_URI'] = db_config.SQLALCHEMY_DATABASE_URI
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = db_config.SQLALCHEMY_TRACK_MODIFICATIONS
        
        # Inicializar base de datos
        db.init_app(app)
        
    except ImportError as e:
        print(f" Error al importar módulos: {e}")
        return
    except Exception as e:
        print(f" Error al configurar la aplicación: {e}")
        return
    
    with app.app_context():
        try:
            # Detectar nombre de la tabla
            inspector = db.inspect(db.engine)
            table_names = inspector.get_table_names()
            
            table_name = None
            if 'document_fields' in table_names:
                table_name = 'document_fields'
            elif 'document_field' in table_names:
                table_name = 'document_field'
            else:
                print(" No se encontró la tabla document_field(s)")
                return
            
            print(f" Usando tabla: {table_name}\n")
            
            campos = [
                "manually_corrected",
                "auto_corrected",
                "correction_date",
                "correction_confidence"
            ]
            
            campos_eliminados = 0
            
            for campo_nombre in campos:
                try:
                    query = text(f"""
                        ALTER TABLE {table_name} 
                        DROP COLUMN {campo_nombre}
                    """)
                    
                    db.session.execute(query)
                    db.session.commit()
                    
                    print(f" Campo '{campo_nombre}' eliminado")
                    campos_eliminados += 1
                
                except Exception as e:
                    print(f"  Error eliminando '{campo_nombre}': {str(e)}")
                    db.session.rollback()
            
            print(f"\n Rollback completado ({campos_eliminados} campos eliminados)")
        
        except Exception as error:
            print(f"\n Error en rollback: {str(error)}")
            db.session.rollback()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        rollback_ml_fields()
    else:
        add_ml_fields()