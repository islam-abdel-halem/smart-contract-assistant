from langchain_openai import ChatOpenAI
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_core.prompts import PromptTemplate

def get_rag_chain(vector_store):
    # Setup GPT-3.5 or GPT-4 model
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0) # temperature=0 for contract accuracy

    # Design an explicit prompt to force the model to rely only on the uploaded file
    prompt_template = """You are a helpful legal assistant for reviewing contracts and documents.
Use the following pieces of context to answer the user's question.
If the answer is not in the context, just say that you don't know, don't try to make up an answer.
Don't say you cannot access the document, YOU ARE given the document context below.

Context:
{context}

Question: {question}
Helpful Answer:"""
    
    QA_PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    # Build the Chain and enable source retrieval [cite: 86]
    # Memory removed since we will rely on Gradio history to prevent session overlap
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vector_store.as_retriever(search_kwargs={"k": 3}), # Retrieve top 3 text chunks [cite: 78]
        return_source_documents=True, # To output Source Citations [cite: 31]
        combine_docs_chain_kwargs={"prompt": QA_PROMPT} # Force the model to use this context
    )
    
    return chain