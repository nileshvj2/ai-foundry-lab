import streamlit as st
import os
from pathlib import Path
from opentelemetry import trace
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential,EnvironmentCredential
from config import PROMPTS_PATH, get_logger, enable_telemetry
from get_documents import get_documents
from dotenv import load_dotenv
from azure.ai.inference.prompts import PromptTemplate
from azure.ai.inference import ChatCompletionsClient, EmbeddingsClient 
from azure.ai.projects.models import ConnectionType
from azure.core.credentials import TokenCredential,AzureKeyCredential
from azure.core.settings import settings 

st.set_page_config(layout="wide")

#Load environment variables
load_dotenv("credentials.env",override=True)

# initialize logging and tracing objects
logger = get_logger(__name__)
tracer = trace.get_tracer(__name__)


enable_telemetry(log_to_project=True)

# Set up the credential to use for authentication
credential = EnvironmentCredential()
aoai_key = os.environ["AZURE_AI_OPENAI_KEY"]

# create a project client using environment variables loaded from the .env file
project = AIProjectClient.from_connection_string(
    conn_str=os.environ["AIPROJECT_CONNECTION_STRING"], credential=DefaultAzureCredential()
)



connection = project.connections.get_default(
    connection_type=ConnectionType.AZURE_OPEN_AI,
    include_credentials=True,  # Optional. Defaults to "False".
)
print(connection)


@tracer.start_as_current_span(name="create_chat_completion")
def create_chat_completion(messages: list, context: dict = None)-> dict:
    if context is None:
        context = {}

    #retrieve documents from the search index
    documents = get_documents(messages, context)

    # do a grounded chat call using the search results
    grounded_chat_prompt = PromptTemplate.from_prompty(Path(PROMPTS_PATH) / "grounded_chat.prompty")

    system_message = grounded_chat_prompt.create_messages(documents=documents, context=context)

    inference_client  = ChatCompletionsClient(
        endpoint=f"{connection.endpoint_url}/models",
        credential=AzureKeyCredential(aoai_key),
        credential_scopes=["https://cognitiveservices.azure.com/.default"],  
    )

    response = inference_client.complete(
        model=os.environ["CHAT_MODEL"],
        messages=system_message + messages,
        **grounded_chat_prompt.parameters,
        stream=False,        
    )
    print(response)
    logger.info(f"💬 Response: {response}")
    
    # Return a chat protocol compliant response
    return {"message": response.choices[0].message, "context": context}
    

def handle_chat_prompt(prompt):
    # Echo the user's prompt to the chat window
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Send the user's prompt to Azure OpenAI and display the response
    # The call to Azure OpenAI is handled in create_chat_completion()
    # This function loops through the responses and displays them as they come in.
    # It also appends the full response to the chat history.
    full_response = ""
    with st.chat_message("assistant"):
        message_placeholder = st.empty()        
        full_response = create_chat_completion(st.session_state.messages)

        # Uncomment the following lines to enable streaming responses
        # for response in create_chat_completion(st.session_state.messages):
        #     full_response += (response["message"].content or "")
        #     message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response["message"].content)
    st.session_state.messages.append({"role": "assistant", "content": full_response["message"].content})
    
     
def main():    
    st.write(
    """
    # AI Assistant Chat

    Chat with own data using Azure OpenAI's On Your Data feature.
    
    """
    )  
    

    if "firstload" not in st.session_state or st.session_state["firstload"] != "false":        
        #first time on this page: Initialize session state variables        
        st.session_state["messages"] = []
        st.session_state["firstload"] = "false"

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])    

    # Await a user message and handle the chat prompt when it comes in.
    if prompt := st.chat_input("Enter a message:"):
        handle_chat_prompt(prompt)

if __name__ == "__main__":
    main()


#note:  Add flags to enable logging of message contents to the project and provision required permissions
#refer https://learn.microsoft.com/en-us/azure/ai-studio/how-to/develop/trace-local-sdk?tabs=python 
# add AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED and AZURE_SDK_TRACING_IMPLEMENTATION in credentials.env file
# After that also add log analytics reader permission to the service principal(or az logged in user) to access the logs in app insights aiworkshop2-insights