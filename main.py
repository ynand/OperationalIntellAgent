from orchestrator import orchestrator
import sys
import os

if __name__ == "__main__":
    print("🤖 Multi-Agent AI System (powered by local LLM)\n")

    if len(sys.argv) < 2:
        print("❌ Please provide the log file path as an argument.")
        print("Usage: python main.py <log_file_path>")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.isfile(file_path):
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    # Read file content
    with open(file_path, 'r', encoding='utf-8') as f:
        print(f"📂 Reading log file: {file_path}")
        user_input = f.read()
    print("🔍 Analyzing logs and generating JIRA ticket...\n")
    result = orchestrator(user_input)

    # print("\n🔍 Log Summary:\n", result['log_summary'])
    # print("\n💻 Code Analysis:\n", result['code_analysis'])
    # print("\n📦 DB Agent Result:\n", result['db_result'])
    # print("\n📝 JIRA Ticket:\n", result['jira_ticket'])

