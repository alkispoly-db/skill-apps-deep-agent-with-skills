#!/usr/bin/env python3
"""
Test deployed Databricks deep agent app.

This script:
1. Tests health endpoint
2. Tests chat completions endpoint
3. Tests multi-turn conversations
4. Validates OpenAI compatibility
"""
import argparse
import json
import subprocess
import sys
import requests
from typing import Dict, Optional


def get_auth_header(profile: str) -> Dict[str, str]:
    """
    Get Databricks OAuth2 token.

    Args:
        profile: Databricks CLI profile

    Returns:
        Authorization header dict
    """
    try:
        result = subprocess.run(
            ["databricks", "auth", "token", "--profile", profile],
            capture_output=True,
            text=True,
            check=True
        )
        token = result.stdout.strip()
        return {"Authorization": f"Bearer {token}"}
    except subprocess.CalledProcessError as e:
        print(f"Error getting auth token: {e}")
        sys.exit(1)


def test_health(app_url: str, headers: Dict[str, str]) -> bool:
    """
    Test /api/v1/healthcheck endpoint.

    Args:
        app_url: App base URL
        headers: Request headers

    Returns:
        True if healthy, False otherwise
    """
    print("Testing health endpoint...")

    url = f"{app_url.rstrip('/')}/api/v1/healthcheck"

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        status = data.get("status")

        if status == "healthy":
            print(f"✓ Health check passed")
            print(f"  Service: {data.get('service')}")
            print(f"  Timestamp: {data.get('timestamp')}")
            return True
        else:
            print(f"✗ Health check failed: status={status}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"✗ Health check failed: {e}")
        return False


def test_chat_completion(
    app_url: str,
    headers: Dict[str, str],
    message: str,
    conversation_history: Optional[list] = None
) -> Optional[Dict]:
    """
    Test /api/v1/chat/completions endpoint.

    Args:
        app_url: App base URL
        headers: Request headers
        message: User message
        conversation_history: Previous messages for multi-turn

    Returns:
        Response dict or None on failure
    """
    url = f"{app_url.rstrip('/')}/api/v1/chat/completions"

    # Build messages
    messages = conversation_history or []
    messages.append({"role": "user", "content": message})

    payload = {"messages": messages}

    try:
        response = requests.post(
            url,
            headers={**headers, "Content-Type": "application/json"},
            json=payload,
            timeout=60
        )
        response.raise_for_status()

        data = response.json()

        # Validate OpenAI format
        if "choices" not in data:
            print(f"✗ Invalid response format: missing 'choices'")
            return None

        if not data["choices"]:
            print(f"✗ Invalid response format: empty 'choices'")
            return None

        choice = data["choices"][0]
        if "message" not in choice:
            print(f"✗ Invalid response format: missing 'message' in choice")
            return None

        return data

    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Response: {e.response.text}")
        return None


def test_single_turn(app_url: str, headers: Dict[str, str]) -> bool:
    """
    Test single-turn conversation.

    Args:
        app_url: App base URL
        headers: Request headers

    Returns:
        True if successful, False otherwise
    """
    print("\nTesting single-turn completion...")

    message = "Hello, how are you?"
    response = test_chat_completion(app_url, headers, message)

    if not response:
        return False

    assistant_message = response["choices"][0]["message"]["content"]
    print(f"✓ Single-turn completion passed")
    print(f"  User: {message}")
    print(f"  Assistant: {assistant_message[:100]}...")

    return True


def test_multi_turn(app_url: str, headers: Dict[str, str]) -> bool:
    """
    Test multi-turn conversation.

    Args:
        app_url: App base URL
        headers: Request headers

    Returns:
        True if successful, False otherwise
    """
    print("\nTesting multi-turn conversation...")

    # First turn
    message1 = "My name is Alice"
    response1 = test_chat_completion(app_url, headers, message1)

    if not response1:
        return False

    assistant_message1 = response1["choices"][0]["message"]["content"]

    # Build conversation history
    history = [
        {"role": "user", "content": message1},
        {"role": "assistant", "content": assistant_message1}
    ]

    # Second turn - test memory
    message2 = "What is my name?"
    response2 = test_chat_completion(app_url, headers, message2, history)

    if not response2:
        return False

    assistant_message2 = response2["choices"][0]["message"]["content"]

    # Check if assistant remembers the name
    if "alice" in assistant_message2.lower():
        print(f"✓ Multi-turn conversation passed")
        print(f"  Turn 1 - User: {message1}")
        print(f"  Turn 1 - Assistant: {assistant_message1[:80]}...")
        print(f"  Turn 2 - User: {message2}")
        print(f"  Turn 2 - Assistant: {assistant_message2[:80]}...")
        return True
    else:
        print(f"✗ Multi-turn conversation failed: assistant didn't remember name")
        print(f"  Response: {assistant_message2}")
        return False


def test_openai_compatibility(response: Dict) -> bool:
    """
    Validate OpenAI response format.

    Args:
        response: API response dict

    Returns:
        True if compatible, False otherwise
    """
    print("\nValidating OpenAI compatibility...")

    required_fields = ["id", "object", "created", "choices"]

    for field in required_fields:
        if field not in response:
            print(f"✗ Missing required field: {field}")
            return False

    if response["object"] != "chat.completion":
        print(f"✗ Invalid object type: {response['object']}")
        return False

    choice = response["choices"][0]
    required_choice_fields = ["index", "message", "finish_reason"]

    for field in required_choice_fields:
        if field not in choice:
            print(f"✗ Missing required choice field: {field}")
            return False

    message = choice["message"]
    if "role" not in message or "content" not in message:
        print(f"✗ Invalid message format")
        return False

    print("✓ OpenAI compatibility validated")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Test deployed Databricks deep agent app"
    )
    parser.add_argument(
        "app_url",
        help="App URL (e.g., https://app-name-xxx.databricksapps.com)"
    )
    parser.add_argument(
        "--profile",
        default="DEFAULT",
        help="Databricks CLI profile (default: DEFAULT)"
    )
    parser.add_argument(
        "--custom-message",
        help="Send custom test message"
    )

    args = parser.parse_args()

    # Ensure URL doesn't end with slash
    app_url = args.app_url.rstrip('/')

    print(f"\n{'='*60}")
    print(f"Testing Databricks Deep Agent App")
    print(f"{'='*60}")
    print(f"App URL: {app_url}")
    print(f"Profile: {args.profile}")
    print(f"{'='*60}\n")

    # Get auth headers
    headers = get_auth_header(args.profile)

    # Run tests
    tests_passed = 0
    tests_total = 0

    # Test 1: Health check
    tests_total += 1
    if test_health(app_url, headers):
        tests_passed += 1

    # Test 2: Single-turn
    tests_total += 1
    if test_single_turn(app_url, headers):
        tests_passed += 1
        # Get response for OpenAI validation
        response = test_chat_completion(app_url, headers, "Hello")
        if response:
            # Test 3: OpenAI compatibility
            tests_total += 1
            if test_openai_compatibility(response):
                tests_passed += 1

    # Test 4: Multi-turn
    tests_total += 1
    if test_multi_turn(app_url, headers):
        tests_passed += 1

    # Custom message test
    if args.custom_message:
        print(f"\nTesting custom message...")
        print(f"  Message: {args.custom_message}")
        response = test_chat_completion(app_url, headers, args.custom_message)
        if response:
            assistant_message = response["choices"][0]["message"]["content"]
            print(f"  Response: {assistant_message}")

    # Summary
    print(f"\n{'='*60}")
    print(f"Test Results: {tests_passed}/{tests_total} passed")
    print(f"{'='*60}")

    if tests_passed == tests_total:
        print("✓ All tests passed! App is ready to use.")
        sys.exit(0)
    else:
        print(f"✗ {tests_total - tests_passed} test(s) failed")
        print("\nTroubleshooting:")
        print(f"  1. Check app logs: databricks apps logs <app-name> --profile {args.profile}")
        print(f"  2. Verify app status: databricks apps get <app-name> --profile {args.profile}")
        print(f"  3. Check app URL is correct")
        sys.exit(1)


if __name__ == "__main__":
    main()
