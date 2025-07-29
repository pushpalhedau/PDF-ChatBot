# 📚🤖 Multi-PDF Chatbot with FAISS + FLAN-T5 (LLM)

A simple and powerful chatbot that lets you upload multiple PDFs and ask questions about their content. It uses **RAG (Retrieval-Augmented Generation)** to combine semantic search with a Large Language Model for accurate, natural answers.

---

## 🔧 Features

- ✅ Upload multiple PDF files
- 🔍 Smart chunking and semantic search using SentenceTransformers + FAISS
- 🧠 FLAN-T5 Large (LLM) generates human-like answers
- 💬 Chat interface built with Gradio
- 💾 Saves and reuses previous uploads and indexes
- 
---

## 🚀 How It Works

1. **PDF Upload:** You upload one or more PDFs.
2. **Text Splitting:** Content is split into overlapping chunks.
3. **Embedding:** Chunks are converted into vector embeddings.
4. **Indexing:** FAISS stores these embeddings for fast retrieval.
5. **Retrieval:** User’s question is embedded and top-matching chunks are fetched.
6. **LLM Response:** FLAN-T5 generates a response using the retrieved context.

This follows the **RAG (Retrieval-Augmented Generation)** architecture.
