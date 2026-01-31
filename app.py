import streamlit as st
# Import LangChain community tools specifically for constructing the SQL Agent
from langchain_community.agent_toolkits.sql.base import create_sql_agent
# Import utilities for establishing database connections and managing schemas
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
# Import the Google Gemini chat model interface
from langchain_google_genai import ChatGoogleGenerativeAI
# Import the specific handler to visualize the agent's reasoning steps (thoughts/actions) in the Streamlit UI
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
# Import custom helper functions for session state management (persistence)
from function import init_state, change_on_api_key, reset_state

# Initialize session state variables (messages, llm, toolkit) immediately 
# to prevent errors during app re-runs
init_state()

# Configure the Streamlit page settings
# This sets the browser tab title, favicon, and layout mode
st.set_page_config(
    page_title="InsightSQL | Basic SQL Agent",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Display the main application header
st.title("📊 InsightSQL: Basic SQL Agent")

# Render the introduction text using Markdown and HTML
# unsafe_allow_html=True is used here to center the subtitle text
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 1.1rem; margin-bottom: 30px;">
        <b>Stop writing complex queries. Start asking questions.</b>
    </div>
    
    Welcome to **InsightSQL**. This application empowers you to interact with your database using natural language. 
    Powered by **Generative AI**, it instantly translates your questions into precise **SQL queries** and executes them to provide real-time, data-driven insights.
    
    ---
    """, 
    unsafe_allow_html=True
)

with st.sidebar:
    # Sidebar header with an emoji for better visual hierarchy
    st.header("⚙️ Page Configuration")

    st.divider()

    # Input widget for the API Key
    # 'type="password"' masks the input characters for security
    # 'on_change' triggers the cleanup function immediately if the key is modified
    st.text_input(
        "🔑 Google API Key", # Improved label with emoji
        type="password",
        key="google_api_key",
        on_change = change_on_api_key,
        help="Paste your Google Gemini API Key here. This is required to power the AI agent." # Filled help text
    )

    st.divider()

    # Button to clear the chat history (Soft Reset)
    # This invokes 'reset_state' to clear messages without breaking the database connection
    st.button(
        "🔄 Reset Conversation", # Improved label with emoji
        on_click=reset_state,
        use_container_width=True,
        help="Clears the current chat history so you can start a fresh topic." # Filled help text
    )

    # Main action button to initialize the Agent
    # Changing "Load Information" to "Connect to Database" is more accurate for an SQL Agent
    connect = st.button(
        "🚀 Connect to Database", # Improved label: Clearer action
        use_container_width=True,
        help="Initializes the connection to the 'dresses.db' file and builds the AI agent." # Filled help text
    )

    st.divider()

    # --- Help & Documentation ---
    # Expandable section for the User Guide
    with st.expander("📖 How to Use"):
        st.markdown(
            """
            1. **Enter API Key:** Paste your Google Gemini API Key in the field above.
            2. **Connect:** Click **'Connect to Database'** to initialize the AI Agent.
            3. **Ask:** Type questions about the data (e.g., *"How many items are rated 5 stars?"*).
            4. **Reset:** Use **'Reset Conversation'** to clear the chat interface. 
               *(Note: This agent is **One-Shot** and has **No Memory**; it treats every question as a brand new request).*
            """
        )

    # Expandable section for Frequently Asked Questions
    with st.expander("❓ FAQ"):
        st.markdown(
            """
            **Q: What data is this?**
            A: This app uses a sample SQLite database (`dresses.db`) containing fashion sales data.

            **Q: Can I use my own database?**
            A: Yes! You can replace `dresses.db` with your own SQLite file. 
            For instructions, visit: [InsightSQL-Simple on GitHub](https://github.com/viochris/InsightSQL-Simple).
            
            **Q: Is my data safe?**
            A: Yes. The AI processes the *schema* (table structure) to generate SQL. It only retrieves data rows when explicitly asked.
            
            **Q: Why 'Quota Exceeded'?**
            A: The Google Gemini Free Tier has rate limits. If this happens, wait a minute and try again.
            """
        )

    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; font-size: 0.85rem; color: #888;">
            © 2026 <b>Silvio Christian, Joe</b><br>
            Powered by <b>Google Gemini</b> 🚀<br><br>
            <a href="https://www.linkedin.com/in/silvio-christian-joe/" target="_blank" style="text-decoration: none; margin-right: 10px;">🔗 LinkedIn</a>
            <a href="mailto:viochristian12@gmail.com" style="text-decoration: none;">📧 Email</a>
        </div>
        """, 
        unsafe_allow_html=True
    )

# Check if the API Key has been provided by the user
if st.session_state.google_api_key:
    # Implement a Singleton pattern: Only initialize the LLM if it hasn't been created yet.
    # This prevents unnecessary re-initialization on every app rerun, saving resources.
    if st.session_state.llm is None:
        st.session_state.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", 
            google_api_key=st.session_state.google_api_key,
            # Set temperature to 0.3 to ensure the model outputs are deterministic and precise,
            # which is critical for generating accurate SQL queries.
            temperature=0.3 
        )
        # Notify the user that the AI model is ready to use with a Success Icon
        st.toast("AI Engine initialized successfully!", icon="🧠")
