# 🤖 AI Team Integration Package

This package provides Claude + Grok collaboration capabilities for any Python application.

## 📁 Package Contents

- `ai_team_integration.py` - Main AI collaboration framework
- `example_ai_app.py` - Complete example implementation
- `requirements.txt` - All dependencies needed
- `README.md` - This documentation

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export OPENAI_API_KEY="your-openai-key"
   export XAI_API_KEY="your-grok-key"  
   export ANTHROPIC_API_KEY="your-claude-key"
   ```

3. **Basic usage:**
   ```python
   from ai_team_integration import AITeamIntegration, AITeamChatbot
   
   # Initialize AI team
   ai_team = AITeamIntegration()
   chatbot = AITeamChatbot()
   
   # Chat with AI team (async)
   response = await chatbot.chat("How do I optimize my database?")
   
   # Solve complex problems
   solution = await ai_team.solve_with_ai_team("Build scalable microservices")
   ```

4. **Run example app:**
   ```bash
   python example_ai_app.py
   # Visit http://localhost:8000 for interactive demo
   ```

## 🔧 Integration Features

- **Multi-AI Collaboration**: Claude + Grok working together
- **Automatic AI Selection**: Best AI chosen based on confidence scores
- **Task Management**: Track and organize AI tasks
- **Chat Interface**: Interactive conversations with AI team
- **Problem Solving**: Complex multi-step problem resolution
- **Status Monitoring**: Track AI team availability and performance

## 📚 Main Classes

- `AITeamIntegration` - Core collaboration framework
- `AITeamChatbot` - Chat interface with AI selection
- `AITask` - Task management and tracking
- `AIResponse` - Structured AI response handling

## 🌐 Web Interface

The example app includes a complete web interface with:
- Real-time AI team chat
- Problem solving interface
- Quick AI consultation
- AI team status monitoring

## 📋 Requirements

- Python 3.8+
- OpenAI API access
- xAI (Grok) API access  
- Anthropic (Claude) API access
- FastAPI (for web features)

## 💡 Use Cases

Perfect for adding AI collaboration to:
- Web applications
- Desktop software
- API services
- Data analysis tools
- Development workflows
- Customer support systems

---

Created by ChatterFix AI Team Integration