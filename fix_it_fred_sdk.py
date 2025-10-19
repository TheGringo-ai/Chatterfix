#!/usr/bin/env python3
"""
Fix It Fred SDK - Universal AI Assistant Integration
===================================================
Easy integration library for any Python application
"""

import requests
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

class FixItFredSDK:
    """
    Python SDK for integrating Fix It Fred Universal AI Assistant
    """
    
    def __init__(self, base_url: str = "http://localhost:8005", app_id: str = None, api_key: str = None):
        """
        Initialize Fix It Fred SDK
        
        Args:
            base_url: Base URL of Fix It Fred service
            app_id: Your application ID (optional, for app-specific features)
            api_key: Your API key (optional, for authenticated requests)
        """
        self.base_url = base_url.rstrip('/')
        self.app_id = app_id
        self.api_key = api_key
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'FixItFred-SDK/1.0'
        })
        
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}'
            })
    
    def chat(self, 
             message: str, 
             provider: str = "anthropic",
             context: str = None,
             conversation_id: str = None,
             model: str = None,
             temperature: float = 0.7,
             max_tokens: int = 2000) -> Dict[str, Any]:
        """
        Send a chat message to Fix It Fred
        
        Args:
            message: The message to send
            provider: AI provider to use ('anthropic', 'openai', 'xai', 'google', 'ollama')
            context: Additional context for the conversation
            conversation_id: ID for conversation tracking
            model: Specific model to use (optional)
            temperature: Response randomness (0.0-1.0)
            max_tokens: Maximum response length
            
        Returns:
            Dict containing the response and metadata
        """
        endpoint = f"{self.base_url}/api/universal/chat"
        
        # Use app-specific endpoint if app_id is configured
        if self.app_id:
            endpoint = f"{self.base_url}/api/apps/{self.app_id}/chat"
        
        payload = {
            "message": message,
            "provider": provider,
            "context": context,
            "conversation_id": conversation_id,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}
        
        try:
            response = self.session.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"❌ Error connecting to Fix It Fred: {str(e)}"
            }
    
    def register_app(self, 
                     app_name: str,
                     webhook_url: str = None,
                     allowed_providers: List[str] = None,
                     default_provider: str = "anthropic",
                     custom_instructions: str = None) -> Dict[str, Any]:
        """
        Register your application with Fix It Fred
        
        Args:
            app_name: Name of your application
            webhook_url: URL for webhook notifications (optional)
            allowed_providers: List of AI providers your app can use
            default_provider: Default AI provider for your app
            custom_instructions: Custom instructions for AI interactions
            
        Returns:
            Dict containing registration details including app_id
        """
        if not self.app_id:
            self.app_id = str(uuid.uuid4())
        
        payload = {
            "app_id": self.app_id,
            "app_name": app_name,
            "webhook_url": webhook_url,
            "allowed_providers": allowed_providers or ["anthropic", "openai"],
            "default_provider": default_provider,
            "custom_instructions": custom_instructions
        }
        
        try:
            response = self.session.post(f"{self.base_url}/api/integrations/register", json=payload)
            response.raise_for_status()
            result = response.json()
            
            # Store app_id for future requests
            if result.get("success"):
                self.app_id = result.get("app_id")
            
            return result
        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_providers(self) -> Dict[str, Any]:
        """
        Get all available AI providers
        
        Returns:
            Dict containing available providers and their details
        """
        try:
            response = self.session.get(f"{self.base_url}/api/providers")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get conversation history
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Dict containing conversation messages
        """
        try:
            response = self.session.get(f"{self.base_url}/api/conversations/{conversation_id}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def clear_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        Clear conversation history
        
        Args:
            conversation_id: ID of the conversation to clear
            
        Returns:
            Dict containing success status
        """
        try:
            response = self.session.delete(f"{self.base_url}/api/conversations/{conversation_id}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if Fix It Fred service is healthy
        
        Returns:
            Dict containing health status
        """
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get service statistics
        
        Returns:
            Dict containing usage statistics
        """
        try:
            response = self.session.get(f"{self.base_url}/api/stats")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }

