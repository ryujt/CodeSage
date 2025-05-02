from SageLibs.config import get_setting
from SageLibs.web_requests import summarize_content

def build_payload(question, previous_answers, relevant_docs):
    """
    Build a standardized payload for the chat API.
    
    Args:
        question (str): User's question
        previous_answers (list): List of previous answers
        relevant_docs (list): List of relevant documents
        
    Returns:
        dict: Formatted payload for the chat API
    """
    data = {
        "prompt": question,
        "context": [],
        "previous_answers": []
    }
    
    # Add previous answers if any
    if previous_answers:
        data["previous_answers"] = previous_answers
    
    # Add relevant documents to context
    for doc in relevant_docs:
        filename = doc.get("filename")
        content = doc.get("content")
        if get_setting("filter_content") == "on":
            content = summarize_content(question, content)
        
        data["context"].append({
            "filename": filename,
            "content": content
        })
    
    return data 