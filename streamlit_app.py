import streamlit as st
from groq import Groq
import json
import os
import time
import hashlib
import logging
import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
CHAT_HISTORY_FILE = "chat_history.json"
USER_PREFERENCES_FILE = "user_preferences.json"
UPDATE_INTERVAL = 1  # seconds
EMOJI_LIST = ["🙂", "😎", "🤓", "😇", "😂", "😍", "🤡", "😃", "😅", "😎", 
              "😜", "🤗", "🤔", "😴", "😱", "😡", "🤠", "😈", "😇", "👻"]

# Initialize files
for file in [CHAT_HISTORY_FILE, USER_PREFERENCES_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)

# File operations
def read_json_file(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

def write_json_file(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f)

# User icon generation
def generate_user_icon(username):
    hash_value = int(hashlib.md5(username.encode()).hexdigest(), 16)
    return EMOJI_LIST[hash_value % len(EMOJI_LIST)]

# Fetch.AI price fetching
def get_fetchai_price():
    try:
        response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=fetch-ai&vs_currencies=usd")
        response.raise_for_status()
        data = response.json()
        return data['fetch-ai']['usd']
    except Exception as e:
        logger.error(f"Error fetching Fetch.AI price: {str(e)}")
        return None

# Decision making
def make_decision(user_preferences, fetchai_price):
    decision = "Based on your preferences, I recommend: "
    interests = user_preferences.get("interests", [])
    
    if "investment" in interests and fetchai_price:
        decision += f"{'Consider investing' if fetchai_price < 0.5 else 'Wait for a dip'} in Fetch.AI tokens. "
    if "technology" in interests:
        decision += "Explore the latest developments in AI and blockchain technology. "
    if "health" in interests:
        decision += "Remember to take regular breaks and stay hydrated while using the chatbot. "
    
    return decision

# Streamlit UI setup
st.set_page_config(page_title="Enhanced Multi-Person Chatbot", page_icon="✨", layout="centered")

st.sidebar.header("About App")
st.sidebar.markdown('This is an enhanced multi-person chatbot with Groq, capable of making decisions based on user preferences and using Fetch.AI data.')

# Groq API setup
groq_api_key = st.secrets["GROQ_KEY"]
username = st.sidebar.text_input("Enter your username:")
user_interests = st.sidebar.text_area("Enter your interests (comma-separated):")

if not groq_api_key:
    st.sidebar.error("Groq API key is missing. Please check your secrets.")
    st.stop()

if not username:
    st.sidebar.info("Please enter a username and interests to continue.", icon="🗣️")
    st.stop()

try:
    client = Groq(api_key=groq_api_key)
    logger.info("Groq client created successfully")
except Exception as e:
    st.error(f"Error creating Groq client: {str(e)}")
    logger.error(f"Error creating Groq client: {str(e)}")
    st.stop()

# User preferences and chat history
user_icon = generate_user_icon(username)
user_preferences = read_json_file(USER_PREFERENCES_FILE)
user_preferences[username] = {"interests": [interest.strip() for interest in user_interests.split(",")]}
write_json_file(USER_PREFERENCES_FILE, user_preferences)

chatroom_messages = read_json_file(CHAT_HISTORY_FILE)

# Main chat interface
st.title("Enhanced Multi-Person Chatbot")
st.write("This is a multi-user chatroom with an AI chatbot capable of making decisions based on user preferences.")

for message in chatroom_messages:
    icon = message.get("icon", "👤")
    content = message.get("content", "")
    role = message.get("role", "user")
    sender_name = message.get("sender_name", "")
    
    st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <div style="position: relative;">
                <span style="font-size: 24px; margin-right: 8px; cursor:pointer;" title="{sender_name}">{icon}</span>
            </div>
            <div style="background-color: {'#f1f1f1' if role == 'user' else '#e1f5fe'}; padding: 8px; border-radius: 8px;">
                {content}
            </div>
        </div>
    """, unsafe_allow_html=True)

# Chat input and processing
if prompt := st.chat_input("What's on your mind?"):
    chatroom_messages.append({"role": "user", "icon": user_icon, "content": prompt, "sender_name": username})
    write_json_file(CHAT_HISTORY_FILE, chatroom_messages)

    st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <div style="position: relative;">
                <span style="font-size: 24px; margin-right: 8px; cursor: pointer;" title="{username}">{user_icon}</span>
            </div>
            <div style="background-color: #f1f1f1; padding: 8px; border-radius: 8px;">
                {prompt}
            </div>
        </div>
    """, unsafe_allow_html=True)

    if prompt.lower().startswith(("nurt", "decide")):
        try:
            fetchai_price = get_fetchai_price()
            fetchai_info = f"The current price of FETCH.AI is ${fetchai_price:.4f} USD. " if fetchai_price else "FETCH.AI price information is currently unavailable. "
            decision = make_decision(user_preferences[username], fetchai_price)

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in chatroom_messages
                ] + [{"role": "system", "content": f"Include this information in your response: {fetchai_info} {decision}"}]
            )

            assistant_message = response.choices[0].message.content
            chatroom_messages.append({"role": "assistant", "icon": "🤖", "content": assistant_message})
            write_json_file(CHAT_HISTORY_FILE, chatroom_messages)

            st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <div style="position: relative;">
                        <span style="font-size: 24px; margin-right: 8px; cursor:pointer;" title="Assistant">🤖</span>
                    </div>
                    <div style="background-color: #e1f5fe; padding: 8px; border-radius: 8px;">
                        {assistant_message}
                    </div>
                </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
            logger.error(f"Error generating response: {str(e)}")

# Sidebar extras
st.sidebar.markdown("""
    <hr />
    <center>
    <div style="border-radius:8px;padding:8px;background:#fff";width:100%;">
    <img src="https://avatars.githubusercontent.com/u/98430977" alt="Oxjdavis" height="100" width="100" border="0" style="border-radius:50%"/>
    <br />
    <span style="height:12px;width:12px;background-color:#77e0b5;border-radius:50%;display:inline-block;"></span> <b style="color:#000000">I'm available for new projects!</b><br />
    <a href="https://calendly.com/0xjdavis" target="_blank"><button style="background:#126ff3;color:#fff;border: 1px #126ff3 solid;border-radius:8px;padding:8px 16px;margin:10px 0">Schedule a call</button></a><br />
    </div>
    </center>
    <br />
""", unsafe_allow_html=True)

st.sidebar.caption("©️ Copyright 2024 J. Davis")

# Auto-refresh mechanism
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > UPDATE_INTERVAL:
    st.session_state.last_refresh = time.time()
    new_messages = read_json_file(CHAT_HISTORY_FILE)
    if new_messages != chatroom_messages:
        st.rerun()
