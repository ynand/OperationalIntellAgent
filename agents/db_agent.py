import json
import re
import csv
import os
from llm_client import chat_with_model
from vector_db_client import get_relevant_context  # Ensure this is implemented

def db_agent(config):
    """
    Uses LLM to iteratively generate diagnostics, runs SQL queries, and exports results to CSV.
    Args:
        config (dict): {
            'log_summary': str,
            'code_analysis': str,
            'db_conn_str': (optional) pyodbc connection string,
            'log_file': (optional) path to log file,
            'output_dir': (optional) directory to save CSV files
        }
    Returns:
        str: Human-readable analysis.
    """
    import pyodbc
    log_file = config.get("log_file", "db_agent.log")
    output_dir = config.get("output_dir", "output")
    os.makedirs(output_dir, exist_ok=True)

    def log(msg):
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
        print(msg)

    def clean_sql(raw_sql):
        # Remove markdown and text before/after SQL
        cleaned = re.sub(r"```[\w]*", "", raw_sql)
        cleaned = cleaned.replace("```", "").strip()

        # Keep only first SELECT/DBCC/EXEC query if multiple exist
        match = re.search(r"(SELECT|DBCC|EXEC|WITH)\s.*", cleaned, re.IGNORECASE | re.DOTALL)
        return match.group(0).strip() if match else cleaned


    log_summary = config.get("log_summary", "")
    code_analysis = config.get("code_analysis", "")
    db_conn_str = config.get("db_conn_str")
    context = {
        "log_summary": log_summary,
        "code_analysis": code_analysis,
        "previous_results": []
    }

    if db_conn_str:
        try:
            conn = pyodbc.connect(db_conn_str)
            cursor = conn.cursor()
            for step in range(10):
                rag_context = get_relevant_context(query=json.dumps(context["previous_results"]), top_k=3)

                prompt = f"""
                    You are an expert SQL Server DBA.
                    Goal: Identify root causes of issues such as:
                    - Long-running or blocking queries
                    - Missing indexes
                    - Memory/TempDB bottlenecks
                    - Database size or file growth issues
                    - High waits or deadlocks

                    **Rules for your response:**
                    - Output ONLY ONE valid T-SQL query.
                    - Do NOT add explanations, markdown, comments, or multiple queries.
                    - Do NOT use fictitious columns like 'percentage_used' or 'total_rows_returned_by_cursor_at_row...'.
                    - If enough information is already collected, reply ONLY with the word: DONE.

                    Example valid query:
                    SELECT TOP 10
                        session_id, status, command, blocking_session_id,
                        wait_type, wait_time, cpu_time, total_elapsed_time
                    FROM sys.dm_exec_requests
                    ORDER BY total_elapsed_time DESC;

                    Now, based on this context:
                    Relevant context:
                    {context['rag_context']}
                    Log summary:
                    {context['log_summary']}

                    Code analysis:
                    {context['code_analysis']}

                    Previous query results:
                    {json.dumps(context['previous_results'], indent=2)}

                    Suggest ONE next diagnostic query or reply DONE.
                    """

                sql_suggestion = chat_with_model(prompt).strip()
                log(f"LLM suggested SQL query:\n{sql_suggestion}")

                if sql_suggestion.upper() == "DONE":
                    log("LLM indicated analysis is complete.")
                    break

                sql_to_run = clean_sql(sql_suggestion)

                try:
                    cursor.execute(sql_to_run)
                    rows = cursor.fetchall()
                    col_names = [desc[0] for desc in cursor.description]
                    result = [dict(zip(col_names, row)) for row in rows]
                    context["previous_results"].append({"query": sql_to_run, "result": result})

                    # Export results to CSV
                    csv_file_path = os.path.join(output_dir, f"query_result_step_{step+1}.csv")
                    with open(csv_file_path, mode="w", newline="", encoding="utf-8") as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=col_names)
                        writer.writeheader()
                        writer.writerows(result)
                    log(f"Executed: {sql_to_run}\nExported results to {csv_file_path}")

                except Exception as e:
                    error_msg = str(e)
                    context["previous_results"].append({"query": sql_to_run, "error": error_msg})
                    log(f"Error executing: {sql_to_run}\nError: {error_msg}")
            cursor.close()
            conn.close()
        except Exception as e:
            log(f"Database connection failed: {e}")
    else:
        log("No database connection string provided. Skipping SQL execution.")

    prompt2 = (
        f"Log summary:\n{log_summary}\n\n"
        f"Code analysis:\n{code_analysis}\n\n"
        f"SQL query results:\n{context['previous_results']}\n\n"
        "Explain likely root causes, recommend query/index/config optimizations, and provide optimized SQL if needed."
    )
    analysis = chat_with_model(prompt2)
    log(f"LLM analysis:\n{analysis}")

    return analysis
