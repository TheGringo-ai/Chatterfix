# Fix It Fred - Universal AI Assistant

## 🤖 Your Personal & Standalone AI Assistant

Fix It Fred is now a **Universal AI Assistant** that serves as both your personal AI helper for ChatterFix CMMS **and** a standalone AI service that can integrate into **any application**.

## 🌟 Key Features

### 🔧 **For You (ChatterFix CMMS)**
- ✅ **Personal AI Assistant** for ChatterFix development and operations
- ✅ **Multi-Provider Support** (OpenAI, Anthropic, Google, xAI, Ollama)
- ✅ **CMMS Context Awareness** for work orders, assets, and maintenance
- ✅ **Real-time Integration** with your existing ChatterFix workflow

### 🌐 **For Any Application**
- ✅ **Universal API** for easy integration into any app
- ✅ **SDK Support** (Python, JavaScript/TypeScript)
- ✅ **Web Components** for instant UI integration
- ✅ **Conversation Memory** with app-specific configurations
- ✅ **Plugin System** for custom integrations

## 🚀 Quick Start

### Start Fix It Fred Universal AI
```bash
# Start as standalone service
python3 fix_it_fred_universal_ai.py

# Or specify port
PORT=8010 python3 fix_it_fred_universal_ai.py
```

### Access Points
- **Web Interface**: http://localhost:8010
- **API Documentation**: http://localhost:8010/docs
- **Health Check**: http://localhost:8010/health

## 📋 API Endpoints

### Universal Chat API
```bash
POST /api/universal/chat
```

```json
{
  "message": "Your question here",
  "provider": "anthropic",
  "context": "Optional context",
  "conversation_id": "optional-conversation-id"
}
```

### App Registration
```bash
POST /api/integrations/register
```

```json
{
  "app_id": "your-app-id",
  "app_name": "Your App Name",
  "custom_instructions": "Custom AI behavior for your app"
}
```

### App-Specific Chat
```bash
POST /api/apps/{app_id}/chat
```

## 🛠️ SDK Integration

### Python SDK
```python
from fix_it_fred_sdk import FixItFredSDK, FixItFredChat

# Simple chat
fred = FixItFredChat(provider="anthropic")
response = fred.ask("Hello! How are you?")
print(response)

# Advanced SDK
sdk = FixItFredSDK()
sdk.register_app(
    app_name="My Application",
    custom_instructions="You are integrated into my app"
)

result = sdk.chat(
    message="Help me with this task",
    provider="anthropic",
    context="User needs assistance"
)
```

### JavaScript SDK
```javascript
import { FixItFredSDK, FixItFredChat } from './fix_it_fred_sdk.js';

// Simple chat
const fred = new FixItFredChat('anthropic');
const response = await fred.ask('Hello! How are you?');
console.log(response);

// Advanced SDK
const sdk = new FixItFredSDK();
await sdk.registerApp({
    appName: 'My Web App',
    customInstructions: 'You are integrated into my web application'
});

const result = await sdk.chat({
    message: 'Help me with this task',
    provider: 'anthropic'
});
```

### React Hook
```jsx
import { useFixItFred } from './fix_it_fred_sdk.js';

function MyComponent() {
    const { ask, loading, error } = useFixItFred();
    
    const handleSubmit = async (message) => {
        const response = await ask(message);
        console.log(response);
    };
    
    return (
        <div>
            {loading && <p>Loading...</p>}
            {error && <p>Error: {error}</p>}
            <button onClick={() => handleSubmit("Hello!")}>
                Ask Fix It Fred
            </button>
        </div>
    );
}
```

### Web Component
```html
<!-- Just add this to your HTML -->
<fix-it-fred-chat></fix-it-fred-chat>
```

## 🔌 Integration Examples

### Discord Bot
```python
from fix_it_fred_sdk import FixItFredSDK
import discord

fred = FixItFredSDK()
fred.register_app(app_name="Discord Bot")

@bot.command()
async def ask(ctx, *, question):
    result = fred.chat(message=question, conversation_id=str(ctx.author.id))
    await ctx.send(result['response'])
```

### Flask Web App
```python
from flask import Flask, request, jsonify
from fix_it_fred_sdk import WebAppIntegration

app = Flask(__name__)
fred_integration = WebAppIntegration("My Web App")

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    result = fred_integration.handle_user_query(data['message'])
    return jsonify(result)
```

### CLI Tool
```bash
# Using the CLI directly
python3 -m fix_it_fred_examples cli "What's the weather like?"

# Or create custom CLI
from fix_it_fred_sdk import FixItFredChat
fred = FixItFredChat()
response = fred.ask("Help me with Python")
```

## 🎯 AI Providers

Fix It Fred supports multiple AI providers:

| Provider | Models | Strengths |
|----------|--------|-----------|
| **Anthropic Claude** | claude-3-5-sonnet, claude-3-opus, claude-3-haiku | Best for reasoning, analysis, coding |
| **OpenAI GPT** | gpt-4o, gpt-4, gpt-3.5-turbo | General purpose, creative tasks |
| **xAI Grok** | grok-beta, grok-vision-beta | Real-time data, humor, personality |
| **Google Gemini** | gemini-1.5-pro, gemini-1.5-flash | Multimodal, fast responses |
| **Local Ollama** | llama3.2, qwen2.5, codegemma | Privacy, offline usage |

