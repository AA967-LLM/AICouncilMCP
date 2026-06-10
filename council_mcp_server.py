"""
AI Council MCP Server v1.0
Antigravity CLI — Council Tool Dispatcher
Exposes each council member as a callable MCP tool.
Logs every delegation decision to council_audit.log
"""

import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# ── Config ────────────────────────────────────────────────────────────────────

OLLAMA_BASE       = "http://localhost:11434/v1"
OLLAMA_MODEL      = "claude-3-5-sonnet:latest"
OLLAMA_API        = "http://localhost:11434/api/generate"
DEEPSEEK_API      = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY  = os.environ.get("DEEPSEEK_API_KEY", "")
AIDER_EXE         = r"C:\Users\AA_p\AppData\Local\Programs\Python\Python312\Scripts\aider.exe"
CLAUDE_CODE_EXE   = r"C:\Users\AA_p\AppData\Roaming\npm\claude.cmd"
LOG_PATH          = r"D:\Google antigravity\SYSTEM\council_audit.log"
VRAM_LIMIT_MIB    = 10500

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def audit(member: str, task: str, duration_s: float, result_preview: str):
    logging.info(
        f"MEMBER={member} | DURATION={duration_s:.2f}s | "
        f"TASK={task[:80]!r} | RESULT={result_preview[:120]!r}"
    )

# ── VRAM check ────────────────────────────────────────────────────────────────

def vram_used_mib() -> int:
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            timeout=5,
        )
        return int(out.decode().strip())
    except Exception:
        return 0

# ── Council members ───────────────────────────────────────────────────────────

def call_zeta(prompt: str, context: str = "") -> dict:
    """Direct Ollama API call — fastest, zero cloud tokens."""
    full = f"{context}\n\n{prompt}".strip() if context else prompt
    start = time.time()
    try:
        r = httpx.post(
            OLLAMA_API,
            json={"model": OLLAMA_MODEL, "prompt": full, "stream": False, "think": False},
            timeout=120,
        )
        r.raise_for_status()
        data = r.json()
        response = data.get("response", "").strip()
        duration = time.time() - start
        audit("Zeta", prompt, duration, response)
        return {"member": "Zeta", "model": OLLAMA_MODEL, "response": response,
                "duration_s": round(duration, 2), "tokens_used": "local_only"}
    except Exception as e:
        return {"member": "Zeta", "error": str(e)}


def call_epsilon(prompt: str, context: str = "") -> dict:
    """DeepSeek V4 Flash — mid-tier cloud, fast."""
    return _call_deepseek("deepseek-chat", "Epsilon", prompt, context)


def call_delta(prompt: str, context: str = "") -> dict:
    """DeepSeek V4 Pro — heavy tier, maximum reasoning."""
    return _call_deepseek("deepseek-reasoner", "Delta", prompt, context)


def _call_deepseek(model: str, member: str, prompt: str, context: str) -> dict:
    if not DEEPSEEK_API_KEY:
        return {"member": member, "error": "DEEPSEEK_API_KEY not set in environment"}
    messages = []
    if context:
        messages.append({"role": "system", "content": context})
    messages.append({"role": "user", "content": prompt})
    start = time.time()
    try:
        r = httpx.post(
            DEEPSEEK_API,
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                     "Content-Type": "application/json"},
            json={"model": model, "messages": messages, "max_tokens": 4096},
            timeout=120,
        )
        r.raise_for_status()
        data = r.json()
        response = data["choices"][0]["message"]["content"].strip()
        usage = data.get("usage", {})
        duration = time.time() - start
        audit(member, prompt, duration, response)
        return {"member": member, "model": model, "response": response,
                "duration_s": round(duration, 2),
                "tokens_used": usage.get("total_tokens", "unknown")}
    except Exception as e:
        return {"member": member, "error": str(e)}


