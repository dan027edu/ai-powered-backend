from transformers import pipeline
import docx2txt
import PyPDF2
import re
from django.conf import settings

class DocumentClassifier:
    """Document classifier using zero-shot classification with pre-trained models"""
    
    def __init__(self):
        # Initialize the zero-shot classification pipeline
        self.classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=settings.MODEL_DEVICE  # Use setting from Django config
        )
        
        # Define the candidate labels
        self.candidate_labels = [
            "academic credentials",
            "certification",  # This includes diplomas and other certifications
            "transcript of records", 
            "service record"
        ]
        
        # Simple hypothesis template
        self.hypothesis_template = "This document is a {}"

    def _extract_text_from_docx(self, file_path):
        """Extract text from DOCX files"""
        try:
            text = docx2txt.process(file_path)
            return self._preprocess_text(text)
        except Exception as e:
            print(f"Error processing DOCX {file_path}: {str(e)}")
            return ""

    def _extract_text_from_pdf(self, file_path):
        """Extract text from PDF files"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + " "
            return self._preprocess_text(text)
        except Exception as e:
            print(f"Error processing PDF {file_path}: {str(e)}")
            return ""

    def _preprocess_text(self, text):
        """Preprocess extracted text"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep important punctuation
        text = re.sub(r'[^a-z0-9\s.,!?-]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text.strip()

    def classify_file(self, file_path):
        """Classify a document file using zero-shot classification"""
        # Extract text based on file type
        if file_path.lower().endswith('.docx'):
            text = self._extract_text_from_docx(file_path)
        elif file_path.lower().endswith('.pdf'):
            text = self._extract_text_from_pdf(file_path)
        else:
            return "unknown"
            
        return self.classify_text(text)
            
    def classify_text(self, text):
        """Classify text using zero-shot classification"""
        if not text or not text.strip():
            return "unknown"
            
        try:
            # Run zero-shot classification
            result = self.classifier(
                text, 
                self.candidate_labels,
                hypothesis_template=self.hypothesis_template,
                multi_label=False
            )
            
            # Get the highest confidence prediction if it meets the threshold
            max_score = max(result['scores'])
            if max_score >= settings.MODEL_CONFIDENCE_THRESHOLD:
                return result['labels'][0]  # Return the top prediction
            
            return "unknown"
            
        except Exception as e:
            print(f"Classification error: {str(e)}")
            return "unknown"