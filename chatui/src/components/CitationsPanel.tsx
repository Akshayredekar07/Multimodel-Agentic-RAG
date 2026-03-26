'use client';

import { useState } from 'react';
import { useChatContext } from '@/context/ChatContext';
import styles from './CitationsPanel.module.css';

function getRelevanceLevel(score: number): {
  label: string;
  className: string;
} {
  if (score >= 0.85) return { label: `${(score * 100).toFixed(0)}% match`, className: styles.relevanceHigh };
  if (score >= 0.7) return { label: `${(score * 100).toFixed(0)}% match`, className: styles.relevanceMedium };
  return { label: `${(score * 100).toFixed(0)}% match`, className: styles.relevanceLow };
}

function getDocIcon(name: string): string {
  if (name.endsWith('.pdf')) return '📕';
  if (name.endsWith('.docx') || name.endsWith('.doc')) return '📘';
  if (name.endsWith('.png') || name.endsWith('.jpg') || name.endsWith('.jpeg')) return '🖼️';
  return '📄';
}

export default function CitationsPanel() {
  const { state, dispatch } = useChatContext();
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const citations = state.activeCitations;

  if (citations.length === 0) {
    return (
      <div className={styles.panel}>
        <div className={styles.panelHeader}>
          <span className={styles.panelTitle}>
            📚 Sources & Citations
          </span>
        </div>
        <div className={styles.emptyPanel}>
          <div className={styles.emptyPanelIcon}>🔍</div>
          <div className={styles.emptyPanelText}>
            Citations will appear here when the assistant references your documents
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.panel}>
      <div className={styles.panelHeader}>
        <span className={styles.panelTitle}>
          📚 Sources
          <span className={styles.citationCount}>{citations.length}</span>
        </span>
        <button
          className={styles.clearBtn}
          onClick={() => dispatch({ type: 'CLEAR_CITATIONS' })}
        >
          Clear
        </button>
      </div>

      <div className={styles.citationList}>
        {citations.map((cit) => {
          const relevance = getRelevanceLevel(cit.relevanceScore);
          const isExpanded = expandedId === cit.id;

          return (
            <div
              key={cit.id}
              className={`${styles.citationCard} ${isExpanded ? styles.expanded : ''}`}
              onClick={() => setExpandedId(isExpanded ? null : cit.id)}
            >
              <div className={styles.citationHeader}>
                <div className={styles.citSourceIcon}>
                  {getDocIcon(cit.documentName)}
                </div>
                <div className={styles.citInfo}>
                  <div className={styles.citDocName}>{cit.documentName}</div>
                  <div className={styles.citMeta}>
                    <span>Page {cit.pageNumber}</span>
                    <span>•</span>
                    <span>Chunk {cit.chunkIndex}</span>
                  </div>
                </div>
                <span className={`${styles.relevanceBadge} ${relevance.className}`}>
                  {relevance.label}
                </span>
              </div>

              {isExpanded ? (
                <div className={styles.citSnippet}>{cit.snippet}</div>
              ) : (
                <div className={styles.snippetPreview}>{cit.snippet}</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
