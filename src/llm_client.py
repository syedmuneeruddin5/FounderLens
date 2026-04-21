import openai
from dotenv import load_dotenv
import os

load_dotenv()

def initialize_client():
    try:
        client = openai.OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY"),
            max_retries=3
        )
        return client
    except Exception as e:
        print("\033[91m" + f"Error initializing OpenAI client: {e}" + "\033[0m")
        return None

def call_llm(messages, json_mode=False, model="openai/gpt-oss-120b", temperature=None):

    client = initialize_client()
    if client is None:
        return None
    
    try:
        kwargs = {
            "model": model,
            "messages": messages,
            "response_format": {"type": "json_object"} if json_mode else None
        }
        if temperature is not None:
            kwargs["temperature"] = temperature
        
        response = client.chat.completions.create(**kwargs)
    except Exception as e:
        print("\033[91m" + f"Error calling LLM: {e}" + "\033[0m")
        return None
    
    return response.choices[0].message.content

def call_llm_stream(messages, json_mode=False, model="openai/gpt-oss-120b", temperature=None):
    client = initialize_client()
    if client is None:
        return None
    
    try:
        kwargs = {
            "model": model,
            "messages": messages,
            "response_format": {"type": "json_object"} if json_mode else None,
            "stream": True
        }
        if temperature is not None:
            kwargs["temperature"] = temperature
        
        response = client.chat.completions.create(**kwargs)
    except Exception as e:
        print("\033[91m" + f"Error calling LLM: {e}" + "\033[0m")
        return None
    
    for chunk in response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

# ENHANCE: Retry Mechanism, Rate Limiting