else:
    # Display a warning with an icon if the user attempts to proceed without an API Key
    st.warning("Please enter your Google API Key to proceed.", icon="⚠️")

# Check if the 'Connect' button was clicked and the LLM is already initialized
if connect and st.session_state.llm is not None:
    # Ensure we don't re-initialize the toolkit if it already exists
    if st.session_state.toolkit is None:
        try:
            # Establish a connection to the SQLite database
            # Note: For MySQL/PostgreSQL, use the format: "dialect+driver://user:pass@host/dbname"
            db = SQLDatabase.from_uri("sqlite:///dresses.db")

            # Initialize the SQL Toolkit
            # This provides the Agent with the necessary tools to inspect the schema and execute queries
            st.session_state.toolkit = SQLDatabaseToolkit(db=db, llm=st.session_state.llm)

            # Notify the user with a Success Icon
            st.toast("✅ Database Connected! System Ready.", icon="🎉")
            
        except Exception as e:
            # Catch and display any errors during connection with an Error Icon
            # Convert error to string for analysis
            error_str = str(e).lower()

            # Check for specific error types to provide better guidance
            if "argumenterror" in error_str:
                # This usually happens if the SQLAlchemy URI string is malformed
                st.error("❌ Invalid Database URI. Please check the connection string format.", icon="📝")
            
            elif "operationalerror" in error_str:
                # This often happens if the file doesn't exist or permissions are denied
                st.error("❌ Operational Error. Is 'dresses.db' in the correct folder?", icon="📂")
            
            else:
                # Catch and display any other unexpected errors
                error_msg = f"❌ Connection Failed: {str(e)}"
                st.error(error_msg, icon="🚨")
    else:
        # Inform the user if the system is already running
        st.toast("⚡ System is already active. Ready to query!", icon="🤖")

# Handle the case where the user clicks 'Connect' without providing an API Key first
elif connect and st.session_state.llm is None:
    st.toast("⚠️ API Key Missing! Please check the sidebar.", icon="🔑")

# Check if the Database Toolkit is missing (meaning the user hasn't connected yet)
if st.session_state.toolkit is None:
    st.warning("⚠️ Database not connected. Please click **'Connect to Database'** in the sidebar.", icon="🔌")

# Check if the Agent Executor needs to be initialized
# We only create it if:
# 1. It doesn't exist in the session state yet (Singleton pattern)
# 2. The LLM is ready (API Key provided)
# 3. The Toolkit is ready (Database connected)
if "agent_executor" not in st.session_state \
    and st.session_state.llm is not None \
    and st.session_state.toolkit is not None:

    try:
        # Initialize the SQL Agent
        # This is the "Brain" that orchestrates the interaction between the LLM and the Database.
        st.session_state.agent_executor = create_sql_agent(
            llm=st.session_state.llm,
            toolkit=st.session_state.toolkit,
            verbose=True, # Enable detailed logging in the terminal for debugging
            agent_type="tool-calling" # Use Gemini's native Function Calling (Modern & Stable)
        )
        
    except Exception as e:
        # Handle critical initialization errors (e.g., version mismatch, toolkit errors)
        # Convert error to string for analysis to handle specific cases
        error_str = str(e).lower()

        if "valueerror" in error_str:
            # This often occurs if the LLM or Toolkit objects are not compatible with the chosen agent type
            st.error("❌ Configuration Error: Invalid LLM or Toolkit parameters provided.", icon="⚙️")
        
        elif "outputparser" in error_str:
            # This occurs if the agent structure cannot interpret the model's output format
            st.error("❌ Parsing Error: The model output format is incompatible with this agent.", icon="🧩")
        
        else:
            # Handle any other critical initialization errors (e.g., version mismatch, system errors)
            # Display the raw error message with a visual alert icon
            error_msg = f"❌ Failed to initialize AI Agent: {str(e)}"
            st.error(error_msg, icon="💥")

