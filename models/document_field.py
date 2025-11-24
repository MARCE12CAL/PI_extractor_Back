"""
==============================================================================
MODELO DE BASE DE DATOS - CAMPOS DE DOCUMENTOS
==============================================================================

Descripcion:
    Modelo SQLAlchemy que representa los campos individuales extraidos de
    documentos mediante OCR. Almacena informacion detallada sobre cada campo
    detectado, incluyendo su valor, nivel de confianza y estado.

Proposito:
    - Almacenar campos extraidos por OCR
    - Registrar nivel de confianza por campo
    - Identificar campos criticos y vacios
    - Mantener trazabilidad de extraccion

Relaciones:
    - Pertenece a: ScannedDocument (many-to-one)
    - Un documento puede tener multiples campos

Autor: OctavoSMG
Version: 1.0.0
==============================================================================
"""

from datetime import datetime
from db.connection import db


class DocumentField(db.Model):
    """
    Modelo de campos extraidos de documentos.
    
    Representa un campo individual detectado y extraido de un documento
    durante el procesamiento OCR. Almacena el nombre del campo, su valor,
    metricas de calidad y metadatos de extraccion.
    """
    
    __tablename__ = 'document_fields'
    
    id = db.Column(
        db.Integer, 
        primary_key=True
    )
    
    document_id = db.Column(
        db.Integer, 
        db.ForeignKey('scanned_documents.id'), 
        nullable=False,
        index=True
    )
    
    field_name = db.Column(
        db.String(255), 
        nullable=False,
        index=True
    )
    
    field_value = db.Column(
        db.Text
    )
    
    is_empty = db.Column(
        db.Boolean, 
        default=False,
        index=True
    )
    
    is_critical = db.Column(
        db.Boolean, 
        default=False,
        index=True
    )
    
    confidence = db.Column(
        db.Float, 
        default=0.0
    )
    
    extracted_at = db.Column(
        db.DateTime, 
        default=datetime.utcnow
    )
    
    def to_dict(self):
        """
        Convierte el modelo a diccionario para serializacion JSON.
        
        Utilizado principalmente para respuestas de API, permite enviar
        la informacion del campo en formato JSON a clientes.
        
        Returns:
            dict: Representacion del campo en formato diccionario
        """
        return {
            'id': self.id,
            'document_id': self.document_id,
            'field_name': self.field_name,
            'field_value': self.field_value,
            'is_empty': self.is_empty,
            'is_critical': self.is_critical,
            'confidence': self.confidence,
            'extracted_at': self.extracted_at.isoformat() if self.extracted_at else None
        }
    
    def __repr__(self):
        """
        Representacion en string del modelo para debugging.
        
        Returns:
            str: Representacion legible del campo
        """
        return f"<DocumentField {self.field_name}='{self.field_value}' confidence={self.confidence}%>"


