import streamlit as st
import google.generativeai as genai
from elevenlabs.client import ElevenLabs
from pymongo import MongoClient
from datetime import datetime
import requests
import re
from tenacity import retry, stop_after_attempt, wait_exponential
from youtube_transcript_api.proxies import GenericProxyConfig
from youtube_transcript_api import YouTubeTranscriptApi

from dotenv import load_dotenv
import random
import os
import time

# Your API keys and MongoDB connection (from Streamlit secrets)
# GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
# ELEVENLABS_API_KEY = st.secrets["ELEVENLABS_API_KEY"]
# MONGODB_URI = st.secrets["MONGODB_URI"]



# Load environment variables from .env file
load_dotenv()

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
MONGODB_URI = os.environ.get("MONGODB_URI")

# Check if the environment variables are set
if not GOOGLE_API_KEY:
    st.error("GOOGLE_API_KEY is not set. Please check your Streamlit secrets.")
    raise SystemExit("GOOGLE_API_KEY not set")  # Use SystemExit to stop the app
if not ELEVENLABS_API_KEY:
    st.error("ELEVENLABS_API_KEY is not set. Please check your Streamlit secrets.")
    raise SystemExit("ELEVENLABS_API_KEY not set")
if not MONGODB_URI:
    st.error("MONGODB_URI is not set. Please check your Streamlit secrets.")
    raise SystemExit("MONGODB_URI not set")






# Set up your API keys and MongoDB connection
genai.configure(api_key=GOOGLE_API_KEY)
try:
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
except Exception as e:
    st.error(f"Error initializing ElevenLabs: {e}")
    raise SystemExit(f"Failed to initialize ElevenLabs: {e}")





# MongoDB Atlas connection setup
try:
    client_mongo = MongoClient(MONGODB_URI)
    db = client_mongo.summaries_db
    summaries_collection = db.summaries
except Exception as e:
    st.error(f"Error connecting to MongoDB: {e}")
    raise SystemExit(f"Failed to connect to MongoDB: {e}")

prompt = """You are a video summarizer. You will be taking the transcript text
and summarizing the entire video and providing the important summary in points
within 250 words. Please provide the summary of the text along with headline in 4 words given here:  """






# Save summary with headline to MongoDB
def save_summary(youtube_url, headline, summary):
    try:
        document = {
            "youtube_url": youtube_url,
            "headline": headline,
            "summary": summary,
            "timestamp": datetime.now(),
        }
        summaries_collection.insert_one(document)
        st.success("Summary saved to MongoDB.")  # explicitly show a success message
    except Exception as e:
        st.error(f"Error saving summary to MongoDB: {e}")

# Fetch the latest summaries from MongoDB based on user selection
def get_latest_saved_summaries(limit):
    try:
        results = summaries_collection.find().sort("timestamp", -1).limit(limit)
        return list(results)
    except Exception as e:
        st.error(f"Error fetching summaries from MongoDB: {e}")
        return []  # Return an empty list on error to avoid crashing the app



# Search summaries in MongoDB by headline
def search_summaries_by_headline(search_query):
    try:
        results = summaries_collection.find({
            "headline": {"$regex": search_query, "$options": "i"},  # Case-insensitive search by headline
        })
        return list(results)
    except Exception as e:
        st.error(f"Error searching summaries in MongoDB: {e}")
        return []

def extract_video_id(url):
    """
    Extracts the YouTube video ID from different URL formats.
    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    """
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11})"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None






def extract_transcript_details(video_id):
    ytt_api = YouTubeTranscriptApi(
    proxy_config=GenericProxyConfig(
        http_url="http://uvmfwcbs-rotate:imui7uhheoxm@p.webshare.io:80",
        https_url="http://uvmfwcbs-rotate:imui7uhheoxm@p.webshare.io:80",
     )
     
     )
    
# all requests done by ytt_api will now be proxied using the defined proxy URLs
    transcripts = ytt_api.list_transcripts(video_id)

    # transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
    available_languages = [t.language_code for t in transcripts]
    print(f"Available transcripts for video {video_id}: {available_languages}") # Removed st.info

    for lang in ["en", "en-IN", "hi"]:
            if lang in available_languages:
                try:
                    transcripts_lang = transcripts.find_transcript([lang])
                    transcript_data = transcripts_lang.fetch()
                    full_transcript = " ".join([item.text for item in transcript_data])
                    print(f"✅ Retrieved transcript for {lang}") # Removed st.info
                    return full_transcript
                except Exception as e:
                    print(f"❌ Error retrieving transcript for {lang}: {e}") # Removed st.error
    raise ValueError(
            f"No transcripts found in preferred languages. Available: {available_languages}"
        )
    

