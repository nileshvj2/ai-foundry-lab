import os
import pandas as pd
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import ConnectionType
from azure.ai.evaluation import evaluate, GroundednessEvaluator
from azure.identity import DefaultAzureCredential

from chat import create_chat_completion

# load environment variables from the .env file at the root of this repo
from dotenv import load_dotenv

load_dotenv("credentials.env", override=True)

# create a project client using environment variables loaded from the .env file
project = AIProjectClient.from_connection_string(
    conn_str=os.environ["AIPROJECT_CONNECTION_STRING"], credential=DefaultAzureCredential()
)

connection = project.connections.get_default(connection_type=ConnectionType.AZURE_OPEN_AI, include_credentials=True)

evaluator_model = {
    "azure_endpoint": connection.endpoint_url,
    "azure_deployment": os.environ["EVALUATION_MODEL"],
    "api_version": "2024-06-01",
    "api_key": os.environ["AZURE_AI_OPENAI_KEY"], #connection.key,
}

groundedness = GroundednessEvaluator(evaluator_model)


def evaluate_chat(query):    
    full_response = ""
    full_response = create_chat_completion(messages=[{"role": "user", "content": query}])
    # for response in create_chat_completion(messages=[{"role": "user", "content": query}]):
    #         full_response += (response.choices[0].delta.content or "")                    
    return {"response": full_response["message"].content, "context": full_response["context"]["grounding_data"]}


# Evaluate must be called inside of __main__, not on import
if __name__ == "__main__":
    from config import DATA_PATH

    # workaround for multiprocessing issue on linux
    from pprint import pprint
    from pathlib import Path
    import multiprocessing
    import contextlib

    with contextlib.suppress(RuntimeError):
        multiprocessing.set_start_method("spawn", force=True)

    # run evaluation with a dataset and target function, log to the project
    result = evaluate(
        data=Path(DATA_PATH) / "chat_eval_data.jsonl",
        target=evaluate_chat,
        evaluation_name="evaluate_chat_benefits_code",
        evaluators={
            "groundedness": groundedness,
        },
        evaluator_config={
            "default": {
                "query": {"${data.query}"},
                "response": {"${target.response}"},
                "context": {"${target.context}"},
            }
        },
        azure_ai_project=project.scope,
        output_path="./myevalresults.json",
    )

    tabular_result = pd.DataFrame(result.get("rows"))

    pprint("-----Summarized Metrics-----")
    pprint(result["metrics"])
    pprint("-----Tabular Result-----")
    pprint(tabular_result)
    pprint(f"View evaluation results in AI Studio: {result['studio_url']}")


###Note: 
# Note: The evaluate function will automatically log the evaluation to the project if the azure_ai_project parameter is provided.
# storage blob data contributor role is required to write to the project (if user is is logged in using Az login then that user or else service principal  which is specified in .env file))