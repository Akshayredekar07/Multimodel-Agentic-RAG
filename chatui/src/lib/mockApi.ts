import { Chat, Message, Citation, UploadedDocument } from './types';

function generateId(): string {
  return Math.random().toString(36).substring(2, 15);
}

const mockCitations: Citation[] = [
  {
    id: 'cit-1',
    documentName: 'Machine_Learning_Fundamentals.pdf',
    pageNumber: 42,
    chunkIndex: 3,
    relevanceScore: 0.94,
    snippet: 'Neural networks consist of interconnected layers of nodes that process information using weighted connections. The learning process involves adjusting these weights through backpropagation...',
  },
  {
    id: 'cit-2',
    documentName: 'Deep_Learning_Architecture.pdf',
    pageNumber: 18,
    chunkIndex: 1,
    relevanceScore: 0.87,
    snippet: 'Transformer architectures have revolutionized natural language processing by introducing self-attention mechanisms that allow the model to weigh the importance of different input tokens...',
  },
  {
    id: 'cit-3',
    documentName: 'RAG_Systems_Overview.docx',
    pageNumber: 7,
    chunkIndex: 2,
    relevanceScore: 0.81,
    snippet: 'Retrieval-Augmented Generation combines the strengths of retrieval-based and generative approaches, grounding model responses in specific document evidence to reduce hallucinations...',
  },
];

const mockResponses = [
  "Based on the retrieved documents, **Retrieval-Augmented Generation (RAG)** works by first retrieving relevant document chunks from a vector store, then feeding those chunks as context to a large language model.\n\nThe key steps are:\n1. **Document Ingestion** — Documents are split into chunks, embedded into vectors, and stored in a vector database.\n2. **Query Retrieval** — When a user asks a question, the query is embedded and similar chunks are retrieved.\n3. **Augmented Generation** — The retrieved chunks are combined with the user's query to generate a grounded response.\n\nThis approach significantly reduces hallucinations by anchoring responses in actual document content.",
  "According to the documents in the knowledge base, **transformer architectures** use self-attention mechanisms to process sequences in parallel, unlike traditional RNNs.\n\nKey advantages include:\n- **Parallel processing** of input tokens\n- **Long-range dependency** capture through attention\n- **Scalability** to very large datasets\n\nThe multi-head attention mechanism allows the model to attend to different representation subspaces at different positions simultaneously.",
  "The uploaded documents indicate that **vector embeddings** are dense numerical representations of text that capture semantic meaning.\n\nWhen two passages discuss similar concepts, their embedding vectors will be close together in the vector space, enabling semantic search that goes beyond keyword matching.\n\n> This is fundamental to how RAG systems retrieve relevant context for answering questions.",
];

let mockChats: Chat[] = [
  {
    id: 'chat-1',
    title: 'How does RAG work?',
    messages: [
      {
        id: 'msg-1',
        role: 'user',
        content: 'Can you explain how RAG systems work?',
        timestamp: new Date(Date.now() - 3600000),
      },
      {
        id: 'msg-2',
        role: 'assistant',
        content: mockResponses[0],
        timestamp: new Date(Date.now() - 3500000),
        citations: [mockCitations[0], mockCitations[2]],
      },
    ],
    createdAt: new Date(Date.now() - 3600000),
    updatedAt: new Date(Date.now() - 3500000),
  },
  {
    id: 'chat-2',
    title: 'Transformer architectures',
    messages: [
      {
        id: 'msg-3',
        role: 'user',
        content: 'Tell me about transformer architectures',
        timestamp: new Date(Date.now() - 86400000),
      },
      {
        id: 'msg-4',
        role: 'assistant',
        content: mockResponses[1],
        timestamp: new Date(Date.now() - 86300000),
        citations: [mockCitations[1]],
      },
    ],
    createdAt: new Date(Date.now() - 86400000),
    updatedAt: new Date(Date.now() - 86300000),
  },
  {
    id: 'chat-3',
    title: 'Vector embeddings explained',
    messages: [],
    createdAt: new Date(Date.now() - 172800000),
    updatedAt: new Date(Date.now() - 172800000),
  },
];

export async function getRecentChats(): Promise<Chat[]> {
  await delay(300);
  return [...mockChats].sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime());
}

export async function getChatById(chatId: string): Promise<Chat | undefined> {
  await delay(200);
  return mockChats.find((c) => c.id === chatId);
}

export async function createChat(): Promise<Chat> {
  await delay(200);
  const newChat: Chat = {
    id: generateId(),
    title: 'New conversation',
    messages: [],
    createdAt: new Date(),
    updatedAt: new Date(),
  };
  mockChats = [newChat, ...mockChats];
  return newChat;
}

export async function sendMessage(
  chatId: string,
  content: string
): Promise<Message> {
  await delay(1500 + Math.random() * 1000);

  const responseIndex = Math.floor(Math.random() * mockResponses.length);
  const numCitations = Math.floor(Math.random() * 3) + 1;
  const shuffledCitations = [...mockCitations]
    .sort(() => Math.random() - 0.5)
    .slice(0, numCitations);

  const assistantMessage: Message = {
    id: generateId(),
    role: 'assistant',
    content: mockResponses[responseIndex],
    timestamp: new Date(),
    citations: shuffledCitations,
  };

  const chat = mockChats.find((c) => c.id === chatId);
  if (chat) {
    if (chat.messages.length === 0) {
      chat.title = content.substring(0, 50) + (content.length > 50 ? '...' : '');
    }
    chat.messages.push(assistantMessage);
    chat.updatedAt = new Date();
  }

  return assistantMessage;
}

export async function uploadDocument(
  file: File,
  onProgress: (progress: number) => void
): Promise<UploadedDocument> {
  const doc: UploadedDocument = {
    id: generateId(),
    name: file.name,
    type: file.type,
    size: file.size,
    status: 'uploading',
    progress: 0,
    uploadedAt: new Date(),
  };

  // Simulate upload progress
  for (let i = 0; i <= 100; i += 10) {
    await delay(150);
    doc.progress = i;
    doc.status = i < 100 ? 'uploading' : 'processing';
    onProgress(i);
  }

  await delay(500);
  doc.status = 'ready';
  doc.progress = 100;
  onProgress(100);

  return doc;
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
