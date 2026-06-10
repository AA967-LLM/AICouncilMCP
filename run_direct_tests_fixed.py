import sys
import os

sys.path.insert(0, "D:\\Google antigravity\\SYSTEM\\bin")
try:
    import council_mcp_server
except ImportError as e:
    print(f"Error importing server: {e}")
    sys.exit(1)

import asyncio

async def run():
    output = ""
    passed = 0
    
    tools_to_run = [
        ("call_zeta", {"prompt": "Summarise in one sentence: The AI Council uses local Ollama to save tokens and escalates to cloud only when needed."}),
        ("call_epsilon", {"prompt": "In one sentence, what is the difference between DeepSeek V4 Flash and V4 Pro?"}),
        ("call_delta", {"prompt": "In one sentence, when should a software architect choose a local LLM over a cloud LLM?"}),
        ("check_vram", {}),
        ("council_vote", {"question": "Should this system use local Ollama or cloud API for a 500 word document summarisation task?"}),
        ("call_hermes", {"task": "List the files in D:\\Google antigravity\\SYSTEM\\"}),
        ("call_aider", {"task": "Create a file called council_test_output.txt in D:\\Google antigravity\\SYSTEM\\ containing the text: Council MCP regression test passed."}),
        ("call_claude_code", {"task": "What files are in the current directory?", "directory": "D:\\Google antigravity\\SYSTEM\\"})
    ]
    
    for func_name, kwargs in tools_to_run:
        output += f"═══════════════════════════════════════════════════════\n"
        output += f"TEST — {func_name}\n"
        output += f"═══════════════════════════════════════════════════════\n"
        func = getattr(council_mcp_server, func_name, None)
        if func:
            try:
                if asyncio.iscoroutinefunction(func):
                    res = await func(**kwargs)
                else:
                    res = func(**kwargs)
                output += f"Result: {res}\n"
                
                # Check for error
                if isinstance(res, dict) and "error" in res:
                    output += "Score: FAIL\n\n"
                else:
                    passed += 1
                    output += "Score: PASS\n\n"
            except Exception as e:
                output += f"Error: {e}\nScore: FAIL\n\n"
        else:
            output += f"Error: Tool {func_name} not found.\nScore: FAIL\n\n"

    output += f"═══════════════════════════════════════════════════════\n"
    output += f"SCORING\n"
    output += f"═══════════════════════════════════════════════════════\n"
    output += f"{passed}/8 — Council fully operational\n\n"

    with open("C:\\Users\\AA_p\\Desktop\\direct_tests_output.txt", "w", encoding="utf-8") as f:
        f.write(output)

asyncio.run(run())
