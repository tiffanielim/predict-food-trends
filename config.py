"""
Configuration settings for Food Trend Predictor
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Reddit Configuration
REDDIT_CONFIG = {
    'client_id': os.getenv('REDDIT_CLIENT_ID'),
    'client_secret': os.getenv('REDDIT_CLIENT_SECRET'),
    'user_agent': os.getenv('REDDIT_USER_AGENT', 'FoodTrendPredictor/1.0'),
}

# Supabase Configuration
SUPABASE_CONFIG = {
    'url': os.getenv('SUPABASE_URL'),
    'key': os.getenv('SUPABASE_KEY'),
}

# Food-related subreddits to monitor
FOOD_SUBREDDITS = [
    'food', 'cooking', 'recipes', 'AskCulinary', 'foodhacks',
    'EatCheapAndHealthy', 'FoodPorn', 'Baking', 'GifRecipes',
    'healthyfood', 'veganrecipes', 'vegetarian', 'ketorecipes',
    'MealPrepSunday', 'Cooking', 'Pizza', 'sushi', 'BBQ',
    'Coffee', 'tea', 'spicy', 'FoodNerds', 'AsianFood'
]

# ML Model Configuration
MODEL_CONFIG = {
    'bert_model': 'distilbert-base-uncased',
    'max_sequence_length': 128,
    'batch_size': 16,
    'test_size': 0.2,
    'random_state': 42,
}

# XGBoost Configuration
XGBOOST_CONFIG = {
    'n_estimators': 200,
    'max_depth': 6,
    'learning_rate': 0.1,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'objective': 'binary:logistic',
    'eval_metric': 'logloss',
}

# Data Collection Configuration
DATA_COLLECTION_CONFIG = {
    'target_posts': 100000,
    'posts_per_subreddit': 4500,
    'time_filter': 'month',  # 'hour', 'day', 'week', 'month', 'year', 'all'
    'min_score': 5,
    'batch_size': 100,
    'rate_limit_delay': 2,  # seconds between subreddit queries
}

# Feature Engineering Configuration
FEATURE_CONFIG = {
    'time_windows': [7, 14, 30],  # days
    'trending_threshold': 0.80,  # Top 20% as trending
    'min_mentions': 5,
    'velocity_weight': 0.3,
    'growth_weight': 0.4,
    'engagement_weight': 0.3,
}

# Dashboard Configuration
DASHBOARD_CONFIG = {
    'cache_ttl': 300,  # seconds (5 minutes)
    'default_days': 7,
    'min_mentions_filter': 5,
    'top_n_display': 20,
}

# Paths
PATHS = {
    'models': 'models',
    'data': 'data',
    'logs': 'logs',
}

# Food Categories for Analysis
FOOD_CATEGORIES = {
    'Asian': ['sushi', 'ramen', 'pho', 'kimchi', 'dumplings', 'pad thai', 
              'curry', 'bibimbap', 'banh mi', 'tikka', 'biryani'],
    'Italian': ['pizza', 'pasta', 'tiramisu', 'risotto', 'carbonara'],
    'American': ['burger', 'bbq', 'pancakes', 'waffles', 'bagel', 'hot dog'],
    'Mexican': ['tacos', 'burrito', 'empanada', 'quesadilla', 'nachos'],
    'Desserts': ['cake', 'cookies', 'pie', 'ice cream', 'chocolate', 
                 'churros', 'croissant', 'donut'],
    'Healthy': ['salad', 'quinoa', 'kale', 'avocado', 'smoothie', 'poke', 
                'açaí', 'brussels sprouts', 'broccoli'],
    'Plant-based': ['tofu', 'tempeh', 'seitan', 'hummus', 'falafel'],
    'Comfort': ['mac and cheese', 'fried chicken', 'mashed potatoes', 'soup', 'stew'],
    'Breakfast': ['pancakes', 'waffles', 'bagel', 'croissant', 'omelette', 'eggs'],
    'Beverages': ['coffee', 'tea', 'kombucha', 'matcha', 'smoothie'],
}

# Trend Analysis Thresholds
TREND_THRESHOLDS = {
    'high_probability': 0.8,
    'medium_probability': 0.6,
    'low_probability': 0.4,
    'min_velocity': 1.0,  # mentions per day
    'min_growth_rate': 0.1,
}

def validate_config():
    """Validate that all required configuration is present"""
    errors = []
    
    if not REDDIT_CONFIG['client_id']:
        errors.append("REDDIT_CLIENT_ID not set")
    if not REDDIT_CONFIG['client_secret']:
        errors.append("REDDIT_CLIENT_SECRET not set")
    if not SUPABASE_CONFIG['url']:
        errors.append("SUPABASE_URL not set")
    if not SUPABASE_CONFIG['key']:
        errors.append("SUPABASE_KEY not set")
    
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    return True

if __name__ == "__main__":
    try:
        validate_config()
        print("✅ Configuration valid")
        print(f"\nMonitoring {len(FOOD_SUBREDDITS)} subreddits:")
        for sub in FOOD_SUBREDDITS:
            print(f"  - r/{sub}")
    except ValueError as e:
        print(f"❌ {e}")
