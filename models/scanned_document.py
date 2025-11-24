"""
==============================================================================
MODELO DE BASE DE DATOS - DOCUMENTOS ESCANEADOS
==============================================================================

Descripcion:
    Modelo SQLAlchemy que representa un documento individual procesado
    mediante OCR. Almacena informacion sobre el archivo, resultados del
    procesamiento y metricas de calidad.

Proposito:
    - Registrar documentos procesados por OCR
    - Almacenar metricas de calidad y confianza
    - Rastrear errores de procesamiento
    - Relacionar con campos extraidos

Relaciones:
    - Pertenece a: ScanJob (many-to-one)
    - Tiene muchos: DocumentField (one-to-many)

Autor: EMPROSERVIS
Version: 1.0.0
==============================================================================
"""

from datetime import datetime
from db.connection import db


class ScannedDocument(db.Model):
    """
    Modelo de documentos escaneados.
    
    Representa un documento individual que ha sido procesado mediante OCR.
    Almacena informacion del archivo, metricas de calidad, errores y
    relacion con los campos extraidos.
    """
    
    __tablename__ = 'scanned_documents'
    
    id = db.Column(
        db.Integer, 
        primary_key=True
    )
    
    scan_job_id = db.Column(
        db.Integer, 
        db.ForeignKey('scan_jobs.id'), 
        nullable=False,
        index=True
    )
    
    file_path = db.Column(
        db.Text, 
        nullable=False
    )
    
    file_type = db.Column(
        db.String(50),
        index=True
    )
    
    has_errors = db.Column(
        db.Boolean, 
        default=False,
        index=True
    )
    
    empty_fields_count = db.Column(
        db.Integer, 
        default=0
    )
    
    confidence_score = db.Column(
        db.Float, 
        default=0.0
    )
    
    output_pdf_path = db.Column(
        db.Text
    )
    
    scanned_at = db.Column(
        db.DateTime, 
        default=datetime.utcnow,
        index=True
    )
    
    fields = db.relationship(
        'DocumentField', 
        backref='document', 
        lazy=True, 
        cascade='all, delete-orphan'
    )
    
    def to_dict(self):
        """
        Convierte el modelo a diccionario para serializacion JSON.
        
        Returns:
            dict: Representacion del documento en formato diccionario
        """
        return {
            'id': self.id,
            'scan_job_id': self.scan_job_id,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'has_errors': self.has_errors,
            'empty_fields_count': self.empty_fields_count,
            'confidence_score': self.confidence_score,
            'output_pdf_path': self.output_pdf_path,
            'scanned_at': self.scanned_at.isoformat() if self.scanned_at else None,
            'fields_count': len(self.fields)
        }
    
    def __repr__(self):
        """
        Representacion en string del modelo para debugging.
        
        Returns:
            str: Representacion legible del documento
        """
        return f"<ScannedDocument {self.id} type='{self.file_type}' confidence={self.confidence_score:.1f}%>"


