import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv
import os
from sklearn.preprocessing import StandardScaler
import re

load_dotenv()

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

class FoodDataProcessor:
    """Process and transform raw Reddit data for ML models"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        
    def fetch_data(self, days_back=90, min_score=5):
        """Fetch data from Supabase"""
        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        try:
            result = supabase.table('reddit_posts')\
                .select('*')\
                .gte('created_utc', cutoff_date)\
                .gte('score', min_score)\
                .execute()
            
            df = pd.DataFrame(result.data)
            print(f"✅ Fetched {len(df)} posts from database")
            return df
        except Exception as e:
            print(f"Error fetching data: {e}")
            return pd.DataFrame()
    
    def calculate_engagement_score(self, df):
        """Calculate engagement score for each post"""
        df['engagement_score'] = (
            df['score'] * 1.0 + 
            df['num_comments'] * 2.0 + 
            df['upvote_ratio'] * 100
        )
        return df
    
    def extract_temporal_features(self, df):
        """Extract time-based features"""
        df['created_utc'] = pd.to_datetime(df['created_utc'])
        df['day_of_week'] = df['created_utc'].dt.dayofweek
        df['hour'] = df['created_utc'].dt.hour
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        df['month'] = df['created_utc'].dt.month
        return df
    
    def calculate_velocity(self, df):
        """Calculate trend velocity (how fast something is growing)"""
        df = df.sort_values('created_utc')
        
        # Calculate 7-day rolling average
        df['days_since_start'] = (df['created_utc'] - df['created_utc'].min()).dt.days
        
        return df
    
    def create_food_dataset(self, df):
        """Create a dataset with one row per food item per time period"""
        food_records = []
        
        for _, row in df.iterrows():
            if not row.get('food_mentions'):
                continue
                
            for food in row['food_mentions']:
                food_records.append({
                    'food': food,
                    'post_id': row['post_id'],
                    'subreddit': row['subreddit'],
                    'score': row['score'],
                    'num_comments': row['num_comments'],
                    'upvote_ratio': row['upvote_ratio'],
                    'engagement_score': row.get('engagement_score', 0),
                    'created_utc': row['created_utc'],
                    'day_of_week': row.get('day_of_week', 0),
                    'hour': row.get('hour', 0),
                    'is_weekend': row.get('is_weekend', 0),
                    'month': row.get('month', 0),
                    'text': row.get('cleaned_text', ''),
                    'title': row.get('title', '')
                })
        
        food_df = pd.DataFrame(food_records)
        print(f"✅ Created food dataset with {len(food_df)} food mentions")
        return food_df
    
    def aggregate_food_metrics(self, food_df, window_days=7):
        """Aggregate metrics for each food item"""
        food_df = food_df.sort_values('created_utc')
        
        # Group by food and calculate metrics
        food_metrics = []
        
        for food in food_df['food'].unique():
            food_subset = food_df[food_df['food'] == food].copy()
            
            if len(food_subset) < 5:  # Skip foods with very few mentions
                continue
            
            # Calculate metrics for different time windows
            now = food_subset['created_utc'].max()
            
            for days in [7, 14, 30]:
                cutoff = now - timedelta(days=days)
                recent = food_subset[food_subset['created_utc'] >= cutoff]
                older = food_subset[food_subset['created_utc'] < cutoff]
                
                if len(recent) == 0:
                    continue
                
                metrics = {
                    'food': food,
                    'window_days': days,
                    'mention_count': len(recent),
                    'avg_score': recent['score'].mean(),
                    'max_score': recent['score'].max(),
                    'avg_comments': recent['num_comments'].mean(),
                    'avg_engagement': recent['engagement_score'].mean(),
                    'unique_subreddits': recent['subreddit'].nunique(),
                    'weekend_ratio': recent['is_weekend'].mean(),
                    'velocity': len(recent) / days,  # Mentions per day
                    'growth_rate': (len(recent) - len(older)) / max(len(older), 1) if len(older) > 0 else 1.0,
                    'avg_upvote_ratio': recent['upvote_ratio'].mean(),
                    'total_engagement': recent['engagement_score'].sum(),
                    'timestamp': now
                }
                
                food_metrics.append(metrics)
        
        metrics_df = pd.DataFrame(food_metrics)
        print(f"✅ Aggregated metrics for {metrics_df['food'].nunique()} unique foods")
        return metrics_df
    
    def create_trend_labels(self, metrics_df):
        """Create labels for trending vs non-trending foods"""
        # Define trending based on multiple criteria
        metrics_df = metrics_df[metrics_df['window_days'] == 7].copy()
        
        # Calculate percentiles
        metrics_df['velocity_percentile'] = metrics_df['velocity'].rank(pct=True)
        metrics_df['growth_percentile'] = metrics_df['growth_rate'].rank(pct=True)
        metrics_df['engagement_percentile'] = metrics_df['avg_engagement'].rank(pct=True)
        
        # Combined trending score
        metrics_df['trending_score'] = (
            metrics_df['velocity_percentile'] * 0.3 +
            metrics_df['growth_percentile'] * 0.4 +
            metrics_df['engagement_percentile'] * 0.3
        )
        
        # Label top 20% as trending
        threshold = metrics_df['trending_score'].quantile(0.80)
        metrics_df['is_trending'] = (metrics_df['trending_score'] >= threshold).astype(int)
        
        print(f"✅ Created labels: {metrics_df['is_trending'].sum()} trending, {len(metrics_df) - metrics_df['is_trending'].sum()} non-trending")
        return metrics_df
    
    def prepare_features(self, metrics_df):
        """Prepare feature matrix for ML models"""
        feature_columns = [
            'mention_count', 'avg_score', 'max_score', 'avg_comments',
            'avg_engagement', 'unique_subreddits', 'weekend_ratio',
            'velocity', 'growth_rate', 'avg_upvote_ratio', 'total_engagement'
        ]
        
        X = metrics_df[feature_columns].copy()
        y = metrics_df['is_trending'].copy()
        
        # Handle any missing values
        X = X.fillna(0)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        X_scaled_df = pd.DataFrame(X_scaled, columns=feature_columns, index=X.index)
        
        return X_scaled_df, y, feature_columns
    
    def process_pipeline(self, days_back=90, min_score=5):
        """Run the complete data processing pipeline"""
        print("\n🚀 Starting data processing pipeline...")
        
        # 1. Fetch data
        df = self.fetch_data(days_back, min_score)
        if df.empty:
            print("❌ No data to process")
            return None, None, None, None
        
        # 2. Calculate engagement scores
        df = self.calculate_engagement_score(df)
        
        # 3. Extract temporal features
        df = self.extract_temporal_features(df)
        
        # 4. Calculate velocity
        df = self.calculate_velocity(df)
        
        # 5. Create food-level dataset
        food_df = self.create_food_dataset(df)
        
        # 6. Aggregate metrics
        metrics_df = self.aggregate_food_metrics(food_df)
        
        # 7. Create labels
        metrics_df = self.create_trend_labels(metrics_df)
        
        # 8. Prepare features
        X, y, feature_columns = self.prepare_features(metrics_df)
        
        print(f"\n✅ Pipeline complete!")
        print(f"   Dataset shape: {X.shape}")
        print(f"   Features: {len(feature_columns)}")
        print(f"   Positive class ratio: {y.mean():.2%}")
        
        return X, y, feature_columns, metrics_df

if __name__ == "__main__":
    processor = FoodDataProcessor()
    X, y, features, metrics = processor.process_pipeline(days_back=90)
    
    if X is not None:
        print("\n📊 Sample of processed data:")
        print(metrics.head(10))
        
        print("\n🔥 Top trending foods:")
        top_trending = metrics.nlargest(10, 'trending_score')[['food', 'trending_score', 'velocity', 'growth_rate', 'is_trending']]
        print(top_trending)
