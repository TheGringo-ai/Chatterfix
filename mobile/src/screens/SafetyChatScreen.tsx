/**
 * SafetyChatScreen - Chat with SafetyFred AI Coach
 *
 * 24/7 AI safety advisor for:
 * - Safety questions and guidance
 * - Hazard analysis
 * - Regulation interpretation
 * - PPE recommendations
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const quickPrompts = [
  "What PPE do I need for welding?",
  "Explain lockout/tagout procedures",
  "How to report a near miss?",
  "Chemical spill response steps",
];

export default function SafetyChatScreen() {
  const { user } = useAuth();
  const scrollViewRef = useRef<ScrollView>(null);

  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: "Hey there! I'm SafetyFred, your AI safety coach. I've got 30+ years of experience keeping workers safe. What can I help you with today? Ask me anything about safety procedures, PPE, hazards, or regulations.",
      timestamp: new Date(),
    },
  ]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Scroll to bottom when messages change
    setTimeout(() => {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }, 100);
  }, [messages]);

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText('');
    setLoading(true);

    try {
      const response = await api.post('/safety/chat', {
        message: text.trim(),
        context: null,
      });

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data?.response || "I'm here to help with safety questions. Could you rephrase that?",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      // Demo response
      const demoResponses: Record<string, string> = {
        'ppe': "Great question about PPE! Here are the basics:\n\n1. **Hard Hat** - Required in all construction and production areas\n2. **Safety Glasses** - Always wear when there's a risk of flying debris\n3. **High-Vis Vest** - Required in forklift traffic areas\n4. **Steel-Toe Boots** - Required in all industrial areas\n5. **Gloves** - Match the glove type to the hazard\n\nRemember: PPE is your last line of defense, not your first. Always look for ways to eliminate hazards first!",
        'lockout': "Lockout/Tagout (LOTO) is critical! Here's the procedure:\n\n1. **Notify** affected employees\n2. **Shut down** the equipment properly\n3. **Isolate** all energy sources\n4. **Apply** your personal lock and tag\n5. **Verify** the equipment is de-energized\n6. **Perform** the work\n7. **Remove** locks in reverse order\n\nNEVER assume equipment is off - always verify!\n\nRefer to OSHA 1910.147 for detailed requirements.",
        'default': "That's an important safety topic. Here are some key points to remember:\n\n- When in doubt, stop work and ask\n- Report all hazards immediately\n- Never take shortcuts with safety\n- Your wellbeing is the top priority\n\nWant me to go into more detail on any specific aspect?",
      };

      let responseText = demoResponses['default'];
      const lowerText = text.toLowerCase();
      if (lowerText.includes('ppe') || lowerText.includes('equipment')) {
        responseText = demoResponses['ppe'];
      } else if (lowerText.includes('lockout') || lowerText.includes('tagout') || lowerText.includes('loto')) {
        responseText = demoResponses['lockout'];
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: responseText,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <KeyboardAvoidingView
        style={styles.keyboardView}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={100}
      >
        {/* Messages */}
        <ScrollView
          ref={scrollViewRef}
          style={styles.messagesContainer}
          contentContainerStyle={styles.messagesContent}
        >
          {messages.map((message) => (
            <View
              key={message.id}
              style={[
                styles.messageBubble,
                message.role === 'user' ? styles.userBubble : styles.assistantBubble,
              ]}
            >
              {message.role === 'assistant' && (
                <Text style={styles.assistantIcon}>🦺</Text>
              )}
              <Text style={styles.messageText}>{message.content}</Text>
            </View>
          ))}

          {loading && (
            <View style={[styles.messageBubble, styles.assistantBubble]}>
              <Text style={styles.assistantIcon}>🦺</Text>
              <ActivityIndicator color="#3498db" size="small" />
              <Text style={styles.typingText}>SafetyFred is thinking...</Text>
            </View>
          )}
        </ScrollView>

        {/* Quick Prompts */}
        {messages.length <= 2 && (
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            style={styles.quickPromptsContainer}
            contentContainerStyle={styles.quickPromptsContent}
          >
            {quickPrompts.map((prompt, index) => (
              <TouchableOpacity
                key={index}
                style={styles.quickPromptButton}
                onPress={() => sendMessage(prompt)}
              >
                <Text style={styles.quickPromptText}>{prompt}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        )}

        {/* Input Area */}
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            placeholder="Ask SafetyFred anything..."
            placeholderTextColor="#666"
            value={inputText}
            onChangeText={setInputText}
            multiline
            maxLength={500}
            onSubmitEditing={() => sendMessage(inputText)}
          />
          <TouchableOpacity
            style={[styles.sendButton, !inputText.trim() && styles.sendButtonDisabled]}
            onPress={() => sendMessage(inputText)}
            disabled={!inputText.trim() || loading}
          >
            <Text style={styles.sendButtonText}>Send</Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0c0c0c',
  },
  keyboardView: {
    flex: 1,
  },
  messagesContainer: {
    flex: 1,
  },
  messagesContent: {
    padding: 16,
    paddingBottom: 8,
  },
  messageBubble: {
    maxWidth: '85%',
    borderRadius: 16,
    padding: 12,
    marginBottom: 12,
  },
  userBubble: {
    backgroundColor: '#1e3c72',
    alignSelf: 'flex-end',
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    backgroundColor: '#1a1a2e',
    alignSelf: 'flex-start',
    borderBottomLeftRadius: 4,
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'flex-start',
  },
  assistantIcon: {
    fontSize: 20,
    marginRight: 8,
    marginTop: 2,
  },
  messageText: {
    color: '#fff',
    fontSize: 15,
    lineHeight: 22,
    flex: 1,
  },
  typingText: {
    color: '#a0a0a0',
    fontSize: 14,
    fontStyle: 'italic',
    marginLeft: 8,
  },
  quickPromptsContainer: {
    maxHeight: 50,
    marginBottom: 8,
  },
  quickPromptsContent: {
    paddingHorizontal: 16,
    alignItems: 'center',
  },
  quickPromptButton: {
    backgroundColor: '#1a1a2e',
    borderRadius: 20,
    paddingVertical: 8,
    paddingHorizontal: 16,
    marginRight: 8,
    borderWidth: 1,
    borderColor: '#3498db',
  },
  quickPromptText: {
    color: '#3498db',
    fontSize: 13,
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 12,
    paddingBottom: 8,
    borderTopWidth: 1,
    borderTopColor: '#2d2d4a',
    backgroundColor: '#0c0c0c',
  },
  input: {
    flex: 1,
    backgroundColor: '#1a1a2e',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    color: '#fff',
    fontSize: 15,
    maxHeight: 100,
    marginRight: 8,
  },
  sendButton: {
    backgroundColor: '#27ae60',
    borderRadius: 20,
    paddingHorizontal: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: '#1a1a2e',
  },
  sendButtonText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '600',
  },
});
