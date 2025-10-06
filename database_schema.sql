-- Food Trend Predictor Database Schema
-- Create tables in Supabase

-- Table 1: Reddit Posts
CREATE TABLE IF NOT EXISTS reddit_posts (
    id SERIAL PRIMARY KEY,
    post_id TEXT UNIQUE NOT NULL,
    subreddit TEXT NOT NULL,
    title TEXT NOT NULL,
    text TEXT,
    cleaned_text TEXT,
    author TEXT,
    score INTEGER DEFAULT 0,
    upvote_ratio FLOAT DEFAULT 0,
    num_comments INTEGER DEFAULT 0,
    created_utc TIMESTAMP NOT NULL,
    url TEXT,
    food_mentions TEXT[], -- Array of food items mentioned
    collected_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table 2: Food Predictions
CREATE TABLE IF NOT EXISTS food_predictions (
    id SERIAL PRIMARY KEY,
    food TEXT NOT NULL,
    trending_score FLOAT,
    is_trending INTEGER DEFAULT 0,
    predicted_trending INTEGER DEFAULT 0,
    trend_probability FLOAT,
    velocity FLOAT, -- Mentions per day
    growth_rate FLOAT,
    mention_count INTEGER DEFAULT 0,
    avg_score FLOAT DEFAULT 0,
    avg_engagement FLOAT DEFAULT 0,
    unique_subreddits INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(food, created_at)
);

-- Table 3: Daily Food Metrics (for time series analysis)
CREATE TABLE IF NOT EXISTS daily_food_metrics (
    id SERIAL PRIMARY KEY,
    food TEXT NOT NULL,
    date DATE NOT NULL,
    mention_count INTEGER DEFAULT 0,
    total_score INTEGER DEFAULT 0,
    total_comments INTEGER DEFAULT 0,
    avg_score FLOAT DEFAULT 0,
    engagement_score FLOAT DEFAULT 0,
    unique_subreddits INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(food, date)
);

-- Table 4: Model Performance Metrics
CREATE TABLE IF NOT EXISTS model_metrics (
    id SERIAL PRIMARY KEY,
    model_version TEXT NOT NULL,
    accuracy FLOAT,
    precision FLOAT,
    recall FLOAT,
    f1_score FLOAT,
    training_samples INTEGER,
    test_samples INTEGER,
    training_date TIMESTAMP DEFAULT NOW(),
    notes TEXT
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_reddit_posts_created_utc ON reddit_posts(created_utc);
CREATE INDEX IF NOT EXISTS idx_reddit_posts_subreddit ON reddit_posts(subreddit);
CREATE INDEX IF NOT EXISTS idx_reddit_posts_food_mentions ON reddit_posts USING GIN(food_mentions);
CREATE INDEX IF NOT EXISTS idx_food_predictions_food ON food_predictions(food);
CREATE INDEX IF NOT EXISTS idx_food_predictions_probability ON food_predictions(trend_probability);
CREATE INDEX IF NOT EXISTS idx_daily_metrics_date ON daily_food_metrics(date);
CREATE INDEX IF NOT EXISTS idx_daily_metrics_food ON daily_food_metrics(food);

-- Views for analytics

-- View 1: Trending Foods Summary
CREATE OR REPLACE VIEW trending_foods_summary AS
SELECT 
    food,
    COUNT(*) as mention_count,
    AVG(score) as avg_score,
    SUM(score) as total_score,
    SUM(num_comments) as total_comments,
    COUNT(DISTINCT subreddit) as subreddit_count,
    MAX(created_utc) as last_mentioned,
    (SUM(score) + SUM(num_comments) * 2) as engagement_score
FROM reddit_posts, unnest(food_mentions) as food
WHERE created_utc >= NOW() - INTERVAL '7 days'
GROUP BY food
ORDER BY engagement_score DESC;

-- View 2: Subreddit Activity
CREATE OR REPLACE VIEW subreddit_activity AS
SELECT 
    subreddit,
    COUNT(*) as post_count,
    AVG(score) as avg_score,
    SUM(score) as total_score,
    SUM(num_comments) as total_comments,
    COUNT(DISTINCT DATE(created_utc)) as active_days,
    MAX(created_utc) as last_post
FROM reddit_posts
WHERE created_utc >= NOW() - INTERVAL '30 days'
GROUP BY subreddit
ORDER BY post_count DESC;

-- View 3: Daily Trends
CREATE OR REPLACE VIEW daily_trends AS
SELECT 
    DATE(created_utc) as date,
    COUNT(*) as post_count,
    AVG(score) as avg_score,
    SUM(score) as total_score,
    SUM(num_comments) as total_comments,
    COUNT(DISTINCT subreddit) as active_subreddits
FROM reddit_posts
WHERE created_utc >= NOW() - INTERVAL '90 days'
GROUP BY DATE(created_utc)
ORDER BY date DESC;

-- Functions

-- Function to calculate food trending score
CREATE OR REPLACE FUNCTION calculate_trending_score(
    p_food TEXT,
    p_days INTEGER DEFAULT 7
)
RETURNS FLOAT AS $$
DECLARE
    v_score FLOAT;
BEGIN
    SELECT 
        (COUNT(*) * 1.0 + 
         AVG(score) * 0.5 + 
         SUM(num_comments) * 0.3 + 
         COUNT(DISTINCT subreddit) * 2.0)
    INTO v_score
    FROM reddit_posts, unnest(food_mentions) as food
    WHERE food = p_food
      AND created_utc >= NOW() - (p_days || ' days')::INTERVAL;
    
    RETURN COALESCE(v_score, 0);
END;
$$ LANGUAGE plpgsql;

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_food_predictions_updated_at
    BEFORE UPDATE ON food_predictions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Sample queries for analytics

-- Get top trending foods in last 7 days
COMMENT ON TABLE food_predictions IS 'Query: SELECT * FROM food_predictions WHERE trend_probability > 0.7 ORDER BY trend_probability DESC LIMIT 10;';

-- Get food trend over time
COMMENT ON TABLE daily_food_metrics IS 'Query: SELECT date, food, engagement_score FROM daily_food_metrics WHERE food = ''pizza'' ORDER BY date DESC LIMIT 30;';

-- Get most active subreddits
COMMENT ON VIEW subreddit_activity IS 'Query: SELECT * FROM subreddit_activity LIMIT 20;';
