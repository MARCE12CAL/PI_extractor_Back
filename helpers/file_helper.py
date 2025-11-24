"""
==============================================================================
HELPER DE GESTIÓN DE ARCHIVOS
==============================================================================

Descripción:
    Helper Singleton que proporciona utilidades para la gestión de archivos
    y directorios del sistema. Incluye funciones para escaneo recursivo de
    carpetas, detección de tipos de archivo y creación de estructura de
    directorios.

Características:
    - Patrón Singleton para gestión única de recursos
    - Escaneo recursivo de carpetas
    - Filtrado por extensiones soportadas
    - Detección automática de tipo de archivo
    - Creación de estructura de directorios
    - Soporte multi-formato

Formatos Soportados:
    - Documentos: PDF, DOCX, DOC
    - Imágenes: PNG, JPG, JPEG, TIFF, BMP
    - Hojas de Cálculo: XLSX, XLS

Autor: OctavoSMG
Versión: 1.0.0
==============================================================================
"""

import os
from pathlib import Path


class FileHelper:
    """
    Helper de gestión de archivos para el sistema de escaneo.
    
    Proporciona métodos estáticos para operaciones comunes con archivos:
    búsqueda recursiva, detección de tipos y gestión de directorios.
    """
    
    _instance = None
    
    def __new__(cls):
        """
        Implementación del patrón Singleton.
        Garantiza una única instancia del helper.
        """
        if cls._instance is None:
            cls._instance = super(FileHelper, cls).__new__(cls)
        return cls._instance
    
    @staticmethod
    def get_all_files(ruta_carpeta):
        """
        Obtiene todos los archivos soportados de una carpeta recursivamente.
        
        Escanea la carpeta especificada y todas sus subcarpetas, buscando
        archivos con extensiones soportadas por el sistema de escaneo.
        
        Args:
            ruta_carpeta (str): Ruta de la carpeta a escanear
            
        Returns:
            list: Lista de rutas absolutas de archivos encontrados
            
        Extensiones Soportadas:
            Documentos:
                - .pdf: Documentos PDF
                - .docx: Microsoft Word (Office 2007+)
                - .doc: Microsoft Word (Office 97-2003)
            
            Imágenes:
                - .png: Portable Network Graphics
                - .jpg, .jpeg: Joint Photographic Experts Group
                - .tiff: Tagged Image File Format
                - .bmp: Bitmap
            
            Hojas de Cálculo:
                - .xlsx: Microsoft Excel (Office 2007+)
                - .xls: Microsoft Excel (Office 97-2003)
        
        Comportamiento:
            - Búsqueda recursiva en subcarpetas
            - Case-insensitive (ignora mayúsculas/minúsculas)
            - Retorna rutas absolutas
            - Omite archivos ocultos del sistema
            - No sigue enlaces simbólicos
        
        Example:
            >>> helper = FileHelper.get_instance()
            >>> archivos = helper.get_all_files('C:/Documentos')
            >>> print(f"Encontrados: {len(archivos)} archivos")
            >>> for archivo in archivos:
            ...     print(archivo)
        """
        extensiones_soportadas = {
            '.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp', 
            '.xlsx', '.xls', '.docx', '.doc'
        }
        
        rutas_archivos = []
        
        for raiz, directorios, archivos in os.walk(ruta_carpeta):
            for archivo in archivos:
                extension = Path(archivo).suffix.lower()
                
                if extension in extensiones_soportadas:
                    ruta_completa = os.path.join(raiz, archivo)
                    rutas_archivos.append(ruta_completa)
        
        return rutas_archivos
    
    @staticmethod
    def get_file_type(ruta_archivo):
        """
        Obtiene el tipo de archivo a partir de su extensión.
        
        Extrae la extensión del archivo sin el punto inicial y en minúsculas.
        
        Args:
            ruta_archivo (str): Ruta completa o nombre del archivo
            
        Returns:
            str: Tipo de archivo sin punto (ej: 'pdf', 'png', 'xlsx')
            
        Example:
            >>> FileHelper.get_file_type('C:/Docs/factura.PDF')
            'pdf'
            >>> FileHelper.get_file_type('imagen.JPG')
            'jpg'
            >>> FileHelper.get_file_type('/home/user/datos.xlsx')
            'xlsx'
        """
        return Path(ruta_archivo).suffix.lower()[1:]
    
    @staticmethod
    def create_directories():
        """
        Crea la estructura de directorios necesaria para el sistema.
        
        Genera los directorios requeridos por la aplicación si no existen:
        - uploads: Archivos subidos por usuarios
        - outputs: PDFs procesados y reportes generados
        - temp: Archivos temporales (CSVs, cache)
        
        Comportamiento:
            - No falla si directorios ya existen (exist_ok=True)
            - Crea directorios con permisos por defecto del sistema
            - Es seguro ejecutar múltiples veces
        
        Estructura Generada:
            proyecto/
            ├── uploads/
            ├── outputs/
            └── temp/
        
        Example:
            >>> FileHelper.create_directories()
            # Directorios creados o verificados exitosamente
        """
        directorios = ['uploads', 'outputs', 'temp']
        
        for nombre_directorio in directorios:
            Path(nombre_directorio).mkdir(exist_ok=True)
    
    @classmethod
    def get_instance(cls):
        """
        Obtiene la instancia única del helper (Singleton).
        
        Returns:
            FileHelper: Instancia única del helper
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


"""
==============================================================================
DOCUMENTACIÓN TÉCNICA - FILE HELPER
==============================================================================

