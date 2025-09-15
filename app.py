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
    




def generate_gemini_content(transcript_text, prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")
    try:
        
        response = model.generate_content(prompt + transcript_text)
        lines = response.text.split("\n", 1)
        headline = lines[0] if len(lines) > 0 else "No headline available"
        summary = lines[1] if len(lines) > 1 else "No summary available"
        return headline, summary
    except Exception as e:
        st.error(f"❌ Error generating summary: {e}")
        raise  # Re-raise to trigger retry




# def generate_audio(response_text):
#     try:
#         audio_stream = client.text_to_speech.convert(
#             text=response_text,
#             voice_id="JBFqnCBsd6RMkjVDRZzb",
#             model_id="eleven_multilingual_v2",
#             output_format="mp3_44100_128",
#         )
#         print("audio is ready... now playing")
#         audio_bytes = b"".join(audio_stream)  # Convert generator to bytes
#         return audio_bytes
#     except Exception as e:
#         print(f"❌ Error generating audio: {e}")
#         st.error(f"❌ Error generating audio.")
#         raise RuntimeError(f"Failed to generate audio: {e}")

# Streamlit app setup
st.set_page_config(page_title="🎙️ Podcast Summary App", layout="centered")
st.title("🎙️ Podcast Summarizer")
st.subheader("Summarize & Search Any Podcast Instantly")






# Search functionality for headlines
search_query = st.text_input("🔍 Search by Headline:")
if search_query:
    st.subheader(f"Searching for summaries with headline containing: {search_query}")
    results = search_summaries_by_headline(search_query)
    if results:
        st.subheader(f"Found {len(results)} result(s):")
        for result in results:
            st.markdown(f"### [Video URL]({result['youtube_url']})")
            st.write(f"**Headline:** {result['headline']}")
            st.write(f"**Summary:** {result['summary']}")
            st.write(f"Timestamp: {result['timestamp']}")
    else:
        st.warning("No summaries found matching your search.")

# Show Latest Saved Summaries Button & Select the number of summaries
with st.expander("Show Latest Saved Summaries"):
    # Add a slider to select the number of summaries to retrieve
    num_summaries = st.slider(
        "Select number of latest summaries to show", 1, 20, 10
    )  # Default: 10, min: 1, max: 20
    if st.button("📑 Show Latest Saved Summaries"):
        with st.spinner(f"⏳ Fetching the latest {num_summaries} saved summaries..."):
            try:
                saved_summaries = get_latest_saved_summaries(num_summaries)
                if saved_summaries:
                    st.subheader(f"Showing the latest {num_summaries} saved summaries:")
                    for summary in saved_summaries:
                        st.markdown(f"### [Video URL]({summary['youtube_url']})")
                        st.write(f"**Headline:** {summary['headline']}")
                        st.write(f"**Summary:** {summary['summary']}")
                        st.write(f"Timestamp: {summary['timestamp']}")
                else:
                    st.warning("No saved summaries found.")
            except Exception as e:
                st.error(f"❌ Error fetching saved summaries: {str(e)}")



