const STORAGE_KEY = 'tcs_admin_documents_rag';

const INITIAL_DOCUMENTS = [
  {
    id: 'doc-rag-001',
    name: 'Semester Timetable',
    fileName: 'Semester_Timetable.pdf',
    fileType: 'PDF',
    sizeBytes: 2516582,
    sizeFormatted: '2.4 MB',
    uploadedAt: 'Today',
    status: 'Ready', // 'Uploaded' | 'Processing' | 'Ready' | 'Failed'
    chunks: 42,
    indexed: true,
    audience: 'All students',
    description: 'Updated timetable for all departments',
    vectorStore: 'SQLite local knowledge base',
  },
  {
    id: 'doc-rag-002',
    name: 'Campus Guidelines & Conduct',
    fileName: 'Campus_Guidelines_2026.pdf',
    fileType: 'PDF',
    sizeBytes: 1258291,
    sizeFormatted: '1.2 MB',
    uploadedAt: 'Yesterday',
    status: 'Ready',
    chunks: 28,
    indexed: true,
    audience: 'All students',
    description: 'Exam rules, laboratory safety, and campus conduct rules',
    vectorStore: 'SQLite local knowledge base',
  },
  {
    id: 'doc-rag-003',
    name: 'AI & Data Science Curriculum Notes',
    fileName: 'Curriculum_Notes_AI_DS.txt',
    fileType: 'TXT',
    sizeBytes: 460800,
    sizeFormatted: '450 KB',
    uploadedAt: '3 days ago',
    status: 'Ready',
    chunks: 16,
    indexed: true,
    audience: 'Third year',
    description: 'Course syllabus and core lecture knowledge reference',
    vectorStore: 'SQLite local knowledge base',
  },
];

function getStoredDocuments() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(INITIAL_DOCUMENTS));
      return INITIAL_DOCUMENTS;
    }
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) && parsed.length > 0 ? parsed : INITIAL_DOCUMENTS;
  } catch {
    return INITIAL_DOCUMENTS;
  }
}

function saveStoredDocuments(docs) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(docs));
  } catch {
    // Storage quota fallback
  }
}

export function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export const documentsService = {
  getDocuments: async () => {
    await new Promise((resolve) => setTimeout(resolve, 80));
    return getStoredDocuments();
  },

  uploadDocument: async ({ file, audience = 'All students', description = '' }) => {
    await new Promise((resolve) => setTimeout(resolve, 150));
    const current = getStoredDocuments();

    const isPdf = file.name.toLowerCase().endsWith('.pdf');
    const fileType = isPdf ? 'PDF' : 'TXT';
    const estimatedChunks = Math.max(4, Math.floor(file.size / 60000));

    const newDoc = {
      id: `doc-rag-${Date.now()}`,
      name: file.name.replace(/\.[^/.]+$/, ''),
      fileName: file.name,
      fileType,
      sizeBytes: file.size,
      sizeFormatted: formatFileSize(file.size),
      uploadedAt: 'Just now',
      status: 'Processing', // starts in Processing state
      chunks: estimatedChunks,
      indexed: false,
      audience,
      description: description.trim() || `Uploaded ${fileType} knowledge source`,
      vectorStore: 'SQLite local knowledge base',
    };

    const updated = [newDoc, ...current];
    saveStoredDocuments(updated);

    // Simulate RAG text extraction & indexing completion after 2.5 seconds
    setTimeout(() => {
      const activeDocs = getStoredDocuments();
      const target = activeDocs.find((d) => d.id === newDoc.id);
      if (target) {
        target.status = 'Ready';
        target.indexed = true;
        saveStoredDocuments(activeDocs);
      }
    }, 2500);

    return newDoc;
  },

  deleteDocument: async (docId) => {
    await new Promise((resolve) => setTimeout(resolve, 100));
    const current = getStoredDocuments();
    const filtered = current.filter((d) => d.id !== docId);
    saveStoredDocuments(filtered);
    return { success: true, id: docId };
  },

  getDocumentDetails: async (docId) => {
    await new Promise((resolve) => setTimeout(resolve, 60));
    const current = getStoredDocuments();
    const doc = current.find((d) => d.id === docId);
    if (!doc) throw new Error('Document not found');
    return doc;
  },
};
