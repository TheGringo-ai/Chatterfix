#!/usr/bin/env python3
"""
Comprehensive Chat Widget Fix Script
Find and fix ALL broken chat widgets across ChatterFix templates and files
"""

import os
import re
import glob

def find_broken_chat_widgets():
    """Find all files with broken chat widget implementations"""
    
    broken_files = []
    patterns_to_find = [
        r'fetch.*[\'"]\/api\/ai\/chat[\'"]',
        r'fetch.*[\'"]\/api\/ai[\'"](?!.*fred)',  # /api/ai but not fix-it-fred
        r'\/api\/ai\/chat',
        r'sendMessage.*function',
        r'toggleChat.*function'
    ]
    
    search_paths = [
        '/Users/fredtaylor/Desktop/Projects/ai-tools/core/cmms/',
        '/Users/fredtaylor/Desktop/Projects/ai-tools/Chatterfix/',
        '/Users/fredtaylor/Desktop/Projects/ai-tools/'
    ]
    
    file_extensions = ['*.py', '*.html', '*.js', '*.ts']
    
    print("🔍 Scanning for broken chat widgets...")
    
    for search_path in search_paths:
        if not os.path.exists(search_path):
            continue
            
        for ext in file_extensions:
            for file_path in glob.glob(os.path.join(search_path, '**', ext), recursive=True):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    for pattern in patterns_to_find:
                        if re.search(pattern, content, re.IGNORECASE):
                            broken_files.append({
                                'file': file_path,
                                'pattern': pattern,
                                'matches': len(re.findall(pattern, content, re.IGNORECASE))
                            })
                            break
                            
                except Exception as e:
                    continue
    
    return broken_files

def fix_chat_widget_in_file(file_path):
    """Fix broken chat widgets in a specific file"""
    
    print(f"🔧 Fixing chat widgets in: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        # Fix 1: Replace /api/ai/chat with Fix It Fred endpoint
        content = re.sub(
            r'fetch\s*\(\s*[\'"]\/api\/ai\/chat[\'"]',
            "fetch('/api/fix-it-fred/troubleshoot'",
            content
        )
        
        # Fix 2: Replace /api/ai with Fix It Fred endpoint (but not if already fix-it-fred)
        content = re.sub(
            r'fetch\s*\(\s*[\'"]\/api\/ai[\'"](?!.*fred)',
            "fetch('/api/fix-it-fred/troubleshoot'",
            content
        )
        
        # Fix 3: Update sendMessage function to use Fix It Fred format
        sendmessage_pattern = r'(function\s+sendMessage\s*\(\s*\)\s*\{[^}]*?)fetch\s*\([^)]*\)\s*\{[^}]*method[^}]*POST[^}]*\}[^}]*\}[^}]*catch[^}]*\}'
        
        def replace_sendmessage(match):
            return """function sendMessage() {
    const input = document.getElementById('chat-input') || document.getElementById('ai-input');
    const message = input.value.trim();
    if (!message) return;
    
    // Add user message
    if (typeof addMessage === 'function') addMessage(message, 'user');
    input.value = '';
    
    // Show typing indicator
    if (typeof showTypingIndicator === 'function') showTypingIndicator();
    
    // 🔧 FIXED: Use working Fix It Fred endpoint
    fetch('/api/fix-it-fred/troubleshoot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            equipment: 'ChatterFix CMMS Platform',
            issue_description: `User question from chat widget: "${message}". Please provide helpful information about ChatterFix CMMS features and capabilities.`
        })
    })
    .then(response => response.json())
    .then(data => {
        if (typeof hideTypingIndicator === 'function') hideTypingIndicator();
        
        if (data.success && data.data && data.data.response) {
            // Transform Fred's response for chat context
            let aiResponse = data.data.response
                .replace(/🔧 Hi there! Fred here\\./g, '👋 Hi! I\\'m Fix It Fred, your ChatterFix AI assistant.')
                .replace(/I can help troubleshoot your ChatterFix CMMS Platform issue!/g, 'I\\'m here to help you with ChatterFix CMMS!')
                .replace(/For detailed step-by-step guidance.*?upgrade to Fix It Fred Pro\\./g, 'ChatterFix CMMS includes comprehensive AI-powered maintenance management features.')
                .replace(/Basic troubleshooting:/g, 'Here\\'s how ChatterFix can help:')
                .replace(/- Fred$/g, '');
            
            if (typeof addMessage === 'function') {
                addMessage(aiResponse, 'assistant');
            }
        } else {
            if (typeof addMessage === 'function') {
                addMessage('👋 Hi! I\\'m Fix It Fred, your ChatterFix AI assistant. I\\'m here to help you with ChatterFix CMMS. What would you like to know?', 'assistant');
            }
        }
    })
    .catch(error => {
        console.error('Chat Error:', error);
        if (typeof hideTypingIndicator === 'function') hideTypingIndicator();
        if (typeof addMessage === 'function') {
            addMessage('👋 Hi! I\\'m Fix It Fred, your ChatterFix AI assistant. I\\'m here to help you with ChatterFix CMMS - our AI-powered maintenance management platform. What would you like to know?', 'assistant');
        }
    });
}"""
        
        # Apply the sendMessage fix
        content = re.sub(sendmessage_pattern, replace_sendmessage, content, flags=re.DOTALL)
        
        # Fix 4: Replace error messages
        content = content.replace(
            'I apologize, but I encountered an issue. Please try again or contact our support team at support@chatterfix.com',
            '👋 Hi! I\'m Fix It Fred, your ChatterFix AI assistant. I\'m here to help you with ChatterFix CMMS!'
        )
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed {file_path}")
            return True
        else:
            print(f"ℹ️ No changes needed in {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def main():
    """Main function to find and fix all broken chat widgets"""
    
    print("🔧 ChatterFix Chat Widget Universal Fix")
    print("=" * 50)
    
    # Find all broken chat widgets
    broken_files = find_broken_chat_widgets()
    
    if not broken_files:
        print("✅ No broken chat widgets found!")
        return
    
    print(f"🔍 Found {len(broken_files)} files with potential chat widget issues:")
    for item in broken_files:
        print(f"  📄 {item['file']} ({item['matches']} matches)")
    
    print("\n🔧 Fixing all broken chat widgets...")
    
    fixed_count = 0
    processed_files = set()
    
    for item in broken_files:
        file_path = item['file']
        if file_path not in processed_files:
            if fix_chat_widget_in_file(file_path):
                fixed_count += 1
            processed_files.add(file_path)
    
    print(f"\n🎉 Fix completed!")
    print(f"✅ Fixed {fixed_count} files")
    print(f"📁 Processed {len(processed_files)} unique files")
    
    print("\n📋 Next steps:")
    print("1. Deploy the fixed files to production")
    print("2. Test all chat widgets")
    print("3. Verify Fix It Fred integration works")

if __name__ == "__main__":
    main()