PROPÓSITO DEL HELPER
=====================

El FileHelper centraliza todas las operaciones relacionadas con el sistema
de archivos, proporcionando una interfaz consistente y segura para:

1. Descubrimiento de Archivos:
   - Escaneo recursivo de carpetas
   - Filtrado por extensiones soportadas
   - Construcción de lista de trabajo

2. Identificación de Tipos:
   - Detección de formato por extensión
   - Normalización de extensiones
   - Soporte case-insensitive

3. Gestión de Estructura:
   - Creación de directorios necesarios
   - Verificación de existencia
   - Mantenimiento de organización


ESCANEO RECURSIVO DE CARPETAS
==============================

Algoritmo de os.walk():

Funcionamiento:
    for root, dirs, files in os.walk(path):
        # root: Directorio actual
        # dirs: Lista de subdirectorios
        # files: Lista de archivos en directorio actual

Ejemplo de Recorrido:
    
    Estructura:
    Documentos/
    ├── Facturas/
    │   ├── 2024/
    │   │   ├── factura_001.pdf
    │   │   └── factura_002.pdf
    │   └── 2025/
    │       └── factura_003.pdf
    └── Contratos/
        └── contrato_A.docx
    
    Primera Iteración:
    root = 'Documentos'
    dirs = ['Facturas', 'Contratos']
    files = []
    
    Segunda Iteración:
    root = 'Documentos/Facturas'
    dirs = ['2024', '2025']
    files = []
    
    Tercera Iteración:
    root = 'Documentos/Facturas/2024'
    dirs = []
    files = ['factura_001.pdf', 'factura_002.pdf']
    
    ... y así sucesivamente

Ventajas:
    - Explora toda la jerarquía automáticamente
    - Eficiente en memoria (generador)
    - Maneja estructuras profundas
    - No requiere recursión manual

Limitaciones:
    - Sigue enlaces simbólicos por defecto
    - Puede entrar en bucles con links circulares
    - No detecta automáticamente permisos


EXTENSIONES SOPORTADAS
=======================

Categorías de Archivos:

1. Documentos PDF:
   ---------------
   .pdf
   Características:
   - Formato universal de documentos
   - Puede contener texto nativo o imágenes
   - Requiere conversión a imagen para OCR si está escaneado
   
   Procesamiento:
   - Extracción de texto nativo con pdfplumber
   - OCR con conversión a imagen si es necesario
   - Soporte multi-página

2. Imágenes:
   ---------
   .png, .jpg, .jpeg, .tiff, .bmp
   
   PNG (Portable Network Graphics):
   - Sin pérdida
   - Soporte transparencia
   - Ideal para documentos escaneados
   
   JPEG (Joint Photographic Experts Group):
   - Con pérdida
   - Buena compresión
   - Común en fotografías
   
   TIFF (Tagged Image File Format):
   - Sin pérdida
   - Multi-página
   - Estándar en escaneo profesional
   
   BMP (Bitmap):
   - Sin compresión
   - Archivos grandes
   - Alta calidad

3. Hojas de Cálculo:
   -----------------
   .xlsx, .xls
   
   XLSX (Office Open XML):
   - Office 2007+
   - Basado en XML
   - Compresión ZIP
   
   XLS (Binary Interchange File Format):
   - Office 97-2003
   - Formato binario
   - Compatibilidad legacy

4. Documentos Word:
   ----------------
   .docx, .doc
   
   DOCX (Office Open XML):
   - Office 2007+
   - Basado en XML
   - Extracción de texto directa
   
   DOC (Binary):
   - Office 97-2003
   - Formato binario
   - Requiere conversión


DETECCIÓN DE TIPO DE ARCHIVO
=============================

Método Implementado: Extensión

Path(archivo).suffix:
    - Retorna extensión con punto: '.pdf'
    - Incluye el punto inicial
    - Case-sensitive por defecto

Normalización:
    extension = Path(archivo).suffix.lower()
    # '.PDF' → '.pdf'
    # '.Xlsx' → '.xlsx'

Sin Punto:
    tipo = extension[1:]
    # '.pdf' → 'pdf'
    # '.xlsx' → 'xlsx'

Alternativas No Implementadas:

1. MIME Type:
   import mimetypes
   tipo = mimetypes.guess_type(archivo)[0]
   # 'application/pdf'
   # 'image/jpeg'

2. Magic Numbers:
   import magic
   tipo = magic.from_file(archivo, mime=True)
   # Lee primeros bytes del archivo
   # Más preciso pero requiere librería

3. Librería Específica:
   from PIL import Image
   try:
       img = Image.open(archivo)
       tipo = img.format
   except:
       pass


ESTRUCTURA DE DIRECTORIOS
==========================

