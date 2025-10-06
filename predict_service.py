"""
Real-time prediction service for food trends
Loads the trained model and provides predictions on demand
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv
import os
from model import FoodTrendPredictor
from data_processor import FoodDataProcessor
import json

load_dotenv()

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

class TrendPredictionService:
    """Service for real-time food trend predictions"""
    
    def __init__(self, model_path='models'):
        self.predictor = FoodTrendPredictor()
        self.processor = FoodDataProcessor()
        self.model_path = model_path
        
        # Load model if exists
        if os.path.exists(os.path.join(model_path, 'xgboost_model.pkl')):
            self.predictor.load_model(model_path)
            print("✅ Model loaded successfully")
        else:
            print("⚠️  No trained model found. Run training first: python model.py")
    
    def get_latest_predictions(self, top_n=20):
        """Get latest predictions from database"""
        try:
            result = supabase.table('food_predictions')\
                .select('*')\
                .order('trend_probability', desc=True)\
                .limit(top_n)\
                .execute()
            
            return pd.DataFrame(result.data)
        except Exception as e:
            print(f"Error fetching predictions: {e}")
            return pd.DataFrame()
    
    def predict_new_food(self, food_name, days_back=30):
        """Predict trending probability for a specific food"""
        try:
            # Fetch posts mentioning this food
            cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            
            result = supabase.table('reddit_posts')\
                .select('*')\
                .contains('food_mentions', [food_name.lower()])\
                .gte('created_utc', cutoff_date)\
                .execute()
            
            if not result.data:
                return {
                    'food': food_name,
                    'status': 'no_data',
                    'message': f'No posts found mentioning {food_name} in the last {days_back} days'
                }
            
            df = pd.DataFrame(result.data)
            
            # Calculate metrics
            metrics = {
                'mention_count': len(df),
                'avg_score': df['score'].mean(),
                'max_score': df['score'].max(),
                'avg_comments': df['num_comments'].mean(),
                'avg_engagement': (df['score'] + df['num_comments'] * 2).mean(),
                'unique_subreddits': df['subreddit'].nunique(),
                'weekend_ratio': 0.5,  # Placeholder
                'velocity': len(df) / days_back,
                'growth_rate': 0.1,  # Placeholder
                'avg_upvote_ratio': df['upvote_ratio'].mean(),
                'total_engagement': (df['score'].sum() + df['num_comments'].sum() * 2)
            }
            
            # Prepare for prediction
            X = pd.DataFrame([metrics])
            X = self.processor.scaler.transform(X)
            
            # Get text sample
            text_sample = f"{df.iloc[0]['title']} {df.iloc[0].get('cleaned_text', '')}"
            
            # Predict
            predictions, probabilities = self.predictor.predict(
                pd.DataFrame(X), 
                [text_sample]
            )
            
            return {
                'food': food_name,
                'status': 'success',
                'trend_probability': float(probabilities[0]),
                'is_trending': bool(predictions[0]),
                'metrics': metrics,
                'recommendation': self._get_recommendation(probabilities[0])
            }
            
        except Exception as e:
            return {
                'food': food_name,
                'status': 'error',
                'message': str(e)
            }
    
    def _get_recommendation(self, probability):
        """Generate actionable recommendation based on trend probability"""
        if probability >= 0.8:
            return {
                'level': 'HIGH',
                'action': 'IMMEDIATE ACTION',
                'suggestions': [
                    'Consider adding to menu immediately',
                    'Stock up on ingredients',
                    'Create marketing campaign',
                    'Monitor competitor offerings'
                ]
            }
        elif probability >= 0.6:
            return {
                'level': 'MEDIUM',
                'action': 'MONITOR CLOSELY',
                'suggestions': [
                    'Add to specials menu',
                    'Test with small batch',
                    'Gather customer feedback',
                    'Track social media mentions'
                ]
            }
        elif probability >= 0.4:
            return {
                'level': 'LOW',
                'action': 'WATCH LIST',
                'suggestions': [
                    'Keep on radar',
                    'Research similar trends',
                    'Consider for seasonal menu'
                ]
            }
        else:
            return {
                'level': 'MINIMAL',
                'action': 'NO ACTION NEEDED',
                'suggestions': [
                    'Standard monitoring only'
                ]
            }
    
    def get_category_trends(self):
        """Analyze trends by food category"""
        # Food categories
        categories = {
            'Asian': ['sushi', 'ramen', 'pho', 'kimchi', 'dumplings', 'pad thai', 'curry'],
            'Italian': ['pizza', 'pasta', 'tiramisu'],
            'American': ['burger', 'bbq', 'pancakes', 'waffles'],
            'Mexican': ['tacos', 'burrito', 'empanada'],
            'Desserts': ['cake', 'cookies', 'pie', 'ice cream', 'chocolate', 'churros'],
            'Healthy': ['salad', 'quinoa', 'kale', 'avocado', 'smoothie', 'poke'],
            'Plant-based': ['tofu', 'tempeh', 'seitan', 'hummus', 'falafel']
        }
        
        predictions = self.get_latest_predictions(top_n=100)
        
        if predictions.empty:
            return {}
        
        category_trends = {}
        
        for category, foods in categories.items():
            category_data = predictions[predictions['food'].isin(foods)]
            
            if not category_data.empty:
                category_trends[category] = {
                    'avg_probability': float(category_data['trend_probability'].mean()),
                    'trending_count': int((category_data['trend_probability'] > 0.7).sum()),
                    'top_food': category_data.nlargest(1, 'trend_probability')['food'].values[0],
                    'growth_momentum': float(category_data['growth_rate'].mean()) if 'growth_rate' in category_data else 0
                }
        
        return category_trends
    
    def generate_insights_report(self, days=7):
        """Generate a comprehensive insights report"""
        print(f"\n{'='*70}")
        print(f"🍕 FOOD TREND INSIGHTS REPORT - {datetime.now().strftime('%Y-%m-%d')}")
        print(f"{'='*70}\n")
        
        # Get predictions
        predictions = self.get_latest_predictions(top_n=50)
        
        if predictions.empty:
            print("❌ No predictions available")
            return
        
        # Top Trending
        print("🔥 TOP 10 TRENDING FOODS:")
        print("-" * 70)
        top_10 = predictions.head(10)
        for idx, row in top_10.iterrows():
            prob = row['trend_probability'] * 100
            trend_indicator = "📈" if row.get('growth_rate', 0) > 0.1 else "📊"
            print(f"{trend_indicator} {row['food'].title():20} | "
                  f"Probability: {prob:5.1f}% | "
                  f"Velocity: {row.get('velocity', 0):.2f}/day")
        
        # Category Analysis
        print(f"\n📊 CATEGORY TRENDS:")
        print("-" * 70)
        category_trends = self.get_category_trends()
        for category, data in sorted(category_trends.items(), 
                                     key=lambda x: x[1]['avg_probability'], 
                                     reverse=True):
            print(f"{category:15} | "
                  f"Avg: {data['avg_probability']*100:5.1f}% | "
                  f"Trending: {data['trending_count']:2} items | "
                  f"Top: {data['top_food'].title()}")
        
        # Actionable Insights
        print(f"\n💡 ACTIONABLE INSIGHTS:")
        print("-" * 70)
        
        high_potential = predictions[predictions['trend_probability'] > 0.7]
        if not high_potential.empty:
            print(f"✅ {len(high_potential)} foods with high trending potential")
            print(f"   Recommend immediate menu consideration for:")
            for food in high_potential.head(5)['food']:
                print(f"   • {food.title()}")
        
        emerging = predictions[
            (predictions['trend_probability'] > 0.5) & 
            (predictions['trend_probability'] <= 0.7)
        ]
        if not emerging.empty:
            print(f"\n⚡ {len(emerging)} emerging trends to monitor:")
            for food in emerging.head(5)['food']:
                print(f"   • {food.title()}")
        
        print(f"\n{'='*70}")
        print("Report generated successfully!")
        print(f"{'='*70}\n")

def main():
    """CLI interface for prediction service"""
    import sys
    
    service = TrendPredictionService()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "predict" and len(sys.argv) > 2:
            food_name = sys.argv[2]
            result = service.predict_new_food(food_name)
            print(json.dumps(result, indent=2))
        
        elif command == "report":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            service.generate_insights_report(days)
        
        elif command == "categories":
            trends = service.get_category_trends()
            print(json.dumps(trends, indent=2))
        
        else:
            print("Usage:")
            print("  python predict_service.py predict <food_name>  - Predict trend for specific food")
            print("  python predict_service.py report [days]        - Generate insights report")
            print("  python predict_service.py categories           - Get category trends")
    
    else:
        # Default: show report
        service.generate_insights_report()

if __name__ == "__main__":
    main()
