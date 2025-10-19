#!/usr/bin/env python3
"""
Fix It Fred Integration Examples
===============================
Real-world examples of integrating Fix It Fred into different applications
"""

import asyncio
import json
from fix_it_fred_sdk import FixItFredSDK, FixItFredChat, WebAppIntegration

# Example 1: Discord Bot Integration
def discord_bot_example():
    """
    Example Discord bot using Fix It Fred
    Note: Requires discord.py library
    """
    try:
        import discord
        from discord.ext import commands
    except ImportError:
        print("❌ discord.py not installed. Run: pip install discord.py")
        return
    
    # Initialize Fix It Fred
    fred = FixItFredSDK()
    fred.register_app(
        app_name="Discord Bot",
        custom_instructions="You are integrated into a Discord bot. Keep responses under 2000 characters and use Discord markdown when helpful. Be friendly and helpful for community discussions."
    )
    
    # Discord bot setup
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix='!fred ', intents=intents)
    
    @bot.event
    async def on_ready():
        print(f'🤖 Fix It Fred Discord Bot logged in as {bot.user}')
    
    @bot.command(name='ask')
    async def ask_fred(ctx, *, question):
        """Ask Fix It Fred a question"""
        async with ctx.typing():
            result = fred.chat(
                message=question,
                context=f"Discord server: {ctx.guild.name if ctx.guild else 'DM'}, Channel: {ctx.channel.name if hasattr(ctx.channel, 'name') else 'DM'}",
                conversation_id=str(ctx.author.id),
                provider="anthropic"
            )
            
            if result.get("success"):
                response = result["response"]
                # Split long responses for Discord's character limit
                if len(response) > 2000:
                    chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                    for chunk in chunks:
                        await ctx.send(chunk)
                else:
                    await ctx.send(response)
            else:
                await ctx.send(f"❌ Error: {result.get('error', 'Unknown error')}")
    
    @bot.command(name='provider')
    async def change_provider(ctx, provider_name):
        """Change AI provider"""
        valid_providers = ["anthropic", "openai", "xai", "google", "ollama"]
        if provider_name.lower() in valid_providers:
            await ctx.send(f"✅ Switched to {provider_name} for this server")
        else:
            await ctx.send(f"❌ Invalid provider. Valid options: {', '.join(valid_providers)}")
    
    print("🔧 Discord bot example created (use bot.run('YOUR_BOT_TOKEN') to start)")
    return bot

