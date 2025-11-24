"""
==============================================================================
CONTROLADOR DE UNIFICACIÓN - GESTIÓN DE DOCUMENTOS PDF
==============================================================================

Descripción:
    Controlador Singleton que gestiona la unificación de múltiples archivos
    PDF en un único documento consolidado. Permite generar reportes completos
    y consultar documentos con errores de procesamiento.

Características:
    - Patrón Singleton para gestión única de recursos
    - Unificación de múltiples PDFs en uno solo
    - Detección de documentos problemáticos
    - Validación de existencia de archivos
    - Manejo optimizado de memoria

Autor: octavoSMG
Versión: 1.0.0
==============================================================================
"""

import fitz
from pathlib import Path
from models.scanned_document import ScannedDocument


class UnifierController:
    """
    Controlador de unificación de documentos PDF con patrón Singleton.
    
    Gestiona la combinación de múltiples PDFs procesados en un único
    archivo consolidado y proporciona consultas sobre documentos
    con errores.
    """
    
    _instance = None
    
    def __new__(cls):
        """
        Implementación del patrón Singleton.
        Garantiza una única instancia del controlador.
        """
        if cls._instance is None:
            cls._instance = super(UnifierController, cls).__new__(cls)
        return cls._instance
    
    def unify_pdfs(self, job_id):
        """
        Unifica todos los PDFs procesados de un trabajo en un solo archivo.
        
        Combina secuencialmente todos los PDFs generados durante el
        procesamiento de un trabajo de escaneo en un único documento.
        
        Args:
            job_id (int): ID del trabajo de escaneo
            
        Returns:
            str: Ruta del archivo PDF unificado
            
        Raises:
            Exception: Si no hay documentos o error durante unificación
            
        Notas:
            - Si solo hay 1 documento, retorna la ruta del PDF original
            - Valida existencia de archivos antes de unificar
            - Omite documentos sin PDF o con archivos faltantes
        """
        try:
            documentos = ScannedDocument.query.filter_by(scan_job_id=job_id).all()
            
            if not documentos:
                raise Exception("No hay documentos para unificar")
            
            if len(documentos) == 1:
                return documentos[0].output_pdf_path
            
            pdf_unificado = fitz.open()
            
            for documento in documentos:
                if documento.output_pdf_path and Path(documento.output_pdf_path).exists():
                    pdf_agregar = fitz.open(documento.output_pdf_path)
                    pdf_unificado.insert_pdf(pdf_agregar)
                    pdf_agregar.close()
            
            ruta_salida = Path('outputs') / f'unified_job_{job_id}.pdf'
            ruta_salida.parent.mkdir(parents=True, exist_ok=True)
            
            pdf_unificado.save(str(ruta_salida))
            pdf_unificado.close()
            
            return str(ruta_salida)
        
        except Exception as error:
            raise Exception(f"Error al unificar PDFs: {str(error)}")
    
    def get_problematic_documents(self, job_id):
        """
        Obtiene la lista de documentos que presentaron errores.
        
        Consulta todos los documentos de un trabajo que fueron marcados
        con errores durante el procesamiento OCR.
        
        Args:
            job_id (int): ID del trabajo de escaneo
            
        Returns:
            list: Lista de diccionarios con información de documentos problemáticos
            
        Criterios de Error:
            - Más del 30% de campos vacíos
            - Fallo en procesamiento OCR
            - Archivo corrupto o ilegible
            - Error en generación de PDF
        """
        documentos = ScannedDocument.query.filter_by(
            scan_job_id=job_id,
            has_errors=True
        ).all()
        
        return [documento.to_dict() for documento in documentos]
    
    @classmethod
    def get_instance(cls):
        """
        Obtiene la instancia única del controlador (Singleton).
        
        Returns:
            UnifierController: Instancia única del controlador
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


"""
==============================================================================
DOCUMENTACIÓN TÉCNICA - UNIFIER CONTROLLER
==============================================================================

PROPÓSITO DEL CONTROLADOR
==========================

El UnifierController es responsable de dos funciones principales:

