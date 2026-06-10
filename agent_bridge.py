import os
import subprocess
import logging
import requests
import json
from typing import Optional, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AgentBridge")

def get_keys():
    keys = {}
    vault_path = r"D:\Google antigravity\.env\.env"
    if os.path.exists(vault_path):
        with open(vault_path, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    k, v = line.split("=", 1)
                    keys[k.strip()] = v.strip().strip('"').strip("'")
    return keys

class Tiers:
    def __init__(self):
        self.keys = get_keys()

    def execute_tier1(self, task: str) -> str:
        """Tier 1: Ollama (local, RTX 4080) - Fast, $0, generates heat."""
        logger.info("Executing on Tier 1 (Local Ollama)...")
        models = ["claude-3-5-sonnet:latest"]
        last_err = None
        for model in models:
            try:
                logger.info(f"Attempting Tier 1 execution using model: {model}")
                payload = {"model": model, "prompt": task, "stream": False}
                resp = requests.post("http://localhost:11434/api/generate", json=payload, timeout=120)
                resp.raise_for_status()
                return resp.json().get("response", "").strip()
            except Exception as e:
                logger.warning(f"Failed to execute model '{model}': {e}")
                last_err = e
                continue
        raise RuntimeError(f"Tier 1 (Local Ollama) failed all models. Last error: {last_err}")

    def execute_tier2(self, task: str) -> str:
        """Tier 2: Gemini CLI - Cloud, $0 marginal (subscription), zero laptop heat."""
        logger.info("Executing on Tier 2 (Gemini CLI)...")
        home = os.path.expanduser("~")
        agy_path = os.path.join(home, "AppData", "Local", "agy", "bin", "agy.exe")
        commands_to_try = []
        if os.path.exists(agy_path):
            commands_to_try.append([agy_path, "--print", task])
        commands_to_try.append(["agy.exe", "--print", task])
        
        last_error = None
        for cmd in commands_to_try:
            try:
                logger.info(f"Running Gemini CLI command: {' '.join(cmd)}")
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=15
                )
                stdout = result.stdout.strip()
                stderr = result.stderr.strip()
                combined = (stdout + "\n" + stderr).lower()
                if any(kw in combined for kw in ["quota reached", "quota exceeded", "overages", "resource_exhausted"]):
                    raise RuntimeError(f"Gemini API Quota Exceeded in output: {combined}")
                return stdout
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
                if isinstance(e, subprocess.CalledProcessError):
                    combined = ((e.stdout or "") + "\n" + (e.stderr or "")).lower()
                    if any(kw in combined for kw in ["quota reached", "quota exceeded", "overages", "resource_exhausted"]):
                        raise RuntimeError(f"Gemini API Quota Exceeded in subprocess error: {combined}")
                elif isinstance(e, subprocess.TimeoutExpired):
                    logger.warning(f"Command {' '.join(cmd)} timed out after 15s")
                last_error = e
                continue
        raise RuntimeError(f"Tier 2 failed to execute Gemini CLI. Last error: {last_error}")

    def execute_tier3(self, task: str) -> str:
        """Tier 3: Web scrape via Carbonyl - Free, but fragile and slow."""
        logger.info("Executing on Tier 3 (Carbonyl Web Scrape)...")
        logger.warning("Council Verdict: Web scraping is fragile. Prefer Tier 2 for bulk tasks.")
        # Placeholder for actual carbonyl automation. 
        # In reality, this requires a complex Playwright/Selenium script to navigate UI and bypass captchas.
        return "[Tier 3 Web Scrape] Functionality restricted due to Captcha/Rate-limit fragility. Routing back to Tier 2 is recommended."

    def execute_tier4(self, task: str) -> str:
        """Tier 4: DeepSeek V4 API - 'God-mode', high logic, paid per token."""
        logger.info("Executing on Tier 4 (DeepSeek API)...")
        api_key = self.keys.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in vault.")
        
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        payload = {"model": "deepseek-reasoner", "messages": [{"role": "user", "content": task}], "stream": False}
        resp = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload, timeout=180)
        resp.raise_for_status()
        return resp.json()['choices'][0]['message']['content'].strip()


