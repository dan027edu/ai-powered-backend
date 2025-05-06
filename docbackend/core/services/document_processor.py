import docx2txt
import PyPDF2
from django.conf import settings

class DocumentProcessor:
    def extract_text(self, file_path):
        """Extract text from document files"""
        if file_path.lower().endswith('.docx'):
            return self._extract_text_from_docx(file_path)
        elif file_path.lower().endswith('.pdf'):
            return self._extract_text_from_pdf(file_path)
        else:
            raise ValueError("Unsupported file format")

    def _extract_text_from_docx(self, file_path):
        """Extract text from DOCX files"""
        try:
            text = docx2txt.process(file_path)
            return text.strip()
        except Exception as e:
            print(f"Error processing DOCX {file_path}: {str(e)}")
            raise ValueError(f"Could not process DOCX file: {str(e)}")

    def _extract_text_from_pdf(self, file_path):
        """Extract text from PDF files"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + " "
            return text.strip()
        except Exception as e:
            print(f"Error processing PDF {file_path}: {str(e)}")
            raise ValueError(f"Could not process PDF file: {str(e)}")