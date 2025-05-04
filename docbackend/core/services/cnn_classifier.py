from transformers import pipeline
import re

class CNNClassifier:
    def __init__(self, model_path=None):
        """Initialize classifier with a pre-trained model"""
        # Using a pre-trained zero-shot classification model
        self.classifier = pipeline("zero-shot-classification",
                                 model="facebook/bart-large-mnli")
        self.candidate_labels = [
            "academic_transcript",  # For TORs and grade reports
            "academic_certificate", # For certificates, diplomas, degrees
            "employment_record",   # For service records, employment history
            "certification_letter", # For various certifications like units earned
            "authenticated_copy",  # For authenticated/certified true copies
            "school_id",          # For identification documents
            "enrollment_record",   # For registration, enrollment documents
            "academic_clearance"   # For clearance documents
        ]
        
        # Define document patterns with weighted indicators
        self.document_patterns = {
            "academic_transcript": {
                "keywords": [
                    "transcript of records", "tor", "academic credentials", "academic records",
                    "course code", "units", "grade", "gwa", "semester", "academic year",
                    "scholastic record", "academic performance"
                ],
                "required_patterns": [
                    r"(?i)(course|subject).*?(code|title|units?|grade)",  # Course details pattern
                    r"(?i)(general weighted average|gwa|units earned)",    # Academic metrics pattern
                    r"(?i)(transcript|academic).*?(records?|credentials?)" # TOR/credentials pattern
                ],
                "score_threshold": 0.5
            },
            "academic_certificate": {
                "keywords": ["diploma", "degree", "conferred", "bachelor", "master", "doctorate", "certificate of completion"],
                "required_patterns": [
                    r"(?i)(conferred|awarded|completed|certifies?).*?(degree|diploma)",  # Degree conferment pattern
                    r"(?i)(bachelor|master|doctor)\s+of",                               # Degree name pattern
                    r"(?i)(diploma|degree)"                                             # Basic diploma/degree pattern
                ],
                "score_threshold": 0.5
            },
            "employment_record": {
                "keywords": ["service record", "employment", "position", "instructor", "professor", "department", "tenure"],
                "required_patterns": [
                    r"(?i)(position|status).*?(instructor|professor|faculty)",  # Position pattern
                    r"(?i)(employment|service).*?(record|history|details)"      # Employment record pattern
                ],
                "score_threshold": 0.7
            },
            "certification_letter": {
                "keywords": ["certification", "earned units", "completed units", "this is to certify"],
                "required_patterns": [
                    r"(?i)this\s+is\s+to\s+certify",           # Certification statement pattern
                    r"(?i)(earned|completed|total).*?units?"    # Units earned pattern
                ],
                "score_threshold": 0.6
            },
            "authenticated_copy": {
                "keywords": ["certified true copy", "authenticated copy", "verified", "attested", "authenticated copies", "ctc"],
                "required_patterns": [
                    r"(?i)(certified\s+true|authenticated).*?(cop(y|ies))",  # Authentication statement pattern
                    r"(?i)verified.*?(against|with).*?original",    # Verification statement pattern
                    r"(?i)(ctc|certified true copy).*?(diploma|transcript|document|credentials?)"      # CTC specific pattern
                ],
                "score_threshold": 0.6
            }
        }

    def _calculate_document_score(self, text_lower, doc_type):
        """Calculate a weighted score for document classification"""
        patterns = self.document_patterns.get(doc_type, {})
        if not patterns:
            return 0.0
        
        score = 0.0
        total_keywords = len(patterns["keywords"])
        total_patterns = len(patterns["required_patterns"])
        
        # Check keywords (40% weight)
        for keyword in patterns["keywords"]:
            if keyword in text_lower:
                score += 0.4 / total_keywords
        
        # Check required patterns (60% weight)
        for pattern in patterns["required_patterns"]:
            if re.search(pattern, text_lower):
                score += 0.6 / total_patterns
        
        return score

    def classify(self, text):
        """Classify the document using zero-shot classification and pattern matching"""
        if not text.strip():
            return ["unknown"]
            
        try:
            text_lower = text.lower()
            
            # Skip short texts
            if len(text.split()) < 20:
                return ["unknown"]
            
            # Calculate scores for each document type
            scores = {}
            for doc_type in self.document_patterns.keys():
                score = self._calculate_document_score(text_lower, doc_type)
                threshold = self.document_patterns[doc_type]["score_threshold"]
                if score >= threshold:
                    scores[doc_type] = score

            # No matches found
            if not scores:
                return ["unknown"]

            # Sort scores by value in descending order
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            
            # Initialize classifications list
            classifications = []
            
            # Add authenticated_copy first if present
            if "authenticated_copy" in scores:
                classifications.append("authenticated_copy")
            
            # Add other high-scoring classifications
            # For academic documents, check specific patterns
            if any(term in text_lower for term in ["academic credentials", "academic records", "scholastic record"]):
                if any(pattern in text_lower for pattern in ["grade", "units", "course", "subject"]):
                    classifications.append("academic_transcript")
                elif any(pattern in text_lower for pattern in ["degree", "diploma", "bachelor", "master"]):
                    classifications.append("academic_certificate")
            else:
                # Add the highest scoring non-authentication classification
                for doc_type, score in sorted_scores:
                    if doc_type != "authenticated_copy" and score >= self.document_patterns[doc_type]["score_threshold"]:
                        if doc_type not in classifications:
                            classifications.append(doc_type)
                        break

            return classifications if classifications else ["unknown"]
            
        except Exception as e:
            print(f"Classification error: {str(e)}")
            return ["unknown"]