class AgentBridge:
    ARCHITECT_KEYWORDS = {"architect", "refactor", "design", "system", "orchestrate", "complex"}
    URGENCY_BOOST = 2

    def __init__(self, temp_threshold: float = 75.0):
        self.temp_threshold = temp_threshold
        self.tiers = Tiers()

    def _get_gpu_temp(self) -> Optional[float]:
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            return float(result.stdout.strip().split()[0])
        except Exception as e:
            logger.warning(f"Failed to read GPU temperature: {e}")
            return None

    def _compute_complexity(self, task: str, output_format: Optional[str] = None) -> int:
        score = 1
        length = len(task)
        if length > 1000:
            score += 3
        elif length > 500:
            score += 2
        elif length > 150:
            score += 1

        task_lower = task.lower()
        keyword_hits = sum(1 for kw in self.ARCHITECT_KEYWORDS if kw in task_lower)
        if keyword_hits >= 2:
            score += 4
        elif keyword_hits == 1:
            score += 2

        if output_format:
            fmt = output_format.lower()
            if fmt in ("code", "architecture", "plan"):
                score += 2
            elif fmt in ("summary", "explain"):
                score += 1

        return min(score, 10)

    def _is_ollama_available(self) -> bool:
        try:
            resp = requests.get("http://localhost:11434/api/tags", timeout=2)
            return resp.status_code == 200
        except:
            return False

    def _execute_with_fallback(self, tier_priority: List[int], task: str) -> str:
        for tier in tier_priority:
            try:
                if tier == 1:
                    return self.tiers.execute_tier1(task)
                elif tier == 2:
                    return self.tiers.execute_tier2(task)
                elif tier == 3:
                    return self.tiers.execute_tier3(task)
                elif tier == 4:
                    return self.tiers.execute_tier4(task)
            except Exception as e:
                logger.error(f"Tier {tier} failed: {e}")
                continue
        raise RuntimeError("All tiers exhausted and failed.")

    def route_task(self, task: str, urgency: bool = False, output_format: Optional[str] = None) -> str:
        complexity = self._compute_complexity(task, output_format)
        if urgency:
            complexity = min(complexity + self.URGENCY_BOOST, 10)

        gpu_temp = self._get_gpu_temp()
        if gpu_temp is None:
            gpu_temp = self.temp_threshold + 1 # Fail-safe offload if we can't read temp

        logger.info(f"Task Complexity: {complexity}/10 | GPU Temp: {gpu_temp}°C | Urgency: {urgency}")

        # Routing Logic
        if complexity >= 9:
            # God-mode required. Prioritize Tier 4, fallback to Gemini.
            logger.info("Routing -> TIER 4 (DeepSeek API) [Reason: High Complexity >= 9]")
            tier_priority = [4, 2, 1, 3]
        elif gpu_temp > self.temp_threshold:
            # Thermal throttle. Force Cloud execution.
            logger.info(f"Routing -> TIER 2 (Gemini CLI) [Reason: Thermal Protection, GPU > {self.temp_threshold}°C]")
            tier_priority = [2, 4, 3]
        else:
            # GPU is cool. Prefer Local Ollama (Tier 1) for all standard tasks to consume local tokens.
            # Since local model is Gemma-4-12B-it-heretic-GGUF, quality is outstanding.
            if self._is_ollama_available():
                logger.info("Routing -> TIER 1 (Local Ollama) [Reason: GPU Cool, prioritizing local tokens]")
                tier_priority = [1, 2, 4, 3]
            else:
                logger.info("Routing -> TIER 2 (Gemini CLI) [Reason: Local Ollama offline, routing to Cloud]")
                tier_priority = [2, 4, 3]

        return self._execute_with_fallback(tier_priority, task)

if __name__ == "__main__":
    bridge = AgentBridge(temp_threshold=75.0)
    
    print("\n=== TEST 1: Low Complexity Bulk Task ===")
    res = bridge.route_task("Summarize the color blue.", urgency=False)
    print(f"Result Preview: {res[:100]}...\n")

    print("\n=== TEST 2: High Complexity / God-Mode Task ===")
    res = bridge.route_task("Architect a comprehensive multi-agent system refactor using Python.", urgency=False)
    print(f"Result Preview: {res[:100]}...\n")
