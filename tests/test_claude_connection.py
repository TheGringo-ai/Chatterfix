"""
Test Claude API Connection
Quick script to verify Anthropic API key is working correctly
"""

import os
from anthropic import Anthropic

def test_claude_connection():
    """Test connection to Claude API"""

    # Load API key from environment
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found in environment")
        return False

    print(f"🔑 API Key found: {api_key[:20]}...")

    try:
        # Initialize Anthropic client
        client = Anthropic(api_key=api_key)

        print("📡 Sending test request to Claude...")

        # Send a simple test message
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[
                {
                    "role": "user",
                    "content": "Say 'ChatterFix Claude API connection successful!' if you can read this."
                }
            ]
        )

        response_text = message.content[0].text
        print(f"\n✅ Claude Response:\n{response_text}\n")

        print("🎉 Connection test PASSED!")
        print(f"📊 Model used: {message.model}")
        print(f"📊 Tokens used: {message.usage.input_tokens} input, {message.usage.output_tokens} output")

        return True

    except Exception as e:
        print(f"\n❌ Connection test FAILED!")
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Testing Claude API Connection for ChatterFix")
    print("=" * 60 + "\n")

    # Load .env file
    from dotenv import load_dotenv
    load_dotenv()

    success = test_claude_connection()

    print("\n" + "=" * 60)
    if success:
        print("✅ Claude API is ready for ChatterFix AI Team!")
    else:
        print("❌ Please check your API key configuration")
    print("=" * 60)
