"""
TwitterNews Main Orchestrator

This script orchestrates a 3-agent pipeline to:
  1. Search news for Mexican automotive articles (news_research_agent)
  2. Analyze impact and select the most relevant article (impact_analysis_agent)
  3. Generate a Twitter post for the selected article (twitter_writer_agent)
  4. Optionally post the generated tweet to Twitter (post_tweet)
  5. Save the posted article to history

Environment / Config:
 - PERPLEXITY_API_KEY (required): API key for Perplexity
 - TWITTER_API_KEY / TWITTER_API_SECRET / TWITTER_ACCESS_TOKEN / TWITTER_ACCESS_TOKEN_SECRET
    (recommended) for posting via Tweepy. CI workflows (GitHub Actions) should set these as secrets.
 - PERPLEXITY_MODEL: Optional model name for Perplexity (e.g., "raptor-mini-preview")

Usage:
 - Locally: ensure config.toml contains keys or use environment variables.
 - In CI: provide secrets in the workflow YAML (see .github/workflows).
"""

# --- Imports (high-level) ---
# - twitternews.config: env/config helpers & source list loader
# - twitternews.history: history persistence (load/save)
# - twitternews.agents: Perplexity-powered agents (news, analysis, writer)
# - twitternews.twitter_utils: posting implementation that reads TWITTER_* from environment
import sys
from urllib.parse import urlparse
from twitternews.config import get_api_key, get_twitter_credentials, load_sources
from twitternews.history import load_history, save_history
from twitternews.agents import news_research_agent, impact_analysis_agent, post_copy_agent, tweet_optimizer_agent
from twitternews.twitter_utils import post_tweet, post_tweet_with_image
from twitternews.image_post import build_post_image
from twitternews.utils import TWEET_TARGET_CHARS, TWEET_MAX_CHARS, source_hashtag
import re
import os
import tempfile

