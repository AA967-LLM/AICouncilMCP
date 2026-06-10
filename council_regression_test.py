# AI Council V7 — MCP Regression Test
# Run this via AGY CLI to verify all council members are reachable
# and delegation is working correctly.
#
# Usage: paste entire block into AGY CLI

COUNCIL_MCP_REGRESSION_TEST = """
Run the following regression test against the council MCP server.
Call each tool explicitly and report exact results. Do not answer
from your own knowledge — actually invoke each MCP tool.

═══════════════════════════════════════════════════════
TEST 1 — Zeta reachability (consult_zeta)
═══════════════════════════════════════════════════════
Tool: consult_zeta
Prompt: "Summarise in one sentence: The AI Council uses local
Ollama to save tokens and escalates to cloud only when needed."
Expected:
- member = Zeta
- tokens_used = local_only
- duration_s < 30
- No error field
Score: PASS / FAIL

═══════════════════════════════════════════════════════
TEST 2 — Epsilon reachability (consult_epsilon)
═══════════════════════════════════════════════════════
Tool: consult_epsilon
Prompt: "In one sentence, what is the difference between
DeepSeek V4 Flash and V4 Pro?"
Expected:
- member = Epsilon
- tokens_used is a number
- duration_s < 30
- No error field
Score: PASS / FAIL

═══════════════════════════════════════════════════════
TEST 3 — Delta reachability (consult_delta)
═══════════════════════════════════════════════════════
Tool: consult_delta
Prompt: "In one sentence, when should a software architect
choose a local LLM over a cloud LLM?"
Expected:
- member = Delta
- tokens_used is a number
- duration_s < 60
- No error field
Score: PASS / FAIL

═══════════════════════════════════════════════════════
TEST 4 — VRAM check (check_vram)
═══════════════════════════════════════════════════════
Tool: check_vram
Expected:
- vram_used_mib is a real number
- vram_limit_mib = 10500
- status = ok or exceeded
- recommendation present
Score: PASS / FAIL

═══════════════════════════════════════════════════════
TEST 5 — Council vote (council_vote)
═══════════════════════════════════════════════════════
Tool: council_vote
Question: "Should this system use local Ollama or cloud API
for a 500 word document summarisation task?"
Expected:
- votes contains 3 entries (Zeta, Epsilon, Delta)
- weighted_confidence is between 0 and 1
- recommendation is present
- duration_s present
Score: PASS / FAIL

═══════════════════════════════════════════════════════
TEST 6 — Hermes reachability (consult_hermes)
═══════════════════════════════════════════════════════
Tool: consult_hermes
Task: "List the files in D:\\Google antigravity\\SYSTEM\\"
Expected:
- member = Hermes
- tokens_used = local_only
- response contains file names
- No error field
Score: PASS / FAIL

═══════════════════════════════════════════════════════
TEST 7 — Aider reachability (consult_aider)
═══════════════════════════════════════════════════════
Tool: consult_aider
Task: "Create a file called council_test_output.txt in
D:\\Google antigravity\\SYSTEM\\ containing the text:
Council MCP regression test passed."
Expected:
- member = Aider
- tokens_used = local_only
- No error field
- File exists after test
Score: PASS / FAIL

═══════════════════════════════════════════════════════
TEST 8 — Claude Code reachability (consult_claude_code)
═══════════════════════════════════════════════════════
Tool: consult_claude_code
Task: "What files are in the current directory?"
Directory: "D:\\Google antigravity\\SYSTEM\\"
Expected:
- member = ClaudeCode
- tokens_used = local_only
- response contains file listing
- No error field
Score: PASS / FAIL

═══════════════════════════════════════════════════════
TEST 9 — Delegation audit
═══════════════════════════════════════════════════════
After all tests confirm:
1. How many tools returned errors?
2. Which members were local_only?
3. Which members used cloud tokens?
4. Is council_audit.log being written?
   Check: type "D:\\Google antigravity\\SYSTEM\\council_audit.log"

═══════════════════════════════════════════════════════
SCORING
═══════════════════════════════════════════════════════
8/8 — Council fully operational
6-7/8 — Minor issues, identify failed tools
4-5/8 — Partial council, escalation chain at risk
Below 4 — Council broken, do not use for production tasks

Report final score, list any failed tests with exact
error messages, and paste last 20 lines of audit log.
Do not summarise. Show all raw tool outputs.
"""

print(COUNCIL_MCP_REGRESSION_TEST)
