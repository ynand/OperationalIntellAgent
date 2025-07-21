from llm_client import chat_with_model

# client = OpenAI(api_key="your_api_key")  # Replace with your API key

def decision_agent(log_summary):
    decision_prompt = f"""
    You are an orchestration decision-maker.
    Here is the log analysis summary:
    {log_summary}

    Decide which agents should be executed:
    - code_agent (for code-related issues)
    - db_agent (for database-related issues)

    Return ONLY a valid JSON object (no extra text, no markdown, no explanation), in this exact format:
    {{
        "run_code_agent": true/false,
        "run_db_agent": true/false,
        "reason": "short reason"
    }}
    """
    # response = client.chat.completions.create(
    #     model="gpt-4o-mini",
    #     messages=[{"role": "system", "content": "You are a helpful assistant for decision-making."},
    #               {"role": "user", "content": decision_prompt}],
    #     temperature=0
    # )
    decision_text = chat_with_model(decision_prompt)
    return decision_text