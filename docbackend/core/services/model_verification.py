import tensorflow as tf
import os
import numpy as np
import argparse

def get_project_root():
    """Get absolute path to project root"""
    current_file = os.path.abspath(__file__)
    # Go up 3 levels: services -> core -> docbackend
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    return project_root

def verify_model(model_path=None, model_type=None):
    project_root = get_project_root()
    
    if model_path is None:
        if model_type == 'ocr':
            model_path = os.path.join(project_root, 'ml_models', 'weights', 'ocr_model.h5')
        else:
            model_path = os.path.join(project_root, 'ml_models', 'weights', 'cnn_model.h5')
    
    # Verify file exists
    if not os.path.exists(model_path):
        print(f"Error: Model file not found at {model_path}")
        return False
    
    print(f"\nVerifying {os.path.basename(model_path)}...")
    
    # Check file size
    file_size = os.path.getsize(model_path) / (1024 * 1024)  # Convert to MB
    print(f"\nModel file size: {file_size:.2f} MB")
    
    try:
        # Load and analyze model
        model = tf.keras.models.load_model(model_path)
        
        # Print model summary
        print("\nModel Architecture:")
        model.summary()
        
        # Calculate memory requirements
        trainable_params = np.sum([np.prod(v.get_shape()) for v in model.trainable_weights])
        non_trainable_params = np.sum([np.prod(v.get_shape()) for v in model.non_trainable_weights])
        
        print(f"\nTrainable parameters: {trainable_params:,}")
        print(f"Non-trainable parameters: {non_trainable_params:,}")
        
        # Estimate memory usage (rough estimate)
        param_size = (trainable_params + non_trainable_params) * 4  # 4 bytes per float32
        memory_mb = param_size / (1024 * 1024)  # Convert to MB
        print(f"Approximate memory usage: {memory_mb:.2f} MB")
        
        return True
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Verify a TensorFlow model')
    parser.add_argument('--model-path', type=str, help='Path to the model file (optional)')
    parser.add_argument('--model-type', type=str, choices=['cnn', 'ocr'], 
                        default='cnn', help='Type of model to verify (default: cnn)')
    args = parser.parse_args()
    
    print("Starting model verification...")
    success = verify_model(args.model_path, args.model_type)
    if success:
        print("\nModel verification completed successfully!")
    else:
        print("\nModel verification failed!")
        exit(1)