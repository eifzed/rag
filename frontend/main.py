import gradio as gr
import requests
import re
import mimetypes

# Backend API URLs
BASE_URL = "http://localhost:8000/api"
CONTEXTS_URL = f"{BASE_URL}/contexts"
CHAT_URL = f"{BASE_URL}/chat"

# Function to create a new context
def create_context(name, description):
    response = requests.post(
        CONTEXTS_URL,
        data={"name": name, "description": description},
    )
    if response.status_code == 200:
        return "Context created successfully!"
    else:
        return f"Error: {response.text}"

# Function to fetch available contexts
def get_contexts():
    response = requests.get(CONTEXTS_URL)
    if response.status_code == 200:
        contexts = response.json()
        # print(contexts)
        return {ctx["id"]: ctx["name"] for ctx in contexts}  # Return a mapping {context_id: name}
    else:
        return {}

# Function to upload a file to a context
def upload_file(context_id, file):
    if not context_id or file is None:
        return "Please select a context and upload a file."

    context_id = extract_id(context_id)

    # Get file name and determine content type
    file_name = getattr(file, "name", "unknown")
    content_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"

    # Ensure the file is correctly structured
    files = {"files": (file_name, file, content_type)}

    try:
        response = requests.post(f"{CONTEXTS_URL}/{context_id}/file", files=files)
        if response.status_code == 200:
            return "File uploaded successfully!"
        else:
            return f"Error: {response.text}"
    except requests.exceptions.RequestException as e:
        return f"Request failed: {e}"

# Function to chat with RAG
def chat_with_rag(context_id, message, history):
    if not context_id:
        return "Please select a context."
    
    payload = {
        "context_id": context_id,
        "message": message,
        "history": history or [],
    }

    response = requests.post(CHAT_URL, json=payload)
    
    if response.status_code == 200:
        bot_message = response.json().get("response", "No response from RAG.")
    else:
        bot_message = "Error connecting to "

    return bot_message

def update_context_dropdown():
    contexts = get_contexts()
    # choices = list(contexts.keys())  # Extract context IDs
    choices = [f"{value} ({key})" for key, value in contexts.items()]
    print("choices", choices)

    return gr.update(choices=choices, value=choices[0] if choices else None)  # Select first option if available


def extract_id(text: str) -> str:
    match = re.search(r"\(([^)]+)\)", text)
    return match.group(1) if match else ""


# Initialize UI
with gr.Blocks() as demo:
    gr.Markdown("# 🔍 RAG-Powered Chatbot with Context Management")

    # Context Creation
    with gr.Row():
        name_input = gr.Textbox(label="Context Name")
        desc_input = gr.Textbox(label="Description")
        create_btn = gr.Button("Create Context")
        create_output = gr.Textbox(label="Status", interactive=False)
    
    create_btn.click(create_context, [name_input, desc_input], create_output)

    # Fetch and Select Context
    context_dropdown = gr.Dropdown(label="Select Context", choices=[], interactive=True)
    refresh_btn = gr.Button("Refresh Contexts")

    # def update_context_dropdown():
    #     contexts = get_contexts()
    #     return list(contexts.keys())

    
    refresh_btn.click(update_context_dropdown, [], context_dropdown)

    # Upload File to Context
    with gr.Row():
        file_input = gr.File(label="Upload File")
        upload_btn = gr.Button("Upload to Selected Context")
        upload_output = gr.Textbox(label="Upload Status", interactive=False)

    upload_btn.click(upload_file, [context_dropdown, file_input], upload_output)

    # Chat Interface
    chatbot = gr.Chatbot()
    msg_input = gr.Textbox(label="Ask a question:")
    def respond(user_message, chat_history, context_id):
        if not context_id:
            return "⚠️ Please select a context before chatting.", chat_history


        # Call backend chat API
        payload = {
            "context_id": extract_id(context_id),
            "message": user_message,
            "history": build_chat_history(chat_history),
        }
        response = requests.post("http://localhost:8000/api/chat", json=payload)

        # Process response
        if response.status_code == 200:
            bot_response = response.json().get("response", "No response from RAG.")
        else:
            bot_response = f"⚠️ Error: {response.text}"

        # Append to chat history
        chat_history.append((user_message, bot_response))
        return "", chat_history

    msg_input.submit(respond, [msg_input, chatbot, context_dropdown], [msg_input, chatbot])


def build_chat_history(history):
    result = []
    for h in history:
        result.append({"role": "user", "content": h[0]})
        result.append({"role": "assistant", "content": h[1]})
    return result

# Launch UI
demo.launch(share=True)