def call_aider(task: str, files: list[str] | None = None) -> dict:
    """Launch Aider with Zeta endpoint for autonomous code editing."""
    start = time.time()
    try:
        cmd = [
            AIDER_EXE,
            "--model", f"openai/{OLLAMA_MODEL}",
            "--openai-api-base", OLLAMA_BASE,
            "--openai-api-key", "ollama",
            "--yes",
            "--message", task,
            "--no-pretty",
        ]
        if files:
            cmd += files
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        response = result.stdout.strip() or result.stderr.strip()
        duration = time.time() - start
        audit("Aider", task, duration, response)
        return {"member": "Aider", "model": OLLAMA_MODEL,
                "response": response, "duration_s": round(duration, 2),
                "tokens_used": "local_only"}
    except Exception as e:
        return {"member": "Aider", "error": str(e)}


def call_hermes(task: str) -> dict:
    """Launch Hermes agent for multi-step agentic workflows."""
    start = time.time()
    try:
        result = subprocess.run(
            ["hermes", "-z", task],
            capture_output=True, text=True, timeout=300,
        )
        response = result.stdout.strip() or result.stderr.strip()
        duration = time.time() - start
        audit("Hermes", task, duration, response)
        return {"member": "Hermes", "model": OLLAMA_MODEL,
                "response": response, "duration_s": round(duration, 2),
                "tokens_used": "local_only"}
    except Exception as e:
        return {"member": "Hermes", "error": str(e)}


def call_claude_code(task: str, directory: str = ".") -> dict:
    """Launch Claude Code with Zeta endpoint for IDE-integrated coding."""
    start = time.time()
    try:
        result = subprocess.run(
            [CLAUDE_CODE_EXE, "-p", task, "--model", "claude-3-5-sonnet-20241022"],
            capture_output=True, text=True, timeout=300,
            cwd=directory,
            env={**os.environ,
                 "ANTHROPIC_BASE_URL": "http://localhost:8000",
                 "ANTHROPIC_API_KEY": "sk-lite-any-key"},
        )
        response = result.stdout.strip() or result.stderr.strip()
        duration = time.time() - start
        audit("ClaudeCode", task, duration, response)
        return {"member": "ClaudeCode", "model": OLLAMA_MODEL,
                "response": response, "duration_s": round(duration, 2),
                "tokens_used": "local_only"}
    except Exception as e:
        return {"member": "ClaudeCode", "error": str(e)}


def council_vote(question: str) -> dict:
    """
    Submit a question to Zeta, Epsilon, and Delta.
    Returns weighted majority verdict.
    Weights: Zeta=1, Epsilon=2, Delta=3
    """
    start = time.time()
    vote_prompt = (
        f"Council vote required. Answer with ONLY a JSON object with keys: "
        f"'verdict' (your recommendation in one sentence), "
        f"'confidence' (0.0-1.0), 'reasoning' (max 2 sentences). "
        f"Question: {question}"
    )
    results = {}
    for member, fn in [("Zeta", call_zeta), ("Epsilon", call_epsilon), ("Delta", call_delta)]:
        r = fn(vote_prompt)
        results[member] = r

    # Parse verdicts
    verdicts = []
    weights = {"Zeta": 1, "Epsilon": 2, "Delta": 3}
    for member, r in results.items():
        if "error" not in r:
            try:
                raw = r["response"]
                # Strip markdown fences if present
                clean = raw.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(clean)
                verdicts.append({
                    "member": member,
                    "weight": weights[member],
                    "verdict": parsed.get("verdict", ""),
                    "confidence": parsed.get("confidence", 0),
                    "reasoning": parsed.get("reasoning", ""),
                })
            except Exception:
                verdicts.append({
                    "member": member,
                    "weight": weights[member],
                    "verdict": r["response"][:200],
                    "confidence": 0.5,
                    "reasoning": "Could not parse structured response",
                })

    # Weighted score
    total_weight = sum(v["weight"] * v["confidence"] for v in verdicts)
    duration = time.time() - start
    audit("CouncilVote", question, duration, str(verdicts))

    return {
        "question": question,
        "votes": verdicts,
        "weighted_confidence": round(total_weight / 6, 3),  # max weight=6
        "duration_s": round(duration, 2),
        "recommendation": verdicts[-1]["verdict"] if verdicts else "No verdict",
    }


