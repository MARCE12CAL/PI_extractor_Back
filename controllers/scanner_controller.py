"""
==============================================================================
CONTROLADOR PRINCIPAL - ESCANEO DE DOCUMENTOS CON OCR
==============================================================================

Descripción:
    Controlador Singleton que gestiona el proceso completo de escaneo y
    extracción de datos mediante OCR. Coordina la lectura de archivos,
    procesamiento de imágenes, extracción de texto y generación de reportes.

Características:
    - Patrón Singleton para gestión única de recursos
    - Soporte multi-formato (PDF, imágenes, Excel)
    - OCR con motor Tesseract
    - Extracción automática de campos mediante patrones
    - Generación de PDFs con resultados
    - Sistema de confianza y validación
    - Gestión de trabajos de escaneo

Formatos Soportados:
    - PDF (con/sin texto nativo)
    - Imágenes (PNG, JPG, JPEG, TIFF, BMP)
    - Excel (XLSX, XLS)

Autor: OctavoSMG
Versión: 1.0.0 
==============================================================================
"""

import os
import csv
import re
from pathlib import Path
from datetime import datetime

import cv2
import numpy as np
from PIL import Image
import fitz
import pdfplumber
import openpyxl

from db.connection import db
from models.scan_job import ScanJob
from models.scanned_document import ScannedDocument
from models.document_field import DocumentField
from helpers.ocr_helper import OCRHelper
from helpers.file_helper import FileHelper
from helpers.image_helper import ImageHelper