# Example 2: Flask Web App Integration
def flask_web_app_example():
    """
    Example Flask web application with Fix It Fred integration
    """
    try:
        from flask import Flask, render_template_string, request, jsonify
    except ImportError:
        print("❌ Flask not installed. Run: pip install flask")
        return
    
    app = Flask(__name__)
    
    # Initialize Fix It Fred
    web_integration = WebAppIntegration("Flask Demo App")
    
    @app.route('/')
    def home():
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Fix It Fred Web Integration</title>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <h1>🤖 Fix It Fred Web Integration Demo</h1>
                <div class="row mt-4">
                    <div class="col-md-8">
                        <div id="chatMessages" class="border p-3 mb-3" style="height: 400px; overflow-y: auto;">
                            <div class="text-muted">
                                <strong>Fix It Fred:</strong> Hello! I'm integrated into this web app. How can I help you?
                            </div>
                        </div>
                        <div class="input-group">
                            <input type="text" id="messageInput" class="form-control" placeholder="Ask me anything..." onkeypress="if(event.key==='Enter') sendMessage()">
                            <button class="btn btn-primary" onclick="sendMessage()">Send</button>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <h5>AI Providers</h5>
                        <select id="providerSelect" class="form-select mb-3">
                            <option value="anthropic">Anthropic Claude</option>
                            <option value="openai">OpenAI GPT</option>
                            <option value="xai">xAI Grok</option>
                            <option value="google">Google Gemini</option>
                        </select>
                        <h5>Features</h5>
                        <ul>
                            <li>Multi-provider AI</li>
                            <li>Conversation memory</li>
                            <li>Context awareness</li>
                            <li>Real-time responses</li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <script>
            async function sendMessage() {
                const messageInput = document.getElementById('messageInput');
                const providerSelect = document.getElementById('providerSelect');
                const chatMessages = document.getElementById('chatMessages');
                
                const message = messageInput.value.trim();
                if (!message) return;
                
                // Add user message
                chatMessages.innerHTML += `
                    <div class="mt-2">
                        <strong>You:</strong> ${message}
                    </div>
                `;
                
                messageInput.value = '';
                chatMessages.scrollTop = chatMessages.scrollHeight;
                
                // Add loading message
                chatMessages.innerHTML += `
                    <div class="mt-2 text-muted" id="loading">
                        <strong>Fix It Fred:</strong> <em>Thinking...</em>
                    </div>
                `;
                chatMessages.scrollTop = chatMessages.scrollHeight;
                
                try {
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            message: message,
                            provider: providerSelect.value
                        })
                    });
                    
                    const result = await response.json();
                    
                    // Remove loading
                    document.getElementById('loading').remove();
                    
                    // Add AI response
                    chatMessages.innerHTML += `
                        <div class="mt-2">
                            <strong>Fix It Fred (${result.provider}):</strong> ${result.response}
                        </div>
                    `;
                    
                } catch (error) {
                    document.getElementById('loading').remove();
                    chatMessages.innerHTML += `
                        <div class="mt-2 text-danger">
                            <strong>Error:</strong> ${error.message}
                        </div>
                    `;
                }
                
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
            </script>
        </body>
        </html>
        ''')
    
    @app.route('/api/chat', methods=['POST'])
    def chat_endpoint():
        data = request.get_json()
        
        result = web_integration.handle_user_query(
            user_message=data['message'],
            user_context=f"Web app user, Provider: {data.get('provider', 'anthropic')}"
        )
        
        return jsonify(result)
    
    print("🌐 Flask web app example created (use app.run() to start)")
    return app

# Example 3: CLI Tool Integration
def cli_tool_example():
    """
    Example command-line tool with Fix It Fred
    """
    import argparse
    
    def main():
        parser = argparse.ArgumentParser(description='Fix It Fred CLI Tool')
        parser.add_argument('message', help='Message to send to Fix It Fred')
        parser.add_argument('--provider', default='anthropic', 
                          choices=['anthropic', 'openai', 'xai', 'google', 'ollama'],
                          help='AI provider to use')
        parser.add_argument('--context', help='Additional context for the query')
        parser.add_argument('--conversation-id', help='Conversation ID for tracking')
        
        args = parser.parse_args()
        
        # Initialize Fix It Fred
        fred = FixItFredChat(provider=args.provider)
        
        print(f"🤖 Fix It Fred CLI ({args.provider})")
        print("=" * 40)
        
        # Send message
        response = fred.ask(args.message, args.context)
        print(f"\nResponse: {response}")
        
        # If conversation ID provided, show conversation stats
        if args.conversation_id:
            fred.conversation_id = args.conversation_id
            print(f"\nConversation ID: {args.conversation_id}")
    
    return main

# Example 4: Slack Bot Integration
def slack_bot_example():
    """
    Example Slack bot integration
    Note: Requires slack-sdk library
    """
    try:
        from slack_sdk import WebClient
        from slack_sdk.socket_mode import SocketModeClient
        from slack_sdk.socket_mode.request import SocketModeRequest
        from slack_sdk.socket_mode.response import SocketModeResponse
    except ImportError:
        print("❌ slack-sdk not installed. Run: pip install slack-sdk")
        return
    
    # Initialize Fix It Fred
    fred = FixItFredSDK()
    fred.register_app(
        app_name="Slack Bot",
        custom_instructions="You are integrated into a Slack workspace. Provide helpful, professional responses suitable for workplace communication. Keep responses concise and use Slack formatting when appropriate."
    )
    
    def process_slack_message(client: WebClient, request: SocketModeRequest):
        if request.type == "events_api":
            event = request.payload["event"]
            
            if event["type"] == "app_mention" or (event["type"] == "message" and "bot_id" not in event):
                # Extract message text
                text = event.get("text", "")
                user_id = event.get("user")
                channel_id = event.get("channel")
                
                # Remove bot mention from text
                if "<@" in text:
                    text = text.split(">", 1)[-1].strip()
                
                if text:
                    # Get AI response
                    result = fred.chat(
                        message=text,
                        context="Slack workspace communication",
                        conversation_id=user_id,
                        provider="anthropic"
                    )
                    
                    if result.get("success"):
                        # Send response to Slack
                        client.chat_postMessage(
                            channel=channel_id,
                            text=result["response"],
                            thread_ts=event.get("ts")  # Reply in thread if it's a thread message
                        )
        
        # Acknowledge the request
        response = SocketModeResponse(envelope_id=request.envelope_id)
        return response
    
    print("🔧 Slack bot example created")
    return process_slack_message

# Example 5: Jupyter Notebook Integration
def jupyter_notebook_example():
    """
    Example Jupyter notebook integration with magic commands
    """
    try:
        from IPython.core.magic import Magics, magics_class, line_magic, cell_magic
        from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring
    except ImportError:
        print("❌ IPython not available (not in Jupyter environment)")
        return
    
    @magics_class
    class FixItFredMagics(Magics):
        
        def __init__(self, shell=None):
            super().__init__(shell)
            self.fred = FixItFredChat()
            self.fred.ask("I'm now integrated into a Jupyter notebook environment. I can help with data science, coding, and analysis tasks.")
        
        @line_magic
        @magic_arguments()
        @argument('--provider', default='anthropic', help='AI provider to use')
        @argument('message', nargs='*', help='Message to send')
        def fred(self, line):
            """Ask Fix It Fred a question"""
            args = parse_argstring(self.fred, line)
            message = ' '.join(args.message)
            
            if not message:
                return "Please provide a message to send to Fix It Fred"
            
            self.fred.switch_provider(args.provider)
            response = self.fred.ask(message, "Jupyter notebook environment")
            
            print(f"🤖 Fix It Fred ({args.provider}): {response}")
        
        @cell_magic
        def fred_analyze(self, line, cell):
            """Analyze code with Fix It Fred"""
            context = f"Please analyze this code and provide insights:\n\n{cell}"
            response = self.fred.ask(context, "Code analysis in Jupyter notebook")
            
            print(f"🤖 Code Analysis:\n{response}")
    
    # Register magic commands
    try:
        get_ipython().register_magic_function(FixItFredMagics)
        print("✅ Fix It Fred magic commands registered!")
        print("Usage: %fred your message here")
        print("       %%fred_analyze")
        print("       your code here")
    except NameError:
        print("❌ Not in IPython/Jupyter environment")
    
    return FixItFredMagics

# Example 6: API Testing Tool
def api_testing_example():
    """
    Test all Fix It Fred API endpoints
    """
    async def test_all_endpoints():
        print("🧪 Testing Fix It Fred Universal AI Assistant")
        print("=" * 50)
        
        # Initialize SDK
        fred = FixItFredSDK()
        
        # Test health check
        print("1. Testing health check...")
        health = fred.health_check()
        print(f"   Status: {health.get('status')}")
        print(f"   Version: {health.get('version')}")
        
        # Test providers
        print("\n2. Testing providers endpoint...")
        providers = fred.get_providers()
        if providers.get('success'):
            print(f"   Available providers: {list(providers['providers'].keys())}")
        
        # Test registration
        print("\n3. Testing app registration...")
        registration = fred.register_app(
            app_name="Test App",
            custom_instructions="This is a test application"
        )
        print(f"   Registration success: {registration.get('success')}")
        print(f"   App ID: {registration.get('app_id')}")
        
        # Test chat with different providers
        test_message = "Hello! This is a test message."
        providers_to_test = ["anthropic", "openai"]
        
        for provider in providers_to_test:
            print(f"\n4. Testing {provider} chat...")
            result = fred.chat(
                message=test_message,
                provider=provider,
                context="API testing"
            )
            
            if result.get('success'):
                response_preview = result['response'][:100] + "..." if len(result['response']) > 100 else result['response']
                print(f"   ✅ {provider}: {response_preview}")
                print(f"   Cached: {result.get('cached', False)}")
            else:
                print(f"   ❌ {provider}: {result.get('error')}")
        
        # Test conversation tracking
        print("\n5. Testing conversation tracking...")
        conv_id = "test-conversation-123"
        
        # Send multiple messages in conversation
        for i, msg in enumerate(["Hello", "How are you?", "What can you do?"]):
            result = fred.chat(
                message=msg,
                conversation_id=conv_id,
                provider="anthropic"
            )
            if result.get('success'):
                print(f"   Message {i+1}: ✅")
        
        # Get conversation history
        conversation = fred.get_conversation(conv_id)
        if conversation.get('success'):
            print(f"   Conversation messages: {conversation['message_count']}")
        
        # Test stats
        print("\n6. Testing statistics...")
        stats = fred.get_stats()
        if stats.get('success'):
            print(f"   Cache hits: {stats['cache_stats'].get('hits', 0)}")
            print(f"   Cache misses: {stats['cache_stats'].get('misses', 0)}")
            print(f"   Active conversations: {stats['active_conversations']}")
        
        print("\n✅ All tests completed!")
    
    return test_all_endpoints

# Main execution
if __name__ == "__main__":
    print("🤖 Fix It Fred Integration Examples")
    print("=" * 50)
    
    examples = {
        "1": ("Discord Bot", discord_bot_example),
        "2": ("Flask Web App", flask_web_app_example),
        "3": ("CLI Tool", cli_tool_example),
        "4": ("Slack Bot", slack_bot_example),
        "5": ("Jupyter Notebook", jupyter_notebook_example),
        "6": ("API Testing", api_testing_example)
    }
    
    print("Available examples:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")
    
    choice = input("\nEnter example number to run (or 'all' for API test): ")
    
    if choice == "all" or choice == "6":
        test_func = api_testing_example()
        asyncio.run(test_func())
    elif choice in examples:
        name, func = examples[choice]
        print(f"\n🚀 Running {name} example...")
        result = func()
        if result:
            print(f"✅ {name} example created successfully!")
    else:
        print("❌ Invalid choice")