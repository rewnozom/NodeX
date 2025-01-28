# ai_agent/models/llm_models.py

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAI, OpenAIEmbeddings, AzureChatOpenAI, AzureOpenAIEmbeddings, AzureOpenAI
from langchain_community.llms.ollama import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory
from pydantic.v1.types import SecretStr
from ai_agent.config.ai_config import Config
config = Config()



# API keys mapped by service
API_KEYS = {
    "OpenAI": config.OPENAI_API_KEY,
    "Anthropic": config.API_KEY_ANTHROPIC,
    "Groq": config.API_KEY_GROQ,
    # Add other services as needed
}


# Dictionary with model names and default temperatures
MODELS = {
    "Anthropic": {
        "Anthropic Haiku": ("claude-3-haiku-20240307", 0.1),
        "Anthropic Sonnet 35": ("claude-3-5-sonnet-20240620", 0.1),
        "Anthropic Sonnet": ("claude-3-sonnet-20240229", 0.1),
        "Anthropic Opus": ("claude-3-opus-20240229", 0.1),
    },
    "OpenAI": {
        "OpenAI GPT-3.5": ("gpt-3.5-turbo", 0.1),
        "OpenAI GPT-3.5 Instruct": ("gpt-3.5-turbo-instruct", 0.1),
        "OpenAI GPT-4": ("gpt-4", 0.1),
        "OpenAI GPT-4o": ("gpt-4o", 0.1),
        "OpenAI GPT-4o Mini": ("gpt-4o-mini", 0.1),
    },
    "Groq": {
        "Groq Gemma 7B": ("gemma-7b-it", 0.1),
        "Groq Gemma2 9B": ("gemma2-9b-it", 0.1),
        "Groq Llama 3.1 405B Reasoning": ("llama-3.1-405b-reasoning", 0.1),
        "Groq Llama 3.1 70B Versatile": ("llama-3.1-70b-versatile", 0.1),
        "Groq Llama 3.1 8B Instant": ("llama-3.1-8b-instant", 0.1),
        "Groq Llama Guard 3 8B": ("llama-guard-3-8b", 0.1),
        "Groq Llama3 70B 8192": ("llama3-70b-8192", 0.1),
        "Groq Llama3 8B 8192": ("llama3-8b-8192", 0.1),
        "Groq Llama3 70B 8192 Tool Use Preview": ("llama3-groq-70b-8192-tool-use-preview", 0.1),
        "Groq Llama3 8B 8192 Tool Use Preview": ("llama3-groq-8b-8192-tool-use-preview", 0.1),
        "Groq Mixtral 8x7B 32768": ("mixtral-8x7b-32768", 0.1),
    },
    "Ollama": {
        "Ollama Dolphin": ("dolphin-llama3:8b-256k-v2.9-fp16", 0.1),
        "Ollama Phi": ("phi3:3.8b-mini-instruct-4k-fp16", 0.1),
    },
    "Google": {
        "Google Chat": ("gemini-1.5-flash-latest", 0.1),
    },
    "LM Studio": {
        "LM Studio Model": ("model-identifier", 0.1),
    },
    "OpenRouter": {
        "OpenRouter Llama 3.1": ("meta-llama/llama-3.1-8b-instruct:free", 0.1),
    },
}

# Dictionary with embedding models
EMBEDDING_MODELS = {
    "HuggingFace Embeddings": "sentence-transformers/all-MiniLM-L6-v2",
    "OpenAI Embeddings": "openai",
    "Ollama Embeddings": "ollama",
    "LM Studio Embeddings": "lm_studio",
    "Azure OpenAI Embeddings": "azure_openai",
}

# Function to get model based on name
def get_model(model_key, temperature=None, api_key=None):
    for company, models in MODELS.items():
        if model_key in models:
            model_name, default_temp = models[model_key]
            temp = temperature if temperature is not None else default_temp
            api_key = api_key or API_KEYS.get(company)

            if company == "Anthropic":
                return ChatAnthropic(model_name=model_name, temperature=temp, api_key=api_key)
            elif company == "OpenAI":
                return ChatOpenAI(model_name=model_name, temperature=temp, api_key=api_key)
            elif company == "Groq":
                return ChatGroq(model_name=model_name, temperature=temp, api_key=api_key)
            elif company == "Ollama":
                return Ollama(model=model_name, temperature=temp)
            elif company == "Google":
                return ChatGoogleGenerativeAI(
                    model=model_name, temperature=temp, google_api_key=api_key,
                    safety_settings={HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE}
                )
            elif company == "LM Studio":
                return get_lm_studio_model(temperature=temp)
            elif company == "OpenRouter":
                return ChatOpenAI(
                    api_key=api_key, base_url="https://openrouter.ai/api/v1", model=model_name, temperature=temp
                )
    
    if model_key in EMBEDDING_MODELS:
        if model_key == "HuggingFace Embeddings":
            return HuggingFaceEmbeddings(model_name=EMBEDDING_MODELS[model_key])
        elif model_key == "OpenAI Embeddings":
            return OpenAIEmbeddings(api_key=api_key)
        elif model_key == "Ollama Embeddings":
            return OllamaEmbeddings(model=EMBEDDING_MODELS[model_key], temperature=temperature)
        elif model_key == "LM Studio Embeddings":
            return get_lm_studio_embedding()
        elif model_key == "Azure OpenAI Embeddings":
            azure_endpoint = os.getenv("OPENAI_AZURE_ENDPOINT")
            return AzureOpenAIEmbeddings(
                deployment_name=model_key, api_key=api_key, azure_endpoint=azure_endpoint
            )
    
    raise ValueError(f"Unknown model key: {model_key}")

# Specific model retrieval functions for LM Studio
from langchain_openai import ChatOpenAI

def get_lm_studio_model(temperature=0.1):
    # Assuming you're using LM Studio, the base URL and API key are specific to LM Studio
    base_url = "http://localhost:1234/v1"
    return ChatOpenAI(model_name="model-identifier", temperature=temperature, openai_api_key="lm-studio", base_url=base_url)



def get_lm_studio_embedding(model="model-identifier"):
    client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
    return lambda text: client.embeddings.create(input=[text.replace("\n", " ")], model=model).data[0].embedding
