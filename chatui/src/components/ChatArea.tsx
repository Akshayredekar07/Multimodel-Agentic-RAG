'use client';

import { useState, useRef, useEffect, useCallback, KeyboardEvent } from 'react';
import { useChatContext } from '@/context/ChatContext';
import { sendMessage, createChat } from '@/lib/mockApi';
import { Message } from '@/lib/types';
import MessageBubble from './MessageBubble';
import styles from './ChatArea.module.css';

const suggestions = [
  'How does RAG work?',
  'Explain vector embeddings',
  'What are transformers?',
  'Summarize my documents',
];

function generateId(): string {
  return Math.random().toString(36).substring(2, 15);
}

export default function ChatArea() {
  const { state, dispatch } = useChatContext();
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [state.messages, isTyping, scrollToBottom]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
    }
  }, [input]);

  const handleSend = useCallback(async (messageText?: string) => {
    const text = messageText || input.trim();
    if (!text || state.isLoading) return;

    let chatId = state.activeChatId;

    // Create a new chat if none is active
    if (!chatId) {
      const chat = await createChat();
      dispatch({ type: 'NEW_CHAT', payload: chat });
      chatId = chat.id;
      // Update the title
      dispatch({
        type: 'UPDATE_CHAT_TITLE',
        payload: { chatId, title: text.substring(0, 50) + (text.length > 50 ? '...' : '') },
      });
    }

    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    };

    dispatch({ type: 'ADD_USER_MESSAGE', payload: userMessage });
    setInput('');
    setIsTyping(true);
    dispatch({ type: 'SET_LOADING', payload: true });

    try {
      const assistantMessage = await sendMessage(chatId, text);
      dispatch({ type: 'ADD_ASSISTANT_MESSAGE', payload: assistantMessage });
      if (assistantMessage.citations) {
        dispatch({ type: 'SET_CITATIONS', payload: assistantMessage.citations });
      }
    } catch {
      const errMsg: Message = {
        id: generateId(),
        role: 'assistant',
        content: 'Sorry, something went wrong. Please try again.',
        timestamp: new Date(),
      };
      dispatch({ type: 'ADD_ASSISTANT_MESSAGE', payload: errMsg });
    } finally {
      setIsTyping(false);
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [input, state.activeChatId, state.isLoading, dispatch]);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const activeChat = state.chats.find((c) => c.id === state.activeChatId);

  return (
    <div className={styles.chatArea}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <button
            className={styles.toggleBtn}
            onClick={() => dispatch({ type: 'TOGGLE_SIDEBAR' })}
          >
            ☰
          </button>
          <span className={styles.chatTitle}>
            {activeChat?.title || 'MultiModal RAG'}
          </span>
        </div>
        <div className={styles.headerRight}>
          <button className={styles.headerBtn}>
            🔍 Search
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className={styles.messages}>
        {state.messages.length === 0 ? (
          <div className={styles.emptyState}>
            <div className={styles.emptyIcon}>⚡</div>
            <h2 className={styles.emptyTitle}>MultiModal RAG Assistant</h2>
            <p className={styles.emptySubtitle}>
              Upload documents and ask questions. I&apos;ll retrieve relevant content
              and provide answers with source citations.
            </p>
            <div className={styles.suggestionGrid}>
              {suggestions.map((s) => (
                <button
                  key={s}
                  className={styles.suggestion}
                  onClick={() => handleSend(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className={styles.messagesInner}>
            {state.messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {isTyping && (
              <div className={styles.typingIndicator}>
                <div className={styles.typingAvatar}>🤖</div>
                <div className={styles.typingDots}>
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className={styles.inputArea}>
        <div className={styles.inputWrapper}>
          <div className={styles.inputContainer}>
            <textarea
              ref={textareaRef}
              className={styles.textInput}
              placeholder="Ask a question about your documents..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              disabled={state.isLoading}
            />
          </div>
          <button
            className={styles.sendBtn}
            onClick={() => handleSend()}
            disabled={!input.trim() || state.isLoading}
          >
            ➤
          </button>
        </div>
        <div className={styles.inputHint}>
          Press Enter to send · Shift+Enter for new line
        </div>
      </div>
    </div>
  );
}
