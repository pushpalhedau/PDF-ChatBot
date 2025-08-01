# -*- coding: utf-8 -*-
"""PDF-ChatBot.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/10P9P8NCxoNE8ZH7fwg2obGlePZJNSIaG

REQUIREMENTS FOR THE PROJECT
"""

!pip install -q langchain faiss-cpu sentence-transformers transformers gradio pypdf
!pip install -q -U langchain-community

"""IMPORT MODULES"""

import torch
import gradio as gr
import faiss
import pickle
import os
import numpy as np
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from transformers import pipeline

"""GPU CHECK!"""

device = "cuda" if torch.cuda.is_available() else "cpu"
print("Using device:", device)

"""LOADING AI MODELS"""

embedding_model = SentenceTransformer("all-MiniLM-L6-v2", device=device)
flan_t5_pipeline = pipeline("text2text-generation", model="google/flan-t5-large", device=0 if device == "cuda" else -1)

"""GLOBAL VARIABLES"""

chunk_texts = []
index = None
INDEX_FILE = "faiss_index.index"
CHUNKS_FILE = "chunks.pkl"
PDF_LIST_FILE = "uploaded_files.txt"

"""UTILITY FUNCTIONS"""

def load_previous_data():
    global chunk_texts, index
    if os.path.exists(INDEX_FILE) and os.path.exists(CHUNKS_FILE):
        index = faiss.read_index(INDEX_FILE)
        with open(CHUNKS_FILE, "rb") as f:
            chunk_texts = pickle.load(f)

def save_pdf_list(pdf_name):
    with open(PDF_LIST_FILE, "a") as f:
        f.write(pdf_name + "\n")

def get_uploaded_pdfs():
    if not os.path.exists(PDF_LIST_FILE):
        return "No PDFs uploaded yet."
    with open(PDF_LIST_FILE, "r") as f:
        return f.read().strip()

"""LOADING PDFs"""

def process_pdf(file):
    global chunk_texts, index

    try:
        loader = PyPDFLoader(file.name)
        docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_documents(docs)
        new_texts = [doc.page_content for doc in chunks]

        new_embeddings = embedding_model.encode(new_texts, show_progress_bar=True).astype("float32")

        # Load existing index or create new
        if os.path.exists(INDEX_FILE):
            index = faiss.read_index(INDEX_FILE)
        else:
            index = faiss.IndexFlatL2(new_embeddings.shape[1])

        # Load existing chunks from disk (before adding new ones)
        if os.path.exists(CHUNKS_FILE):
            with open(CHUNKS_FILE, "rb") as f:
                chunk_texts = pickle.load(f)
        else:
            chunk_texts = []

        # Add new chunks to chunk_texts
        chunk_texts.extend(new_texts)

        # Add new embeddings to index
        index.add(new_embeddings)

        # Save updated index and chunks
        faiss.write_index(index, INDEX_FILE)
        with open(CHUNKS_FILE, "wb") as f:
            pickle.dump(chunk_texts, f)

        save_pdf_list(os.path.basename(file.name))

        return f"✅ Added {len(new_texts)} chunks from '{os.path.basename(file.name)}'."

    except Exception as e:
        return f"❌ Error: {str(e)}"

"""RAG APPROACH"""

def get_most_relevant_chunks(question, top_k=3):
    question_embedding = embedding_model.encode([question])
    D, I = index.search(np.array(question_embedding).astype("float32"), top_k)
    return [chunk_texts[i] for i in I[0] if i < len(chunk_texts)]

def answer_question(question, history):
    if not chunk_texts or not index:
        load_previous_data()
        if not chunk_texts or not index:
            return "❌ Please upload and process a PDF first.", history

    relevant_chunks = get_most_relevant_chunks(question)
    if not relevant_chunks:
        return "❌ No relevant content found.", history

    context = "\n".join(relevant_chunks)
    prompt = f"Answer the question based on the context.\n\nContext: {context}\n\nQuestion: {question}"

    try:
        response = flan_t5_pipeline(prompt, max_new_tokens=1000)[0]["generated_text"]
    except Exception as e:
        response = f"❌ Generation error: {str(e)}"

    history.append((question, response.strip()))
    return "", history

"""GRADIO UI"""

with gr.Blocks() as demo:
    gr.Markdown("# 📚🤖 Multi-PDF Chatbot with FAISS + FLAN-T5")

    with gr.Row():
        pdf_input = gr.File(label="📄 Upload New PDF", file_types=[".pdf"])
        status = gr.Textbox(label="Status", interactive=False)

    with gr.Row():
        pdf_list_box = gr.Textbox(label="📂 Uploaded PDFs", value=get_uploaded_pdfs(), interactive=False)

    chat = gr.Chatbot(label="Chat about all PDFs")
    msg = gr.Textbox(placeholder="Ask a question about the uploaded PDFs", label="Your Question")
    clear = gr.Button("🧹 Clear Chat")

    state = gr.State([])

    # Actions
    pdf_input.change(fn=process_pdf, inputs=pdf_input, outputs=status).then(
        fn=lambda: get_uploaded_pdfs(), inputs=None, outputs=pdf_list_box
    )
    msg.submit(fn=answer_question, inputs=[msg, state], outputs=[msg, chat])
    clear.click(lambda: [], None, chat)

demo.launch()