"""
Utility functions for Food Trend Predictor
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/food_trends.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def setup_logging(log_file='logs/food_trends.log'):
    """Set up logging configuration"""
    Path('logs').mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def save_json(data, filepath):
    """Save data to JSON file"""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    logger.info(f"Saved data to {filepath}")

def load_json(filepath):
    """Load data from JSON file"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    logger.info(f"Loaded data from {filepath}")
    return data

def calculate_growth_rate(current_count, previous_count):
    """Calculate growth rate between two periods"""
    if previous_count == 0:
        return 1.0 if current_count > 0 else 0.0
    return (current_count - previous_count) / previous_count

def calculate_velocity(mentions, days):
    """Calculate mentions per day"""
    if days == 0:
        return 0
    return mentions / days

def normalize_food_name(food_name):
    """Normalize food name for consistency"""
    return food_name.lower().strip()

def get_date_range(days_back):
    """Get date range for queries"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    return start_date, end_date

def format_percentage(value, decimals=1):
    """Format value as percentage"""
    return f"{value * 100:.{decimals}f}%"

def format_number(value, decimals=0):
    """Format number with commas"""
    if decimals == 0:
        return f"{int(value):,}"
    return f"{value:,.{decimals}f}"

def calculate_engagement_score(score, comments, upvote_ratio=None):
    """Calculate total engagement score"""
    engagement = score * 1.0 + comments * 2.0
    if upvote_ratio is not None:
        engagement += upvote_ratio * 100
    return engagement

def get_trend_emoji(probability):
    """Get emoji based on trend probability"""
    if probability >= 0.8:
        return "🔥"
    elif probability >= 0.6:
        return "📈"
    elif probability >= 0.4:
        return "📊"
    else:
        return "📉"

def get_recommendation_level(probability):
    """Get recommendation level based on probability"""
    if probability >= 0.8:
        return "HIGH"
    elif probability >= 0.6:
        return "MEDIUM"
    elif probability >= 0.4:
        return "LOW"
    else:
        return "MINIMAL"

def batch_process(items, batch_size=100):
    """Process items in batches"""
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]

def safe_divide(numerator, denominator, default=0):
    """Safely divide with default value for zero denominator"""
    if denominator == 0:
        return default
    return numerator / denominator

def deduplicate_posts(posts_df):
    """Remove duplicate posts based on post_id"""
    before_count = len(posts_df)
    posts_df = posts_df.drop_duplicates(subset=['post_id'], keep='first')
    after_count = len(posts_df)
    
    if before_count > after_count:
        logger.info(f"Removed {before_count - after_count} duplicate posts")
    
    return posts_df

def filter_by_date_range(df, start_date, end_date, date_column='created_utc'):
    """Filter dataframe by date range"""
    df[date_column] = pd.to_datetime(df[date_column])
    mask = (df[date_column] >= start_date) & (df[date_column] <= end_date)
    return df[mask]

def get_top_n(df, column, n=10, ascending=False):
    """Get top N rows by column value"""
    return df.nlargest(n, column) if not ascending else df.nsmallest(n, column)

def create_time_buckets(df, date_column='created_utc', freq='D'):
    """Create time buckets for aggregation"""
    df[date_column] = pd.to_datetime(df[date_column])
    df['time_bucket'] = df[date_column].dt.to_period(freq)
    return df

def calculate_percentile(value, series):
    """Calculate percentile of value in series"""
    return (series < value).sum() / len(series)

def moving_average(series, window=7):
    """Calculate moving average"""
    return series.rolling(window=window, min_periods=1).mean()

def exponential_moving_average(series, alpha=0.3):
    """Calculate exponential moving average"""
    return series.ewm(alpha=alpha, adjust=False).mean()

def detect_outliers(series, threshold=3):
    """Detect outliers using z-score method"""
    z_scores = np.abs((series - series.mean()) / series.std())
    return z_scores > threshold

def summarize_dataframe(df):
    """Print summary statistics of dataframe"""
    logger.info(f"DataFrame shape: {df.shape}")
    logger.info(f"Columns: {', '.join(df.columns)}")
    logger.info(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    logger.info(f"Missing values:\n{df.isnull().sum()}")

def export_to_csv(df, filename, index=False):
    """Export dataframe to CSV"""
    Path('data').mkdir(exist_ok=True)
    filepath = f"data/{filename}"
    df.to_csv(filepath, index=index)
    logger.info(f"Exported to {filepath}")

def create_feature_importance_plot(feature_importance_df, top_n=20):
    """Create feature importance data for plotting"""
    top_features = feature_importance_df.head(top_n)
    return {
        'features': top_features['feature'].tolist(),
        'importance': top_features['importance'].tolist()
    }

def validate_data_quality(df, required_columns):
    """Validate data quality"""
    issues = []
    
    # Check required columns
    missing_cols = set(required_columns) - set(df.columns)
    if missing_cols:
        issues.append(f"Missing columns: {missing_cols}")
    
    # Check for nulls
    null_counts = df[required_columns].isnull().sum()
    high_null_cols = null_counts[null_counts > len(df) * 0.5].index.tolist()
    if high_null_cols:
        issues.append(f"High null percentage (>50%) in: {high_null_cols}")
    
    # Check for duplicates
    if df.duplicated().any():
        issues.append(f"Found {df.duplicated().sum()} duplicate rows")
    
    if issues:
        logger.warning(f"Data quality issues: {'; '.join(issues)}")
        return False, issues
    
    logger.info("Data quality validation passed")
    return True, []

def format_timestamp(timestamp):
    """Format timestamp for display"""
    if isinstance(timestamp, str):
        timestamp = pd.to_datetime(timestamp)
    return timestamp.strftime('%Y-%m-%d %H:%M:%S')

def get_system_info():
    """Get system information"""
    import platform
    import psutil
    
    return {
        'platform': platform.system(),
        'python_version': platform.python_version(),
        'cpu_count': psutil.cpu_count(),
        'memory_gb': psutil.virtual_memory().total / (1024**3),
        'disk_usage_percent': psutil.disk_usage('/').percent
    }

def estimate_processing_time(num_items, items_per_second=10):
    """Estimate processing time"""
    seconds = num_items / items_per_second
    
    if seconds < 60:
        return f"{seconds:.0f} seconds"
    elif seconds < 3600:
        return f"{seconds/60:.0f} minutes"
    else:
        return f"{seconds/3600:.1f} hours"

# Food-specific utilities

FOOD_EMOJIS = {
    'pizza': '🍕', 'burger': '🍔', 'sushi': '🍣', 'ramen': '🍜',
    'tacos': '🌮', 'pasta': '🍝', 'salad': '🥗', 'cake': '🍰',
    'ice cream': '🍦', 'coffee': '☕', 'tea': '🍵', 'smoothie': '🥤',
    'avocado': '🥑', 'bacon': '🥓', 'egg': '🥚', 'bread': '🍞',
    'croissant': '🥐', 'bagel': '🥯', 'pancakes': '🥞', 'waffle': '🧇',
}

def get_food_emoji(food_name):
    """Get emoji for food item"""
    return FOOD_EMOJIS.get(food_name.lower(), '🍴')

def categorize_food(food_name):
    """Categorize food item"""
    from config import FOOD_CATEGORIES
    
    food_lower = food_name.lower()
    for category, foods in FOOD_CATEGORIES.items():
        if food_lower in foods:
            return category
    return 'Other'

def get_seasonal_foods(month):
    """Get typical seasonal foods for a month"""
    seasonal = {
        1: ['soup', 'stew', 'hot chocolate'],  # Winter
        2: ['soup', 'stew', 'hot chocolate'],
        3: ['salad', 'smoothie'],  # Spring
        4: ['salad', 'smoothie'],
        5: ['salad', 'smoothie'],
        6: ['ice cream', 'popsicle', 'bbq'],  # Summer
        7: ['ice cream', 'popsicle', 'bbq'],
        8: ['ice cream', 'popsicle', 'bbq'],
        9: ['pumpkin', 'apple pie'],  # Fall
        10: ['pumpkin', 'apple pie'],
        11: ['turkey', 'stuffing'],
        12: ['cookies', 'gingerbread'],  # Winter
    }
    return seasonal.get(month, [])

if __name__ == "__main__":
    # Test utilities
    print("Testing Food Trend Predictor Utilities")
    print(f"Growth rate (100 -> 150): {calculate_growth_rate(150, 100):.2%}")
    print(f"Velocity (100 mentions / 7 days): {calculate_velocity(100, 7):.2f}")
    print(f"Engagement score: {calculate_engagement_score(100, 50, 0.9):.0f}")
    print(f"Pizza emoji: {get_food_emoji('pizza')}")
    print(f"System info: {get_system_info()}")
