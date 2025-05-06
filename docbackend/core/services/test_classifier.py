import os
from cnn_classifier import DocumentClassifier

def test_classifier():
    # Initialize classifier
    classifier = DocumentClassifier()
    
    # Get path to test documents
    test_docs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'test_docs')
    
    print("Testing document classification...")
    print("-" * 50)
    
    # Test each document
    for filename in os.listdir(test_docs_dir):
        file_path = os.path.join(test_docs_dir, filename)
        
        # Get classification
        prediction = classifier.classify_file(file_path)
        
        print(f"\nDocument: {filename}")
        print(f"Prediction: {prediction}")
        
        # Get detailed scores for analysis
        text = ""
        if file_path.lower().endswith('.docx'):
            text = classifier._extract_text_from_docx(file_path)
        elif file_path.lower().endswith('.pdf'):
            text = classifier._extract_text_from_pdf(file_path)
            
        if text:
            result = classifier.classifier(
                text, 
                classifier.candidate_labels,
                hypothesis_template=classifier.hypothesis_template
            )
            print("\nDetailed scores:")
            for label, score in sorted(zip(result['labels'], result['scores']), key=lambda x: x[1], reverse=True):
                print(f"{label}: {score:.3f}")

if __name__ == "__main__":
    test_classifier()