#!/usr/bin/env python3
"""
Terminal AI Chat - Claude + ChatGPT Collaboration Interface
Allows real-time conversation between Claude and ChatGPT via terminal
"""
import requests
import json
import os
import sys
from datetime import datetime

class TerminalAIChat:
    def __init__(self):
        self.session_id = f"claude-chatgpt-terminal-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.conversation_history = []
        
    def chat_with_openai(self, message, context=""):
        """Send message to ChatGPT via ChatterFix AI system"""
        try:
            # Try main ChatterFix endpoint
            response = requests.post(
                "https://chatterfix.com/api/ai/chat-enhanced",
                json={
                    "message": message,
                    "agent": "developer",
                    "context": f"Terminal collaboration session. {context}",
                    "session_id": self.session_id,
                    "provider": "openai"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "No response received")
            else:
                return f"Error: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"Connection error: {str(e)}"
    
    def save_conversation(self, speaker, message):
        """Save conversation to history"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = {
            "timestamp": timestamp,
            "speaker": speaker,
            "message": message
        }
        self.conversation_history.append(entry)
        
        # Also save to file
        with open(f"ai_collaboration_{self.session_id}.log", "a") as f:
            f.write(f"[{timestamp}] {speaker}: {message}\n\n")
    
    def display_message(self, speaker, message):
        """Display formatted message in terminal"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if speaker == "Claude":
            print(f"\n🤖 \033[94m[{timestamp}] Claude:\033[0m")
        elif speaker == "ChatGPT":
            print(f"\n🧠 \033[92m[{timestamp}] ChatGPT:\033[0m")
        elif speaker == "User":
            print(f"\n👤 \033[93m[{timestamp}] Fred:\033[0m")
        
        print(f"{message}")
        print("-" * 80)
    
    def start_collaboration(self):
        """Start the Claude + ChatGPT collaboration session"""
        print("🚀 \033[95mChatterFix AI Collaboration Terminal\033[0m")
        print("💫 Claude + ChatGPT Working Together")
        print("📝 Session ID:", self.session_id)
        print("=" * 80)
        
        # Initial greeting to ChatGPT
        initial_message = """Hello ChatGPT! This is Claude speaking through the ChatterFix terminal. 
        
Fred wants us to collaborate on his ChatterFix CMMS vision. I've been working on:
- Microservices architecture with 8+ services
- Manager AI Agent for executive decisions  
- Voice-to-text and OCR capabilities
- Advanced maintenance prediction systems

What ideas do you have for enhancing this platform? Let's work together to make Fred's vision a reality!"""

        self.display_message("Claude", initial_message)
        self.save_conversation("Claude", initial_message)
        
        # Send to ChatGPT
        chatgpt_response = self.chat_with_openai(initial_message, "Initial collaboration greeting from Claude")
        self.display_message("ChatGPT", chatgpt_response)
        self.save_conversation("ChatGPT", chatgpt_response)
        
        # Interactive loop
        while True:
            try:
                print("\n" + "=" * 80)
                print("Commands: 'claude: <message>' | 'chatgpt: <message>' | 'quit' | 'history'")
                user_input = input("\n💬 Enter command: ").strip()
                
                if user_input.lower() == 'quit':
                    print("\n👋 Ending AI collaboration session...")
                    break
                elif user_input.lower() == 'history':
                    self.show_history()
                elif user_input.startswith('claude:'):
                    message = user_input[7:].strip()
                    self.display_message("Claude", f"[Simulated] {message}")
                    self.save_conversation("Claude", message)
                    
                    # Send Claude's message to ChatGPT
                    context = f"Claude says: {message}. Please respond as ChatGPT collaborating on ChatterFix CMMS."
                    chatgpt_response = self.chat_with_openai(context, "Claude's message forwarded")
                    self.display_message("ChatGPT", chatgpt_response)
                    self.save_conversation("ChatGPT", chatgpt_response)
                    
                elif user_input.startswith('chatgpt:'):
                    message = user_input[8:].strip()
                    chatgpt_response = self.chat_with_openai(message, "Direct message to ChatGPT")
                    self.display_message("ChatGPT", chatgpt_response)
                    self.save_conversation("ChatGPT", chatgpt_response)
                else:
                    # Treat as Fred's message to both AIs
                    self.display_message("User", user_input)
                    self.save_conversation("User", user_input)
                    
                    chatgpt_response = self.chat_with_openai(user_input, "Message from Fred")
                    self.display_message("ChatGPT", chatgpt_response)
                    self.save_conversation("ChatGPT", chatgpt_response)
                    
            except KeyboardInterrupt:
                print("\n\n👋 Session ended by user")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    def show_history(self):
        """Display conversation history"""
        print("\n📚 \033[96mConversation History:\033[0m")
        print("=" * 80)
        for entry in self.conversation_history[-10:]:  # Show last 10 messages
            speaker_color = {
                "Claude": "\033[94m",
                "ChatGPT": "\033[92m", 
                "User": "\033[93m"
            }.get(entry["speaker"], "\033[0m")
            
            print(f"{speaker_color}[{entry['timestamp']}] {entry['speaker']}:\033[0m")
            print(f"{entry['message'][:200]}{'...' if len(entry['message']) > 200 else ''}")
            print()

if __name__ == "__main__":
    chat = TerminalAIChat()
    chat.start_collaboration()