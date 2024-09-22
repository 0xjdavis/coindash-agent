import streamlit as st
from groq import Groq
import json
import os
import time
import hashlib
import logging
import requests

GROQ_KEY = st.secrets["GROQ_KEY"]
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHAT_HISTORY_FILE = "chat_history.json"
USER_PREFERENCES_FILE = "user_preferences.json"
UPDATE_INTERVAL = 5  # seconds

# Initialize the chat history and user preferences files if they don't exist
for file in [CHAT_HISTORY_FILE, USER_PREFERENCES_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump([], f)

# Function to read chat history from the file
def read_chat_history():
    try:
        with open(CHAT_HISTORY_FILE, "r") as f:
            history = json.load(f)
        return history if isinstance(history, list) else []
    except json.JSONDecodeError:
        logger.error("Error decoding chat history JSON. Returning empty list.")
        return []
    except Exception as e:
        logger.error(f"Error reading chat history: {str(e)}")
        return []

# Function to write chat history to the file
def write_chat_history(messages):
    try:
        with open(CHAT_HISTORY_FILE, "w") as f:
            json.dump(messages, f)
    except Exception as e:
        logger.error(f"Error writing chat history: {str(e)}")

# Function to read user preferences from the file
def read_user_preferences():
    try:
        with open(USER_PREFERENCES_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error("Error decoding user preferences JSON. Returning empty dict.")
        return {}
    except Exception as e:
        logger.error(f"Error reading user preferences: {str(e)}")
        return {}

# Function to write user preferences to the file
def write_user_preferences(preferences):
    try:
        with open(USER_PREFERENCES_FILE, "w") as f:
            json.dump(preferences, f)
    except Exception as e:
        logger.error(f"Error writing user preferences: {str(e)}")

# Function to generate a unique emoji based on username
def generate_user_icon(username):
    hash_value = int(hashlib.md5(username.encode()).hexdigest(), 16)
    emoji_index = hash_value % len(EMOJI_LIST)
    return EMOJI_LIST[emoji_index]

# Function to get Fetch.AI token price
def get_fetchai_price():
    try:
        url = "https://api.coindesk.com/v1/bpi/currentprice.json"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        logger.info(f"API response: {data}")

        btc_price_usd = data['bpi']['USD']['rate']
        
        st.toast(btc_price_usd)

        
        if data:
            return (f"Current Bitcoin price in USD: {btc_price_usd}")
        else:
            logger.error("Price key not found in API response")
            return None
    except requests.RequestException as e:
        logger.error(f"Error fetching price: {str(e)}")
        return None
    except (KeyError, ValueError) as e:
        logger.error(f"Error parsing price: {str(e)}")
        return None

# Function to make decisions based on user preferences and metadata
def make_decision(user_preferences, fetchai_price):
    decision = "Based on your preferences, I recommend: "
    
    if "investment" in user_preferences.get("interests", []):
        if fetchai_price < 63000:
            decision += "Consider investing in BTC tokens as the price is relatively low. "
        else:
            decision += "BTC price is relatively high, you might want to wait for a dip before investing. "
    
    if "technology" in user_preferences.get("interests", []):
        decision += "Explore the latest developments in AI and blockchain technology. "
    
    if "health" in user_preferences.get("interests", []):
        decision += "Remember to take regular breaks and stay hydrated while using the chatbot. "
    
    return decision

# List of emojis to use
EMOJI_LIST = [
    "🙂", "😎", "🤓", "😇", "😂", "😍", "🤡", "😃", "😅", "😎", 
    "😜", "🤗", "🤔", "😴", "😱", "😡", "🤠", "😈", "😇", "👻"
]

# Setting page layout
st.set_page_config(
    page_title="Enhanced Multi-Person Chatbot",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Sidebar for API Key and User Info
st.sidebar.header("About App")
st.sidebar.markdown('This is an enhanced multi-person chatbot with Groq, capable of making decisions based on user preferences and using Fetch.AI data.', unsafe_allow_html=True)

groq_api_key = GROQ_KEY #st.sidebar.text_input("Groq API Key", type="password")
username = st.sidebar.text_input("Enter your username:")
user_interests = st.sidebar.text_area("Enter your interests (comma-separated):")

if not groq_api_key:
    st.sidebar.info("Please add your Groq API key to continue.", icon="🗝️")
elif not username:
    st.sidebar.info("Please enter a username and interests to continue.", icon="🗣️")
else:
    try:
        # Create a Groq client
        client = Groq(api_key=groq_api_key)
        logger.info("Groq client created successfully")
    except Exception as e:
        st.error(f"Error creating Groq client: {str(e)}")
        logger.error(f"Error creating Groq client: {str(e)}")
        st.stop()

    # Generate a unique icon for the user
    user_icon = generate_user_icon(username)

    # Update user preferences
    user_preferences = read_user_preferences()
    user_preferences[username] = {
        "interests": [interest.strip() for interest in user_interests.split(",")]
    }
    write_user_preferences(user_preferences)

    # Load the chat history from the file
    chatroom_messages = read_chat_history()

    # Show title and description
    st.title("Enhanced Multi-Person Chatbot")
    st.write("This is a multi-user chatroom with an AI chatbot capable of making decisions based on user preferences.")

    # Display all chatroom messages with user icons and tooltips
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

    # Create a chat input field for user input
    prompt = st.chat_input("What's on your mind?")

    if prompt:
        # Add the user's message to the chat history and display it
        new_message = {"role": "user", "icon": user_icon, "content": prompt, "sender_name": username}
        chatroom_messages.append(new_message)
        write_chat_history(chatroom_messages)

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

        # Check if the prompt starts with "nurt" or "decide"
        if prompt.lower().startswith("nurt") or prompt.lower().startswith("decide"):
            try:
                logger.info("Sending request to Groq API")

                # Get Fetch.AI price
                fetchai_price = get_fetchai_price()
                fetchai_info = f"The current price of FETCH.AI is ${fetchai_price:.4f} USD. " if fetchai_price else "FETCH.AI price information is currently unavailable. "
                logger.info(f"Fetch.AI price info: {fetchai_info}")

                # Make a decision based on user preferences
                decision = make_decision(user_preferences[username], fetchai_price)

                # Generate a response using the Groq API
                response = client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in chatroom_messages
                    ] + [{"role": "system", "content": f"Include this information in your response: {fetchai_info} {decision}"}]
                )
                logger.info("Received response from Groq API")

                # Extract the assistant's response from the Groq response object
                assistant_message = response.choices[0].message.content
                logger.info(f"Assistant message: {assistant_message}")

                # Add the assistant's message to the chat history and display it
                chatroom_messages.append({"role": "assistant", "icon": "🤖", "content": f"{assistant_message}"})
                write_chat_history(chatroom_messages)

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

    # Calendly
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

    # Copyright
    st.sidebar.caption("©️ Copyright 2024 J. Davis")

    # Rerun the app every UPDATE_INTERVAL seconds
    time.sleep(UPDATE_INTERVAL)
    st.rerun()
