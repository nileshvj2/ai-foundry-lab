import os
from pathlib import Path
from opentelemetry import trace
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import ConnectionType
from azure.identity import EnvironmentCredential, DefaultAzureCredential
from azure.core.credentials import TokenCredential,AzureKeyCredential
from azure.search.documents import SearchClient
from config import PROMPTS_PATH, get_logger
from azure.ai.inference.prompts import PromptTemplate
from azure.search.documents.models import VectorizedQuery
from dotenv import load_dotenv
from azure.ai.inference import ChatCompletionsClient, EmbeddingsClient 
from typing import cast

#Load environment variables
load_dotenv("credentials.env",override=True)

# initialize logging and tracing objects
logger = get_logger(__name__)
tracer = trace.get_tracer(__name__)
credential = EnvironmentCredential()

aoai_key = os.environ["AZURE_AI_OPENAI_KEY"]

# create a project client using environment variables loaded from the .env file
project = AIProjectClient.from_connection_string(
    conn_str=os.environ["AIPROJECT_CONNECTION_STRING"], credential=DefaultAzureCredential()
)

# connections = project.connections.list(
#     connection_type=ConnectionType.AZURE_OPEN_AI,
# )
# for connection in connections:
#     print(connection)

connection = project.connections.get_default(
    connection_type=ConnectionType.AZURE_OPEN_AI,
    include_credentials=True,  # Optional. Defaults to "False".
)
print(connection)

# create a vector embeddings client that will be used to generate vector embeddings
chat = project.inference.get_chat_completions_client()
embeddings = project.inference.get_embeddings_client()

# use the project client to get the default search connection
search_connection = project.connections.get_default(
    connection_type=ConnectionType.AZURE_AI_SEARCH, include_credentials=True
)

# Create a search index client using the search connection
# This client will be used to create and delete search indexes

search_client = SearchClient(
    index_name=os.environ["AISEARCH_INDEX_NAME"],
    endpoint=search_connection.endpoint_url,
    credential=credential,
)




@tracer.start_as_current_span(name="get_documents")
def get_documents(messages: list, context: dict = None) -> dict:
    if context is None:
        context = {}

    overrides = context.get("overrides", {})
    top = overrides.get("top", 5)

    # generate a search query from the chat messages
    intent_prompty = PromptTemplate.from_prompty(Path(PROMPTS_PATH) / "intent_mapping.prompty")

    # inference_client = ChatCompletionsClient(
    #         endpoint=f"{connection.endpoint_url}/models",
    #         credential=cast(TokenCredential, connection.token_credential),
    #         credential_scopes=["https://cognitiveservices.azure.com/.default"],
    #     )

    inference_client  = ChatCompletionsClient(
        endpoint=f"{connection.endpoint_url}/models",
        credential=AzureKeyCredential(aoai_key),
        credential_scopes=["https://cognitiveservices.azure.com/.default"],  
    )


    intent_mapping_response = inference_client.complete(
        model=os.environ["INTENT_MAPPING_MODEL"],
        messages=intent_prompty.create_messages(conversation=messages),
        **intent_prompty.parameters                
    )

    # intent_mapping_response = chat.complete(
    #     model=os.environ["INTENT_MAPPING_MODEL"],
    #     messages=intent_prompty.create_messages(conversation=messages),
    #     **intent_prompty.parameters        
    # )

    search_query = intent_mapping_response.choices[0].message.content
    logger.debug(f"🧠 Intent mapping: {search_query}")


    
    # generate a vector representation of the search query
    #embedding = embeddings.embed(model=os.environ["EMBEDDINGS_MODEL"], input=search_query)
    embeddings_client  = EmbeddingsClient(
        endpoint=f"{connection.endpoint_url}/models",
        credential=AzureKeyCredential(aoai_key),
        credential_scopes=["https://cognitiveservices.azure.com/.default"],  
    )
    embedding = embeddings_client.embed(
        model=os.environ["EMBEDDINGS_MODEL"],
        input=search_query,        
    )

    search_vector = embedding.data[0].embedding

    # search the index for products matching the search query
    vector_query = VectorizedQuery(vector=search_vector, k_nearest_neighbors=top, fields="contentVector")

    search_results = search_client.search(
        search_text=search_query, vector_queries=[vector_query], select=["id", "content", "filepath", "title", "url"]
    )

    documents = [
        {
            "id": result["id"],
            "content": result["content"],
            "filepath": result["filepath"],
            "title": result["title"],
            "url": result["url"],
        }
        for result in search_results
    ]

    # add results to the provided context
    if "thoughts" not in context:
        context["thoughts"] = []

    # add thoughts and documents to the context object so it can be returned to the caller
    context["thoughts"].append(
        {
            "title": "Generated search query",
            "description": search_query,
        }
    )

    if "grounding_data" not in context:
        context["grounding_data"] = []
    context["grounding_data"].append(documents)

    logger.debug(f"📄 {len(documents)} documents retrieved: {documents}")
    return documents

#code to test the function when you run the script directly
if __name__ == "__main__":
    import logging
    import argparse

    # set logging level to debug when running this module directly
    logger.setLevel(logging.DEBUG)

    # load command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--query",
        type=str,
        help="Query to use to search product",
        default="I need a new tent for 4 people, what would you recommend?",
    )

    args = parser.parse_args()
    query = args.query

    result = get_documents(messages=[{"role": "user", "content": query}])