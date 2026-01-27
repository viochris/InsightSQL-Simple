import streamlit as st

def init_state():
    """
    Initializes the Session State variables if they do not exist.
    This ensures the app has a stable memory structure across re-runs.
    """
    # Initialize the chat history list
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Initialize the LLM object placeholder
    if "llm" not in st.session_state:
        st.session_state.llm = None
    
    # Initialize the Database Toolkit placeholder
    if "toolkit" not in st.session_state:
        st.session_state.toolkit = None

def change_on_api_key():
    """
    Triggered when the user modifies the API Key.
    Performs a 'Hard Reset' to ensure the new key is used for future connections.
    """
    # 1. Clear chat history to avoid context mismatch
    st.session_state.messages = []
    
    # 2. Reset the LLM and Toolkit to force re-initialization
    st.session_state.llm = None
    st.session_state.toolkit = None
    
    # 3. Completely remove the Agent Executor from memory
    # Using .pop() ensures the key is deleted, forcing the app to rebuild the agent
    st.session_state.pop("agent_executor", None)
    
    # Notify the user that the system has been reset
    st.toast("API Key updated! System reset.", icon="🔄")

def reset_state():
    """
    Triggered when the user clicks 'Reset Conversation'.
    Performs a 'Soft Reset' (clearing only the chat) while keeping the DB connection alive.
    """
    # Clear the message history list
    st.session_state.messages = []
    
    # Notify the user that the chat is clean
    st.toast("Conversation history cleared!", icon="🧹")