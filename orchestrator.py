from agents.log_agent import log_agent
from agents.code_agent import code_agent
from agents.jira_agent import jira_agent
from agents.db_agent import db_agent
import os

def orchestrator(user_input):
    print("🤖 Orchestrator: Coordinating agents...\n")
    log_summary = log_agent(user_input)
    print("🔍 Log Summary Generated:\n", log_summary)
    project_path = "c:/Hack"
    source_code = collect_project_source_code(project_path)

    code_analysis = code_agent(log_summary, source_code)
    print("💻 Code Analysis Completed:\n", code_analysis)
    db_result = db_agent({
        "log_summary": log_summary,
        "code_analysis": code_analysis,
        "db_conn_str": "DRIVER={ODBC Driver 17 for SQL Server};SERVER=hostmachine;DATABASE=Test;UID=sa;PWD=titan#12",
        # "log_file": "db_agent.log"  # optional
    })
    # jira_ticket = jira_agent(code_analysis)
    # print("📝 JIRA Ticket Created:\n", jira_ticket)

    return {
        "log_summary": log_summary,
        "code_analysis": code_analysis,
        "db_result": db_result
        # "jira_ticket": jira_ticket
    }

def collect_project_source_code(project_path, max_size_kb=200):
    source_code = ""
    for root, _, files in os.walk(project_path):
        for file in files:
            if not file.endswith((".py", ".cs", ".js", ".ts")):  # Only code files
                continue
            file_path = os.path.join(root, file)
            try:
                if os.path.getsize(file_path) > max_size_kb * 1024:
                    continue  # Skip big files
                with open(file_path, "r", encoding="utf-8") as f:
                    source_code += f"\n# File: {file_path}\n"
                    source_code += f.read() + "\n"
            except (UnicodeDecodeError, PermissionError, IsADirectoryError):
                continue
    return source_code
