# Import necessary modules from Flask and LangChain
from flask import Flask, request, jsonify
from langchain_community.llms import Ollama
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
import requests # Import the requests library for making HTTP calls

# Initialize the Flask application
app = Flask(__name__)

# --- LangChain Setup ---
# Define a dictionary to store chat histories for different sessions.
# In a real-world application, this would typically be a database or a more persistent store.
store = {}

# Hardcoded session ID for a single chat instance
FIXED_SESSION_ID = "jim"

# Define a function to get the session history for a given session ID.
# This function is crucial for `RunnableWithMessageHistory` to retrieve the correct history.
def get_session_history(session_id: str) -> BaseChatMessageHistory:
    # This function will now always use the FIXED_SESSION_ID for history management
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# Initialize the Ollama LLM.
# Make sure Ollama is running and you have a model pulled (e.g., 'llama3').
# You can pull a model using: ollama pull llama3
llm = Ollama(model="llama3")

# Define the chat prompt template.
# MessagesPlaceholder is used to inject the chat history into the prompt.
prompt = ChatPromptTemplate.from_messages(
    [
        # Updated system prompt to include a persona
        ("system", "Your name is Jim, you like to talk about obscure topics, be creative with your background and interests and make up random stories, you were never a snail trainer, you dont ask questions you state facts but still contribute to the conversation.  Dont be too verbose but keep it interesting.  This is a conversation not a lecture."),
        MessagesPlaceholder(variable_name="history"), # This will hold the chat history
        ("human", "{message}"), # This will be the current user message
    ]
)

# Create a chain: prompt -> llm -> output_parser
chain = prompt | llm | StrOutputParser()

# Wrap the chain with RunnableWithMessageHistory to manage chat history.
# 'history' is the key that corresponds to MessagesPlaceholder in the prompt.
# 'get_session_history' is the function that provides the chat history for a session.
with_message_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="message", # Key for the current user message
    history_messages_key="history", # Key for the chat history in the prompt
)

# --- Flask API Endpoint ---
@app.route('/chat', methods=['POST'])
def chat_endpoint():
    """
    Handles POST requests to the /chat endpoint.
    Expects a JSON payload with a 'message' field.
    The session_id is now hardcoded.
    """
    data = request.get_json()

    # Check if the 'message' field is present in the request body
    if not data or 'message' not in data:
        return jsonify({"error": "Missing 'message' in request body"}), 400

    user_message = data['message']
    
    # Use the hardcoded session ID
    session_id = FIXED_SESSION_ID

    # Store the responses to return to the user
    response_data = {}

    # Define the prefix for output to the text file
    FILE_PREFIX = "Jim ----------------------------------------"

    try:
        # 1. Invoke the LangChain runnable with the user message and the fixed session ID.
        # The history will be automatically managed by `with_message_history`.
        initial_llm_response = with_message_history.invoke(
            {"message": user_message},
            config={"configurable": {"session_id": session_id}}
        )
        response_data["initial_llm_response"] = initial_llm_response

        # Write the initial LLM response to convo.txt
       

        # 2. Prepare for an external API request to its own /chat endpoint
        # The message for this new request will be the initial LLM's response
        self_triggered_message = initial_llm_response
        response_data["self_triggered_message"] = self_triggered_message

        # Define the URL for the external request (pointing back to this API)
        api_url = "http://127.0.0.1:5000/chat" # Assuming Flask runs on port 5000

        # Prepare the payload for the external request
        # We only send the message, as the session_id is hardcoded on the receiving end.
        external_payload = {"message": self_triggered_message}
        
        # Make the external POST request to the same endpoint
        # This simulates an external service calling your API
        print(f"Making external call to {api_url} with message: '{self_triggered_message}'")
        external_response = requests.post(api_url, json=external_payload)
        
        # Check if the external request was successful
        if external_response.status_code == 200:
            # Extract the initial_llm_response from the external call's JSON response
            self_triggered_response = external_response.json().get("initial_llm_response")
        else:
            self_triggered_response = f"Error in external call: {external_response.status_code} - {external_response.text}"
            print(self_triggered_response)

        response_data["self_triggered_response"] = self_triggered_response
        
        # Write the self-triggered response to convo.txt
        with open("convo.txt", "a") as f:
            f.write(f"{FILE_PREFIX}\n")
            f.write(f"Self-Triggered Message: {self_triggered_message}\n")
            f.write(f"Self-Triggered Response: {self_triggered_response}\n\n")

        # Return both the initial LLM response and the self-triggered response
        return jsonify(response_data)

    except Exception as e:
        # Catch any exceptions during the LLM invocation and return an error
        print(f"Error processing request: {e}")
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500

# Main entry point for the Flask application
if __name__ == '__main__':
    # Run the Flask app.
    # In a production environment, use a production-ready WSGI server like Gunicorn.
    app.run(debug=True, port=5001)
