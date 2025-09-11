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




