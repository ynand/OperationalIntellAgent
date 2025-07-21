from llm_client import chat_with_model

def jira_agent(issue_description):
    prompt = f"Generate a JIRA ticket description based on the following issue:\n{issue_description}"
    return chat_with_model(prompt)
