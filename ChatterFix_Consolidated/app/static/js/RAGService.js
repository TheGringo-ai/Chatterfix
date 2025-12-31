// RAG Processing Service for document analysis and vector embeddings

class RAGService {
  constructor(config) {
    this.config = config;
    this.embeddingModel = config.embeddingModel || 'text-embedding-ada-002';
    this.vectorStore = config.vectorStore || 'chromadb';
    this.chunkSize = config.chunkSize || 1000;
    this.chunkOverlap = config.chunkOverlap || 200;
  }

  async processDocument(document, settings = {}) {
    try {
      // Extract text from document
      const extractedText = await this.extractText(document);
      
      // Split into chunks
      const chunks = await this.createChunks(extractedText, settings);
      
      // Generate embeddings
      const embeddings = await this.generateEmbeddings(chunks);
      
      // Extract metadata
      const metadata = await this.extractMetadata(document, extractedText);
      
      // Store in vector database
      const vectorIds = await this.storeVectors(chunks, embeddings, metadata);
      
      return {
        success: true,
        documentId: document.id,
        chunks: chunks.length,
        vectorIds,
        metadata,
        extractedText: extractedText.substring(0, 500) + '...' // Preview
      };
    } catch (error) {
      console.error('RAG processing failed:', error);
      return {
        success: false,
        error: error.message,
        documentId: document.id
      };
    }
  }

  async extractText(document) {
    const mimeType = document.type || document.metadata?.mimeType;
    
    switch (mimeType) {
      case 'text/plain':
        return this.extractTextFromPlainText(document);
      case 'application/pdf':
        return this.extractTextFromPDF(document);
      case 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        return this.extractTextFromDocx(document);
      case 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        return this.extractTextFromXlsx(document);
      case 'text/csv':
        return this.extractTextFromCSV(document);
      case 'image/jpeg':
      case 'image/png':
      case 'image/gif':
        return this.extractTextFromImage(document);
      default:
        throw new Error(`Unsupported file type: ${mimeType}`);
    }
  }

  async extractTextFromPlainText(document) {
    if (document.file) {
      return await document.file.text();
    } else if (document.content) {
      return document.content;
    } else {
      // Fetch from storage
      const response = await fetch(document.url);
      return await response.text();
    }
  }

  async extractTextFromPDF(document) {
    // In a real implementation, you would use PDF.js or a backend service
    // For now, return mock extracted text
    return `[PDF Content from ${document.name}]\n\nThis would contain the extracted text from the PDF document. In a real implementation, this would use PDF.js library or a backend service with pdf2text capabilities to extract all text content from the PDF file.`;
  }

  async extractTextFromDocx(document) {
    // In a real implementation, you would use mammoth.js or a backend service
    return `[DOCX Content from ${document.name}]\n\nThis would contain the extracted text from the Word document. The implementation would use libraries like mammoth.js to parse the .docx file and extract the plain text content.`;
  }

  async extractTextFromXlsx(document) {
    // In a real implementation, you would use SheetJS or a backend service
    return `[XLSX Content from ${document.name}]\n\nThis would contain the extracted data from the Excel spreadsheet. The implementation would parse all sheets and convert the data into a structured text format suitable for RAG processing.`;
  }

  async extractTextFromCSV(document) {
    if (document.file) {
      const text = await document.file.text();
      return `[CSV Data]\n${text}`;
    }
    return `[CSV Content from ${document.name}]\n\nExtracted CSV data would appear here.`;
  }

  async extractTextFromImage(document) {
    // In a real implementation, you would use Tesseract.js for OCR
    return `[Image OCR from ${document.name}]\n\nThis would contain text extracted from the image using OCR (Optical Character Recognition). The implementation would use libraries like Tesseract.js to process the image and extract any readable text.`;
  }

  async createChunks(text, settings = {}) {
    const chunkSize = settings.chunkSize || this.chunkSize;
    const overlap = settings.chunkOverlap || this.chunkOverlap;
    
    const chunks = [];
    let startIndex = 0;
    
    while (startIndex < text.length) {
      const endIndex = Math.min(startIndex + chunkSize, text.length);
      let chunk = text.substring(startIndex, endIndex);
      
      // Try to break at sentence boundaries
      if (endIndex < text.length) {
        const lastSentenceEnd = Math.max(
          chunk.lastIndexOf('.'),
          chunk.lastIndexOf('!'),
          chunk.lastIndexOf('?')
        );
        
        if (lastSentenceEnd > chunk.length * 0.5) {
          chunk = chunk.substring(0, lastSentenceEnd + 1);
          endIndex = startIndex + lastSentenceEnd + 1;
        }
      }
      
      chunks.push({
        id: chunks.length,
        text: chunk.trim(),
        startIndex,
        endIndex,
        length: chunk.length
      });
      
      startIndex = endIndex - overlap;
      if (startIndex >= text.length) break;
    }
    
    return chunks;
  }

