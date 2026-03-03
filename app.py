import gradio as gr
import os
from dotenv import load_dotenv
from processor import process_document
from database import create_vector_store
from engine import get_rag_chain

# Load API keys
load_dotenv()

# Variable to store Chain state
app_chain = None

def upload_and_process(file):
    global app_chain
    if file is None:
        return "Please upload a file first."
    
    # 1. Process and split the file
    chunks = process_document(file.name)
    
    # 2. Create Vector Store
    vector_db = create_vector_store(chunks)
    
    # 3. Build RAG engine
    app_chain = get_rag_chain(vector_db)
    
    return "Document processed successfully! You can now start chatting."

def chat_response(message, history):
    global app_chain
    if app_chain is None:
        return "Please upload a document in the 'Upload' tab first."
    
    # 1. Clean message if it's a Dictionary or List (occurs in newer Gradio versions)
    if isinstance(message, dict) and "text" in message:
        user_query = str(message["text"])
    elif isinstance(message, (list, tuple)) and len(message) > 0:
        val = message[0]
        user_query = str(val.get("text", val) if isinstance(val, dict) else val)
    else:
        user_query = str(message)

    # 2. Convert Gradio history to Tuples of Strings for Langchain to avoid Concatenation error
    formatted_history = []
    if history and isinstance(history[0], dict):
        user_msg = None
        for msg in history:
            content = msg.get('content', '')
            if isinstance(content, (tuple, list)): 
                content = str(content[0]) if len(content) > 0 else ""
            else:
                content = str(content)
                
            if msg['role'] == 'user':
                user_msg = content
            elif msg['role'] == 'assistant' and user_msg is not None:
                formatted_history.append((user_msg, content))
                user_msg = None
    elif history and (isinstance(history[0], list) or isinstance(history[0], tuple)):
        for turn in history:
            user = turn[0]
            bot = turn[1]
            if isinstance(user, (tuple, list)): 
                user = str(user[0]) if len(user) > 0 else ""
            else:
                user = str(user)
                
            if isinstance(bot, (tuple, list)): 
                bot = str(bot[0]) if len(bot) > 0 else ""
            else:
                bot = str(bot)
                
            formatted_history.append((user, bot))
            
    # Run the Chain to get an answer (replaced () with invoke to avoid Warning)
    response = app_chain.invoke({"question": user_query, "chat_history": formatted_history})
    answer = response['answer']
    
    # Clean and format Citations
    unique_sources = set()
    for doc in response.get('source_documents', []):
        page = doc.metadata.get('page', 'N/A')
        page_display = int(page) + 1 if str(page).isdigit() else page
        source_name = os.path.basename(doc.metadata.get('source', 'Unknown'))
        unique_sources.add(f"{source_name} (Page {page_display})")
        
    sources = "\n\nSources:\n"
    if unique_sources:
        for s in unique_sources:
            sources += f"- {s}\n"
    else:
        sources += "- No sources retrieved.\n"
    
    return answer + sources

# Build Gradio Interface with Tabs 
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 📑 Smart Contract Assistant")
    gr.Markdown("Upload your contract and ask any questions.")
    
    with gr.Tabs():
        # Upload and Process Tab
        with gr.TabItem("1. Ingestion & Setup"):
            file_input = gr.File(label="Upload Contract (PDF/DOCX)")
            process_btn = gr.Button("Process Document")
            status_output = gr.Textbox(label="Status", interactive=False)
            process_btn.click(upload_and_process, inputs=[file_input], outputs=[status_output])
            
        # Chat Tab
        with gr.TabItem("2. Chat with Contract"):
            chatbot = gr.ChatInterface(
                fn=chat_response,
                title="Contract Q&A",
                description="The assistant will answer based on the context of the uploaded file."
            )

if __name__ == "__main__":
    demo.launch()