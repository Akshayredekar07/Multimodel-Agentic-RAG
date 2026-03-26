'use client';

import Sidebar from '@/components/Sidebar';
import ChatArea from '@/components/ChatArea';
import DocumentUpload from '@/components/DocumentUpload';
import CitationsPanel from '@/components/CitationsPanel';
import styles from './page.module.css';

export default function Home() {
  return (
    <div className={styles.main}>
      <Sidebar />
      <div className={styles.content}>
        <div className={styles.center}>
          <ChatArea />
        </div>
        <div className={styles.rightPanel}>
          <DocumentUpload />
          <CitationsPanel />
        </div>
      </div>
    </div>
  );
}
