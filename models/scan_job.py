"""
==============================================================================
MODELO DE BASE DE DATOS - TRABAJOS DE ESCANEO
==============================================================================

Descripcion:
    Modelo SQLAlchemy que representa un trabajo de escaneo completo.
    Gestiona el procesamiento de multiples documentos de una carpeta,
    rastreando el progreso y estado del trabajo.

Proposito:
    - Registrar trabajos de escaneo de carpetas
    - Rastrear progreso de procesamiento
    - Gestionar estado del trabajo (pending, processing, completed, failed)
    - Mantener referencia a documentos procesados

Relaciones:
    - Tiene muchos: ScannedDocument (one-to-many)
    - Un trabajo puede procesar multiples documentos

Autor: OctavoSMG
Version: 1.0.0
==============================================================================
"""

from datetime import datetime
from db.connection import db


class ScanJob(db.Model):
    """
    Modelo de trabajos de escaneo.
    
    Representa un trabajo completo de escaneo que procesa todos los
    archivos de una carpeta. Rastrea el progreso, estado y resultados
    del procesamiento.
    """
    
    __tablename__ = 'scan_jobs'
    
    id = db.Column(
        db.Integer, 
        primary_key=True
    )
    
    folder_path = db.Column(
        db.Text, 
        nullable=False
    )
    
    status = db.Column(
        db.String(50), 
        default='pending',
        index=True
    )
    
    total_files = db.Column(
        db.Integer, 
        default=0
    )
    
    processed_files = db.Column(
        db.Integer, 
        default=0
    )
    
    csv_path = db.Column(
        db.Text
    )
    
    created_at = db.Column(
        db.DateTime, 
        default=datetime.utcnow,
        index=True
    )
    
    completed_at = db.Column(
        db.DateTime
    )
    
    documents = db.relationship(
        'ScannedDocument', 
        backref='scan_job', 
        lazy=True, 
        cascade='all, delete-orphan'
    )
    
    def to_dict(self):
        """
        Convierte el modelo a diccionario para serializacion JSON.
        
        Utilizado principalmente para respuestas de API, permite enviar
        la informacion del trabajo en formato JSON a clientes.
        
        Returns:
            dict: Representacion del trabajo en formato diccionario
        """
        return {
            'id': self.id,
            'folder_path': self.folder_path,
            'status': self.status,
            'total_files': self.total_files,
            'processed_files': self.processed_files,
            'progress_percentage': self.get_progress_percentage(),
            'csv_path': self.csv_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def get_progress_percentage(self):
        """
        Calcula el porcentaje de progreso del trabajo.
        
        Returns:
            float: Porcentaje de archivos procesados (0-100)
        """
        if self.total_files == 0:
            return 0.0
        return (self.processed_files / self.total_files) * 100
    
    def __repr__(self):
        """
        Representacion en string del modelo para debugging.
        
        Returns:
            str: Representacion legible del trabajo
        """
        return f"<ScanJob {self.id} status='{self.status}' progress={self.processed_files}/{self.total_files}>"


"""
==============================================================================
DOCUMENTACION TECNICA - SCAN JOB MODEL
==============================================================================

ESTRUCTURA DE LA TABLA
=======================

Nombre de Tabla: scan_jobs

Columnas:

1. id (INTEGER, PRIMARY KEY)
   Proposito: Identificador unico del trabajo
   Tipo: Entero autoincremental
   Constraints: PRIMARY KEY, NOT NULL, AUTO_INCREMENT

2. folder_path (TEXT)
   Proposito: Ruta de la carpeta a escanear
   Tipo: Texto sin limite de longitud
   Constraints: NOT NULL
   Ejemplo: 'C:/Documentos/Facturas/2025'

3. status (VARCHAR(50))
   Proposito: Estado actual del trabajo
   Tipo: String de hasta 50 caracteres
   Default: 'pending'
   Constraints: INDEX
   
   Valores Posibles:
   - 'pending': Trabajo creado, esperando procesamiento
   - 'processing': Procesamiento en curso
   - 'completed': Procesamiento finalizado exitosamente
   - 'failed': Procesamiento fallo
   - 'cancelled': Trabajo cancelado por usuario

4. total_files (INTEGER)
   Proposito: Cantidad total de archivos a procesar
   Tipo: Entero
   Default: 0
   Actualizacion: Se establece despues de escanear la carpeta

5. processed_files (INTEGER)
   Proposito: Cantidad de archivos ya procesados
   Tipo: Entero
   Default: 0
   Actualizacion: Se incrementa por cada archivo procesado

6. csv_path (TEXT)
   Proposito: Ruta del archivo CSV con lista de archivos
   Tipo: Texto
   Constraints: Nullable
   Ejemplo: 'temp/scan_job_123_files.csv'

7. created_at (DATETIME)
   Proposito: Timestamp de creacion del trabajo
   Tipo: Fecha y hora
   Default: datetime.utcnow
   Constraints: INDEX
   Formato: ISO 8601

8. completed_at (DATETIME)
   Proposito: Timestamp de finalizacion del trabajo
   Tipo: Fecha y hora
   Constraints: Nullable
   Actualizacion: Se establece cuando status = 'completed'


RELACIONES DE BASE DE DATOS
============================

Relacion con ScannedDocument:
    Tipo: One-to-Many (Uno a Muchos)
    Descripcion: Un trabajo puede tener multiples documentos
    Backref: scan_job (acceso desde documento al trabajo)
    Cascade: all, delete-orphan (elimina documentos al eliminar trabajo)

Acceso desde ScanJob:
    trabajo = ScanJob.query.get(1)
    documentos = trabajo.documents
    
    print(f"Total documentos: {len(documentos)}")
    for doc in documentos:
        print(f"- {doc.file_path}")

Acceso desde ScannedDocument:
    documento = ScannedDocument.query.get(1)
    trabajo = documento.scan_job
    
    print(f"Trabajo ID: {trabajo.id}")
    print(f"Estado: {trabajo.status}")


INDICES DE LA TABLA
====================

Indices Definidos:

1. PRIMARY KEY (id)
   Automatico, unico, busqueda O(log n)

2. INDEX (status)
   Mejora consultas por estado
   Util para dashboards y monitoreo
   Queries frecuentes: "trabajos activos", "trabajos completados"

3. INDEX (created_at)
   Ordenamiento cronologico eficiente
   Consultas por rango de fechas
   Listados recientes


CICLO DE VIDA DE UN TRABAJO
============================

1. Creacion (pending):
   trabajo = ScanJob(
       folder_path='C:/Docs',
       status='pending'
   )
   db.session.add(trabajo)
   db.session.commit()

2. Inicializacion (processing):
   trabajo.status = 'processing'
   trabajo.total_files = 100
   db.session.commit()

3. Procesamiento (processing):
   for archivo in archivos:
       procesar_archivo(archivo)
       trabajo.processed_files += 1
       db.session.commit()

4. Finalizacion (completed):
   trabajo.status = 'completed'
   trabajo.completed_at = datetime.utcnow()
   db.session.commit()

5. Error (failed):
   try:
       procesar()
   except Exception as e:
       trabajo.status = 'failed'
       db.session.commit()


CONSULTAS COMUNES
=================

1. Trabajos Pendientes:
   pendientes = ScanJob.query.filter_by(status='pending').all()

2. Trabajos en Proceso:
   en_proceso = ScanJob.query.filter_by(status='processing').all()

3. Trabajos Completados Hoy:
   from datetime import date
   hoy = date.today()
   
   completados_hoy = ScanJob.query.filter(
       ScanJob.status == 'completed',
       db.func.date(ScanJob.completed_at) == hoy
   ).all()

4. Trabajos Recientes (ultimos 10):
   recientes = ScanJob.query.order_by(
       ScanJob.created_at.desc()
   ).limit(10).all()

5. Trabajos con Errores:
   fallidos = ScanJob.query.filter_by(status='failed').all()

6. Progreso de Trabajo Especifico:
   trabajo = ScanJob.query.get(123)
   porcentaje = (trabajo.processed_files / trabajo.total_files) * 100
   print(f"Progreso: {porcentaje:.1f}%")

7. Estadisticas Generales:
   from sqlalchemy import func
   
   stats = db.session.query(
       ScanJob.status,
       func.count(ScanJob.id).label('cantidad')
   ).group_by(ScanJob.status).all()
   
   for estado, cantidad in stats:
       print(f"{estado}: {cantidad}")


METODOS UTILES DEL MODELO
==========================

get_progress_percentage():
    Calcula porcentaje de progreso (0-100)
    
    trabajo = ScanJob.query.get(1)
    print(f"Progreso: {trabajo.get_progress_percentage():.1f}%")

to_dict():
    Serializa modelo a diccionario JSON
    Incluye porcentaje de progreso automaticamente
    
    trabajo = ScanJob.query.get(1)
    datos = trabajo.to_dict()
    
    return jsonify(datos)


VALIDACIONES Y REGLAS DE NEGOCIO
=================================

Validacion de Estado:

def validar_cambio_estado(trabajo, nuevo_estado):
    transiciones_validas = {
        'pending': ['processing', 'cancelled'],
        'processing': ['completed', 'failed', 'cancelled'],
        'completed': [],
        'failed': ['processing'],
        'cancelled': []
    }
    
    if nuevo_estado not in transiciones_validas.get(trabajo.status, []):
        raise ValueError(f"Transicion invalida: {trabajo.status} -> {nuevo_estado}")
    
    trabajo.status = nuevo_estado
    db.session.commit()


Validacion de Progreso:

def validar_progreso(trabajo):
    if trabajo.processed_files > trabajo.total_files:
        raise ValueError("Archivos procesados excede total")
    
    if trabajo.processed_files < 0:
        raise ValueError("Archivos procesados no puede ser negativo")
    
    return True


Actualizacion Segura de Progreso:

def incrementar_progreso(trabajo_id):
    trabajo = ScanJob.query.get(trabajo_id)
    
    if trabajo.status != 'processing':
        raise ValueError("Trabajo no esta en procesamiento")
    
    trabajo.processed_files += 1
    
    if trabajo.processed_files >= trabajo.total_files:
        trabajo.status = 'completed'
        trabajo.completed_at = datetime.utcnow()
    
    db.session.commit()


INTEGRACION CON SCANNER CONTROLLER
===================================

Crear Trabajo:
    def start_scan(self, folder_path):
        trabajo = ScanJob(
            folder_path=folder_path,
            status='processing'
        )
        db.session.add(trabajo)
        db.session.commit()
        
        archivos = self.file_helper.get_all_files(folder_path)
        trabajo.total_files = len(archivos)
        db.session.commit()
        
        return trabajo.to_dict()


Procesar Trabajo:
    def process_scan(self, job_id):
        trabajo = ScanJob.query.get(job_id)
        
        if not trabajo:
            raise Exception("Trabajo no encontrado")
        
        # Procesar archivos
        for archivo in archivos:
            self._escanear_documento(trabajo.id, archivo, tipo)
            trabajo.processed_files += 1
            db.session.commit()
        
        trabajo.status = 'completed'
        trabajo.completed_at = datetime.utcnow()
        db.session.commit()


EJEMPLO DE USO COMPLETO
========================

Crear Nuevo Trabajo:
    from models.scan_job import ScanJob
    from db.connection import db
    
    trabajo = ScanJob(
        folder_path='C:/Documentos/Facturas',
        status='pending'
    )
    
    db.session.add(trabajo)
    db.session.commit()
    
    print(f"Trabajo creado con ID: {trabajo.id}")


Actualizar Trabajo:
    trabajo = ScanJob.query.get(1)
    trabajo.status = 'processing'
    trabajo.total_files = 50
    db.session.commit()


Consultar Progreso:
    trabajo = ScanJob.query.get(1)
    
    print(f"Estado: {trabajo.status}")
    print(f"Progreso: {trabajo.processed_files}/{trabajo.total_files}")
    print(f"Porcentaje: {trabajo.get_progress_percentage():.1f}%")


Finalizar Trabajo:
    trabajo = ScanJob.query.get(1)
    trabajo.status = 'completed'
    trabajo.completed_at = datetime.utcnow()
    db.session.commit()


Listar Documentos del Trabajo:
    trabajo = ScanJob.query.get(1)
    
    for documento in trabajo.documents:
        print(f"Archivo: {documento.file_path}")
        print(f"Estado: {documento.status}")
        print(f"Confianza: {documento.confidence_score}%")


Serializar para API:
    trabajo = ScanJob.query.get(1)
    datos = trabajo.to_dict()
    
    from flask import jsonify
    return jsonify(datos)


CONSIDERACIONES DE DISEÑO
==========================

Atomicidad:
    Cada actualizacion de progreso hace commit individual
    Permite monitoreo en tiempo real
    Asegura persistencia ante fallos

Escalabilidad:
    Indices en campos de consulta frecuente
    TEXT para rutas sin limite
    Progreso incremental sin bloqueos

Auditoria:
    created_at: Momento de creacion
    completed_at: Momento de finalizacion
    Permite calcular tiempo de procesamiento

Performance:
    Relacion lazy=True: Carga bajo demanda
    Cascade delete: Limpieza automatica
    Indices optimizados

Monitoreo:
    Status permite dashboard en tiempo real
    Progreso calculable instantaneamente
    Facil identificacion de trabajos bloqueados

==============================================================================
"""