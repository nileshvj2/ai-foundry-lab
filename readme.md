
## Overview
This repository serves as a comprehensive guide for developers looking to implement Retrieval-Augmented Generation (RAG) solutions using the Azure AI Foundry SDK. It features a complete, production-ready example that demonstrates:

- Building streaming responses with RAG architecture 
- Implementing evaluation frameworks for model performance (using Azure AI SDKs)
- Setting up CI/CD pipelines for AI applications (using GIT actions)
- Configuring tracing and monitoring with Azure AI Foundry

Perfect for beginners and practitioners wanting to build production-grade AI applications with Azure's latest tooling.

## File structure: 
- chat.py - Example of using Azure AI Foundry SDK/API to build chat app using perksplus index created in Azure AI Foundry portal
- evaluate.py - which can be called to perform evaluation of the LLM app using various metrics and those metrics are synced to Azure AI portal evaluation metrics dashboard
- get_documents.py - retrieves documents using Azure AI search Index (created through portal)
- online_evaluate.py - For doing online evaluations of AI deployed app.

## Pre-reqs:
AI Search Index is already created (using AI Foundry portal) and all required configurations provided in env file.


## Disclaimer
The information and code contained in this repo and any accompanying materials (including, but not limited to, scripts, sample codes, etc.) are provided “AS-IS” and “WITH ALL FAULTS.” by owner and contributors of the repo. 

Code and information in this repo is provided solely for demonstration purposes and does not represent Microsoft or any other company's official documentation. Author assumes no liability arising from your use of this material.