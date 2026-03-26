'use client';

import { useState, useRef, useCallback, DragEvent, ChangeEvent } from 'react';
import { useChatContext } from '@/context/ChatContext';
import { uploadDocument } from '@/lib/mockApi';
import styles from './DocumentUpload.module.css';

const ACCEPTED_TYPES = [
  'application/pdf',
  'image/png',
  'image/jpeg',
  'image/webp',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
];

const ACCEPTED_EXTENSIONS = '.pdf,.png,.jpg,.jpeg,.webp,.docx';

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getStatusIcon(status: string): string {
  switch (status) {
    case 'ready': return '✅';
    case 'uploading': return '⬆️';
    case 'processing': return '⚙️';
    case 'error': return '❌';
    default: return '📄';
  }
}

export default function DocumentUpload() {
  const { state, dispatch } = useChatContext();
  const [isDragActive, setIsDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(async (files: FileList | File[]) => {
    const fileArray = Array.from(files).filter(
      (f) => ACCEPTED_TYPES.includes(f.type) || f.name.endsWith('.pdf') || f.name.endsWith('.docx')
    );

    for (const file of fileArray) {
      const tempDoc = {
        id: Math.random().toString(36).substring(2, 15),
        name: file.name,
        type: file.type,
        size: file.size,
        status: 'uploading' as const,
        progress: 0,
        uploadedAt: new Date(),
      };
      dispatch({ type: 'ADD_DOCUMENT', payload: tempDoc });

      try {
        const result = await uploadDocument(file, (progress) => {
          dispatch({
            type: 'UPDATE_DOCUMENT',
            payload: {
              id: tempDoc.id,
              updates: {
                progress,
                status: progress < 100 ? 'uploading' : 'processing',
              },
            },
          });
        });
        dispatch({
          type: 'UPDATE_DOCUMENT',
          payload: {
            id: tempDoc.id,
            updates: { status: result.status, progress: 100 },
          },
        });
      } catch {
        dispatch({
          type: 'UPDATE_DOCUMENT',
          payload: { id: tempDoc.id, updates: { status: 'error' } },
        });
      }
    }
  }, [dispatch]);

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    setIsDragActive(true);
  };

  const handleDragLeave = (e: DragEvent) => {
    e.preventDefault();
    setIsDragActive(false);
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setIsDragActive(false);
    if (e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(e.target.files);
      e.target.value = '';
    }
  };

  return (
    <div className={styles.upload}>
      <div className={styles.uploadTitle}>
        📁 Documents
      </div>

      <div
        className={`${styles.dropzone} ${isDragActive ? styles.active : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
      >
        <div className={styles.dropzoneIcon}>📤</div>
        <div className={styles.dropzoneText}>
          Drop files here or click to browse
        </div>
        <div className={styles.dropzoneHint}>
          PDF, PNG, JPG, DOCX supported
        </div>
        <input
          ref={inputRef}
          type="file"
          className={styles.dropzoneInput}
          accept={ACCEPTED_EXTENSIONS}
          multiple
          onChange={handleInputChange}
          onClick={(e) => e.stopPropagation()}
        />
      </div>

      {state.documents.length > 0 && (
        <div className={styles.documentList}>
          {state.documents.map((doc) => (
            <div key={doc.id} className={styles.documentItem}>
              <div className={`${styles.docIcon} ${styles[doc.status]}`}>
                {getStatusIcon(doc.status)}
              </div>
              <div className={styles.docInfo}>
                <div className={styles.docName}>{doc.name}</div>
                <div className={styles.docMeta}>
                  <span>{formatFileSize(doc.size)}</span>
                </div>
                {(doc.status === 'uploading' || doc.status === 'processing') && (
                  <div className={styles.progressBar}>
                    <div
                      className={styles.progressFill}
                      style={{ width: `${doc.progress}%` }}
                    />
                  </div>
                )}
              </div>
              <span className={`${styles.statusBadge} ${styles[doc.status]}`}>
                {doc.status}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