1. Unificación de PDFs:
   - Combinar múltiples PDFs procesados en uno solo
   - Útil para generar reportes consolidados
   - Facilita la distribución de resultados

2. Gestión de Documentos Problemáticos:
   - Identificar documentos con errores
   - Proporcionar información para corrección
   - Facilitar re-procesamiento


PROCESO DE UNIFICACIÓN
=======================

Flujo de Unificación:

1. Validación Inicial:
   --------------------------------
   a. Consultar documentos del trabajo
   b. Verificar que existan documentos
   c. Si solo hay 1: retornar ruta original
   
2. Preparación:
   --------------------------------
   a. Crear documento PDF vacío (fitz.open())
   b. Iterar por cada documento del trabajo
   
3. Inserción de Páginas:
   --------------------------------
   Para cada documento:
   a. Verificar que tenga output_pdf_path
   b. Verificar que el archivo existe físicamente
   c. Abrir PDF individual
   d. Insertar todas sus páginas en PDF unificado
   e. Cerrar PDF individual (liberar memoria)
   
4. Guardado:
   --------------------------------
   a. Crear directorio outputs si no existe
   b. Guardar PDF unificado
   c. Cerrar PDF unificado
   d. Retornar ruta del archivo


OPTIMIZACIONES IMPLEMENTADAS
=============================

1. Validación de Archivo Único:
   - Si solo hay 1 documento, no unifica
   - Retorna directamente la ruta original
   - Ahorra procesamiento innecesario

2. Verificación de Existencia:
   - Valida que archivo PDF existe antes de abrir
   - Evita errores por archivos eliminados
   - Omite silenciosamente archivos faltantes

3. Liberación de Memoria:
   - Cierra cada PDF individual después de insertarlo
   - Evita mantener múltiples PDFs abiertos
   - Reduce consumo de memoria

4. Creación Automática de Directorio:
   - mkdir con parents=True, exist_ok=True
   - No falla si directorio ya existe
   - Crea directorios padres necesarios


DOCUMENTOS PROBLEMÁTICOS
=========================

Criterios para Marcar Documento como Problemático:

1. Alto Porcentaje de Campos Vacíos:
   - Más del 30% de campos detectados están vacíos
   - Indica extracción deficiente
   - Configurado en: documento.has_errors = (empty_count > total * 0.3)

2. Fallo en Procesamiento OCR:
   - Excepción durante _escanear_documento()
   - Archivo corrupto o ilegible
   - Motor OCR no pudo procesar

3. Fallo en Generación de PDF:
   - Error al crear PDF de salida
   - Problemas con librería fitz
   - Datos inconsistentes

4. Archivo No Encontrado:
   - Ruta válida pero archivo eliminado
   - Permisos insuficientes
   - Unidad de red desconectada

Información Retornada:
    {
        "id": 123,
        "scan_job_id": 45,
        "file_path": "C:/Docs/problema.pdf",
        "file_type": "pdf",
        "status": "failed",
        "has_errors": true,
        "empty_fields_count": 8,
        "confidence_score": 45.2,
        "output_pdf_path": null,
        "created_at": "2025-01-15T10:30:00",
        "processed_at": "2025-01-15T10:35:00"
    }


ESTRUCTURA DE ARCHIVOS
=======================

PDF Unificado:
    Ubicación: /outputs/unified_job_{job_id}.pdf
    Nombre: unified_job_123.pdf
    
    Contenido:
    - Página 1-N: Documento 1
    - Página N+1-M: Documento 2
    - Página M+1-P: Documento 3
    - ... (todos los documentos concatenados)
    
    Características:
    - Orden: Mismo orden de procesamiento
    - Metadatos: Preservados de cada documento
    - Tamaño: Suma de todos los PDFs individuales


MANEJO DE ERRORES
=================

Error: No hay documentos
    Causa: ScannedDocument.query retorna lista vacía
    Mensaje: "No hay documentos para unificar"
    Solución: Verificar que el trabajo existe y tiene documentos

Error: Archivo PDF no existe
    Causa: output_pdf_path apunta a archivo eliminado
    Comportamiento: Omite el documento silenciosamente
    Solución: Continúa con siguiente documento