  async generateEmbeddings(chunks) {
    const embeddings = [];
    
    for (const chunk of chunks) {
      try {
        const embedding = await this.getEmbedding(chunk.text);
        embeddings.push({
          chunkId: chunk.id,
          vector: embedding,
          dimensions: embedding.length
        });
      } catch (error) {
        console.error(`Failed to generate embedding for chunk ${chunk.id}:`, error);
        // Continue with other chunks
      }
    }
    
    return embeddings;
  }

  async getEmbedding(text) {
    switch (this.embeddingModel) {
      case 'text-embedding-ada-002':
      case 'text-embedding-3-small':
      case 'text-embedding-3-large':
        return this.getOpenAIEmbedding(text);
      case 'sentence-transformers':
        return this.getSentenceTransformerEmbedding(text);
      default:
        throw new Error(`Unsupported embedding model: ${this.embeddingModel}`);
    }
  }

  async getOpenAIEmbedding(text) {
    const response = await fetch('https://api.openai.com/v1/embeddings', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.getOpenAIKey()}`
      },
      body: JSON.stringify({
        model: this.embeddingModel,
        input: text
      })
    });

    if (!response.ok) {
      throw new Error(`OpenAI embedding failed: ${response.statusText}`);
    }

    const data = await response.json();
    return data.data[0].embedding;
  }

  async getSentenceTransformerEmbedding(text) {
    // In a real implementation, this would call your backend service
    // that runs sentence-transformers locally
    const response = await fetch('/api/embeddings/sentence-transformers', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.getAuthToken()}`
      },
      body: JSON.stringify({
        text: text,
        model: 'all-MiniLM-L6-v2'
      })
    });

    if (!response.ok) {
      throw new Error(`Sentence transformer embedding failed: ${response.statusText}`);
    }

    const data = await response.json();
    return data.embedding;
  }

  async extractMetadata(document, extractedText) {
    const metadata = {
      originalName: document.name,
      fileSize: document.size || document.file?.size,
      mimeType: document.type || document.metadata?.mimeType,
      uploadedAt: document.uploadedAt || new Date().toISOString(),
      processedAt: new Date().toISOString(),
      textLength: extractedText.length,
      language: await this.detectLanguage(extractedText),
      keywords: await this.extractKeywords(extractedText),
      summary: await this.generateSummary(extractedText),
      topics: await this.extractTopics(extractedText)
    };

    return metadata;
  }

  async detectLanguage(text) {
    // Simple language detection based on common words
    // In a real implementation, use a proper language detection library
    const sample = text.substring(0, 500).toLowerCase();
    
    const spanishWords = ['el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'está'];
    const frenchWords = ['le', 'de', 'et', 'à', 'un', 'il', 'être', 'et', 'en', 'avoir', 'que', 'pour', 'dans', 'ce', 'son', 'une', 'sur', 'avec', 'ne', 'se'];
    const germanWords = ['der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das', 'mit', 'sich', 'des', 'auf', 'für', 'ist', 'im', 'dem', 'nicht', 'ein', 'eine', 'als'];
    
    let spanishCount = 0, frenchCount = 0, germanCount = 0;
    
    spanishWords.forEach(word => {
      if (sample.includes(` ${word} `)) spanishCount++;
    });
    
    frenchWords.forEach(word => {
      if (sample.includes(` ${word} `)) frenchCount++;
    });
    
    germanWords.forEach(word => {
      if (sample.includes(` ${word} `)) germanCount++;
    });
    
    if (spanishCount > frenchCount && spanishCount > germanCount && spanishCount > 2) return 'es';
    if (frenchCount > germanCount && frenchCount > 2) return 'fr';
    if (germanCount > 2) return 'de';
    
    return 'en'; // Default to English
  }

  async extractKeywords(text) {
    // Simple keyword extraction
    // In a real implementation, use NLP libraries like compromise.js or call an API
    const words = text.toLowerCase()
      .replace(/[^\w\s]/g, ' ')
      .split(/\s+/)
      .filter(word => word.length > 3);
    
    const frequency = {};
    words.forEach(word => {
      frequency[word] = (frequency[word] || 0) + 1;
    });
    
    const commonWords = new Set(['this', 'that', 'with', 'have', 'will', 'been', 'from', 'they', 'know', 'want', 'been', 'good', 'much', 'some', 'time', 'very', 'when', 'come', 'here', 'just', 'like', 'long', 'make', 'many', 'over', 'such', 'take', 'than', 'them', 'well', 'your']);
    
    return Object.entries(frequency)
      .filter(([word, count]) => count > 1 && !commonWords.has(word))
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([word]) => word);
  }

  async generateSummary(text) {
    // Simple extractive summarization
    // In a real implementation, use AI models for better summarization
    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 20);
    
    if (sentences.length <= 3) {
      return sentences.join('. ') + '.';
    }
    
    // Take first, middle, and last sentences as a simple summary
    const summary = [
      sentences[0],
      sentences[Math.floor(sentences.length / 2)],
      sentences[sentences.length - 1]
    ].join('. ') + '.';
    
    return summary.substring(0, 200) + '...';
  }

  async extractTopics(text) {
    // Simple topic extraction based on keywords
    const keywords = await this.extractKeywords(text);
    
    const topicMap = {
      safety: ['safety', 'hazard', 'protection', 'emergency', 'risk', 'security'],
      training: ['training', 'learning', 'education', 'course', 'skill', 'development'],
      policy: ['policy', 'procedure', 'rule', 'regulation', 'guideline', 'standard'],
      hr: ['employee', 'human', 'resource', 'personnel', 'staff', 'worker'],
      compliance: ['compliance', 'audit', 'regulation', 'legal', 'requirement', 'standard']
    };
    
    const topics = [];
    
    Object.entries(topicMap).forEach(([topic, relatedWords]) => {
      const matches = relatedWords.filter(word => 
        keywords.some(keyword => keyword.includes(word) || word.includes(keyword))
      );
      
      if (matches.length > 0) {
        topics.push(topic);
      }
    });
    
    return topics;
  }

  async storeVectors(chunks, embeddings, metadata) {
    switch (this.vectorStore) {
      case 'chromadb':
        return this.storeInChromaDB(chunks, embeddings, metadata);
      case 'pinecone':
        return this.storeInPinecone(chunks, embeddings, metadata);
      case 'weaviate':
        return this.storeInWeaviate(chunks, embeddings, metadata);
      case 'qdrant':
        return this.storeInQdrant(chunks, embeddings, metadata);
      default:
        throw new Error(`Unsupported vector store: ${this.vectorStore}`);
    }
  }

  async storeInChromaDB(chunks, embeddings, metadata) {
    const response = await fetch('/api/vector-store/chromadb/store', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.getAuthToken()}`
      },
      body: JSON.stringify({
        chunks,
        embeddings,
        metadata,
        collection: 'training_documents'
      })
    });

    if (!response.ok) {
      throw new Error(`ChromaDB storage failed: ${response.statusText}`);
    }

    const result = await response.json();
    return result.vectorIds;
  }

  async storeInPinecone(chunks, embeddings, metadata) {
    // Pinecone implementation
    const response = await fetch('/api/vector-store/pinecone/store', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.getAuthToken()}`
      },
      body: JSON.stringify({
        chunks,
        embeddings,
        metadata,
        namespace: 'training_documents'
      })
    });

    if (!response.ok) {
      throw new Error(`Pinecone storage failed: ${response.statusText}`);
    }

    const result = await response.json();
    return result.vectorIds;
  }

  async storeInWeaviate(chunks, embeddings, metadata) {
    // Weaviate implementation
    const response = await fetch('/api/vector-store/weaviate/store', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.getAuthToken()}`
      },
      body: JSON.stringify({
        chunks,
        embeddings,
        metadata,
        className: 'TrainingDocument'
      })
    });

    if (!response.ok) {
      throw new Error(`Weaviate storage failed: ${response.statusText}`);
    }

    const result = await response.json();
    return result.vectorIds;
  }

  async storeInQdrant(chunks, embeddings, metadata) {
    // Qdrant implementation
    const response = await fetch('/api/vector-store/qdrant/store', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.getAuthToken()}`
      },
      body: JSON.stringify({
        chunks,
        embeddings,
        metadata,
        collection: 'training_documents'
      })
    });

    if (!response.ok) {
      throw new Error(`Qdrant storage failed: ${response.statusText}`);
    }

    const result = await response.json();
    return result.vectorIds;
  }

  async searchSimilarDocuments(query, limit = 5) {
    // Generate embedding for the query
    const queryEmbedding = await this.getEmbedding(query);
    
    // Search in vector store
    const response = await fetch('/api/vector-store/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.getAuthToken()}`
      },
      body: JSON.stringify({
        vector: queryEmbedding,
        limit,
        vectorStore: this.vectorStore
      })
    });

    if (!response.ok) {
      throw new Error(`Vector search failed: ${response.statusText}`);
    }

    return response.json();
  }

  // Utility methods
  getOpenAIKey() {
    return localStorage.getItem('openai_api_key') || process.env.REACT_APP_OPENAI_API_KEY;
  }

  getAuthToken() {
    return localStorage.getItem('authToken') || '';
  }
}

export default RAGService;
