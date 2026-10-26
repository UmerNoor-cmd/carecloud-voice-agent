import os
import requests
from typing import Dict, Any, Optional
from .prompts import CARECLOUD_INTAKE_SYSTEM_PROMPT, FIRST_MESSAGE
from .tools import VAPI_TOOLS

VAPI_BASE_URL = "https://api.vapi.ai"

def get_headers(api_key: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json"
    }

def create_or_update_assistant(api_key: str, server_url: str, assistant_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Creates or updates the CareCloud Intake Coordinator Assistant in Vapi.
    """
    headers = get_headers(api_key)
    
    # Assistant configuration
    payload = {
        "name": "CareCloud Patient Intake Coordinator",
        "firstMessage": FIRST_MESSAGE,
        "model": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": CARECLOUD_INTAKE_SYSTEM_PROMPT
                }
            ],
            "tools": VAPI_TOOLS
        },
        "voice": {
            "provider": "11labs",
            "voiceId": "21m00Tcm4TlvDq8ikWAM"  # Rachel - warm, conversational
        },
        "serverUrl": f"{server_url.rstrip('/')}/api/vapi/webhook",
        "recordingEnabled": True,
        "silenceTimeoutSeconds": 30,
        "maxDurationSeconds": 600,
        "endCallMessage": "Thank you for calling CareCloud. Take care and goodbye!"
    }

    if assistant_id:
        url = f"{VAPI_BASE_URL}/assistant/{assistant_id}"
        resp = requests.patch(url, json=payload, headers=headers)
    else:
        url = f"{VAPI_BASE_URL}/assistant"
        resp = requests.post(url, json=payload, headers=headers)

    if resp.status_code not in [200, 201]:
        raise RuntimeError(f"Vapi API Error ({resp.status_code}): {resp.text}")

    return resp.json()

def list_phone_numbers(api_key: str) -> list:
    headers = get_headers(api_key)
    resp = requests.get(f"{VAPI_BASE_URL}/phone-number", headers=headers)
    if resp.status_code != 200:
        raise RuntimeError(f"Failed to list phone numbers: {resp.text}")
    return resp.json()

def link_phone_number_to_assistant(api_key: str, phone_number_id: str, assistant_id: str) -> Dict[str, Any]:
    headers = get_headers(api_key)
    resp = requests.patch(
        f"{VAPI_BASE_URL}/phone-number/{phone_number_id}",
        json={"assistantId": assistant_id},
        headers=headers
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Failed to link phone number: {resp.text}")
    return resp.json()
