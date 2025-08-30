import os
import praw
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Connect to Reddit
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
)

# Test: fetch 5 posts from r/AskCulinary
for submission in reddit.subreddit("AskCulinary").hot(limit=5):
    print(submission.title)