## 🔧 Configuration

### Environment Variables
```bash
# API Keys (optional - only for providers you want to use)
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export GOOGLE_API_KEY="your-google-key"
export XAI_API_KEY="your-xai-key"
# Ollama runs locally, no key needed

# Service Configuration
export PORT=8010  # Default port for Fix It Fred Universal
```

### App Registration
```python
# Register your app for custom configurations
config = {
    "app_name": "Your Application",
    "allowed_providers": ["anthropic", "openai"],
    "default_provider": "anthropic",
    "custom_instructions": "You are integrated into my application. Be helpful and concise."
}
```

## 📊 Features & Capabilities

### 🧠 **AI Intelligence**
- **Multi-Provider Support**: Switch between AI providers based on task
- **Context Awareness**: Maintains conversation context and app-specific knowledge
- **Conversation Memory**: Tracks conversations across sessions
- **Custom Instructions**: App-specific AI behavior configuration

### 🔗 **Integration**
- **Universal API**: RESTful API for any programming language
- **SDK Support**: Native Python and JavaScript/TypeScript SDKs
- **Web Components**: Drop-in UI components
- **React Hooks**: Ready-to-use React integration
- **CLI Tools**: Command-line interface for automation

### 🛡️ **Enterprise Ready**
- **App Registration**: Manage multiple application integrations
- **Usage Statistics**: Track API usage and performance
- **Conversation Tracking**: Audit trail and conversation history
- **Health Monitoring**: Service health and status endpoints
- **Caching**: Intelligent response caching for performance

### 📱 **Platforms Supported**
- ✅ **Web Applications** (React, Vue, Angular, vanilla JS)
- ✅ **Mobile Apps** (via REST API)
- ✅ **Desktop Applications** (Electron, Tauri, native)
- ✅ **Chat Bots** (Discord, Slack, Telegram, etc.)
- ✅ **CLI Tools** and automation scripts
- ✅ **Jupyter Notebooks** with magic commands
- ✅ **Any application** that can make HTTP requests

## 🎨 Use Cases

### **For ChatterFix CMMS (Your Personal Assistant)**
- 🔧 **Maintenance Guidance**: "How should I prioritize these work orders?"
- 📊 **Data Analysis**: "Analyze our asset maintenance patterns"
- 🤖 **Code Help**: "Help me debug this Python function"
- 📋 **Process Optimization**: "Suggest improvements for our CMMS workflow"

### **For Other Applications**
- 💬 **Customer Support**: AI-powered chat for your website
- 📚 **Educational Apps**: Intelligent tutoring and help systems
- 🎮 **Gaming**: NPCs with AI personalities
- 📊 **Business Intelligence**: AI analysis of data and reports
- 🔧 **Development Tools**: AI coding assistants for IDEs
- 📱 **Mobile Apps**: Voice assistants and chat features

## 🚀 Deployment Options

### **Development**
```bash
# Local development
python3 fix_it_fred_universal_ai.py
```

### **Production**
```bash
# Docker deployment
docker build -t fix-it-fred-universal .
docker run -p 8010:8010 fix-it-fred-universal

# Or with environment variables
docker run -p 8010:8010 \
  -e ANTHROPIC_API_KEY="your-key" \
  -e OPENAI_API_KEY="your-key" \
  fix-it-fred-universal
```

### **Cloud Deployment**
- ✅ Deploy to any cloud provider (AWS, GCP, Azure, etc.)
- ✅ Kubernetes ready
- ✅ Auto-scaling support
- ✅ Load balancer compatible

## 📈 Performance & Monitoring

### **Built-in Analytics**
- 📊 **Usage Statistics**: API calls, provider usage, response times
- 💾 **Cache Performance**: Hit rates, cache size, performance metrics
- 🔍 **Conversation Analytics**: Active conversations, message counts
- 🏥 **Health Monitoring**: Service uptime, provider availability

### **Endpoints**
- `GET /api/stats` - Usage statistics
- `GET /health` - Service health
- `GET /api/integrations` - Registered applications

## 🎯 Benefits

### **For You**
- 🤖 **Personal AI Assistant** always available for ChatterFix tasks
- 🔧 **CMMS Expertise** with understanding of maintenance workflows
- ⚡ **Instant Help** for coding, analysis, and problem-solving

### **For Integration**
- 🚀 **Quick Integration** - Add AI to any app in minutes
- 🎛️ **Flexible Configuration** - Customize AI behavior per application
- 📈 **Scalable** - Handle multiple apps and thousands of users
- 💰 **Cost Effective** - Share AI infrastructure across projects

## 🆘 Support & Documentation

- 📖 **API Documentation**: http://localhost:8010/docs
- 🧪 **Interactive Testing**: http://localhost:8010/redoc
- 💻 **Example Code**: See `fix_it_fred_examples.py`
- 🛠️ **SDK Reference**: Python and JavaScript SDKs included

## 🎉 Ready to Use!

Fix It Fred Universal AI Assistant is **ready for production use** with:
- ✅ **Standalone Service** running on http://localhost:8010
- ✅ **Web Interface** for immediate testing
- ✅ **Complete API** with documentation
- ✅ **SDKs** for Python and JavaScript
- ✅ **Integration Examples** for common platforms
- ✅ **Your Personal Assistant** for ChatterFix CMMS

**Start integrating AI into your applications today with Fix It Fred!** 🚀