# Convenience class for simple chat interactions
class FixItFredChat:
    """
    Simple chat interface for Fix It Fred
    """
    
    def __init__(self, provider: str = "anthropic", base_url: str = "http://localhost:8005"):
        self.sdk = FixItFredSDK(base_url=base_url)
        self.provider = provider
        self.conversation_id = str(uuid.uuid4())
    
    def ask(self, message: str, context: str = None) -> str:
        """
        Ask Fix It Fred a question and get the response text
        
        Args:
            message: Question or message
            context: Additional context
            
        Returns:
            Response text from AI
        """
        result = self.sdk.chat(
            message=message,
            context=context,
            provider=self.provider,
            conversation_id=self.conversation_id
        )
        
        if result.get("success"):
            return result.get("response", "No response received")
        else:
            return f"Error: {result.get('error', 'Unknown error')}"
    
    def switch_provider(self, provider: str):
        """
        Switch AI provider
        
        Args:
            provider: New provider to use
        """
        self.provider = provider
    
    def new_conversation(self):
        """
        Start a new conversation (clear history)
        """
        self.conversation_id = str(uuid.uuid4())

# Integration examples for different use cases
class WebAppIntegration:
    """
    Example integration for web applications
    """
    
    def __init__(self, app_name: str):
        self.fred = FixItFredSDK()
        self.app_name = app_name
        
        # Register the app
        registration = self.fred.register_app(
            app_name=app_name,
            custom_instructions="You are integrated into a web application. Provide helpful, concise responses."
        )
        
        if registration.get("success"):
            print(f"✅ {app_name} registered with Fix It Fred")
        else:
            print(f"❌ Failed to register {app_name}")
    
    def handle_user_query(self, user_message: str, user_context: str = None) -> Dict[str, Any]:
        """
        Handle a user query from the web app
        """
        return self.fred.chat(
            message=user_message,
            context=user_context,
            provider="anthropic"  # Use most reliable provider for web apps
        )

class ChatbotIntegration:
    """
    Example integration for chatbots
    """
    
    def __init__(self, bot_name: str, platform: str = "discord"):
        self.fred = FixItFredSDK()
        self.bot_name = bot_name
        self.platform = platform
        
        # Register with platform-specific instructions
        platform_instructions = {
            "discord": "You are integrated into a Discord bot. Keep responses under 2000 characters and use Discord markdown when helpful.",
            "slack": "You are integrated into a Slack bot. Use Slack formatting and keep responses concise for workplace communication.",
            "telegram": "You are integrated into a Telegram bot. Provide helpful responses suitable for mobile messaging."
        }
        
        self.fred.register_app(
            app_name=f"{bot_name} ({platform.title()} Bot)",
            custom_instructions=platform_instructions.get(platform, "You are integrated into a chatbot platform.")
        )
    
    def respond_to_message(self, message: str, user_id: str = None) -> str:
        """
        Generate bot response to user message
        """
        context = f"Platform: {self.platform}"
        if user_id:
            context += f", User ID: {user_id}"
        
        result = self.fred.chat(
            message=message,
            context=context,
            conversation_id=user_id,  # Use user_id as conversation_id for user-specific history
            provider="anthropic"
        )
        
        return result.get("response", "Sorry, I couldn't process that request.")

# Example usage
if __name__ == "__main__":
    # Simple chat example
    print("🤖 Fix It Fred SDK Example")
    print("=" * 40)
    
    # Initialize simple chat
    fred_chat = FixItFredChat(provider="anthropic")
    
    # Test basic functionality
    response = fred_chat.ask("Hello! Can you help me with Python programming?")
    print(f"Fix It Fred: {response}")
    
    # Test SDK with different provider
    fred_sdk = FixItFredSDK()
    
    result = fred_sdk.chat(
        message="What's the weather like for coding today?",
        provider="openai",
        context="This is a test of the Fix It Fred SDK"
    )
    
    if result.get("success"):
        print(f"\nOpenAI Response: {result['response']}")
        print(f"Provider: {result['provider']}")
        print(f"Cached: {result.get('cached', False)}")
    
    # Check health
    health = fred_sdk.health_check()
    print(f"\nService Status: {health.get('status')}")
    print(f"Version: {health.get('version')}")