# Render the chat history
# We iterate through the 'messages' list in the session state to persist the conversation
# across Streamlit re-runs (which happen every time the user interacts).
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Capture user input
# The := operator assigns the input to 'prompt_text' and returns True if input exists.
if prompt_text := st.chat_input("Ask a question about your data..."):
    
    # --- Pre-flight Checks (Guardrails) ---
    # Before processing, we ensure all components (LLM, Toolkit, Agent) are ready.
    
    if st.session_state.llm is None:
        st.warning("⚠️ AI Engine is not active. Please enter your API Key in the sidebar.", icon="🚫")
        
    elif st.session_state.toolkit is None:
        st.warning("⚠️ Database Toolkit is missing. Please click 'Connect to Database'.", icon="🔌")
        
    elif not st.session_state.agent_executor:
        st.warning("⚠️ Agent is not initialized. Please reload the connection.", icon="🤖")
        
    else:
        # --- Process Valid Input ---
        
        # 1. Append User Message to History
        st.session_state.messages.append({"role": "human", "content": prompt_text})
        
        # 2. Display User Message immediately in the UI
        st.chat_message("human").write(prompt_text)

        # 3. Generate AI Response
        with st.chat_message("ai"):
            try:
                # Initialize the StreamlitCallbackHandler
                # This handler creates an interactive container in the UI that displays 
                # the agent's "Thought Process" (SQL generation, execution, and observation) in real-time.
                st_callback = StreamlitCallbackHandler(st.container())

                # Invoke the SQL Agent with the Callback
                # We pass 'st_callback' to the invoke method so the agent can render its 
                # intermediate steps (Thought -> Action -> Observation) directly into the Streamlit container.
                response = st.session_state.agent_executor.invoke(
                    {"input": prompt_text},
                    {"callbacks": [st_callback]}
                )

                # Validate and Display Final Output
                # Once the reasoning is complete, we display the final natural language answer.
                if "output" in response and len(response["output"]) > 0:
                    st.markdown(response["output"])

                # 4. Append AI Response to History
                st.session_state.messages.append({"role": "ai", "content": response["output"]})

            except Exception as e:
                # Handle Runtime Errors (e.g., Invalid SQL generated, Database locked, etc.)
                # Convert error object to string for analysis
                error_str = str(e).lower()

                if "429" in error_str or "resource" in error_str:
                    # Specific handling for Google API Quota limits (Resource Exhausted)
                    st.error("⏳ API Quota Exceeded. Please wait a moment or check your Google Cloud plan.", icon="🛑")

                elif "api_key" in error_str or "400" in error_str:
                    # Specific handling for Invalid API Key errors (Authentication failed)
                    st.error("🔑 Invalid API Key. Please check your Google API Key in the sidebar.", icon="🚫")

                elif "parsing" in error_str:
                    # Handling for when the LLM output cannot be parsed by the Agent
                    st.error("🧩 Parsing Error. The model response could not be interpreted. Please try again.", icon="😵‍💫")

                elif "operationalerror" in error_str:
                    # Handling for SQL syntax errors or database locking issues
                    st.error("🛠️ Database Error. The generated SQL query failed to execute.", icon="📉")

                else:
                    # Handle any other unexpected runtime errors
                    error_msg = f"❌ An error occurred: {str(e)}"
                    st.error(error_msg, icon="🚨")