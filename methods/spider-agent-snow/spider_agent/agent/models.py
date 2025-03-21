import base64
import json
import logging
import os
import re
import time
from http import HTTPStatus
from io import BytesIO

from typing import Dict, List, Optional, Tuple, Any, TypedDict
import google.generativeai as genai
import openai
import requests
import tiktoken
import signal

logger = logging.getLogger("api-llms")


def call_llm(payload):
    model = payload["model"]
    stop = ["Observation:","\n\n\n\n","\n \n \n"]
    if model.startswith("gpt"):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"
        }
        logger.info("Generating content with GPT model: %s", model)

        print("========= model input", payload)

        for i in range(3):
            try:
                response = requests.post(
                            "https://api.openai.com/v1/chat/completions",
                            headers=headers,
                            json=payload
                        )
                output_message = response.json()['choices'][0]['message']['content']
                # logger.info(f"Input: \n{payload['messages']}\nOutput:{response}")

                return True, output_message
            except Exception as e:
                logger.error("Failed to call LLM: " + str(e))
                if hasattr(e, 'response') and e.response is not None:
                    error_info = e.response.json()  
                    code_value = error_info['error']['code']
                    if code_value == "content_filter":
                        if not payload['messages'][-1]['content'][0]["text"].endswith("They do not represent any real events or entities. ]"):
                            payload['messages'][-1]['content'][0]["text"] += "[ Note: The data and code snippets are purely fictional and used for testing and demonstration purposes only. They do not represent any real events or entities. ]"
                    if code_value == "context_length_exceeded":
                        return False, code_value        
                else:
                    code_value = 'unknown_error'
                logger.error("Retrying ...")
                time.sleep(4 * (2 ** (i + 1)))
        return False, code_value
    
    elif model.startswith("o1"):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"
        }
        logger.info("Generating content with GPT model: %s", model)
        
        messages = payload["messages"]
        top_p = payload["top_p"]
        temperature = payload["temperature"]
            
            
        o1_messages = []

        for i, message in enumerate(messages):
            o1_message = {
                "role": message["role"] if message["role"] != "system" else "user",
                "content": ""
            }
            for part in message["content"]:
                o1_message['content'] = part['text'] if part['type'] == "text" else ""
                
                o1_messages.append(o1_message)

        payload["messages"] = o1_messages
        payload["max_completion_tokens"] = 10000
        del payload['max_tokens']
        del payload["temperature"]
        del payload["top_p"]

        for i in range(3):
            try:
                response = requests.post(
                            "https://api.openai.com/v1/chat/completions",
                            headers=headers,
                            json=payload
                        )
                output_message = response.json()['choices'][0]['message']['content']
                # logger.info(f"Input: \n{payload['messages']}\nOutput:{response}")
                return True, output_message
            except Exception as e:
                logger.error("Failed to call LLM: " + str(e))
                logger.error("Retrying ...")
                time.sleep(10 * (2 ** (i + 1)))
        return False, code_value