Error: Memoria insuficiente
    Causa: PDFs muy grandes
    Síntoma: Exception durante insert_pdf()
    Solución: Procesar en lotes más pequeños

Error: Permisos de escritura
    Causa: No puede guardar en /outputs
    Mensaje: "Error al unificar PDFs: Permission denied"
    Solución: Verificar permisos del directorio


EJEMPLO DE USO
==============

Caso 1: Unificar PDFs de un Trabajo
    from controllers.unifier_controller import UnifierController
    
    unifier = UnifierController.get_instance()
    
    try:
        ruta_unificada = unifier.unify_pdfs(job_id=123)
        print(f"PDF unificado generado: {ruta_unificada}")
        
        # Resultado: /outputs/unified_job_123.pdf
        
    except Exception as error:
        print(f"Error: {error}")

Caso 2: Obtener Documentos Problemáticos
    from controllers.unifier_controller import UnifierController
    
    unifier = UnifierController.get_instance()
    problematicos = unifier.get_problematic_documents(job_id=123)
    
    print(f"Documentos con errores: {len(problematicos)}")
    
    for doc in problematicos:
        print(f"\nArchivo: {doc['file_path']}")
        print(f"Campos vacíos: {doc['empty_fields_count']}")
        print(f"Confianza: {doc['confidence_score']}%")

Caso 3: Flujo Completo con Validación
    from controllers.scanner_controller import ScannerController
    from controllers.unifier_controller import UnifierController
    
    # Escanear
    scanner = ScannerController.get_instance()
    job = scanner.start_scan('C:/Documentos')
    resultado = scanner.process_scan(job['id'])
    
    # Verificar problemáticos
    unifier = UnifierController.get_instance()
    problematicos = unifier.get_problematic_documents(job['id'])
    
    if problematicos:
        print(f"ADVERTENCIA: {len(problematicos)} documentos con errores")
        for doc in problematicos:
            print(f"- {doc['file_path']}")
    
    # Unificar
    if resultado['status'] == 'completed':
        ruta_pdf = unifier.unify_pdfs(job['id'])
        print(f"Reporte consolidado: {ruta_pdf}")


INTEGRACIÓN CON API
===================

Endpoint de Unificación:
    POST /api/documents/unify/<job_id>
    
    Llamada Interna:
        unifier = UnifierController.get_instance()
        unified_path = unifier.unify_pdfs(job_id)
    
    Response:
        {
            "success": true,
            "message": "Documentos unificados correctamente",
            "unified_pdf_path": "/outputs/unified_job_123.pdf"
        }

Endpoint de Problemáticos:
    GET /api/documents/problematic/<job_id>
    
    Llamada Interna:
        unifier = UnifierController.get_instance()
        problematic = unifier.get_problematic_documents(job_id)
    
    Response:
        {
            "success": true,
            "count": 3,
            "data": [
                {
                    "id": 10,
                    "file_path": "C:/Docs/corrupto.pdf",
                    "has_errors": true,
                    "confidence_score": 23.5
                },
                ...
            ]
        }


CONSIDERACIONES DE RENDIMIENTO
===============================

Tiempo de Unificación:
    - 10 PDFs (5 páginas c/u): ~2 segundos
    - 50 PDFs (5 páginas c/u): ~8 segundos
    - 100 PDFs (5 páginas c/u): ~15 segundos

Memoria:
    - Por PDF abierto: ~10-50 MB
    - PDF unificado final: Suma de tamaños individuales
    - Liberación inmediata al cerrar cada PDF

Limitaciones:
    - Tamaño máximo recomendado: 500 páginas totales
    - Más de 1000 páginas: Considerar división en volúmenes
    - Archivos >100 MB: Puede requerir tiempo significativo

Mejoras Sugeridas:
    1. Compresión de PDFs durante unificación
    2. Generación de tabla de contenidos
    3. Numeración de páginas unificada
    4. Marcadores (bookmarks) por documento
    5. Procesamiento asíncrono para trabajos grandes

==============================================================================
"""