"""
==============================================================================
DOCUMENTACION TECNICA - DOCUMENT FIELD MODEL
==============================================================================

ESTRUCTURA DE LA TABLA
=======================

Nombre de Tabla: document_fields

Columnas:

1. id (INTEGER, PRIMARY KEY)
   Proposito: Identificador unico del campo
   Tipo: Entero autoincremental
   Constraints: PRIMARY KEY, NOT NULL, AUTO_INCREMENT

2. document_id (INTEGER, FOREIGN KEY)
   Proposito: Relacionar campo con su documento
   Tipo: Entero
   Constraints: FOREIGN KEY, NOT NULL, INDEX
   Relacion: Many-to-One con ScannedDocument

3. field_name (VARCHAR(255))
   Proposito: Nombre identificador del campo
   Tipo: String de hasta 255 caracteres
   Constraints: NOT NULL, INDEX
   Valores Tipicos: nombre, apellido, cedula, fecha, direccion, telefono, email

4. field_value (TEXT)
   Proposito: Valor extraido del campo
   Tipo: Texto de longitud variable
   Constraints: Nullable

5. is_empty (BOOLEAN)
   Proposito: Indicar si el campo esta vacio
   Tipo: Booleano
   Default: False
   Constraints: INDEX

6. is_critical (BOOLEAN)
   Proposito: Marcar campos criticos para el documento
   Tipo: Booleano
   Default: False
   Constraints: INDEX
   Campos Criticos: nombre, apellido, cedula, dni

7. confidence (FLOAT)
   Proposito: Nivel de confianza de la extraccion OCR
   Tipo: Punto flotante
   Default: 0.0
   Rango: 0.0 - 100.0
   
   Interpretacion:
   - 0-50: Confianza muy baja, requiere revision
   - 51-70: Confianza baja, verificar
   - 71-85: Confianza media, aceptable
   - 86-95: Confianza alta, confiable
   - 96-100: Confianza muy alta, excelente

8. extracted_at (DATETIME)
   Proposito: Timestamp de extraccion del campo
   Tipo: Fecha y hora
   Default: datetime.utcnow
   Formato: ISO 8601 (YYYY-MM-DDTHH:MM:SS)


RELACIONES DE BASE DE DATOS
============================

Relacion con ScannedDocument:
    Tipo: Many-to-One (Muchos a Uno)
    Foreign Key: document_id -> scanned_documents.id
    Cascada: ON DELETE CASCADE

Acceso desde ScannedDocument:
    documento = ScannedDocument.query.get(1)
    campos = documento.fields
    
    for campo in campos:
        print(f"{campo.field_name}: {campo.field_value}")

Acceso desde DocumentField:
    campo = DocumentField.query.get(1)
    documento = campo.document


INDICES DE LA TABLA
====================

Indices Definidos:

1. PRIMARY KEY (id)
   Automatico, unico, busqueda O(log n)

2. INDEX (document_id)
   Mejora consultas por documento, esencial para JOINs

3. INDEX (field_name)
   Busqueda por tipo de campo, util para estadisticas

4. INDEX (is_empty)
   Identificar campos vacios rapidamente, metricas de calidad

5. INDEX (is_critical)
   Filtrar campos criticos, validaciones importantes


CONSULTAS COMUNES
=================

1. Obtener Campos de un Documento:
   campos = DocumentField.query.filter_by(document_id=123).all()

2. Buscar Campos Vacios:
   vacios = DocumentField.query.filter_by(
       document_id=123,
       is_empty=True
   ).all()

3. Obtener Campos Criticos:
   criticos = DocumentField.query.filter_by(
       document_id=123,
       is_critical=True
   ).all()

4. Campos con Baja Confianza:
   baja_confianza = DocumentField.query.filter(
       DocumentField.document_id == 123,
       DocumentField.confidence < 70
   ).all()

5. Buscar por Nombre de Campo:
   nombres = DocumentField.query.filter_by(
       document_id=123,
       field_name='nombre'
   ).all()

6. Estadisticas por Documento:
   from sqlalchemy import func
   
   stats = db.session.query(
       func.count(DocumentField.id).label('total'),
       func.sum(DocumentField.is_empty.cast(db.Integer)).label('vacios'),
       func.avg(DocumentField.confidence).label('confianza_promedio')
   ).filter(
       DocumentField.document_id == 123
   ).first()


VALIDACIONES Y REGLAS DE NEGOCIO
=================================

Validacion de Campos Criticos:

def validar_documento_completo(document_id):
    campos_criticos = DocumentField.query.filter_by(
        document_id=document_id,
        is_critical=True
    ).all()
    
    for campo in campos_criticos:
        if campo.is_empty or not campo.field_value:
            return False, f"Campo critico vacio: {campo.field_name}"
    
    return True, "Documento completo"


Validacion de Confianza:

def validar_confianza_minima(document_id, umbral=70.0):
    campos_criticos = DocumentField.query.filter_by(
        document_id=document_id,
        is_critical=True
    ).all()
    
    campos_baja_confianza = [
        c for c in campos_criticos 
        if c.confidence < umbral
    ]
    
    if campos_baja_confianza:
        return False, campos_baja_confianza
    
    return True, []


EJEMPLO DE USO COMPLETO
========================

Crear Nuevo Campo:
    from models.document_field import DocumentField
    from db.connection import db
    
    campo = DocumentField(
        document_id=456,
        field_name='nombre',
        field_value='Juan Perez',
        is_empty=False,
        is_critical=True,
        confidence=95.5
    )
    
    db.session.add(campo)
    db.session.commit()


Consultar Campos:
    campos = DocumentField.query.filter_by(document_id=456).all()
    
    for campo in campos:
        print(f"Campo: {campo.field_name}")
        print(f"Valor: {campo.field_value}")
        print(f"Confianza: {campo.confidence}%")
        print(f"Critico: {'Si' if campo.is_critical else 'No'}")


Actualizar Campo:
    campo = DocumentField.query.get(1)
    campo.field_value = "Nuevo Valor"
    campo.confidence = 98.0
    db.session.commit()


Eliminar Campo:
    campo = DocumentField.query.get(1)
    db.session.delete(campo)
    db.session.commit()


Serializar para API:
    campo = DocumentField.query.get(1)
    datos_json = campo.to_dict()
    
    from flask import jsonify
    return jsonify(datos_json)


INTEGRACION CON SCANNER CONTROLLER
===================================

Extraccion y Almacenamiento:
    def _escanear_documento(self, job_id, ruta_archivo, tipo_archivo):
        # ... procesamiento OCR ...
        
        for datos_campo in datos_campos:
            campo = DocumentField(
                document_id=documento.id,
                field_name=datos_campo['name'],
                field_value=datos_campo['value'],
                is_empty=datos_campo['is_empty'],
                is_critical=datos_campo.get('is_critical', False),
                confidence=datos_campo.get('confidence', 0.0)
            )
            db.session.add(campo)
        
        db.session.commit()


CONSIDERACIONES DE DISENO
==========================

Normalizacion:
    Tercera Forma Normal (3NF)
    No redundancia de datos
    Integridad referencial garantizada

Escalabilidad:
    Indices optimizados para consultas frecuentes
    TEXT para valores sin limite
    Particionamiento posible por document_id

Auditoria:
    extracted_at registra momento de creacion
    No hay campos de modificacion (immutable)
    Trazabilidad completa

Performance:
    Indices en columnas de busqueda frecuente
    Foreign key indexada automaticamente
    Consultas optimizadas con JOINs

==============================================================================
"""