import os
import json
import urllib.request
import sys
import hashlib
import sqlite3
import time

# Configure stdout encoding
sys.stdout.reconfigure(encoding='utf-8')

# Import FastMCP
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("Error: mcp package not installed. Run via: uv run --with mcp donkey_mcp.py")
    sys.exit(1)

# Initialize FastMCP server
mcp = FastMCP("donkey-offloader")

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "claude-3-5-sonnet:latest"
CACHE_DB = r"D:\Google antigravity\.env\cache.db"

# Initialize Cache DB
def init_db():
    try:
        os.makedirs(os.path.dirname(CACHE_DB), exist_ok=True)
        conn = sqlite3.connect(CACHE_DB)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                hash TEXT PRIMARY KEY,
                task_type TEXT,
                summary TEXT,
                timestamp INTEGER
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Warning: Failed to initialize cache database: {e}", file=sys.stderr)

def get_cached_summary(text: str, task_type: str) -> str:
    try:
        key = hashlib.sha256(text.encode('utf-8', errors='ignore')).hexdigest()
        conn = sqlite3.connect(CACHE_DB)
        row = conn.execute("SELECT summary FROM cache WHERE hash=? AND task_type=?", (key, task_type)).fetchone()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        print(f"Warning: Cache read error: {e}", file=sys.stderr)
        return None

def store_cache(text: str, task_type: str, summary: str):
    try:
        key = hashlib.sha256(text.encode('utf-8', errors='ignore')).hexdigest()
        conn = sqlite3.connect(CACHE_DB)
        conn.execute("INSERT OR REPLACE INTO cache VALUES (?,?,?,?)", (key, task_type, summary, int(time.time())))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Warning: Cache write error: {e}", file=sys.stderr)

def query_ollama(prompt: str) -> str:
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "think": False
    }
    headers = {'Content-Type': 'application/json'}
    req = urllib.request.Request(OLLAMA_URL, data=json.dumps(payload).encode('utf-8'), headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data.get("response", "No response from Ollama.")
    except Exception as e:
        return f"Error communicating with local Ollama service: {e}. Make sure Ollama is running and model '{MODEL_NAME}' is loaded."

@mcp.tool()
def summarize_file(file_path: str) -> str:
    """Reads a local text file and generates a token-saving structured summary using local Qwen-14B (with local SQLite cache)."""
    if not os.path.exists(file_path):
        return f"Error: File not found at {file_path}"
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        return f"Error reading file: {e}"
        
    if not content.strip():
        return "File is empty."

    # Check Cache
    cached = get_cached_summary(content, "summarize_file")
    if cached:
        return f"[CACHE HIT] {cached}"

    # If the file is extremely large, warn
    if len(content) > 100000:
        content = content[:100000] + "\n... [TRUNCATED DUE TO SIZE] ..."

    prompt = f"""You are a code/document compression agent.
Analyze the following file and return a concise, token-efficient summary.
File Path: {file_path}
Content:
---
{content}
---

Provide a highly compact, comments-free, and token-saving summary. List only:
- Primary purpose.
- Crucial configuration details/exports.
- A minified outline of its structure/dependencies.
"""
    summary = query_ollama(prompt)
    if not summary.startswith("Error"):
        store_cache(content, "summarize_file", summary)
    return summary

@mcp.tool()
def compress_context(text: str, focus: str = "") -> str:
    """Compresses any large raw text into a minified, high-density summary (with local SQLite cache)."""
    if not text.strip():
        return "Context is empty."
        
    # Check Cache
    cache_key = f"{text}||focus:{focus}"
    cached = get_cached_summary(cache_key, "compress_context")
    if cached:
        return f"[CACHE HIT] {cached}"

    focus_str = f" Focus specifically on: {focus}" if focus else ""

    prompt = f"""Compress the following context into a high-density, token-efficient representation.{focus_str}
Remove all boilerplate, excessive formatting, and redundant descriptions. Keep only core semantic facts.
Context:
---
{text}
---
"""
    summary = query_ollama(prompt)
    if not summary.startswith("Error"):
        store_cache(cache_key, "compress_context", summary)
    return summary

@mcp.tool()
def parse_log_file(file_path: str) -> str:
    """Parses a large system log file, filters out noise, and extracts a compact summary of critical errors (with local SQLite cache)."""
    if not os.path.exists(file_path):
        return f"Error: Log file not found at {file_path}"
        
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        return f"Error reading log file: {e}"

    # Filter lines that look like errors/warnings to reduce input tokens
    relevant_lines = []
    for line in lines:
        l_lower = line.lower()
        if "error" in l_lower or "fail" in l_lower or "warn" in l_lower or "critical" in l_lower or "exception" in l_lower:
            relevant_lines.append(line)
            
    if not relevant_lines:
        return "No errors, failures, or warnings detected in the log file."

    filtered_text = "".join(relevant_lines)
    
    # Check Cache
    cached = get_cached_summary(filtered_text, "parse_log_file")
    if cached:
        return f"[CACHE HIT] {cached}"

    log_snippet = "".join(relevant_lines[:1000]) # Cap input to prevent context blowup
    
    prompt = f"""You are a log analysis agent. Analyze this filtered log snippet and output a compact report of:
1. The root cause of the primary failure/error.
2. A bulleted list of distinct critical errors/warnings (deduplicated).
3. The frequency or count of these errors if detectable.

Log Snippet:
---
{log_snippet}
---
"""
    summary = query_ollama(prompt)
    if not summary.startswith("Error"):
        store_cache(filtered_text, "parse_log_file", summary)
    return summary

# Initialize Cache Database
init_db()

if __name__ == "__main__":
    mcp.run()
