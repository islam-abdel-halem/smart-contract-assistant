import os
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

def create_vector_store(chunks):
    # Use OpenAI model to convert text to Embeddings 
    embeddings = OpenAIEmbeddings()
    
    # Build Vector Store using FAISS 
    vector_db = FAISS.from_documents(chunks, embeddings)
    
    # Save the index locally to avoid consuming API on every run (optional but professional) 
    vector_db.save_local("faiss_index")
    
    return vector_db

def load_vector_store():
    embeddings = OpenAIEmbeddings()
    return FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)