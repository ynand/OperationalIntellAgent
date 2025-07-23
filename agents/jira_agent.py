from jira import JIRA
from llm_client import chat_with_model
import os
import glob
   
 
 
 
def jira_agent(data):
    # Extract connection info and context
    server = data.get("server") or os.getenv("JIRA_SERVER")
    username = data.get("username") or os.getenv("EMAIL")
    password = data.get("password") or os.getenv("API_TOKEN")
    project_key = os.getenv("PROJECT_KEY", "STS")

    # Compose prompt for LLM
    prompt = f"""
    You are a Jira ticket creation assistant in a multi-agent AI system for operational intelligence.
    
    Format:
    **Summary:** [Short summary]
    **Steps to Reproduce:**
    1. ...
    **Observed Behavior:**
    ...
    **Expected Behavior:**
    ...
    **Root Cause Analysis:**
    ...
    **Suggested Fix:**
    ...
    
    Input:
    Log Summary: {data.get('log_summary')}
    Decision: {data.get('decision')}
    Code Analysis: {data.get('code_analysis')}
    DB Result: {data.get('db_result')}
    """

    generated_description = chat_with_model(prompt)

    jira = JIRA(
        server=server,
        basic_auth=(username, password)
    )

    # Sanitize summary: remove newlines and trim
    raw_summary = str(data.get('log_summary') or '').replace('\n', ' ').replace('\r', ' ').strip()[:255]
    # Use AI to rewrite summary, ask for <255 chars, no newlines, and do not cut words
    rewrite_prompt = (
    f"Rewrite the following text as a concise Jira ticket summary. "
    f"Respond with only the rewritten summary and nothing else. "
    f"Keep it under 255 characters, do not include newlines or extra punctuation. "
    f"Do NOT preface your answer with any explanation.\n\n"
    f"{raw_summary}"
)

    summary = chat_with_model(rewrite_prompt)
    summary = summary.replace('\n', ' ').replace('\r', ' ').strip()

    # Add required custom fields (replace with your actual values or logic)
    issue_dict = {
        'project': {'key': project_key},
        'summary': summary,
        'description': generated_description,
        'issuetype': {'name': 'Story'},
        # Story Checklist (array of objects)
        'customfield_18805': [{'value': 'Does the change impact Reports/UWD/AR?'}],
        # Classification (option object with valid id)
        'customfield_18109': {'id': '28852'},  
        # ENG Category (array of objects with valid id)
        'customfield_19690': [{'id': '73558'}], 
        # Acceptance Criteria (string)
        'customfield_16406': 'Acceptance Criteria value',
        # Documentation Required (option object with valid id)
        'customfield_16800': {'id': '18900'} 
    }

    new_issue = jira.create_issue(fields=issue_dict)
    print(f"✅ Issue created: {new_issue.key}")

    # Attach all files from the attachments list provided by orchestrator
    attachments = data.get('attachments', [])
    if attachments:
        for file_path in attachments:
            if os.path.isfile(file_path):
                with open(file_path, 'rb') as f:
                    jira.add_attachment(issue=new_issue, attachment=f, filename=os.path.basename(file_path))
                print(f"📎 Attached: {os.path.basename(file_path)} to {new_issue.key}")
    else:
        print("⚠️ No files found in attachments to attach.")
    return new_issue.key