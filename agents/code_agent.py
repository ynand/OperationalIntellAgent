from llm_client import chat_with_model

def code_agent(log_summary, source_code):
    prompt = (
        f"The following error was found in logs:\n'{log_summary}'\n"
        "Here is the relevant source code:\n"
        f"{source_code}\n"
        "Analyze the source code and identify the most probable root cause. "
        "Provide the specific code block (function, method, or class) where the issue likely occurred, "
        "and explain your reasoning."
    )
    return chat_with_model(prompt)