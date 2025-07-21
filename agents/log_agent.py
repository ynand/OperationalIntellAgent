from llm_client import chat_with_model

def log_agent(input_text):
    print("🤖 Log Agent: Analyzing logs...\n")
    prompt = f"Analyze the following system log and summarize any error:\n\n{input_text}"
    result = chat_with_model(prompt)
    return result
