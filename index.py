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

def main():    
    st.write(
    """
    # AI Foundry App - Test Page

    Welcome to the AI Foundry App. This is test page! 
    
    """
    )  
    


if __name__ == "__main__":
    main()