"""
==============================================================================
DOCUMENTACION TECNICA - SCANNED DOCUMENT MODEL
==============================================================================

ESTRUCTURA DE LA TABLA
=======================

Nombre de Tabla: scanned_documents

Columnas:

1. id (INTEGER, PRIMARY KEY)
   Proposito: Identificador unico del documento
   Tipo: Entero autoincremental
   Constraints: PRIMARY KEY, NOT NULL, AUTO_INCREMENT

2. scan_job_id (INTEGER, FOREIGN KEY)
   Proposito: Relacionar documento con su trabajo
   Tipo: Entero
   Constraints: FOREIGN KEY, NOT NULL, INDEX
   Relacion: Many-to-One con ScanJob

3. file_path (TEXT)
   Proposito: Ruta completa del archivo original
   Tipo: Texto sin limite
   Constraints: NOT NULL
   Ejemplo: 'C:/Documentos/Facturas/factura_001.pdf'

4. file_type (VARCHAR(50))
   Proposito: Tipo/extension del archivo
   Tipo: String de hasta 50 caracteres
   Constraints: INDEX
   Valores: pdf, png, jpg, jpeg, tiff, bmp, xlsx, xls

5. has_errors (BOOLEAN)
   Proposito: Indica si hubo errores en procesamiento
   Tipo: Booleano
   Default: False
   Constraints: INDEX
   
   Criterios de Error:
   - Mas del 30% de campos vacios
   - Fallo en procesamiento OCR
   - Archivo corrupto
   - Error en generacion de PDF

6. empty_fields_count (INTEGER)
   Proposito: Cantidad de campos detectados pero vacios
   Tipo: Entero
   Default: 0
   Uso: Metrica de calidad del documento

7. confidence_score (FLOAT)
   Proposito: Promedio de confianza de todos los campos
   Tipo: Punto flotante
   Default: 0.0
   Rango: 0.0 - 100.0
   Calculo: Promedio de confidence de todos los DocumentField

8. output_pdf_path (TEXT)
   Proposito: Ruta del PDF generado con resultados
   Tipo: Texto
   Constraints: Nullable
   Ejemplo: 'outputs/doc_123_output.pdf'

9. scanned_at (DATETIME)
   Proposito: Timestamp de procesamiento del documento
   Tipo: Fecha y hora
   Default: datetime.utcnow
   Constraints: INDEX


RELACIONES DE BASE DE DATOS
============================

Relacion con ScanJob:
    Tipo: Many-to-One (Muchos a Uno)
    Foreign Key: scan_job_id -> scan_jobs.id
    Cascade: ON DELETE CASCADE
    
    documento = ScannedDocument.query.get(1)
    trabajo = documento.scan_job

Relacion con DocumentField:
    Tipo: One-to-Many (Uno a Muchos)
    Backref: document
    Cascade: all, delete-orphan
    
    documento = ScannedDocument.query.get(1)
    campos = documento.fields
    
    for campo in campos:
        print(f"{campo.field_name}: {campo.field_value}")


INDICES DE LA TABLA
====================

Indices Definidos:

1. PRIMARY KEY (id)
   Automatico, unico

2. INDEX (scan_job_id)
   Mejora consultas por trabajo
   Esencial para JOINs con scan_jobs

3. INDEX (file_type)
   Permite filtrar por tipo de archivo
   Util para estadisticas

4. INDEX (has_errors)
   Identificacion rapida de documentos problematicos
   Importante para validacion de calidad

5. INDEX (scanned_at)
   Ordenamiento cronologico
   Consultas por fecha


CONSULTAS COMUNES
=================

1. Documentos de un Trabajo:
   documentos = ScannedDocument.query.filter_by(scan_job_id=123).all()

2. Documentos con Errores:
   con_errores = ScannedDocument.query.filter_by(
       scan_job_id=123,
       has_errors=True
   ).all()

3. Documentos por Tipo:
   pdfs = ScannedDocument.query.filter_by(
       scan_job_id=123,
       file_type='pdf'
   ).all()

4. Documentos con Baja Confianza:
   baja_confianza = ScannedDocument.query.filter(
       ScannedDocument.scan_job_id == 123,
       ScannedDocument.confidence_score < 70
   ).all()

5. Estadisticas de Trabajo:
   from sqlalchemy import func
   
   stats = db.session.query(
       func.count(ScannedDocument.id).label('total'),
       func.sum(ScannedDocument.has_errors.cast(db.Integer)).label('con_errores'),
       func.avg(ScannedDocument.confidence_score).label('confianza_promedio')
   ).filter(
       ScannedDocument.scan_job_id == 123
   ).first()


CALCULO DE METRICAS
====================

Confidence Score:
    Promedio de confianza de todos los campos del documento
    
    total_confianza = sum(campo.confidence for campo in documento.fields)
    documento.confidence_score = total_confianza / len(documento.fields)

Empty Fields Count:
    Cantidad de campos detectados pero sin valor
    
    documento.empty_fields_count = sum(
        1 for campo in documento.fields if campo.is_empty
    )

Has Errors:
    Se marca True si mas del 30% de campos estan vacios
    
    porcentaje_vacios = empty_fields_count / total_fields
    documento.has_errors = (porcentaje_vacios > 0.3)


EJEMPLO DE USO COMPLETO
========================

Crear Documento:
    from models.scanned_document import ScannedDocument
    from db.connection import db
    
    documento = ScannedDocument(
        scan_job_id=123,
        file_path='C:/Docs/factura.pdf',
        file_type='pdf'
    )
    
    db.session.add(documento)
    db.session.commit()


Actualizar Metricas:
    documento = ScannedDocument.query.get(1)
    documento.empty_fields_count = 5
    documento.confidence_score = 87.5
    documento.has_errors = False
    db.session.commit()


Consultar con Campos:
    documento = ScannedDocument.query.get(1)
    
    print(f"Archivo: {documento.file_path}")
    print(f"Confianza: {documento.confidence_score}%")
    print(f"Campos vacios: {documento.empty_fields_count}")
    print(f"\nCampos extraidos:")
    
    for campo in documento.fields:
        print(f"- {campo.field_name}: {campo.field_value}")


Serializar para API:
    documento = ScannedDocument.query.get(1)
    datos = documento.to_dict()
    
    from flask import jsonify
    return jsonify(datos)


INTEGRACION CON SCANNER CONTROLLER
===================================

Creacion y Procesamiento:
    def _escanear_documento(self, job_id, ruta_archivo, tipo_archivo):
        documento = ScannedDocument(
            scan_job_id=job_id,
            file_path=ruta_archivo,
            file_type=tipo_archivo
        )
        db.session.add(documento)
        db.session.flush()
        
        # Procesar OCR
        datos_campos = self._escanear_pdf(ruta_archivo)
        
        # Crear campos
        cantidad_vacios = 0
        confianza_total = 0
        
        for datos_campo in datos_campos:
            campo = DocumentField(
                document_id=documento.id,
                field_name=datos_campo['name'],
                field_value=datos_campo['value'],
                is_empty=datos_campo['is_empty'],
                confidence=datos_campo['confidence']
            )
            db.session.add(campo)
            
            if datos_campo['is_empty']:
                cantidad_vacios += 1
            
            confianza_total += datos_campo['confidence']
        
        # Actualizar metricas
        documento.empty_fields_count = cantidad_vacios
        documento.confidence_score = confianza_total / len(datos_campos)
        documento.has_errors = (cantidad_vacios > len(datos_campos) * 0.3)
        
        # Generar PDF salida
        pdf_salida = self._generar_pdf_salida(documento, datos_campos)
        documento.output_pdf_path = pdf_salida
        
        db.session.commit()


CONSIDERACIONES DE DISEÑO
==========================

Normalizacion:
    Tercera Forma Normal (3NF)
    Separacion de datos de documento y campos
    Relaciones bien definidas

Escalabilidad:
    Indices en columnas de consulta frecuente
    TEXT para rutas sin limite
    Lazy loading de relaciones

Auditoria:
    scanned_at registra momento de procesamiento
    Trazabilidad completa del flujo
    Metricas de calidad persistidas

Performance:
    Indices optimizados
    Consultas con JOINs eficientes
    Cascade delete automatico

Calidad:
    Metricas automaticas (confidence, empty_fields)
    Deteccion de errores
    PDF de salida para validacion

==============================================================================
"""