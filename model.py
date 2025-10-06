import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_score, recall_score, f1_score
import xgboost as xgb
from transformers import AutoTokenizer, AutoModel
import torch
from torch.utils.data import DataLoader, Dataset
import pickle
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from data_processor import FoodDataProcessor
import json

load_dotenv()

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

class TextDataset(Dataset):
    """PyTorch dataset for text data"""
    def __init__(self, texts, tokenizer, max_length=128):
        self.texts = texts
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = str(self.texts[idx])
        encoding = self.tokenizer(
            text,
            add_special_tokens=True,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten()
        }

class FoodTrendPredictor:
    """BERT + XGBoost model for predicting food trends"""
    
    def __init__(self, model_name='distilbert-base-uncased'):
        self.model_name = model_name
        self.tokenizer = None
        self.bert_model = None
        self.xgb_model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Using device: {self.device}")
        
    def initialize_bert(self):
        """Initialize BERT model and tokenizer"""
        print(f"Loading BERT model: {self.model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.bert_model = AutoModel.from_pretrained(self.model_name)
        self.bert_model.to(self.device)
        self.bert_model.eval()
        print("✅ BERT model loaded")
    
    def extract_bert_embeddings(self, texts, batch_size=16):
        """Extract BERT embeddings for texts"""
        if self.bert_model is None:
            self.initialize_bert()
        
        dataset = TextDataset(texts, self.tokenizer)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
        
        embeddings = []
        
        print(f"Extracting BERT embeddings for {len(texts)} texts...")
        with torch.no_grad():
            for batch_idx, batch in enumerate(dataloader):
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                
                outputs = self.bert_model(
                    input_ids=input_ids,
                    attention_mask=attention_mask
                )
                
                # Use [CLS] token embedding (first token)
                cls_embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
                embeddings.append(cls_embeddings)
                
                if (batch_idx + 1) % 10 == 0:
                    print(f"  Processed {(batch_idx + 1) * batch_size}/{len(texts)} texts")
        
        embeddings = np.vstack(embeddings)
        print(f"✅ Extracted embeddings shape: {embeddings.shape}")
        return embeddings
    
    def train(self, X_structured, X_text, y, test_size=0.2, random_state=42):
        """Train the hybrid BERT + XGBoost model"""
        print("\n🚀 Starting model training...")
        
        # Extract BERT embeddings
        text_embeddings = self.extract_bert_embeddings(X_text)
        
        # Combine structured features with text embeddings
        X_combined = np.hstack([X_structured.values, text_embeddings])
        print(f"Combined feature shape: {X_combined.shape}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_combined, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        print(f"Training set: {X_train.shape}, Test set: {X_test.shape}")
        
        # Train XGBoost
        print("\nTraining XGBoost classifier...")
        self.xgb_model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            objective='binary:logistic',
            eval_metric='logloss',
            random_state=random_state,
            use_label_encoder=False
        )
        
        self.xgb_model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False
        )
        
        # Evaluate
        y_pred = self.xgb_model.predict(X_test)
        y_pred_proba = self.xgb_model.predict_proba(X_test)[:, 1]
        
        print("\n📊 Model Evaluation:")
        print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
        print(f"Precision: {precision_score(y_test, y_pred):.4f}")
        print(f"Recall: {recall_score(y_test, y_pred):.4f}")
        print(f"F1 Score: {f1_score(y_test, y_pred):.4f}")
        
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred, target_names=['Not Trending', 'Trending']))
        
        print("\nConfusion Matrix:")
        print(confusion_matrix(y_test, y_pred))
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': [f'structured_{i}' for i in range(X_structured.shape[1])] + 
                      [f'bert_{i}' for i in range(text_embeddings.shape[1])],
            'importance': self.xgb_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\n🔝 Top 10 Important Features:")
        print(feature_importance.head(10))
        
        return {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1': f1_score(y_test, y_pred),
            'feature_importance': feature_importance
        }
    
    def predict(self, X_structured, X_text):
        """Predict trend probability for new data"""
        if self.xgb_model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Extract BERT embeddings
        text_embeddings = self.extract_bert_embeddings(X_text)
        
        # Combine features
        X_combined = np.hstack([X_structured.values, text_embeddings])
        
        # Predict
        predictions = self.xgb_model.predict(X_combined)
        probabilities = self.xgb_model.predict_proba(X_combined)[:, 1]
        
        return predictions, probabilities
    
    def save_model(self, path='models'):
        """Save the trained model"""
        os.makedirs(path, exist_ok=True)
        
        # Save XGBoost model
        xgb_path = os.path.join(path, 'xgboost_model.pkl')
        with open(xgb_path, 'wb') as f:
            pickle.dump(self.xgb_model, f)
        
        # Save model metadata
        metadata = {
            'bert_model_name': self.model_name,
            'timestamp': pd.Timestamp.now().isoformat()
        }
        
        metadata_path = os.path.join(path, 'model_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Model saved to {path}")
    
    def load_model(self, path='models'):
        """Load a trained model"""
        # Load XGBoost model
        xgb_path = os.path.join(path, 'xgboost_model.pkl')
        with open(xgb_path, 'rb') as f:
            self.xgb_model = pickle.load(f)
        
        # Load metadata
        metadata_path = os.path.join(path, 'model_metadata.json')
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        self.model_name = metadata['bert_model_name']
        self.initialize_bert()
        
        print(f"✅ Model loaded from {path}")

def train_pipeline():
    """Complete training pipeline"""
    print("="*60)
    print("🎯 Food Trend Predictor - Training Pipeline")
    print("="*60)
    
    # 1. Process data
    processor = FoodDataProcessor()
    X, y, feature_columns, metrics_df = processor.process_pipeline(days_back=90)
    
    if X is None:
        print("❌ No data available for training")
        return
    
    # 2. Get text data for BERT
    # Fetch original posts for food items
    food_texts = []
    for food in metrics_df['food'].unique():
        # Get sample post text for this food
        result = supabase.table('reddit_posts')\
            .select('title, cleaned_text')\
            .contains('food_mentions', [food])\
            .limit(1)\
            .execute()
        
        if result.data:
            text = f"{result.data[0].get('title', '')} {result.data[0].get('cleaned_text', '')}"
            food_texts.append(text)
        else:
            food_texts.append(food)  # Use food name as fallback
    
    # 3. Train model
    predictor = FoodTrendPredictor()
    metrics = predictor.train(X, food_texts, y)
    
    # 4. Save model
    predictor.save_model()
    
    # 5. Store predictions in database
    predictions, probabilities = predictor.predict(X, food_texts)
    
    # Update metrics with predictions
    metrics_df['predicted_trending'] = predictions
    metrics_df['trend_probability'] = probabilities
    
    # Store in Supabase
    print("\n💾 Storing predictions in database...")
    prediction_records = metrics_df[['food', 'trending_score', 'is_trending', 
                                      'predicted_trending', 'trend_probability', 
                                      'velocity', 'growth_rate']].to_dict('records')
    
    try:
        supabase.table('food_predictions').upsert(prediction_records).execute()
        print(f"✅ Stored {len(prediction_records)} predictions")
    except Exception as e:
        print(f"⚠️  Error storing predictions: {e}")
    
    print("\n" + "="*60)
    print("🎉 Training pipeline complete!")
    print("="*60)
    
    return predictor, metrics

if __name__ == "__main__":
    predictor, metrics = train_pipeline()
    
    if metrics is not None:
        print("\n🔥 Top 10 Predicted Trending Foods:")
        top_predictions = metrics.nlargest(10, 'trend_probability')[
            ['food', 'trend_probability', 'is_trending', 'trending_score']
        ]
        print(top_predictions)
