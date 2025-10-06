import os
import praw
import time
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
import re
from collections import Counter

# Load environment variables
load_dotenv()

# Initialize Reddit client
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
)

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Food-related subreddits to monitor
FOOD_SUBREDDITS = [
    'food', 'cooking', 'recipes', 'AskCulinary', 'foodhacks',
    'EatCheapAndHealthy', 'FoodPorn', 'Baking', 'GifRecipes',
    'healthyfood', 'veganrecipes', 'vegetarian', 'ketorecipes',
    'MealPrepSunday', 'Cooking', 'Pizza', 'sushi', 'BBQ',
    'Coffee', 'tea', 'spicy', 'FoodNerds', 'AsianFood'
]

def clean_text(text):
    """Clean and normalize text data"""
    if not text:
        return ""
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?-]', '', text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text

def extract_food_mentions(text):
    """Extract potential food items from text"""
    # Common food keywords (simplified - could be expanded)
    food_keywords = [
        'pizza', 'pasta', 'burger', 'sushi', 'ramen', 'tacos', 'burrito',
        'sandwich', 'salad', 'soup', 'steak', 'chicken', 'beef', 'pork',
        'fish', 'salmon', 'tuna', 'shrimp', 'tofu', 'tempeh', 'seitan',
        'rice', 'noodles', 'bread', 'cake', 'cookies', 'pie', 'ice cream',
        'chocolate', 'cheese', 'egg', 'bacon', 'avocado', 'kimchi',
        'curry', 'biryani', 'dumplings', 'pho', 'banh mi', 'croissant',
        'bagel', 'pancakes', 'waffles', 'smoothie', 'kombucha', 'matcha',
        'açaí', 'quinoa', 'kale', 'cauliflower', 'broccoli', 'brussels sprouts',
        'hummus', 'falafel', 'shawarma', 'kebab', 'tikka', 'pad thai',
        'bibimbap', 'poke', 'ceviche', 'empanada', 'churros', 'tiramisu'
    ]
    
    text_lower = text.lower()
    found_foods = [food for food in food_keywords if food in text_lower]
    return list(set(found_foods))  # Remove duplicates

def fetch_reddit_posts(subreddit_name, limit=1000, time_filter='month'):
    """Fetch posts from a specific subreddit"""
    posts = []
    try:
        subreddit = reddit.subreddit(subreddit_name)
        
        # Fetch from multiple sources for diversity
        for submission in subreddit.top(time_filter=time_filter, limit=limit // 3):
            posts.append(submission)
        
        for submission in subreddit.hot(limit=limit // 3):
            posts.append(submission)
            
        for submission in subreddit.new(limit=limit // 3):
            posts.append(submission)
            
    except Exception as e:
        print(f"Error fetching from r/{subreddit_name}: {e}")
    
    return posts

def process_submission(submission, subreddit_name):
    """Process a single Reddit submission"""
    # Combine title and selftext for analysis
    full_text = f"{submission.title} {submission.selftext}"
    cleaned_text = clean_text(full_text)
    
    # Extract food mentions
    food_mentions = extract_food_mentions(cleaned_text)
    
    return {
        'post_id': submission.id,
        'subreddit': subreddit_name,
        'title': submission.title,
        'text': submission.selftext[:5000],  # Limit text length
        'cleaned_text': cleaned_text[:5000],
        'author': str(submission.author),
        'score': submission.score,
        'upvote_ratio': submission.upvote_ratio,
        'num_comments': submission.num_comments,
        'created_utc': datetime.fromtimestamp(submission.created_utc).isoformat(),
        'url': submission.url,
        'food_mentions': food_mentions,
        'collected_at': datetime.now().isoformat()
    }

def store_posts_in_supabase(posts):
    """Store processed posts in Supabase"""
    try:
        # Insert posts in batches
        batch_size = 100
        for i in range(0, len(posts), batch_size):
            batch = posts[i:i + batch_size]
            supabase.table('reddit_posts').upsert(batch).execute()
            print(f"Stored batch {i // batch_size + 1}: {len(batch)} posts")
            time.sleep(0.5)  # Rate limiting
        
        return True
    except Exception as e:
        print(f"Error storing posts in Supabase: {e}")
        return False

def collect_posts(target_posts=100000):
    """Main function to collect posts from all food subreddits"""
    all_posts = []
    posts_per_subreddit = target_posts // len(FOOD_SUBREDDITS)
    
    print(f"Starting data collection. Target: {target_posts} posts")
    print(f"Collecting ~{posts_per_subreddit} posts from each of {len(FOOD_SUBREDDITS)} subreddits")
    
    for idx, subreddit_name in enumerate(FOOD_SUBREDDITS, 1):
        print(f"\n[{idx}/{len(FOOD_SUBREDDITS)}] Fetching from r/{subreddit_name}...")
        
        try:
            submissions = fetch_reddit_posts(subreddit_name, limit=posts_per_subreddit)
            print(f"  Retrieved {len(submissions)} posts")
            
            # Process each submission
            for submission in submissions:
                post_data = process_submission(submission, subreddit_name)
                all_posts.append(post_data)
            
            # Store posts periodically to avoid memory issues
            if len(all_posts) >= 1000:
                print(f"\n  Storing {len(all_posts)} posts in database...")
                store_posts_in_supabase(all_posts)
                all_posts = []  # Clear memory
                
        except Exception as e:
            print(f"  Error processing r/{subreddit_name}: {e}")
            continue
        
        # Rate limiting
        time.sleep(2)
    
    # Store remaining posts
    if all_posts:
        print(f"\nStoring final {len(all_posts)} posts...")
        store_posts_in_supabase(all_posts)
    
    print("\n✅ Data collection complete!")
    
    # Get statistics
    try:
        result = supabase.table('reddit_posts').select('*', count='exact').execute()
        print(f"\nTotal posts in database: {result.count}")
    except Exception as e:
        print(f"Error getting statistics: {e}")

def get_trending_foods(days=7):
    """Analyze which foods are trending based on recent data"""
    try:
        # Query recent posts
        result = supabase.table('reddit_posts')\
            .select('food_mentions, score, num_comments')\
            .gte('created_utc', 
                 datetime.fromtimestamp(time.time() - days * 86400).isoformat())\
            .execute()
        
        # Count food mentions weighted by engagement
        food_scores = Counter()
        for post in result.data:
            if post.get('food_mentions'):
                weight = (post.get('score', 0) + post.get('num_comments', 0) * 2)
                for food in post['food_mentions']:
                    food_scores[food] += weight
        
        # Get top trending foods
        trending = food_scores.most_common(20)
        
        print(f"\n🔥 Top Trending Foods (Last {days} days):")
        for idx, (food, score) in enumerate(trending, 1):
            print(f"{idx}. {food.title()}: {score} engagement points")
        
        return trending
        
    except Exception as e:
        print(f"Error analyzing trends: {e}")
        return []

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "collect":
            # Collect posts (default: 100K)
            target = int(sys.argv[2]) if len(sys.argv) > 2 else 100000
            collect_posts(target)
        elif sys.argv[1] == "trends":
            # Show trending foods
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            get_trending_foods(days)
    else:
        # Default: collect a smaller sample for testing
        print("Usage:")
        print("  python etl.py collect [num_posts]  - Collect posts (default: 100000)")
        print("  python etl.py trends [days]        - Show trending foods (default: 7)")
        print("\nRunning test collection (1000 posts)...")
        collect_posts(1000)
