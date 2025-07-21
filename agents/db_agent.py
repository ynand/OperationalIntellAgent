import json
from llm_client import chat_with_model

def db_agent(config):
    """
    Uses LLM to generate diagnostics, runs SQL queries, and returns/explains results.
    Args:
        config (dict): {
            'log_summary': str,
            'code_analysis': str,
            'db_conn_str': (optional) pyodbc connection string,
            'log_file': (optional) path to log file
        }
    Returns:
        str: Human-readable analysis.
    """
    import pyodbc
    log_file = config.get("log_file", "db_agent.log")
    def log(msg):
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
        print(msg)

    log_summary = config.get("log_summary", "")
    code_analysis = config.get("code_analysis", "")

    # 1. Ask LLM for diagnostic SQL queries
    prompt = (
        f"Given this log summary from a SQL Server app:\n{log_summary}\n"
        f"Code analysis:\n{code_analysis}\n"
        "Suggest SQL Server diagnostic queries to help identify root causes (e.g., timeouts, slow queries, connection issues). "
        "Return only valid T-SQL statements, one per line, with no explanations."
    )
    sql_suggestions = chat_with_model(prompt)
    log(f"LLM suggested SQL queries:\n{sql_suggestions}")

    # 2. Execute SQL queries (if db_conn_str provided)
    results = []
    db_conn_str = config.get("db_conn_str")
    if db_conn_str:
        try:
            conn = pyodbc.connect(db_conn_str)
            cursor = conn.cursor()
            for sql in sql_suggestions.strip().splitlines():
                try:
                    cursor.execute(sql)
                    rows = cursor.fetchall()
                    col_names = [desc[0] for desc in cursor.description]
                    result = [dict(zip(col_names, row)) for row in rows]
                    results.append({"query": sql, "result": result})
                    log(f"Executed: {sql}\nResult: {result}")
                except Exception as e:
                    results.append({"query": sql, "error": str(e)})
                    log(f"Error executing: {sql}\nError: {e}")
            cursor.close()
            conn.close()
        except Exception as e:
            log(f"Database connection failed: {e}")
    else:
        log("No database connection string provided. Skipping SQL execution.")

    # 3. Ask LLM for analysis and recommendations
    prompt2 = (
        f"Log summary:\n{log_summary}\n\n"
        f"Code analysis:\n{code_analysis}\n\n"
        f"SQL query results:\n{results}\n\n"
        "Explain likely root causes, recommend query/index/config optimizations, "
        "and provide optimized SQL if needed. Respond for a human DBA."
    )
    analysis = chat_with_model(prompt2)
    log(f"LLM analysis:\n{analysis}")

    # 4. Return human-readable analysis
    return analysis