#!/usr/bin/env python3
"""
Setup script to automatically configure the Vapi Voice Agent with CareCloud prompt, tools, and webhook.
Usage:
  python scripts/setup_vapi.py --api-key <VAPI_KEY> --server-url <URL>
"""

import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.voice.vapi_service import create_or_update_assistant, list_phone_numbers, link_phone_number_to_assistant

def main():
    parser = argparse.ArgumentParser(description="Configure Vapi for CareCloud Voice Intake Agent")
    parser.add_argument("--api-key", help="Vapi Private API Key (or set VAPI_API_KEY env var)", default=os.getenv("VAPI_API_KEY"))
    parser.add_argument("--server-url", help="Public HTTPS URL of your deployed CareCloud API", default=os.getenv("BASE_URL"))
    parser.add_argument("--assistant-id", help="Existing Assistant ID to update (optional)", default=os.getenv("VAPI_ASSISTANT_ID"))
    args = parser.parse_args()

    api_key = args.api_key
    server_url = args.server_url

    if not api_key:
        api_key = input("Enter your Vapi API Key: ").strip()

    if not server_url:
        server_url = input("Enter your public Server URL (e.g., https://your-app.railway.app): ").strip()

    print("\n[1/3] Creating/Updating CareCloud Intake Assistant on Vapi...")
    assistant = create_or_update_assistant(api_key, server_url, assistant_id=args.assistant_id)
    assistant_id = assistant.get("id")
    print(f"✓ Assistant Ready: {assistant.get('name')} (ID: {assistant_id})")

    print("\n[2/3] Checking provisioned phone numbers on Vapi...")
    phone_numbers = list_phone_numbers(api_key)
    
    if not phone_numbers:
        print("! No phone number currently found in this Vapi account.")
        print("  You can buy or import a US phone number directly in the Vapi Dashboard (https://dashboard.vapi.ai/phone-numbers) or via API.")
    else:
        print(f"Found {len(phone_numbers)} phone number(s):")
        selected_number = phone_numbers[0]
        number_str = selected_number.get("number")
        phone_id = selected_number.get("id")
        print(f"  -> Phone Number: {number_str} (ID: {phone_id})")

        print(f"\n[3/3] Linking phone number {number_str} to CareCloud Assistant {assistant_id}...")
        link_phone_number_to_assistant(api_key, phone_id, assistant_id)
        print("✓ Phone number successfully linked to CareCloud Assistant!")
        print("\n=======================================================")
        print("🎉 CARECLOUD VOICE AI AGENT READY TO RECEIVE CALLS!")
        print(f"• Phone Number to call: {number_str}")
        print(f"• Webhook URL: {server_url}/api/vapi/webhook")
        print(f"• Dashboard URL: {server_url}")
        print("=======================================================\n")

if __name__ == "__main__":
    main()
