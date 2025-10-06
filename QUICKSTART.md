# 🚀 Quick Start Guide

Get the Food Trend Predictor running in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- Reddit API credentials
- Supabase account

## Step-by-Step Setup

### 1. Get Reddit API Credentials (2 minutes)

1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Fill in:
   - **Name**: Food Trend Predictor
   - **Type**: Select "script"
   - **Description**: ML-powered food trend analysis
   - **About URL**: (leave blank)
   - **Redirect URI**: http://localhost:8080
4. Click "Create app"
5. Note down:
   - **Client ID**: (under app name)
   - **Client Secret**: (under "secret")

### 2. Get Supabase Credentials (2 minutes)

1. Go to https://supabase.com
2. Sign up or log in
3. Create a new project
4. Go to Project Settings > API
5. Note down:
   - **Project URL** (API URL)
   - **Project API Key** (anon public key)

### 3. Install and Configure (1 minute)

```bash
# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

Your `.env` should look like:
```
REDDIT_CLIENT_ID=abc123xyz
REDDIT_CLIENT_SECRET=def456uvw
REDDIT_USER_AGENT=FoodTrendPredictor/1.0

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key_here
```

### 4. Set Up Database (30 seconds)

1. Go to your Supabase project dashboard
2. Click "SQL Editor" in the left sidebar
3. Copy the contents of `database_schema.sql`
4. Paste and run in the SQL Editor
5. Verify tables were created (check "Table Editor")

### 5. Run Setup Verification

```bash
python setup.py
```

This will verify:
- ✅ Python version
- ✅ Dependencies installed
- ✅ Environment variables configured
- ✅ Reddit API connection
- ✅ Supabase connection

## Usage

### Option A: Full Pipeline (Recommended for First Run)

```bash
# Collect 1000 posts, train model, and launch dashboard
./run_pipeline.sh 1000
```

This will:
1. Collect 1000 Reddit posts
2. Train the ML model
3. Generate predictions
4. Launch the dashboard at http://localhost:8501

### Option B: Step-by-Step

```bash
# 1. Collect data (start small)
python etl.py collect 1000

# 2. Train model
python model.py

# 3. Generate insights
python predict_service.py report

# 4. Launch dashboard
streamlit run dashboard.py
```

## Quick Commands Reference

```bash
# Data Collection
python etl.py collect 1000          # Collect 1000 posts
python etl.py collect 100000        # Collect 100K posts (full dataset)
python etl.py trends 7              # Show trending foods (last 7 days)

# Model & Predictions
python model.py                     # Train model
python predict_service.py report    # Generate insights report
python predict_service.py predict pizza  # Predict specific food

# Dashboard
streamlit run dashboard.py          # Launch dashboard

# Utilities
python config.py                    # Validate configuration
python setup.py                     # Run setup checks
```

## Expected Timeline

### Small Dataset (1,000 posts)
- Data collection: ~5 minutes
- Model training: ~3 minutes
- **Total**: ~10 minutes

### Medium Dataset (10,000 posts)
- Data collection: ~30 minutes
- Model training: ~10 minutes
- **Total**: ~45 minutes

### Full Dataset (100,000 posts)
- Data collection: ~4 hours
- Model training: ~30 minutes
- **Total**: ~5 hours

💡 **Tip**: Start with 1,000 posts to verify everything works, then scale up!

## Troubleshooting

### "No module named 'X'"
```bash
pip install -r requirements.txt
```

### "Reddit API Error"
- Verify credentials in `.env`
- Check that app type is "script" in Reddit
- Wait a few seconds and try again (rate limiting)

### "Supabase Connection Failed"
- Verify URL and key in `.env`
- Check that tables exist in Supabase
- Ensure you're using the "anon public" key, not service key

### "No data available"
- Run data collection first: `python etl.py collect 1000`
- Check Supabase dashboard to verify posts were stored

### "Model not found"
- Run training: `python model.py`
- Check that `models/` directory was created

## What You'll See

### Dashboard Preview

Once running, you'll see:

1. **Key Metrics**: Total posts, engagement, trending foods
2. **Trending Now**: Top 15 foods with rankings
3. **Analytics**: Time series charts, distributions
4. **ML Predictions**: Trend probabilities and recommendations
5. **Heatmap**: Food mentions across subreddits

### Sample Insights Output

```
🔥 TOP 10 TRENDING FOODS:
📈 Kimchi           | Probability: 87.3% | Velocity: 15.2/day
📈 Açaí Bowl        | Probability: 84.1% | Velocity: 12.8/day
📈 Sourdough        | Probability: 81.5% | Velocity: 11.4/day
...

📊 CATEGORY TRENDS:
Asian        | Avg: 78.2% | 5 trending items
Plant-based  | Avg: 72.5% | 3 trending items
Healthy      | Avg: 68.9% | 4 trending items
```

## Next Steps

1. ✅ **Verify**: Check dashboard shows data correctly
2. 📈 **Scale Up**: Collect more posts for better predictions
3. 🎨 **Customize**: Edit `config.py` to add your subreddits
4. 🔄 **Automate**: Set up daily cron jobs for data collection
5. 📊 **Analyze**: Use predictions for menu planning or research

## Daily Operations

```bash
# Morning: Collect fresh data
python etl.py collect 5000

# Afternoon: Retrain model
python model.py

# Continuous: Monitor dashboard
streamlit run dashboard.py
```

## Need Help?

1. Check `README.md` for full documentation
2. Review `config.py` for settings
3. Look at logs in `logs/` directory
4. Verify `.env` configuration

## Performance Tips

- Start with small datasets (1K posts)
- Use GPU for faster BERT processing (optional)
- Run data collection during off-peak hours
- Cache dashboard data (already configured)
- Set up scheduled jobs for automation

---

**Ready to discover food trends? Let's go! 🚀**

```bash
./run_pipeline.sh 1000
```

Then open your browser to: **http://localhost:8501**