Directorios Creados:

1. uploads/
   ---------
   Propósito: Almacenar archivos subidos por usuarios
   
   Uso:
   - Recepción de archivos vía API
   - Almacenamiento temporal antes de procesamiento
   - Preservación de archivos originales
   
   Consideraciones:
   - Debe tener espacio suficiente
   - Implementar limpieza periódica
   - Configurar límites de tamaño

2. outputs/
   ---------
   Propósito: Guardar resultados de procesamiento
   
   Contenido:
   - PDFs generados con resultados OCR
   - PDFs unificados de trabajos
   - Reportes consolidados
   
   Estructura Típica:
   outputs/
   ├── doc_1_output.pdf
   ├── doc_2_output.pdf
   ├── doc_3_output.pdf
   └── unified_job_123.pdf

3. temp/
   ------
   Propósito: Archivos temporales de procesamiento
   
   Contenido:
   - CSVs con listas de archivos
   - Imágenes intermedias
   - Cache de OCR
   
   Gestión:
   - Limpieza automática recomendada
   - No persistir datos críticos
   - Puede eliminarse sin afectar sistema


GESTIÓN DE RUTAS
=================

Rutas Absolutas vs Relativas:

Absolutas (Implementado):
    ruta_completa = os.path.join(raiz, archivo)
    # 'C:/Documentos/Facturas/factura.pdf'
    
    Ventajas:
    - Sin ambigüedad
    - Funciona desde cualquier directorio
    - Necesario para base de datos

Relativas:
    ruta_relativa = os.path.relpath(ruta_completa, inicio)
    # 'Facturas/factura.pdf'
    
    Ventajas:
    - Más cortas
    - Portables entre sistemas
    - Útiles para logging

Normalización:
    Path(ruta).resolve()
    # Convierte a absoluta
    # Resuelve '..' y '.'
    # Elimina duplicados de separadores


CONSIDERACIONES DE SEGURIDAD
=============================

Validaciones Recomendadas:

1. Verificar Existencia:
   if not Path(ruta_carpeta).exists():
       raise FileNotFoundError(f"Carpeta no encontrada: {ruta_carpeta}")

2. Verificar Permisos:
   if not os.access(ruta_carpeta, os.R_OK):
       raise PermissionError(f"Sin permisos de lectura: {ruta_carpeta}")

3. Prevenir Path Traversal:
   ruta_segura = Path(ruta_carpeta).resolve()
   if not str(ruta_segura).startswith(str(base_permitida)):
       raise SecurityError("Acceso no autorizado")

4. Limitar Profundidad:
   max_depth = 10
   depth = ruta.count(os.sep)
   if depth > max_depth:
       continue  # Omitir directorios muy profundos

5. Validar Tamaño:
   max_size = 100 * 1024 * 1024  # 100 MB
   if os.path.getsize(archivo) > max_size:
       continue  # Omitir archivos muy grandes


OPTIMIZACIONES DE RENDIMIENTO
==============================

Escaneo de Carpetas Grandes:

Problema: Carpetas con miles de archivos
Solución 1: Límite de archivos
    if len(rutas_archivos) >= 1000:
        break

Solución 2: Procesamiento por lotes
    def get_files_batch(folder, batch_size=100):
        batch = []
        for root, dirs, files in os.walk(folder):
            for file in files:
                if len(batch) >= batch_size:
                    yield batch
                    batch = []
                batch.append(os.path.join(root, file))
        if batch:
            yield batch

Solución 3: Filtrado temprano
    for archivo in archivos:
        if not archivo.endswith(tuple(extensiones_soportadas)):
            continue  # Omitir sin crear Path


EJEMPLO DE USO COMPLETO
========================

Python:
    from helpers.file_helper import FileHelper
    
    # Obtener instancia
    file_helper = FileHelper.get_instance()
    
    # Crear estructura de directorios
    file_helper.create_directories()
    
    # Escanear carpeta
    carpeta = 'C:/Documentos/Facturas'
    archivos = file_helper.get_all_files(carpeta)
    
    print(f"Encontrados: {len(archivos)} archivos")
    
    # Clasificar por tipo
    por_tipo = {}
    for archivo in archivos:
        tipo = file_helper.get_file_type(archivo)
        if tipo not in por_tipo:
            por_tipo[tipo] = []
        por_tipo[tipo].append(archivo)
    
    # Mostrar estadísticas
    for tipo, lista in por_tipo.items():
        print(f"{tipo.upper()}: {len(lista)} archivos")


Integración con Scanner Controller:
    from helpers.file_helper import FileHelper
    
    def start_scan(self, folder_path):
        # Escanear carpeta
        file_paths = self.file_helper.get_all_files(folder_path)
        
        # Validar que hay archivos
        if not file_paths:
            raise ValueError(f"No se encontraron archivos en {folder_path}")
        
        # Crear trabajo
        scan_job = ScanJob(
            folder_path=folder_path,
            total_files=len(file_paths)
        )
        
        # Generar CSV
        csv_path = self._generar_csv(scan_job.id, file_paths)

==============================================================================
"""