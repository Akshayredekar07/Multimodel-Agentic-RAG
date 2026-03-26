'use client';

import { Message } from '@/lib/types';
import { useChatContext } from '@/context/ChatContext';
import styles from './MessageBubble.module.css';

interface MessageBubbleProps {
  message: Message;
}

function formatTimestamp(date: Date): string {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function renderMarkdown(text: string): string {
  const lines = text.split('\n');
  const result: string[] = [];
  let inList = false;
  let listType: 'ul' | 'ol' = 'ul';

  for (let i = 0; i < lines.length; i++) {
    let line = lines[i];

    // Apply inline formatting
    line = line
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/`([^`]+)`/g, '<code>$1</code>');

    // Ordered list item: "1. something"
    const olMatch = line.match(/^\d+\.\s+(.*)/);
    // Unordered list item: "- something"
    const ulMatch = line.match(/^-\s+(.*)/);
    // Blockquote: "> something"
    const bqMatch = line.match(/^>\s+(.*)/);

    if (olMatch) {
      if (!inList || listType !== 'ol') {
        if (inList) result.push(listType === 'ul' ? '</ul>' : '</ol>');
        result.push('<ol>');
        inList = true;
        listType = 'ol';
      }
      result.push(`<li>${olMatch[1]}</li>`);
    } else if (ulMatch) {
      if (!inList || listType !== 'ul') {
        if (inList) result.push(listType === 'ul' ? '</ul>' : '</ol>');
        result.push('<ul>');
        inList = true;
        listType = 'ul';
      }
      result.push(`<li>${ulMatch[1]}</li>`);
    } else {
      // Close list if we were in one
      if (inList) {
        result.push(listType === 'ul' ? '</ul>' : '</ol>');
        inList = false;
      }

      if (bqMatch) {
        result.push(`<blockquote>${bqMatch[1]}</blockquote>`);
      } else if (line.trim() === '') {
        result.push('<br/>');
      } else {
        result.push(`<p>${line}</p>`);
      }
    }
  }

  // Close any open list
  if (inList) {
    result.push(listType === 'ul' ? '</ul>' : '</ol>');
  }

  return result.join('');
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const { dispatch } = useChatContext();
  const isUser = message.role === 'user';

  const handleShowCitations = () => {
    if (message.citations && message.citations.length > 0) {
      dispatch({ type: 'SET_CITATIONS', payload: message.citations });
    }
  };

  return (
    <div className={`${styles.bubble} ${isUser ? styles.user : styles.assistant}`}>
      <div className={styles.avatar}>
        {isUser ? '👤' : '🤖'}
      </div>
      <div className={styles.content}>
        <div
          className={styles.messageBody}
          dangerouslySetInnerHTML={
            isUser
              ? undefined
              : { __html: renderMarkdown(message.content) }
          }
        >
          {isUser ? message.content : undefined}
        </div>
        <div className={styles.meta}>
          <span className={styles.timestamp}>
            {formatTimestamp(message.timestamp)}
          </span>
          {!isUser && message.citations && message.citations.length > 0 && (
            <span className={styles.citationBadge} onClick={handleShowCitations}>
              📄 {message.citations.length} source{message.citations.length > 1 ? 's' : ''}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
