/**
 * @file documentsService.js
 * @description Client-side service for document (knowledge-base) management.
 *
 * Unlike other services that call the Django REST API, this service uses
 * localStorage as a simulated backend. Documents represent files uploaded
 * for the RAG (Retrieval-Augmented Generation) pipeline used by Ignite Buddy.
 *
 * Key concepts:
 *   - Documents are persisted in localStorage under STORAGE_KEY.
 *   - Uploaded file Blobs are kept in an in-memory Map (`fileBlobRegistry`)
 *     so they can be opened as browser object-URLs until the page is refreshed.
 *   - New uploads start in "Processing" status and transition to "Ready"
 *     after a simulated 2-second delay (mimicking chunking / vectorization).
 *
 * Data flow:
 *   AddDocuments page / useDocuments hook → documentsService → localStorage
 *
 * @exports {Function} formatFileSize - Converts byte count to human-readable string.
 * @exports {Object}   documentsService - CRUD methods for document management.
 */

/** localStorage key used to persist the document list across sessions */
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

/**
 * Reads the document list from localStorage, seeding it with INITIAL_DOCUMENTS
 * on first access or when the stored data is corrupted / empty.
 * @returns {Array<Object>} The stored document list.
 */
function getStoredDocuments() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      // First visit — seed localStorage with demo documents
      localStorage.setItem(STORAGE_KEY, JSON.stringify(INITIAL_DOCUMENTS));
      return INITIAL_DOCUMENTS;
    }
    const parsed = JSON.parse(raw);
    // Fall back to seed data if parse yields non-array or empty array
    return Array.isArray(parsed) && parsed.length > 0 ? parsed : INITIAL_DOCUMENTS;
  } catch {
    return INITIAL_DOCUMENTS;
  }
}

/**
 * Persists the document list to localStorage.
 * Silently catches quota-exceeded errors so the app doesn't crash.
 * @param {Array<Object>} docs - The full document list to save.
 */
function saveStoredDocuments(docs) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(docs));
  } catch {
    // Storage quota fallback
  }
}

/**
 * Converts a raw byte count into a human-readable size string (e.g. "2.4 MB").
 * Uses base-1024 (binary) unit progression: B → KB → MB → GB.
 * @param {number} bytes - File size in bytes.
 * @returns {string} Formatted file size string.
 */
export function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  // Determine the appropriate unit index using logarithm
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export const documentsService = {
  /**
   * Retrieves all documents. Adds a small artificial delay to simulate network latency.
   * @returns {Promise<Array<Object>>} The full list of stored documents.
   */
  getDocuments: async () => {
    await new Promise((resolve) => setTimeout(resolve, 80));
    return getStoredDocuments();
  },

  /**
   * Uploads a new document to the local knowledge base.
   * Extracts text content (for TXT files) or generates a metadata stub (for PDFs),
   * persists the document in localStorage, and schedules a 2-second simulated
   * "processing → ready" transition to mimic RAG vectorization.
   *
   * @param {Object} params
   * @param {File}   params.file        - The browser File object to upload.
   * @param {string} [params.name]      - Display name (falls back to filename without extension).
   * @param {string} [params.audience]  - Target audience label (default: 'All students').
   * @param {string} [params.description] - Optional description of the document.
   * @returns {Promise<Object>} The newly created document record.
   */
  uploadDocument: async ({ file, name, audience = 'All students', description = '' }) => {
    // Simulate upload network delay
    await new Promise((resolve) => setTimeout(resolve, 350));
    const current = getStoredDocuments();

    const isPdf = file.name.toLowerCase().endsWith('.pdf');
    const fileType = isPdf ? 'PDF' : 'TXT';
    // Estimate the number of RAG chunks based on ~40KB per chunk, with a minimum of 4
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

    // Generate a unique ID using timestamp to avoid collisions in localStorage
    const docId = `doc-rag-${Date.now()}`;

    // Register file in memory for native PDF viewing
    fileBlobRegistry.set(docId, file);

    // Use provided name, or strip file extension to create a clean display title
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

    // Prepend the new document so it appears first in the list
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

  /**
   * Deletes a document by ID from localStorage and the in-memory blob registry.
   * @param {string} docId - The document's unique ID.
   * @returns {Promise<{success: boolean, id: string}>}
   */
  deleteDocument: async (docId) => {
    await new Promise((resolve) => setTimeout(resolve, 100));
    const current = getStoredDocuments();
    const filtered = current.filter((d) => d.id !== docId);
    saveStoredDocuments(filtered);
    fileBlobRegistry.delete(docId);
    return { success: true, id: docId };
  },

  /**
   * Retrieves a single document's full details by ID.
   * @param {string} docId - The document's unique ID.
   * @returns {Promise<Object>} The document object.
   * @throws {Error} If the document is not found.
   */
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
