import json
from llm_client import chat_with_model
from vector_db_client import get_relevant_context  # You need to implement this

def db_agent(config):
    """
    Uses LLM to iteratively generate diagnostics, runs SQL queries, and returns/explains results.
    Each SQL suggestion is generated one at a time based on previous results.
    Args:
        config (dict): {
            'log_summary': str,
            'code_analysis': str,
            'db_conn_str': (optional) pyodbc connection string,
            'log_file': (optional) path to log file
        }
    Returns:
        dict: Human-readable analysis and query results.
    """
    import pyodbc
    log_file = config.get("log_file", "db_agent.log")
    def log(msg):
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
        print(msg)

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
            for step in range(10):  # Limit to 10 steps to avoid infinite loops
                # Retrieve relevant context using RAG
                rag_context = get_relevant_context(
                    query=json.dumps(context["previous_results"]),
                    top_k=3
                )

                # Ask LLM for the next diagnostic SQL query based on context + RAG
                prompt = (
                    f"Relevant context:\n{rag_context}\n"
                    f"Log summary:\n{context['log_summary']}\n"
                    f"Code analysis:\n{context['code_analysis']}\n"
                    f"Previous query results:\n{json.dumps(context['previous_results'], indent=2)}\n"
                    "Suggest the next most relevant SQL Server diagnostic query to help identify root causes. "
                    "Only return the T-SQL statement, or reply 'DONE' if enough information is available for analysis."
                )
                sql_suggestion = chat_with_model(prompt).strip()
                log(f"LLM suggested SQL query:\n{sql_suggestion}")

                if sql_suggestion.upper() == "DONE":
                    log("LLM indicated analysis is complete.")
                    break

                # Execute the suggested SQL query
                try:
                    cursor.execute(sql_suggestion)
                    rows = cursor.fetchall()
                    col_names = [desc[0] for desc in cursor.description]
                    result = [dict(zip(col_names, row)) for row in rows]
                    context["previous_results"].append({"query": sql_suggestion, "result": result})
                    log(f"Executed: {sql_suggestion}\nResult: {result}")
                except Exception as e:
                    error_msg = str(e)
                    context["previous_results"].append({"query": sql_suggestion, "error": error_msg})
                    log(f"Error executing: {sql_suggestion}\nError: {error_msg}")

                    # Ask LLM to correct the query
                    correction_prompt = (
                        f"The following SQL Server query failed with error:\n"
                        f"Query: {sql_suggestion}\n"
                        f"Error: {error_msg}\n"
                        "Please correct the query for SQL Server syntax and return only the corrected T-SQL statement."
                    )
                    corrected_query = chat_with_model(correction_prompt).strip()
                    log(f"LLM suggested corrected query:\n{corrected_query}")

                    # Try executing the corrected query once
                    try:
                        cursor.execute(corrected_query)
                        rows = cursor.fetchall()
                        col_names = [desc[0] for desc in cursor.description]
                        result = [dict(zip(col_names, row)) for row in rows]
                        context["previous_results"].append({"query": corrected_query, "result": result})
                        log(f"Executed corrected query: {corrected_query}\nResult: {result}")
                    except Exception as e2:
                        error_msg2 = str(e2)
                        context["previous_results"].append({"query": corrected_query, "error": error_msg2})
                        log(f"Error executing corrected query: {corrected_query}\nError: {error_msg2}")
            cursor.close()
            conn.close()
        except Exception as e:
            log(f"Database connection failed: {e}")
    else:
        log("No database connection string provided. Skipping SQL execution.")

    # Ask LLM for analysis and recommendations
    prompt2 = (
        f"Log summary:\n{log_summary}\n\n"
        f"Code analysis:\n{code_analysis}\n\n"
        f"SQL query results:\n{context['previous_results']}\n\n"
        "Explain likely root causes, recommend query/index/config optimizations, "
        "and provide optimized SQL if needed. Respond for a human DBA."
    )
    analysis = chat_with_model(prompt2)
    log(f"LLM analysis:\n{analysis}")

    # Return human-readable analysis and query results
    return {
        "analysis": analysis,
        "query_results": context["previous_results"]
    }