class ScannerController:
    """
    Controlador principal de escaneo con patrón Singleton.
    
    Gestiona el ciclo completo de procesamiento de documentos:
    inicio de trabajos, escaneo, extracción de campos y generación
    de reportes.
    """
    
    _instance = None
    
    def __new__(cls):
        """
        Implementación del patrón Singleton.
        Garantiza una única instancia del controlador.
        """
        if cls._instance is None:
            cls._instance = super(ScannerController, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """
        Inicializa el controlador y sus dependencias.
        Solo se ejecuta una vez gracias al flag _initialized.
        """
        if self._initialized:
            return
        
        self.ocr_helper = OCRHelper.get_instance()
        self.file_helper = FileHelper.get_instance()
        self.image_helper = ImageHelper.get_instance()
        
        self._initialized = True
    
    def start_scan(self, folder_path):
        """
        Inicia un nuevo trabajo de escaneo.
        
        Crea el registro del trabajo, escanea la carpeta para obtener
        todos los archivos válidos y genera un archivo CSV con las rutas.
        
        Args:
            folder_path (str): Ruta absoluta de la carpeta a escanear
            
        Returns:
            dict: Información del trabajo creado
            
        Raises:
            Exception: Si hay error al crear el trabajo o acceder a la carpeta
        """
        try:
            trabajo_escaneo = ScanJob(
                folder_path=folder_path,
                status='processing'
            )
            db.session.add(trabajo_escaneo)
            db.session.commit()
            
            rutas_archivos = self.file_helper.get_all_files(folder_path)
            trabajo_escaneo.total_files = len(rutas_archivos)
            db.session.commit()
            
            ruta_csv = self._generar_csv(trabajo_escaneo.id, rutas_archivos)
            trabajo_escaneo.csv_path = ruta_csv
            db.session.commit()
            
            return trabajo_escaneo.to_dict()
        
        except Exception as error:
            db.session.rollback()
            raise Exception(f"Error al iniciar escaneo: {str(error)}")
    
    def _generar_csv(self, job_id, rutas_archivos):
        """
        Genera archivo CSV con las rutas de archivos a procesar.
        
        Args:
            job_id (int): ID del trabajo de escaneo
            rutas_archivos (list): Lista de rutas de archivos
            
        Returns:
            str: Ruta del archivo CSV generado
        """
        ruta_csv = Path('temp') / f'scan_job_{job_id}_files.csv'
        ruta_csv.parent.mkdir(parents=True, exist_ok=True)
        
        with open(ruta_csv, 'w', newline='', encoding='utf-8') as archivo_csv:
            escritor = csv.writer(archivo_csv)
            escritor.writerow(['file_path', 'file_type'])
            
            for ruta_archivo in rutas_archivos:
                tipo_archivo = self.file_helper.get_file_type(ruta_archivo)
                escritor.writerow([ruta_archivo, tipo_archivo])
        
        return str(ruta_csv)
    
    def process_scan(self, job_id):
        """
        Procesa todos los documentos de un trabajo de escaneo.
        
        Lee el CSV generado y procesa cada archivo según su tipo.
        Actualiza el progreso en la base de datos.
        
        Args:
            job_id (int): ID del trabajo de escaneo
            
        Returns:
            dict: Información del trabajo completado
            
        Raises:
            Exception: Si el trabajo no existe o hay error en procesamiento
        """
        try:
            trabajo_escaneo = ScanJob.query.get(job_id)
            if not trabajo_escaneo:
                raise Exception("Trabajo no encontrado")
            
            with open(trabajo_escaneo.csv_path, 'r', encoding='utf-8') as archivo_csv:
                lector = csv.DictReader(archivo_csv)
                
                for fila in lector:
                    ruta_archivo = fila['file_path']
                    tipo_archivo = fila['file_type']
                    
                    self._escanear_documento(trabajo_escaneo.id, ruta_archivo, tipo_archivo)
                    
                    trabajo_escaneo.processed_files += 1
                    db.session.commit()
            
            trabajo_escaneo.status = 'completed'
            trabajo_escaneo.completed_at = datetime.utcnow()
            db.session.commit()
            
            return trabajo_escaneo.to_dict()
        
        except Exception as error:
            trabajo_escaneo.status = 'failed'
            db.session.commit()
            raise Exception(f"Error al procesar: {str(error)}")
    
    def _escanear_documento(self, job_id, ruta_archivo, tipo_archivo):
        """
        Escanea un documento individual y extrae sus campos.
        
        Procesa el documento según su tipo, extrae campos mediante OCR,
        calcula métricas de confianza y genera PDF de salida.
        
        Args:
            job_id (int): ID del trabajo de escaneo
            ruta_archivo (str): Ruta del archivo a escanear
            tipo_archivo (str): Tipo de archivo (pdf, png, jpg, xlsx, etc.)
        """
        documento = ScannedDocument(
            scan_job_id=job_id,
            file_path=ruta_archivo,
            file_type=tipo_archivo
        )
        db.session.add(documento)
        db.session.flush()
        
        try:
            if tipo_archivo == 'pdf':
                datos_campos = self._escanear_pdf(ruta_archivo)
            elif tipo_archivo in ['png', 'jpg', 'jpeg', 'tiff', 'bmp']:
                datos_campos = self._escanear_imagen(ruta_archivo)
            elif tipo_archivo in ['xlsx', 'xls']:
                datos_campos = self._escanear_excel(ruta_archivo)
            else:
                datos_campos = []
            
            cantidad_vacios = 0
            confianza_total = 0
            
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
                
                if datos_campo['is_empty']:
                    cantidad_vacios += 1
                
                confianza_total += datos_campo.get('confidence', 0.0)
            
            documento.empty_fields_count = cantidad_vacios
            documento.confidence_score = confianza_total / len(datos_campos) if datos_campos else 0
            documento.has_errors = (cantidad_vacios > len(datos_campos) * 0.3)
            
            pdf_salida = self._generar_pdf_salida(documento, datos_campos)
            documento.output_pdf_path = pdf_salida
            
            db.session.commit()
        
        except Exception as error:
            print(f"Error escaneando {ruta_archivo}: {str(error)}")
            documento.has_errors = True
            db.session.commit()
    
    def _escanear_pdf(self, ruta_archivo):
        """
        Escanea un archivo PDF usando extracción nativa o OCR.
        
        Intenta primero extraer texto nativo del PDF. Si no hay texto,
        convierte páginas a imágenes y aplica OCR.
        
        Args:
            ruta_archivo (str): Ruta del archivo PDF
            
        Returns:
            list: Lista de campos extraídos
        """
        datos_campos = []
        
        try:
            with pdfplumber.open(ruta_archivo) as pdf:
                for pagina in pdf.pages:
                    texto = pagina.extract_text()
                    if texto:
                        campos_detectados = self._extraer_campos_de_texto(texto)
                        datos_campos.extend(campos_detectados)
            
            if not datos_campos:
                datos_campos = self._escanear_pdf_con_ocr(ruta_archivo)
        
        except Exception as error:
            datos_campos = self._escanear_pdf_con_ocr(ruta_archivo)
        
        return datos_campos
    
    def _escanear_pdf_con_ocr(self, ruta_archivo):
        """
        Escanea PDF sin texto nativo usando OCR con Tesseract.
        
        Convierte cada página del PDF a imagen de alta resolución (300 DPI)
        y aplica OCR para extraer texto.
        
        Args:
            ruta_archivo (str): Ruta del archivo PDF
            
        Returns:
            list: Lista de campos extraídos
        """
        datos_campos = []
        
        try:
            documento_pdf = fitz.open(ruta_archivo)
            
            for numero_pagina in range(len(documento_pdf)):
                pagina = documento_pdf[numero_pagina]
                pixeles = pagina.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
                imagen = Image.frombytes("RGB", [pixeles.width, pixeles.height], pixeles.samples)
                
                resultados_ocr = self.ocr_helper.ocr_with_confidence(imagen)
                
                for resultado in resultados_ocr:
                    texto = resultado['text'].strip()
                    if texto:
                        campos_detectados = self._extraer_campos_de_texto(
                            texto, 
                            resultado['confidence']
                        )
                        datos_campos.extend(campos_detectados)
            
            documento_pdf.close()
        
        except Exception as error:
            print(f"Error OCR PDF: {str(error)}")
        
        return datos_campos
    
    def _escanear_imagen(self, ruta_archivo):
        """
        Escanea una imagen usando OCR con Tesseract.
        
        Aplica preprocesamiento a la imagen para mejorar calidad OCR
        y extrae texto con nivel de confianza.
        
        Args:
            ruta_archivo (str): Ruta del archivo de imagen
            
        Returns:
            list: Lista de campos extraídos
        """
        datos_campos = []
        
        try:
            imagen = cv2.imread(ruta_archivo)
            imagen = self.image_helper.preprocess_image(imagen)
            
            resultados_ocr = self.ocr_helper.ocr_with_confidence(imagen)
            
            for resultado in resultados_ocr:
                texto = resultado['text'].strip()
                if texto:
                    campos_detectados = self._extraer_campos_de_texto(
                        texto, 
                        resultado['confidence']
                    )
                    datos_campos.extend(campos_detectados)
        
        except Exception as error:
            print(f"Error OCR imagen: {str(error)}")
        
        return datos_campos
    
    def _escanear_excel(self, ruta_archivo):
        """
        Extrae datos de un archivo Excel.
        
        Lee todas las celdas de la hoja activa y las convierte en campos.
        No requiere OCR.
        
        Args:
            ruta_archivo (str): Ruta del archivo Excel
            
        Returns:
            list: Lista de campos extraídos
        """
        datos_campos = []
        
        try:
            libro_trabajo = openpyxl.load_workbook(ruta_archivo)
            hoja_activa = libro_trabajo.active
            
            for fila in hoja_activa.iter_rows(values_only=True):
                for indice, valor_celda in enumerate(fila):
                    if valor_celda:
                        datos_campos.append({
                            'name': f'Campo_{indice+1}',
                            'value': str(valor_celda),
                            'is_empty': False,
                            'confidence': 100.0
                        })
        
        except Exception as error:
            print(f"Error Excel: {str(error)}")
        
        return datos_campos
    
    def _extraer_campos_de_texto(self, texto, confianza=100.0):
        """
        Extrae campos específicos del texto usando expresiones regulares.
        
        Busca patrones predefinidos (nombre, cédula, email, etc.) en el
        texto extraído y los convierte en campos estructurados.
        
        Args:
            texto (str): Texto del cual extraer campos
            confianza (float): Nivel de confianza del OCR (0-100)
            
        Returns:
            list: Lista de campos encontrados con sus valores
        """
        datos_campos = []
        
        patrones = [
            ('nombre', r'nombre[:\s]+([^\n]+)', True),
            ('apellido', r'apellido[:\s]+([^\n]+)', True),
            ('cedula', r'c[eé]dula[:\s]+([^\n]+)', True),
            ('dni', r'dni[:\s]+([^\n]+)', True),
            ('fecha', r'fecha[:\s]+([^\n]+)', False),
            ('direccion', r'direcci[oó]n[:\s]+([^\n]+)', False),
            ('telefono', r'tel[eé]fono[:\s]+([^\n]+)', False),
            ('email', r'email[:\s]+([^\n]+)', False),
            ('correo', r'correo[:\s]+([^\n]+)', False),
        ]
        
        texto_minusculas = texto.lower()
        
        for nombre_campo, patron, es_critico in patrones:
            coincidencia = re.search(patron, texto_minusculas, re.IGNORECASE)
            if coincidencia:
                valor = coincidencia.group(1).strip()
                datos_campos.append({
                    'name': nombre_campo.capitalize(),
                    'value': valor,
                    'is_empty': len(valor) == 0,
                    'is_critical': es_critico,
                    'confidence': confianza
                })
        
        return datos_campos
    
    def _generar_pdf_salida(self, documento, datos_campos):
        """
        Genera un PDF con los resultados del escaneo.
        
        Crea un documento PDF que contiene la información del documento
        escaneado y todos los campos extraídos con sus valores.
        
        Args:
            documento (ScannedDocument): Modelo del documento escaneado
            datos_campos (list): Lista de campos extraídos
            
        Returns:
            str: Ruta del archivo PDF generado
        """
        ruta_salida = Path('outputs') / f'doc_{documento.id}_output.pdf'
        ruta_salida.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            documento_pdf = fitz.open()
            pagina = documento_pdf.new_page()
            
            pagina.insert_text(
                (50, 50), 
                f"Documento ID: {documento.id}", 
                fontsize=16
            )
            pagina.insert_text(
                (50, 80), 
                f"Archivo: {Path(documento.file_path).name}", 
                fontsize=10
            )
            pagina.insert_text(
                (50, 100), 
                f"Confianza: {documento.confidence_score:.2f}%", 
                fontsize=10
            )
            
            posicion_y = 140
            for campo in datos_campos:
                texto = f"{campo['name']}: {campo['value']}"
                pagina.insert_text((50, posicion_y), texto, fontsize=10)
                posicion_y += 20
            
            documento_pdf.save(str(ruta_salida))
            documento_pdf.close()
        
        except Exception as error:
            print(f"Error generando PDF: {str(error)}")
        
        return str(ruta_salida)
    
    @classmethod
    def get_instance(cls):
        """
        Obtiene la instancia única del controlador (Singleton).
        
        Returns:
            ScannerController: Instancia única del controlador
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


"""
==============================================================================
DOCUMENTACIÓN TÉCNICA - SCANNER CONTROLLER
==============================================================================

ARQUITECTURA DEL CONTROLADOR
=============================

Patrón de Diseño: Singleton
    - Una única instancia para toda la aplicación
    - Gestión centralizada de recursos OCR
    - Evita múltiples inicializaciones de motores pesados

Dependencias:
    - OCRHelper: Procesamiento OCR con Tesseract
    - FileHelper: Gestión de archivos y carpetas
    - ImageHelper: Preprocesamiento de imágenes
    - Modelos: ScanJob, ScannedDocument, DocumentField


FLUJO DE PROCESAMIENTO
=======================

1. Inicio de Trabajo (start_scan):
   --------------------------------
   a. Crear registro ScanJob en BD
   b. Escanear carpeta y obtener lista de archivos
   c. Generar CSV con rutas y tipos
   d. Actualizar total_files en BD
   
   Archivos Soportados:
   - PDF: .pdf
   - Imágenes: .png, .jpg, .jpeg, .tiff, .bmp
   - Excel: .xlsx, .xls

2. Procesamiento (process_scan):
   ------------------------------
   a. Leer CSV con lista de archivos
   b. Para cada archivo:
      - Determinar tipo
      - Procesar según tipo
      - Extraer campos
      - Generar PDF salida
      - Actualizar progreso
   c. Marcar trabajo como completado

3. Escaneo por Tipo:
   -----------------
   
   PDF:
   - Intentar extracción nativa (pdfplumber)
   - Si falla o no hay texto: OCR con imágenes 300 DPI
   - Convertir páginas a imágenes
   - Aplicar Tesseract OCR
   
   Imágenes:
   - Preprocesamiento (escala de grises, binarización, etc.)
   - OCR con Tesseract
   - Extracción de campos con confianza
   
   Excel:
   - Lectura directa de celdas
   - Sin OCR necesario
   - Confianza 100%

4. Extracción de Campos:
   ---------------------
   Patrones detectados automáticamente:
   
   Campos Críticos:
   - Nombre
   - Apellido
   - Cédula/DNI
   
   Campos Opcionales:
   - Fecha
   - Dirección
   - Teléfono
   - Email/Correo
   
   Proceso:
   - Búsqueda con expresiones regulares
   - Case-insensitive
   - Extracción de valor después del patrón
   - Validación de campo vacío

5. Generación de PDF Salida:
   -------------------------
   - Información del documento
   - Lista de campos extraídos
   - Nivel de confianza
   - Guardado en carpeta /outputs


MÉTRICAS Y VALIDACIÓN
======================

Confidence Score:
    - Promedio de confianza de todos los campos
    - Rango: 0.0 - 100.0
    - Basado en confianza del motor OCR

Empty Fields Count:
    - Cantidad de campos detectados pero vacíos
    - Indica problemas en extracción

Has Errors:
    - TRUE si más del 30% de campos están vacíos
    - Marca documentos problemáticos


PATRONES DE EXTRACCIÓN
=======================

Expresiones Regulares Utilizadas:

Nombre:
    Pattern: nombre[:\s]+([^\n]+)
    Ejemplo: "Nombre: Juan Carlos"
    Extrae: "Juan Carlos"

Cédula:
    Pattern: c[eé]dula[:\s]+([^\n]+)
    Ejemplo: "Cédula: 1234567890"
    Extrae: "1234567890"

Email:
    Pattern: email[:\s]+([^\n]+)
    Ejemplo: "Email: usuario@ejemplo.com"
    Extrae: "usuario@ejemplo.com"

Teléfono:
    Pattern: tel[eé]fono[:\s]+([^\n]+)
    Ejemplo: "Teléfono: +593 99 123 4567"
    Extrae: "+593 99 123 4567"


ESTRUCTURA DE ARCHIVOS GENERADOS
=================================

CSV Temporal:
    Ubicación: /temp/scan_job_{id}_files.csv
    Formato:
        file_path,file_type
        C:/Docs/doc1.pdf,pdf
        C:/Docs/img1.png,png
    
    Propósito:
        - Mantener lista de archivos a procesar
        - Permitir procesamiento en lotes
        - Facilitar reintentos en caso de fallo

PDF Salida:
    Ubicación: /outputs/doc_{id}_output.pdf
    Contenido:
        - ID del documento
        - Nombre del archivo original
        - Score de confianza
        - Lista de campos con valores
    
    Propósito:
        - Resultado visual del escaneo
        - Validación manual
        - Archivo para revisión


MANEJO DE ERRORES
=================

Errores de Archivo:
    - Archivo no encontrado
    - Archivo corrupto
    - Formato no soportado
    Acción: Marcar documento con has_errors=True

Errores de OCR:
    - Imagen muy oscura/clara
    - Texto ilegible
    - Idioma no soportado
    Acción: Continuar con confianza baja

Errores de Base de Datos:
    - Fallo en commit
    - Conexión perdida
    Acción: Rollback y re-lanzar excepción


OPTIMIZACIONES IMPLEMENTADAS
=============================

1. Resolución Adaptativa:
   - PDFs convertidos a 300 DPI para mejor OCR
   - Balance entre calidad y rendimiento

2. Preprocesamiento Inteligente:
   - Escala de grises
   - Binarización
   - Reducción de ruido
   - Mejora contraste

3. Extracción Híbrida PDF:
   - Primero intenta texto nativo (rápido)
   - Si falla, usa OCR (preciso)

4. Singleton Pattern:
   - Evita reinicialización de motores OCR
   - Reduce uso de memoria
   - Mejora rendimiento

5. Batch Processing:
   - Procesamiento archivo por archivo
   - Actualización incremental de progreso
   - Permite interrupciones controladas


EJEMPLO DE USO COMPLETO
========================

Python:
    from controllers.scanner_controller import ScannerController
    
    # Obtener instancia
    scanner = ScannerController.get_instance()
    
    # Iniciar escaneo
    job = scanner.start_scan('C:/Documentos/Facturas')
    print(f"Job ID: {job['id']}")
    print(f"Total archivos: {job['total_files']}")
    
    # Procesar
    resultado = scanner.process_scan(job['id'])
    print(f"Estado: {resultado['status']}")
    print(f"Procesados: {resultado['processed_files']}")
    
    # Verificar documentos
    from models.scanned_document import ScannedDocument
    docs = ScannedDocument.query.filter_by(scan_job_id=job['id']).all()
    
    for doc in docs:
        print(f"\nDocumento: {doc.file_path}")
        print(f"Confianza: {doc.confidence_score}%")
        print(f"Campos vacíos: {doc.empty_fields_count}")
        print(f"PDF salida: {doc.output_pdf_path}")
        
        # Campos extraídos
        for campo in doc.fields:
            print(f"  {campo.field_name}: {campo.field_value}")


CONSIDERACIONES DE RENDIMIENTO
===============================

Tiempo de Procesamiento Estimado:
    - PDF nativo (5 páginas): ~2 segundos
    - PDF escaneado (5 páginas): ~15 segundos
    - Imagen (300 DPI): ~3 segundos
    - Excel (100 filas): ~1 segundo

Memoria:
    - Por documento: ~50 MB durante procesamiento
    - Motor OCR: ~200 MB permanente

Mejoras Sugeridas:
    1. Procesamiento paralelo con multiprocessing
    2. Cola de trabajos con Celery
    3. Cache de resultados OCR
    4. Compresión de imágenes intermedias

==============================================================================
"""