def check_vram() -> dict:
    """Check current VRAM usage and report council routing recommendation."""
    used = vram_used_mib()
    status = "ok" if used < VRAM_LIMIT_MIB else "exceeded"
    recommendation = (
        "Route to Zeta normally" if used < VRAM_LIMIT_MIB
        else "VRAM limit exceeded — defer local tasks to Epsilon"
    )
    return {
        "vram_used_mib": used,
        "vram_limit_mib": VRAM_LIMIT_MIB,
        "status": status,
        "recommendation": recommendation,
    }

# ── MCP Server ────────────────────────────────────────────────────────────────

server = Server("council-mcp")

TOOLS = [
    Tool(
        name="consult_zeta",
        description=(
            "Consult Zeta — Ollama Agent (Gemma 4 local). "
            "Use for: summarisation, file reading, code explanation, "
            "drafting, boilerplate, regex, any task under 24K tokens. "
            "Zero cloud token cost."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Task to delegate to Zeta"},
                "context": {"type": "string", "description": "Optional context or background"},
            },
            "required": ["prompt"],
        },
    ),
    Tool(
        name="consult_epsilon",
        description=(
            "Consult Epsilon — DeepSeek V4 Flash. "
            "Use when: Zeta confidence below 0.7, moderate coding tasks, "
            "cloud reasoning needed but speed matters, 24K-100K tokens."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Task to delegate to Epsilon"},
                "context": {"type": "string", "description": "Optional context"},
            },
            "required": ["prompt"],
        },
    ),
    Tool(
        name="consult_delta",
        description=(
            "Consult Delta — DeepSeek V4 Pro. "
            "Use when: complex architecture, multi-file debugging, "
            "strategic planning, Epsilon fails. Maximum reasoning depth."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Task to delegate to Delta"},
                "context": {"type": "string", "description": "Optional context"},
            },
            "required": ["prompt"],
        },
    ),
    Tool(
        name="consult_aider",
        description=(
            "Consult Aider — autonomous code writing and editing via Zeta. "
            "Use for: writing new code files, refactoring existing code, "
            "automated multi-file edits. Optionally pass file paths."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Coding task for Aider"},
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of file paths for Aider to edit",
                },
            },
            "required": ["task"],
        },
    ),
    Tool(
        name="consult_hermes",
        description=(
            "Consult Hermes — agentic multi-step workflows via Zeta. "
            "Use for: tasks requiring tool use, file operations, "
            "web browsing, multi-step automation."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Agentic task for Hermes"},
            },
            "required": ["task"],
        },
    ),
    Tool(
        name="consult_claude_code",
        description=(
            "Consult Claude Code — IDE-integrated coding via Zeta. "
            "Use for: codebase-aware tasks, project-level coding, "
            "when working within a specific directory."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Coding task for Claude Code"},
                "directory": {
                    "type": "string",
                    "description": "Working directory for Claude Code (default: current)",
                },
            },
            "required": ["task"],
        },
    ),
    Tool(
        name="council_vote",
        description=(
            "Submit a question to Zeta, Epsilon, and Delta for a weighted majority vote. "
            "Use when Alpha is uncertain and needs council consensus. "
            "Returns weighted verdict with confidence scores."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "Question requiring council vote"},
            },
            "required": ["question"],
        },
    ),
    Tool(
        name="check_vram",
        description=(
            "Check current GPU VRAM usage and get routing recommendation. "
            "Use before any local Zeta task if system feels slow."
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
]


@server.list_tools()
async def list_tools() -> list[Tool]:
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    dispatch = {
        "consult_zeta":       lambda: call_zeta(arguments["prompt"], arguments.get("context", "")),
        "consult_epsilon":    lambda: call_epsilon(arguments["prompt"], arguments.get("context", "")),
        "consult_delta":      lambda: call_delta(arguments["prompt"], arguments.get("context", "")),
        "consult_aider":      lambda: call_aider(arguments["task"], arguments.get("files")),
        "consult_hermes":     lambda: call_hermes(arguments["task"]),
        "consult_claude_code":lambda: call_claude_code(arguments["task"], arguments.get("directory", ".")),
        "council_vote":       lambda: council_vote(arguments["question"]),
        "check_vram":         lambda: check_vram(),
    }
    fn = dispatch.get(name)
    if not fn:
        result = {"error": f"Unknown tool: {name}"}
    else:
        result = fn()
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


# ── Entry point ───────────────────────────────────────────────────────────────

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream,
                         server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
