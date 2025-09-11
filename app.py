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