def main():
    """
    Main orchestrator: runs the pipeline and handles I/O.

    Sections:
      1. Startup & Configuration: load API keys, Twitter credentials, and configuration.
      2. Data Loading: load sources.json and post_history.json
      3. Agent Pipeline:
           - Agent 1: Call news_research_agent to find candidate articles
           - Agent 2: Call impact_analysis_agent to pick most relevant article
           - Agent 3: Call twitter_writer_agent to generate the tweet text
      4. Posting (optional): post_tweet to Twitter (requires TWITTER_* env keys)
      5. History: persist the posted article to avoid reposting
    """

    # -------------------------------
    # --- Startup & Configuration ---
    # -------------------------------

    # Print startup message for visibility in CI logs
    print("Starting the Twitter post generation pipeline...")

    # Perplexity API key - required
    # Will attempt to read PERPLEXITY_API_KEY env var or config.toml
    api_key = get_api_key()

    # Load Twitter credentials: prefer environment, fallback to config.toml
    # These will be exported to os.environ by get_twitter_credentials() if found in config.
    twitter_creds = get_twitter_credentials()
    if len(twitter_creds) < 4:
        # Informative warning: posting may fail if not provided
        # This is not fatal: the pipeline can still run to generate content
        print("Some Twitter credentials are missing. Posting may fail if required credentials are not provided.")
    else:
        print("Twitter credentials loaded.")


    # -------------------------------
    # --- Data Loading ---
    # -------------------------------

    # Load valid sources to search and the existing history of posted URLs
    sources = load_sources()
    history = load_history()

    print(f"Loaded {len(sources)} news sources. Found {len(history)} articles in history.")


    # -------------------------------
    # --- Agent 1: News Research Agent ---
    # -------------------------------

    print("\n[Agent 1/3] Searching for news...")
    found_articles = news_research_agent(api_key, sources)

    # Report results of agent 1
    print("\n--- Found URLs ---")
    if found_articles:
        for article in found_articles:
            # Use getattr for 'date' because search results may not always include it
            print(f"- {getattr(article, 'date', '')}: {article.title} - {article.url}")
    else:
        print("No articles found.")
    print("------------------\n")

    # Filter articles already posted in the last week (history)
    history_urls = [item["url"] for item in history]
    articles = [a for a in found_articles if a.url not in history_urls]
    print(f"Found {len(found_articles)} total articles, {len(articles)} are new.")

    if not articles:
        # If there's nothing new, stop early
        print("No relevant articles found. Exiting.")
        return

    # print(f"\n\nDEBUG\n {found_articles} \n")

    
    # -------------------------------
    # --- Agent 2: Impact Analysis Agent ---
    # -------------------------------

    # Select the most impactful article for the target audience
    print("\n[Agent 2/3] Analyzing articles for impact...")
    most_relevant = impact_analysis_agent(api_key, articles)
    if not most_relevant:
        print("Could not determine the most relevant article. Exiting.")
        return

    print(f"Most relevant article: '{most_relevant.title}'")


    # -------------------------------
    # --- Agent 3: Post copy (one LLM call) ---
    # -------------------------------

    # One call returns the short tweet text and the longer text that goes on the image
    print("\n[Agent 3/3] Generating post copy...")
    tweet, image_text = post_copy_agent(api_key, most_relevant)
    print(f"\n--- Tweet Text ({len(tweet)} characters) ---")
    print(tweet)
    print(f"\n--- Image Text ({len(image_text)} characters) ---")
    print(image_text)
    print("-----------------------\n")

    # The image text aims for TWEET_TARGET_CHARS. Longer ones are optimized once,
    # and the shorter version is kept.
    if len(image_text) > TWEET_TARGET_CHARS:
        print(f"Warning: Image text is {len(image_text)} characters, exceeds the {TWEET_TARGET_CHARS} target.")
        optimized = tweet_optimizer_agent(api_key, image_text, max_length=TWEET_TARGET_CHARS)
        candidates = [t for t in (image_text, optimized) if t]
        image_text = min(candidates, key=len)
        print(f"Image text after optimization: {len(image_text)} characters")

    # Add the brand hashtag, then the newspaper name as a hashtag, e.g. #Motorpasion
    if "#DataAutomotriz" not in tweet:
        tweet = f"{tweet} #DataAutomotriz"
    source_tag = source_hashtag(most_relevant.url)
    if source_tag not in tweet:
        tweet = f"{tweet} {source_tag}"

    if len(tweet) > TWEET_MAX_CHARS:
        print(f"Error: Tweet is {len(tweet)} characters, exceeds the {TWEET_MAX_CHARS} character limit.")
        print("Cannot proceed with posting. Please review the optimization logic.")
        return
    print(f"Tweet length: {len(tweet)} characters (limit {TWEET_MAX_CHARS})")
    print("\n--- Generated Full Tweet Text ---")
    print(tweet)

    # -------------------------------
    # --- Posting ---
    # -------------------------------

    # The post is published as an image. The image is written to a temporary folder, never the repo.
    # If the image or its upload fails, the plain text tweet is posted instead.
    posted_id = None
    with tempfile.TemporaryDirectory() as tmp_dir:
        image_path = os.path.join(tmp_dir, "post.jpg")
        try:
            build_post_image(image_text, image_path)
            posted_id = post_tweet_with_image(tweet, image_path)
        except Exception as e:
            print(f"Image post failed, falling back to text-only tweet: {e}")

        try:
            if not posted_id:
                posted_id = post_tweet(tweet)
        except Exception as e:
            # Be explicit about failures: often indicates permissions (403) or invalid credentials
            print(f"Failed to post tweet: {e}")

    # Only a successful post marks the article as used. A failed post leaves the history file
    # unchanged, so the next run can pick the article up again, and the run fails.
    if not posted_id:
        print("Tweet was not posted. Article NOT saved to history.")
        sys.exit(1)

    print(f"Posted tweet id: {posted_id}")
    # --- History: Persist the posted URL ---
    save_history(most_relevant.url, history)
    print(f"\nArticle '{most_relevant.title}' saved to history.")

if __name__ == "__main__":
    main()
