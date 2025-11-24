"""
==============================================================================
MACHINE LEARNING OCR CONTROLLER
==============================================================================
Sistema de aprendizaje automático para mejorar OCR con el tiempo.
==============================================================================
"""

from collections import defaultdict
from difflib import get_close_matches
from datetime import datetime

from db.connection import db
from models.document_field import DocumentField
from models.scanned_document import ScannedDocument


class MLOCRLearner:
    """
    Controlador de Machine Learning para OCR
    Aprende de correcciones manuales y mejora automáticamente
    """
    
    def __init__(self):
        self.patterns = defaultdict(list)
        self.corrections_cache = {}
        
    
    def learn_from_correction(self, field_id, original_value, corrected_value, field_type):
        """
        Aprende de una corrección manual
        
        Args:
            field_id: ID del campo corregido
            original_value: Valor original del OCR
            corrected_value: Valor corregido por el usuario
            field_type: Tipo de campo (nombre, cedula, etc.)
        """
        try:
            # Obtener el campo
            field = DocumentField.query.get(field_id)
            if not field:
                return {"error": "Campo no encontrado"}, 404
            
            # Detectar el tipo de corrección
            correction_type = self._detect_correction_type(original_value, corrected_value)
            
            # Guardar en la base de datos
            field.manually_corrected = True
            field.correction_date = datetime.now()
            field.correction_confidence = 1.0  # Corrección manual = 100% confianza
            
            db.session.commit()
            
            # Agregar al patrón de aprendizaje
            pattern = {
                'original': original_value,
                'corrected': corrected_value,
                'type': correction_type,
                'field_type': field_type,
                'date': datetime.now().isoformat()
            }
            
            self.patterns[field_type].append(pattern)
            
            return {
                "success": True,
                "pattern_learned": pattern,
                "total_patterns": len(self.patterns[field_type]),
                "message": f"Patrón aprendido exitosamente para {field_type}"
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500
    
    
    def suggest_correction(self, field_id):
        """
        Sugiere una corrección basada en patrones aprendidos
        
        Args:
            field_id: ID del campo a corregir
        """
        try:
            field = DocumentField.query.get(field_id)
            if not field:
                return {"error": "Campo no encontrado"}, 404
            
            original_value = field.value
            field_type = field.field_type
            
            # Buscar patrones similares
            suggestions = []
            
            if field_type in self.patterns:
                for pattern in self.patterns[field_type]:
                    similarity = self._calculate_similarity(
                        original_value, 
                        pattern['original']
                    )
                    
                    if similarity > 0.7:  # 70% de similitud
                        suggestions.append({
                            'value': pattern['corrected'],
                            'confidence': similarity,
                            'reason': f"Similar a: {pattern['original']}"
                        })
            
            # Ordenar por confianza
            suggestions.sort(key=lambda x: x['confidence'], reverse=True)
            
            # Tomar la mejor sugerencia
            best_suggestion = suggestions[0] if suggestions else None
            
            return {
                "field_id": field_id,
                "original_value": original_value,
                "suggestions": suggestions[:3],  # Top 3
                "best_suggestion": best_suggestion,
                "has_patterns": len(self.patterns[field_type]) > 0
            }, 200
            
        except Exception as e:
            return {"error": str(e)}, 500
    
    
    def auto_correct_document(self, document_id):
        """
        Auto-corrige todos los campos de un documento
        
        Args:
            document_id: ID del documento
        """
        try:
            # Obtener todos los campos del documento
            fields = DocumentField.query.filter_by(
                scanned_document_id=document_id
            ).all()
            
            corrections_made = []
            
            for field in fields:
                # Intentar auto-corrección
                suggestion_response, status = self.suggest_correction(field.id)
                
                if status == 200 and suggestion_response.get('best_suggestion'):
                    suggestion = suggestion_response['best_suggestion']
                    
                    # Si la confianza es alta, auto-corregir
                    if suggestion['confidence'] > 0.85:  # 85% de confianza
                        field.value = suggestion['value']
                        field.auto_corrected = True
                        field.correction_date = datetime.now()
                        field.correction_confidence = suggestion['confidence']
                        
                        corrections_made.append({
                            'field_id': field.id,
                            'field_type': field.field_type,
                            'original': suggestion_response['original_value'],
                            'corrected': suggestion['value'],
                            'confidence': suggestion['confidence']
                        })
            
            db.session.commit()
            
            return {
                "document_id": document_id,
                "corrections_made": len(corrections_made),
                "details": corrections_made,
                "message": f"Se auto-corrigieron {len(corrections_made)} campos"
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500
    
    
    def get_learning_stats(self):
        """Obtiene estadísticas del sistema de aprendizaje"""
        try:
            # Contar correcciones manuales
            manual_corrections = DocumentField.query.filter_by(
                manually_corrected=True
            ).count()
            
            # Contar auto-correcciones
            auto_corrections = DocumentField.query.filter_by(
                auto_corrected=True
            ).count()
            
            # Estadísticas por tipo de campo
            stats_by_type = {}
            for field_type, patterns in self.patterns.items():
                stats_by_type[field_type] = {
                    'total_patterns': len(patterns),
                    'accuracy_estimate': min(len(patterns) * 5, 95)  # Estimación
                }
            
            return {
                "manual_corrections": manual_corrections,
                "auto_corrections": auto_corrections,
                "total_patterns_learned": sum(len(p) for p in self.patterns.values()),
                "patterns_by_type": stats_by_type,
                "learning_status": self._get_learning_status(manual_corrections)
            }, 200
            
        except Exception as e:
            return {"error": str(e)}, 500
    
    
    def export_patterns(self):
        """Exporta los patrones aprendidos a JSON"""
        try:
            patterns_dict = {}
            for field_type, patterns in self.patterns.items():
                patterns_dict[field_type] = patterns
            
            return {
                "patterns": patterns_dict,
                "export_date": datetime.now().isoformat(),
                "total_patterns": sum(len(p) for p in self.patterns.values())
            }, 200
            
        except Exception as e:
            return {"error": str(e)}, 500
    
    
    def import_patterns(self, patterns_data):
        """Importa patrones desde JSON"""
        try:
            for field_type, patterns in patterns_data.items():
                self.patterns[field_type].extend(patterns)
            
            return {
                "success": True,
                "patterns_imported": sum(len(p) for p in patterns_data.values()),
                "message": "Patrones importados exitosamente"
            }, 200
            
        except Exception as e:
            return {"error": str(e)}, 500
    
    
    # === MÉTODOS PRIVADOS ===
    
    def _detect_correction_type(self, original, corrected):
        """Detecta el tipo de corrección realizada"""
        if self._is_accent_correction(original, corrected):
            return "accent_correction"
        elif self._is_case_correction(original, corrected):
            return "case_correction"
        elif self._is_spacing_correction(original, corrected):
            return "spacing_correction"
        elif self._is_typo_correction(original, corrected):
            return "typo_correction"
        else:
            return "general_correction"
    
    
    def _is_accent_correction(self, original, corrected):
        """Detecta si es corrección de acentos"""
        def remove_accents(s):
            replacements = {
                'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
                'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
                'ñ': 'n', 'Ñ': 'N'
            }
            for old, new in replacements.items():
                s = s.replace(old, new)
            return s
        
        return remove_accents(original.lower()) == remove_accents(corrected.lower())
    
    
    def _is_case_correction(self, original, corrected):
        """Detecta si es corrección de mayúsculas/minúsculas"""
        return original.lower() == corrected.lower()
    
    
    def _is_spacing_correction(self, original, corrected):
        """Detecta si es corrección de espacios"""
        return original.replace(' ', '') == corrected.replace(' ', '')
    
    
    def _is_typo_correction(self, original, corrected):
        """Detecta si es corrección de errores tipográficos"""
        if len(original) != len(corrected):
            return False
        
        differences = sum(c1 != c2 for c1, c2 in zip(original, corrected))
        return 1 <= differences <= 2
    
    
    def _calculate_similarity(self, str1, str2):
        """Calcula similitud entre dos strings (0-1)"""
        if not str1 or not str2:
            return 0.0
        
        # Normalizar
        s1 = str1.lower().strip()
        s2 = str2.lower().strip()
        
        # Similitud exacta
        if s1 == s2:
            return 1.0
        
        # Distancia de Levenshtein normalizada
        max_len = max(len(s1), len(s2))
        distance = self._levenshtein_distance(s1, s2)
        
        return 1 - (distance / max_len)
    
    
    def _levenshtein_distance(self, s1, s2):
        """Calcula distancia de Levenshtein entre dos strings"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    
    def _get_learning_status(self, corrections_count):
        """Determina el estado de aprendizaje del sistema"""
        if corrections_count < 10:
            return "🌱 Principiante - Necesita más correcciones"
        elif corrections_count < 50:
            return "📚 Básico - Aprendiendo patrones"
        elif corrections_count < 200:
            return "🎓 Intermedio - Buen nivel de aprendizaje"
        elif corrections_count < 500:
            return "🏆 Avanzado - Alta precisión"
        else:
            return "🚀 Experto - Máxima precisión"


# Instancia global del controlador
ml_learner = MLOCRLearner()