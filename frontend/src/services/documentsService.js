const STORAGE_KEY = 'ignite_buddy_documents_rag';

// In-memory registry for uploaded file Blobs so real uploaded PDFs can be opened in browser tabs
const fileBlobRegistry = new Map();

const INITIAL_DOCUMENTS = [
  {
    id: 'doc-rag-001',
    name: 'Semester Timetable',
    fileName: 'Semester_Timetable.pdf',
    fileType: 'PDF',
    sizeBytes: 2516582,
    sizeFormatted: '2.4 MB',
    uploadedAt: 'Today',
    status: 'Ready', // 'Processing' | 'Ready' | 'Failed'
    chunks: 42,
    indexed: true,
    audience: 'All students',
    description: 'Updated timetable for all departments',
    vectorStore: 'SQLite local knowledge base',
    content: `CAMPUS ACADEMIC & EXAMINATION TIMETABLE — FALL SEMESTER 2026
Department of Computer Science, Information Technology, and Engineering

Week 1–4: Core Lectures & Laboratory Practical Sessions
Week 5: Mid-term Assessment & Quiz Period
Week 6–10: Advanced Specialization Seminars & Project Reviews
Week 11–12: Reading Week & Exam Preparation
Week 13–14: Final Semester Comprehensive Examinations

Timings: Monday through Friday: 09:00 AM – 05:00 PM
Examination Venues: Academic Blocks A, B, and Central Auditorium
Contact Campus Administration for special scheduling requirements.`,
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
    content: `CAMPUS GUIDELINES & ACADEMIC CODE OF CONDUCT (2026)

1. General Campus Etiquette
All students and staff must display campus identification while on premises. Quiet zones are observed in library study hubs and examination corridors.

2. Examination Protocol
Electronic devices other than authorized calculators must be silenced and placed in lockers. AI assistants including Ignite Buddy are placed in exam-restricted mode during assessment windows.

3. Laboratory Safety Standards
Eye protection and appropriate lab coats are mandatory in all robotics, chemistry, and hardware engineering laboratories.

4. Digital Resources & Knowledge Access
Campus OneDrive and learning management links are refreshed on a scheduled basis. Report broken or restricted resource URLs to IT support.`,
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
    content: `DEPARTMENT OF ADVANCED COMPUTING
AI & DATA SCIENCE SPECIALIZATION — LECTURE SYLLABUS & KNOWLEDGE RETRIEVAL

Module 1: Machine Learning Foundations
- Supervised and unsupervised learning architectures
- Linear regression, gradient descent, cost function optimization
- Decision trees, random forests, and ensemble methods

Module 2: Deep Learning & Neural Networks
- Perceptrons, multi-layer networks, backpropagation
- Activation functions: ReLU, Sigmoid, GeLU
- Convolutional Neural Networks (CNNs) for vision processing
- Recurrent Neural Networks (RNNs) and Long Short-Term Memory (LSTM)

Module 3: Retrieval-Augmented Generation (RAG) & Vector Databases
- Embedding models and vector spaces
- Chunking strategies: fixed size, sliding window, semantic boundaries
- Cosine similarity, Euclidean distance, approximate nearest neighbors
- Knowledge retrieval injection and hallucination mitigation`,
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

  uploadDocument: async ({ file, name, audience = 'All students', description = '' }) => {
    await new Promise((resolve) => setTimeout(resolve, 350));
    const current = getStoredDocuments();

    const isPdf = file.name.toLowerCase().endsWith('.pdf');
    const fileType = isPdf ? 'PDF' : 'TXT';
    const estimatedChunks = Math.max(4, Math.floor(file.size / 40000));

    // Read text content if .txt file
    let extractedText = '';
    if (!isPdf) {
      try {
        extractedText = await file.text();
      } catch {
        extractedText = 'Extracted text content from uploaded text document.';
      }
    } else {
      extractedText = `PDF Document: ${file.name}\nSize: ${formatFileSize(file.size)}\nStatus: Processed & Vectorized for RAG.\nReady for semantic search queries.`;
    }

    const docId = `doc-rag-${Date.now()}`;

    // Register file in memory for native PDF viewing
    fileBlobRegistry.set(docId, file);

    const docTitle = (name || '').trim() || file.name.replace(/\.[^/.]+$/, '');

    const newDoc = {
      id: docId,
      name: docTitle,
      fileName: file.name,
      fileType,
      sizeBytes: file.size,
      sizeFormatted: formatFileSize(file.size),
      uploadedAt: 'Today',
      status: 'Processing', // Starts in Processing state
      chunks: estimatedChunks,
      indexed: false,
      audience,
      description: description.trim() || `Uploaded ${fileType} knowledge source`,
      vectorStore: 'SQLite local knowledge base',
      content: extractedText,
      hasBlob: true,
    };

    const updated = [newDoc, ...current];
    saveStoredDocuments(updated);

    // Transition from Processing -> Ready for RAG after 2 seconds
    setTimeout(() => {
      const activeDocs = getStoredDocuments();
      const target = activeDocs.find((d) => d.id === docId);
      if (target) {
        target.status = 'Ready';
        target.indexed = true;
        saveStoredDocuments(activeDocs);
      }
    }, 2000);

    return newDoc;
  },

  deleteDocument: async (docId) => {
    await new Promise((resolve) => setTimeout(resolve, 100));
    const current = getStoredDocuments();
    const filtered = current.filter((d) => d.id !== docId);
    saveStoredDocuments(filtered);
    fileBlobRegistry.delete(docId);
    return { success: true, id: docId };
  },

  getDocumentDetails: async (docId) => {
    await new Promise((resolve) => setTimeout(resolve, 60));
    const current = getStoredDocuments();
    const doc = current.find((d) => d.id === docId);
    if (!doc) throw new Error('Document not found');
    return doc;
  },

  /**
   * Retrieves an active Blob/URL for opening or viewing the document
   */
  getDocumentBlobUrl: (doc) => {
    if (!doc) return null;

    // If an actual File is in memory from recent upload
    if (fileBlobRegistry.has(doc.id)) {
      const file = fileBlobRegistry.get(doc.id);
      return URL.createObjectURL(file);
    }

    // Fallback: Generate a clean text Blob if content exists
    if (doc.content) {
      const mime = doc.fileType === 'PDF' ? 'text/plain' : 'text/plain';
      const blob = new Blob([doc.content], { type: mime });
      return URL.createObjectURL(blob);
    }

    return null;
  },
};
