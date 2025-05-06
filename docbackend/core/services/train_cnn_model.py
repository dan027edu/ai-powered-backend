import tensorflow as tf
from tensorflow.keras import layers, models, Model
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import numpy as np
import os
import docx2txt
import PyPDF2
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
import re
from tensorflow.keras.regularizers import l2
from .document_feature_extractor import DocumentFeatureExtractor

class DocumentCNNTrainer:
    def __init__(self, max_words=15000, max_length=2000):
        self.max_words = max_words
        self.max_length = max_length
        self.tokenizer = Tokenizer(num_words=max_words, oov_token='<OOV>')
        self.label_encoder = LabelEncoder()
        self.feature_extractor = DocumentFeatureExtractor()
        self.feature_scaler = StandardScaler()
        
    def _preprocess_text(self, text):
        """Enhanced text preprocessing"""
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s.,!?-]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\.+', '.', text)
        return text.strip()
        
    def _extract_text_from_docx(self, file_path):
        """Extract text from DOCX files with preprocessing"""
        try:
            text = docx2txt.process(file_path)
            return self._preprocess_text(text)
        except Exception as e:
            print(f"Error processing DOCX {file_path}: {str(e)}")
            return ""

    def _extract_text_from_pdf(self, file_path):
        """Extract text from PDF files with preprocessing"""
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
            
    def _augment_text(self, text):
        """Apply enhanced text augmentation techniques"""
        augmented_texts = [text]
        text_lower = text.lower()
        augmented_texts.append(text_lower)
        text_no_punct = re.sub(r'[^\w\s]', ' ', text)
        augmented_texts.append(text_no_punct)
        words = text.split()
        if len(words) > 10:
            for _ in range(2):
                remove_indices = np.random.choice(len(words), size=int(len(words) * 0.2), replace=False)
                noisy_text = ' '.join([w for i, w in enumerate(words) if i not in remove_indices])
                augmented_texts.append(noisy_text)
        sentences = [s for s in re.split(r'[.!?]+', text) if s.strip()]
        if len(sentences) > 2:
            for _ in range(2):
                shuffled = sentences.copy()
                np.random.shuffle(shuffled)
                shuffled_text = '. '.join(shuffled)
                augmented_texts.append(shuffled_text)
        return augmented_texts

    def prepare_data(self, docs_dir):
        """Prepare training data with enhanced features"""
        texts = []
        labels = []
        doc_features = []
        
        for filename in os.listdir(docs_dir):
            file_path = os.path.join(docs_dir, filename)
            
            if filename.lower().endswith('.docx'):
                text = self._extract_text_from_docx(file_path)
            elif filename.lower().endswith('.pdf'):
                text = self._extract_text_from_pdf(file_path)
            else:
                continue
                
            if not text:
                continue
            
            features = self.feature_extractor.extract_features(text, file_path)
            normalized_features = self.feature_extractor.normalize_features(features)
            feature_list = [v for k, v in sorted(normalized_features.items()) 
                          if isinstance(v, (int, float))]
            
            augmented_texts = self._augment_text(text)
            label = self._get_label_from_filename(filename)
            
            for aug_text in augmented_texts:
                texts.append(aug_text)
                labels.append(label)
                doc_features.append(feature_list)
        
        self.tokenizer.fit_on_texts(texts)
        sequences = self.tokenizer.texts_to_sequences(texts)
        X_text = pad_sequences(sequences, maxlen=self.max_length)
        
        X_features = np.array(doc_features)
        self.feature_scaler.fit(X_features)
        X_features = self.feature_scaler.transform(X_features)
        
        y = self.label_encoder.fit_transform(labels)
        
        return X_text, X_features, y
    
    def _get_label_from_filename(self, filename):
        """Extract document type label from filename"""
        filename = filename.lower()
        if 'academic' in filename or 'credentials' in filename:
            return 'academic_credentials'
        elif 'certification' in filename or 'earned-units' in filename:
            return 'certification'
        elif 'tor' in filename or 'transcript' in filename:
            return 'transcript'
        elif 'service' in filename:
            return 'service_record'
        elif 'diploma' in filename or 'ctc-diploma' in filename:
            return 'diploma'
        else:
            return 'other'
            
    def build_model(self, num_classes, feature_dim):
        """Build enhanced model architecture with document features"""
        text_input = layers.Input(shape=(self.max_length,), name='text_input')
        text_embedding = layers.Embedding(self.max_words, 128, input_length=self.max_length)(text_input)
        text_features = layers.SpatialDropout1D(0.2)(text_embedding)
        
        conv1 = layers.Conv1D(64, 3, padding='same', activation='relu', kernel_regularizer=l2(0.01))(text_features)
        pool1 = layers.MaxPooling1D(2)(conv1)
        conv2 = layers.Conv1D(128, 4, padding='same', activation='relu', kernel_regularizer=l2(0.01))(pool1)
        pool2 = layers.MaxPooling1D(2)(conv2)
        
        attention = layers.Dense(1, activation='tanh')(pool2)
        attention = layers.Flatten()(attention)
        attention = layers.Activation('softmax')(attention)
        attention = layers.RepeatVector(128)(attention)
        attention = layers.Permute([2, 1])(attention)
        
        merged = layers.Multiply()([pool2, attention])
        text_vector = layers.GlobalMaxPooling1D()(merged)
        
        feature_input = layers.Input(shape=(feature_dim,), name='feature_input')
        feature_dense = layers.Dense(64, activation='relu', kernel_regularizer=l2(0.01))(feature_input)
        feature_bn = layers.BatchNormalization()(feature_dense)
        
        combined = layers.Concatenate()([text_vector, feature_bn])
        
        dense1 = layers.Dense(128, activation='relu', kernel_regularizer=l2(0.01))(combined)
        bn1 = layers.BatchNormalization()(dense1)
        drop1 = layers.Dropout(0.3)(bn1)
        
        outputs = layers.Dense(num_classes, activation='softmax')(drop1)
        
        model = Model(inputs=[text_input, feature_input], outputs=outputs)
        
        optimizer = tf.keras.optimizers.Adam(learning_rate=0.001)
        model.compile(
            optimizer=optimizer,
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
        
    def train(self, docs_dir, epochs=100, batch_size=16, validation_split=0.2):
        """Train with document features and monitoring"""
        X_text, X_features, y = self.prepare_data(docs_dir)
        
        X_text_train, X_text_val, X_features_train, X_features_val, y_train, y_val = train_test_split(
            X_text, X_features, y, 
            test_size=validation_split, 
            random_state=42, 
            stratify=y
        )
        
        from sklearn.utils.class_weight import compute_class_weight
        classes = np.unique(y)
        class_weights = compute_class_weight(
            class_weight='balanced',
            classes=classes,
            y=y
        )
        class_weight_dict = dict(zip(classes, class_weights))
        
        num_classes = len(set(y))
        feature_dim = X_features.shape[1]
        model = self.build_model(num_classes, feature_dim)
        
        early_stopping = tf.keras.callbacks.EarlyStopping(
            monitor='val_accuracy',
            patience=15,
            restore_best_weights=True,
            mode='max'
        )
        
        reduce_lr = tf.keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.2,
            patience=5,
            min_lr=0.00001
        )
        
        history = model.fit(
            {'text_input': X_text_train, 'feature_input': X_features_train},
            y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=({'text_input': X_text_val, 'feature_input': X_features_val}, y_val),
            callbacks=[early_stopping, reduce_lr],
            class_weight=class_weight_dict,
            verbose=1
        )
        
        val_loss, val_acc = model.evaluate(
            {'text_input': X_text_val, 'feature_input': X_features_val},
            y_val,
            verbose=0
        )
        print(f"\nFinal validation accuracy: {val_acc:.2%}")
        print(f"Final validation loss: {val_loss:.4f}")
        
        from sklearn.metrics import classification_report
        y_pred = model.predict({'text_input': X_text_val, 'feature_input': X_features_val})
        y_pred_classes = np.argmax(y_pred, axis=1)
        print("\nClassification Report:")
        print(classification_report(
            y_val,
            y_pred_classes,
            target_names=self.label_encoder.classes_
        ))
        
        return model, history
        
    def save_model(self, model, model_path, tokenizer_path=None):
        """Save the trained model and preprocessing objects"""
        model.save(model_path.replace('.h5', '.keras'))
        
        if tokenizer_path:
            import pickle
            preprocessing_data = {
                'tokenizer': self.tokenizer,
                'label_encoder': self.label_encoder,
                'feature_scaler': self.feature_scaler
            }
            with open(tokenizer_path, 'wb') as f:
                pickle.dump(preprocessing_data, f)

if __name__ == "__main__":
    trainer = DocumentCNNTrainer()
    
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'test_docs')
    model, history = trainer.train(docs_dir, epochs=100, batch_size=16)
    
    model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'ml_models', 'weights')
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, 'cnn_model.h5')
    tokenizer_path = os.path.join(model_dir, 'preprocessing.pkl')
    
    trainer.save_model(model, model_path, tokenizer_path)
    print(f"\nModel saved to: {model_path}")
    print(f"Preprocessing objects saved to: {tokenizer_path}")