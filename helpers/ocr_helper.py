"""
==============================================================================
HELPER DE OCR - RECONOCIMIENTO OPTICO DE CARACTERES MULTI-MOTOR
==============================================================================

Descripcion:
    Helper Singleton que proporciona servicios de OCR utilizando dos motores
    de reconocimiento: Tesseract OCR y EasyOCR. Permite extraccion de texto
    de imagenes y documentos escaneados con alta precision.

Motores Implementados:
    - Tesseract OCR: Motor tradicional de Google (95-97% precision)
    - EasyOCR: Motor basado en Deep Learning (92-95% precision)

Caracteristicas:
    - Patron Singleton para gestion unica de recursos
    - Soporte para español
    - Procesamiento sin GPU (compatible con cualquier hardware)
    - Modo combinado para maxima precision
    - Niveles de confianza por resultado
    - Compatible con Windows

Nota Tecnica:
    PaddleOCR fue removido por problemas de compatibilidad en Windows.
    Este helper esta optimizado para entornos Windows corporativos.

Autor: OctavoSMG
Version: 1.0.0 - Optimizado para Windows
==============================================================================
"""

import pytesseract
from PIL import Image
import easyocr
import numpy as np


class OCRHelper:
    """
    Helper de OCR con dos motores para maxima compatibilidad.
    
    Proporciona servicios de reconocimiento optico de caracteres usando
    Tesseract (tradicional) y EasyOCR (deep learning) con soporte para
    procesamiento individual o combinado.
    """
    
    _instance = None
    
    def __new__(cls):
        """
        Implementacion del patron Singleton.
        Garantiza una unica instancia del helper.
        """
        if cls._instance is None:
            cls._instance = super(OCRHelper, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """
        Inicializa los motores OCR.
        
        Configuracion:
            - Tesseract: Ruta del ejecutable en Windows
            - EasyOCR: Modelo en español, sin GPU
        
        Notas:
            - Solo se inicializa una vez gracias al flag _initialized
            - EasyOCR descarga modelos en primera ejecucion (~100 MB)
            - Tesseract debe estar instalado en el sistema
        """
        if self._initialized:
            return
        
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        print("Inicializando EasyOCR...")
        self.lector_easyocr = easyocr.Reader(['es'], gpu=False)
        print("EasyOCR inicializado correctamente")
        
        self._initialized = True
        print("OCR Helper inicializado (Tesseract + EasyOCR)")
    
    def ocr_image(self, imagen, motor='easy'):
        """
        Extrae texto de una imagen usando el motor especificado.
        
        Args:
            imagen: Imagen a procesar (str, np.ndarray, PIL.Image)
            motor: Motor OCR a utilizar (easy, tesseract, all)
        
        Returns:
            list: Lista de diccionarios con texto extraido
        """
        if motor == 'easy':
            return self._ocr_con_easyocr(imagen)
        elif motor == 'tesseract':
            return self._ocr_con_tesseract(imagen)
        elif motor == 'all':
            return self._ocr_combinado(imagen)
        else:
            return self._ocr_con_easyocr(imagen)
    
    def ocr_with_confidence(self, imagen):
        """
        Metodo de compatibilidad usado por scanner_controller.
        Usa EasyOCR por defecto.
        
        Args:
            imagen: Imagen a procesar
            
        Returns:
            list: Resultados de OCR con confianza
        """
        return self._ocr_con_easyocr(imagen)
    
    def _ocr_con_easyocr(self, imagen):
        """
        Extrae texto usando EasyOCR (Deep Learning).
        
        Precision: 92-95%
        Velocidad: Media (~3 segundos por imagen)
        
        Args:
            imagen: Imagen a procesar
            
        Returns:
            list: Lista de diccionarios con resultados
        """
        if isinstance(imagen, str):
            resultado = self.lector_easyocr.readtext(imagen)
        else:
            if isinstance(imagen, np.ndarray):
                resultado = self.lector_easyocr.readtext(imagen)
            else:
                resultado = self.lector_easyocr.readtext(np.array(imagen))
        
        resultados_texto = []
        for deteccion in resultado:
            resultados_texto.append({
                'text': deteccion[1],
                'confidence': float(deteccion[2]) * 100,
                'engine': 'easy'
            })
        
        return resultados_texto
    
    def _ocr_con_tesseract(self, imagen):
        """
        Extrae texto usando Tesseract OCR (Tradicional).
        
        Precision: 95-97%
        Velocidad: Rapida (~1 segundo por imagen)
        
        Args:
            imagen: Imagen a procesar
            
        Returns:
            list: Lista de diccionarios con resultados
        """
        if isinstance(imagen, str):
            imagen = Image.open(imagen)
        
        datos = pytesseract.image_to_data(
            imagen, 
            lang='spa', 
            output_type=pytesseract.Output.DICT
        )
        
        resultados = []
        cantidad_cajas = len(datos['text'])
        
        for i in range(cantidad_cajas):
            texto = datos['text'][i].strip()
            confianza = int(datos['conf'][i])
            
            if texto != "" and confianza > 0:
                resultados.append({
                    'text': texto,
                    'confidence': float(confianza),
                    'engine': 'tesseract'
                })
        
        return resultados
    
    def _ocr_combinado(self, imagen):
        """
        Ejecuta ambos motores y combina resultados por confianza.
        
        Args:
            imagen: Imagen a procesar
            
        Returns:
            list: Resultados combinados ordenados por confianza
        """
        print("Ejecutando OCR combinado (EasyOCR + Tesseract)...")
        
        resultados_easy = self._ocr_con_easyocr(imagen)
        resultados_tesseract = self._ocr_con_tesseract(imagen)
        
        todos_resultados = resultados_easy + resultados_tesseract
        
        todos_resultados.sort(key=lambda x: x['confidence'], reverse=True)
        
        return todos_resultados
    
    @classmethod
    def get_instance(cls):
        """
        Obtiene la instancia unica del helper (Singleton).
        
        Returns:
            OCRHelper: Instancia unica del helper
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance