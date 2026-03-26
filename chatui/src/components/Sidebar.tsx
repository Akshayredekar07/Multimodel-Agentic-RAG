'use client';

import { useEffect, useCallback } from 'react';
import { useChatContext } from '@/context/ChatContext';
import { getRecentChats, createChat, getChatById } from '@/lib/mockApi';
import styles from './Sidebar.module.css';

function formatTime(date: Date): string {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;
  return date.toLocaleDateString();
}

export default function Sidebar() {
  const { state, dispatch } = useChatContext();

  useEffect(() => {
    async function loadChats() {
      const chats = await getRecentChats();
      dispatch({ type: 'SET_CHATS', payload: chats });
    }
    loadChats();
  }, [dispatch]);

  const handleNewChat = useCallback(async () => {
    const chat = await createChat();
    dispatch({ type: 'NEW_CHAT', payload: chat });
  }, [dispatch]);

  const handleSelectChat = useCallback(
    async (chatId: string) => {
      const chat = await getChatById(chatId);
      if (chat) {
        dispatch({
          type: 'SET_ACTIVE_CHAT',
          payload: { chatId: chat.id, messages: chat.messages },
        });
      }
    },
    [dispatch]
  );

  return (
    <aside className={`${styles.sidebar} ${state.isSidebarOpen ? '' : styles.collapsed}`}>
      <div className={styles.header}>
        <div className={styles.logo}>
          <div className={styles.logoIcon}>⚡</div>
          <span className={styles.logoText}>MultiModal RAG</span>
        </div>
        <button className={styles.newChatBtn} onClick={handleNewChat}>
          <span>＋</span>
          New Chat
        </button>
      </div>

      <div className={styles.section}>
        <div className={styles.sectionTitle}>Recent Chats</div>
        <div className={styles.chatList}>
          {state.chats.map((chat) => (
            <div
              key={chat.id}
              className={`${styles.chatItem} ${
                state.activeChatId === chat.id ? styles.active : ''
              }`}
              onClick={() => handleSelectChat(chat.id)}
            >
              <div className={styles.chatIcon}>💬</div>
              <div className={styles.chatItemContent}>
                <div className={styles.chatTitle}>{chat.title}</div>
                <div className={styles.chatTime}>
                  {formatTime(chat.updatedAt)}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className={styles.footer}>
        <div className={styles.footerInfo}>
          Multimodal Agentic RAG v1.0
        </div>
      </div>
    </aside>
  );
}
