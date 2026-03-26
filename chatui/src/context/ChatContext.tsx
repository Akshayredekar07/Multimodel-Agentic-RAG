'use client';

import React, { createContext, useContext, useReducer, useCallback } from 'react';
import { Chat, Message, Citation, UploadedDocument } from '@/lib/types';

interface ChatState {
  chats: Chat[];
  activeChatId: string | null;
  messages: Message[];
  documents: UploadedDocument[];
  activeCitations: Citation[];
  isLoading: boolean;
  isSidebarOpen: boolean;
}

type ChatAction =
  | { type: 'SET_CHATS'; payload: Chat[] }
  | { type: 'SET_ACTIVE_CHAT'; payload: { chatId: string; messages: Message[] } }
  | { type: 'NEW_CHAT'; payload: Chat }
  | { type: 'ADD_USER_MESSAGE'; payload: Message }
  | { type: 'ADD_ASSISTANT_MESSAGE'; payload: Message }
  | { type: 'SET_CITATIONS'; payload: Citation[] }
  | { type: 'CLEAR_CITATIONS' }
  | { type: 'ADD_DOCUMENT'; payload: UploadedDocument }
  | { type: 'UPDATE_DOCUMENT'; payload: { id: string; updates: Partial<UploadedDocument> } }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'TOGGLE_SIDEBAR' }
  | { type: 'UPDATE_CHAT_TITLE'; payload: { chatId: string; title: string } };

const initialState: ChatState = {
  chats: [],
  activeChatId: null,
  messages: [],
  documents: [],
  activeCitations: [],
  isLoading: false,
  isSidebarOpen: true,
};

function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'SET_CHATS':
      return { ...state, chats: action.payload };
    case 'SET_ACTIVE_CHAT':
      return {
        ...state,
        activeChatId: action.payload.chatId,
        messages: action.payload.messages,
        activeCitations: [],
      };
    case 'NEW_CHAT':
      return {
        ...state,
        chats: [action.payload, ...state.chats],
        activeChatId: action.payload.id,
        messages: [],
        activeCitations: [],
      };
    case 'ADD_USER_MESSAGE':
      return { ...state, messages: [...state.messages, action.payload] };
    case 'ADD_ASSISTANT_MESSAGE':
      return { ...state, messages: [...state.messages, action.payload] };
    case 'SET_CITATIONS':
      return { ...state, activeCitations: action.payload };
    case 'CLEAR_CITATIONS':
      return { ...state, activeCitations: [] };
    case 'ADD_DOCUMENT':
      return { ...state, documents: [...state.documents, action.payload] };
    case 'UPDATE_DOCUMENT':
      return {
        ...state,
        documents: state.documents.map((d) =>
          d.id === action.payload.id ? { ...d, ...action.payload.updates } : d
        ),
      };
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'TOGGLE_SIDEBAR':
      return { ...state, isSidebarOpen: !state.isSidebarOpen };
    case 'UPDATE_CHAT_TITLE':
      return {
        ...state,
        chats: state.chats.map((c) =>
          c.id === action.payload.chatId ? { ...c, title: action.payload.title } : c
        ),
      };
    default:
      return state;
  }
}

interface ChatContextValue {
  state: ChatState;
  dispatch: React.Dispatch<ChatAction>;
}

const ChatContext = createContext<ChatContextValue | undefined>(undefined);

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(chatReducer, initialState);

  return (
    <ChatContext.Provider value={{ state, dispatch }}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChatContext() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChatContext must be used within a ChatProvider');
  }
  return context;
}
