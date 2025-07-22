from agents.log_agent import log_agent
from agents.code_agent import code_agent
from agents.db_agent import db_agent
from agents.decision_agent import decision_agent
from agents.jira_agent import jira_agent
import os
import json
from openai import OpenAI
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from textwrap import wrap
import re
from datetime import datetime
from jira import JIRA

client = OpenAI(api_key="your_api_key")  # Replace with your API key


def orchestrator(user_input):
    print("🤖 Orchestrator: Coordinating agents...\n")
    output_dir = "output\\analysis_{timestamp}".format(timestamp=datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(output_dir, exist_ok=True) 
    # Step 1: Run Log Agent
    log_summary = log_agent(user_input)
    print("🔍 Log Summary Generated:\n", log_summary)
    print("🤖 Log Agent completed.\n")

    # Step 2: Use Decision Agent
    decision_text = decision_agent(log_summary)
    decision_text_clean = re.sub(r"```(?:json)?|```", "", decision_text).strip()
    print("🤖 LLM Decision:\n", decision_text)
    print("🤖 Decision-making completed.\n")

    try:
        decision = json.loads(decision_text)
    except json.JSONDecodeError:
        decision = {"run_code_agent": False, "run_db_agent": False, "reason": "Failed to parse decision"}

    print (decision.get("run_code_agent"), decision.get("run_db_agent"))
    # Step 3: Execute agents
    code_analysis = None
    db_result = None
    jira_ticket = None


    if decision.get("run_code_agent"):
        print("💻 Running Code Agent...")
        project_path = "C:\hack"
        source_code = collect_project_source_code(project_path)
        code_analysis = code_agent(log_summary, source_code)
        print("💻 Code Analysis Generated:\n", code_analysis)
        print("✅ Code Analysis Completed.")

    if decision.get("run_db_agent"):
        print("🛢️ Running DB Agent...")
        db_result = db_agent({
            "log_summary": log_summary,
            "code_analysis": code_analysis or "",
            "db_conn_str": "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=Test;UID=sa;PWD=titan#12",
            "log_file": f"{output_dir}\\db_agent.log",
            "output_dir": output_dir
        })

        print("🛢️ DB Analysis Result:\n", db_result)
        print("✅ DB Analysis Completed.")

        # Step 5: Generate Report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"{output_dir}\\analysis_report_{timestamp}.pdf"
    generate_pdf_report(report_path, log_summary, decision, code_analysis, db_result, jira_ticket)
    print(f"📄 Report generated: {report_path}")

    # Step 6: Generate JIRA Ticket
    print("📝 Creating JIRA ticket...")
    # Only pass required arguments to jira_agent
    jira_server = "https://jira-stg.csod.com"  
    jira_username = os.getenv("USER")  
    jira_password = os.getenv("PASS")  
    jira_ticket = jira_agent({
        "server": jira_server,
        "username": jira_username,
        "password": jira_password,
        "log_summary": log_summary,
        "decision": decision,
        "code_analysis": code_analysis,
        "db_result": db_result
    })
    print("📝 JIRA Ticket Created:\n", jira_ticket)
    print("✅ JIRA Ticket Completed.")



    return {
        "log_summary": log_summary,
        "decision": decision,
        "code_analysis": code_analysis,
        "db_result": db_result,
        "jira_ticket": jira_ticket,
        "report_path": report_path
    }

def collect_project_source_code(project_path, max_size_kb=200):
    source_code = ""
    for root, _, files in os.walk(project_path):
        for file in files:
            if not file.endswith((".py", ".cs", ".js", ".ts")):
                continue
            file_path = os.path.join(root, file)
            try:
                if os.path.getsize(file_path) > max_size_kb * 1024:
                    continue
                with open(file_path, "r", encoding="utf-8") as f:
                    source_code += f"\n# File: {file_path}\n"
                    source_code += f.read() + "\n"
            except (UnicodeDecodeError, PermissionError, IsADirectoryError):
                continue
    return source_code

def generate_pdf_report(output_path, log_summary, decision, code_analysis, db_result, jira_ticket=None):
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    def add_section(title, content, style="Heading2", space_after=0.2):
        story.append(Paragraph(f"<b>{title}</b>", styles[style]))
        story.append(Spacer(1, space_after * inch))
        if isinstance(content, dict) or isinstance(content, list):
            pretty = json.dumps(content, indent=2)
            for line in pretty.splitlines():
                story.append(Paragraph(line, styles["Code"]))
        else:
            for para in str(content).split("\n"):
                story.append(Paragraph(para, styles["Normal"]))
        story.append(Spacer(1, 0.3 * inch))

    add_section("📌 Log Summary", log_summary)
    add_section("🤖 Decision", decision)
    add_section("💻 Code Analysis", code_analysis if code_analysis else "Not Executed")
    add_section("🛢️ DB Analysis", db_result if db_result else "Not Executed")
    add_section("📝 JIRA Ticket", jira_ticket if jira_ticket else "Not Created")

    doc.build(story)



