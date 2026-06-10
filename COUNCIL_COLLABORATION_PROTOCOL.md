# Antigravity AI Council Collaboration Protocol v6.0

## 1. Overview

The **Antigravity AI Council** is a distributed, self‑healing multi‑agent system designed to produce production‑grade software and systems. It comprises three specialized roles—**Alpha (Architect)**, **Delta (Strategist)**, and **Zeta (Sentinel)**—that collaborate through defined protocols to ensure correctness, security, and operational stability. This document formalizes the communication, conflict resolution, memory management, and recovery mechanisms that govern the council.

## 2. Roles & Responsibilities

### 2.1 Alpha – Architect (Gemini CLI – Implementation & Orchestration)

Alpha translates strategic directives into executable code and orchestrates the entire build pipeline. Key responsibilities:
- **Ingestion & Scheduling**: Converts Delta’s JSON directives into a Directed Acyclic Graph (DAG) for parallel execution.
- **GitOps Workflow**: Pushes all code changes to feature branches, triggers static analysis (via Zeta’s Gemma 4 / SonarQube), and merges to `main` only after Delta’s PR approval.
- **Design Patterns**: Implements **Repository Pattern** for data access, **Observer Pattern** for event propagation, and **Circuit Breaker** to pause branches when Zeta’s validation score < 0.7.
- **Grounding**: Maintains a RAG endpoint (FAISS index) populated by Google Custom Search API results; Delta’s queries are context‑aware by default.
- **Containerization**: Each agent operates in a dedicated Docker container with a shared `working_dir`.

### 2.2 Delta – Strategist (DeepSeek V4 Pro – Logic & Planning)

Delta drives long‑term vision and ensures logical coherence across all decisions. Key responsibilities:
- **Critique Loops**: Initiates asynchronous rounds (max 3 iterations) where Alpha proposes architecture, Delta evaluates logical coherence and scalability, Zeta validates security, and Delta synthesizes feedback.
- **Logic Validation**: Applies O1‑style chain‑of‑thought; decomposes goals into formal pre/post‑conditions, exposes hidden assumptions, and flags contradictions.
- **Majority Voting**: For critical choices, each agent votes with a weighted rationale; Delta breaks ties based on long‑term strategic fit.
- **Roadmap Synthesis**: Combines Alpha’s capability map with Zeta’s risk heatmap into phased plans (Phase 0: minimal viable logic; Phase 1: secure integration; Phase 2: optimization & scale).

### 2.3 Zeta – Sentinel (Local Ollama Gemma 4 – Local State & Diagnostics)

Zeta enforces operational stability within hardware constraints (e.g., 12 GB RTX 4080). Key responsibilities:
- **VRAM Locking & Precision Management**: Enforces 4‑bit / NF4 quantization; partitions VRAM (80% weights, 20% KV cache) to prevent OOM.
- **Real‑time Telemetry**: Monitors `nvidia-smi` and CUDA logs; intercepts `cuda_malloc` failures and TDR events, flagging the exact instruction for Alpha.
- **Local Repository Integrity**: Runs periodic SHA‑256 checksums on weights and vector database to detect bit‑rot.
- **Cache Optimization**: Maintains an LRU cache for frequently requested data to minimise I/O overhead.

## 3. Cognitive Workflow

The council operates in a continuous, asynchronous feedback loop. The workflow is divided into three primary phases:

### 3.1 Triadic Orchestration (Alpha‑led)

1. **Delta proposes** a high‑level objective as a JSON directive (e.g., `{"task": "refactor authentication", "pattern": "Strategy", "priority": 0.9}`).
2. **Alpha ingests** the directive into a DAG scheduler, creating execution nodes.
3. **Zeta validates** each node in real‑time using local Gemma 4 (OWASP checks, context relevance).  
   - If Zeta’s score < 0.7 → Alpha pauses the branch (Circuit Breaker) and logs for Delta’s review.
4. **Alpha executes** the DAG, writing code in a dedicated container, and pushes to a feature branch.

### 3.2 Critique Loop (Delta‑initiated)

1. Alpha proposes an architecture → Delta evaluates logical coherence & scalability → Zeta validates security & runtime.
2. Delta synthesizes feedback, flags contradictions, and may re‑route the plan.
3. Loop repeats until convergence (max 3 iterations). Each iteration tightens scope.

### 3.3 Hard‑Bound Execution (Zeta‑enforced)

Every code generation and deployment step is subject to Zeta’s resource constraints:
- All operations must respect VRAM limits (pre‑quantized models).
- Memory fetches and KV cache expansion are throttled by LRU eviction.
- Any operation that risks OOM or TDR is aborted and logged for Alpha.

## 4. Conflict Resolution & Majority Voting

For any decision of critical impact—dependency selection, deployment strategy, architectural pattern—the council employs a formal voting process.

### 4.1 Voting Protocol

- Each agent submits a **vote** along with a **weighted rationale** (1–10 scale).
- Delta acts as tie‑breaker, evaluating long‑term strategic fit over immediate convenience.
- All votes are logged to a shared state file (`council_votes.log`) to prevent regressions.

### 4.2 Example Voting Flow

| Issue                  | Alpha vote (weight) | Delta vote (weight) | Zeta vote (weight) | Tally | Delta’s tie‑break |
|------------------------|---------------------|---------------------|---------------------|-------|-------------------|
| Use PostgreSQL vs MySQL| 0.9 Postgres        | 0.8 Postgres        | 0.7 MySQL           | Postgres wins | –                 |
| Micro‑frontend lib     | 0.8 ModuleFederation| 0.6 SingleSPA       | 0.5 ModuleFederation| ModuleFederation wins (tie‑break not needed) | – |
| Deployment to AWS vs GCP| 0.7 AWS            | 0.9 GCP             | 0.8 GCP             | Tie (2 vs 1?) | Delta chooses GCP (strategic fit) |

*Note: Ties are resolved by Delta’s strategic assessment. A unanimous vote always overrides.*

## 5. Local VRAM & Memory Locks

Zeta enforces strict policies to guarantee stability on consumer‑grade GPUs.

### 5.1 VRAM Partitioning

| Region        | Allocation | Purpose                               |
|---------------|------------|---------------------------------------|
| Weights       | 80%        | Quantized model weights (NF4/4‑bit)  |
| KV Cache      | 20%        | Context window expansion              |

- Any attempt to exceed the 20% KV cache limit triggers an immediate abort and logging.

### 5.2 Memory Locking & OOM Prevention

- **Precision enforcement**: All models are pre‑quantized to 4‑bit NF4 before loading.
- **`cuda_malloc` interception**: Zeta intercepts CUDA memory allocation calls. If a request would exceed total VRAM, it is rejected and the exact instruction is flagged.
- **TDR (Timeout Detection & Recovery)**: Zeta monitors kernel execution times. If a kernel exceeds a configurable threshold (default 2s), it is killed and the instruction flagged for Alpha’s re‑architecting.

### 5.3 Cache Optimization

- **LRU cache**: Stores frequently accessed data (kernel outputs, vector embeddings). Eviction occurs when cache size exceeds 2 GB.
- **Periodic SHA‑256 checks**: Zeta verifies local weight files and FAISS index every 10 minutes to detect corruption. Corrupted files are reported to Alpha for re‑download or regeneration.

## 6. Self‑Healing Loop

The council is designed to recover from failures automatically, using the **Circuit Breaker**, **Critique Loop**, and **Zeta’s error feedback** as building blocks.

### 6.1 Circuit Breaker (Alpha‑Zeta interaction)

- **Normal state**: Code is written and pushed to feature branch.
- **Open state**: If Zeta’s validation score on any node < 0.7 → Alpha pauses that branch and logs it.
- **Half‑open state**: Delta reviews the log and may propose a revised directive. Alpha re‑evaluates the branch.
- **Closed state**: Once the new directive passes Zeta’s validation, execution resumes.

### 6.2 Error Recovery Workflow

1. **Zeta detects a failure** (OOM, TDR, checksum mismatch, score < 0.7).  
   → Flags the exact instruction and logs the context.
2. **Alpha receives the flag** and labels the affected DAG node as `FAILED`.
3. **Delta is notified** and initiates a new critique loop (max 2 iterations) to redesign the failed component.
4. **Alpha implements the revised design** and pushes to a new feature branch.
5. **Zeta re‑validates** the branch. If score ≥ 0.7, the branch is merged; otherwise the loop repeats.

### 6.3 Self‑Healing Properties

- **Idempotent operations**: All state‑mutating actions (PR merges, cache updates) are idempotent to allow safe retries.
- **Shared state integrity**: The `council_state.json` file is read‑only for all agents except Alpha (which writes after merge) and Zeta (which writes error logs and validation scores). Delta reads only.
- **Rollback capability**: Every Git merge creates a tag. If the self‑healing loop fails after 3 retries, Alpha initiates an automatic rollback to the last known good tag.

## 7. Tooling & Infrastructure

| Aspect                 | Implementation                                     |
|------------------------|----------------------------------------------------|
| Containerization       | Docker (each agent in its own container)           |
| Code Repository        | Git (GitHub) – feature‑branch workflow             |
| Static Analysis        | SonarQube (via Ollama)                             |
| Vector Store           | FAISS index (on disk)                              |
| RAG Endpoint           | Alpha‑hosted HTTP server                           |
| Grounding Source       | Google Custom Search API (top 3 results per query) |
| Telemetry              | `nvidia-smi`, CUDA logs, custom metrics endpoint   |
| Shared State File      | `council_state.json` (JSON + SHA‑256 integrity)    |

## 8. Constraints & Assumptions

- **Hardware**: Minimum 12 GB VRAM (RTX 4080 or equivalent). All models quantized accordingly.
- **Network**: Internet access for Google Custom Search API; local network for inter‑container communication.
- **Latency**: Critique loops are asynchronous; no real‑time sync required.
- **Security**: All code changes go through GitOps. No direct write access to production.

## 9. Versioning & Amendments

This protocol is version 6.0. Amendments require a **unanimous vote** among Alpha, Delta, and Zeta, followed by a formal pull request into the `antigravity-protocol` repository. The document is versioned in lockstep with the council’s own deployment tags.

---

*Last updated: 2026-06-09*  
*Maintained by the Antigravity AI Council.*

---

## Council V7 Amendments

### Updated Model Registry
| Role | Codename | Model | Tier |
|------|----------|-------|------|
| Architect | Alpha | Gemini CLI | Orchestrator |
| Sentinel | Zeta | claude-3-5-sonnet:latest (Gemma 4 Q4_K_M, local) | 1 |
| Accelerator | Epsilon | DeepSeek V4 Flash | 2 |
| Strategist | Delta | DeepSeek V4 Pro | 3 |

### Task Delegation Thresholds

**Route to Zeta (local, zero token cost) when:**
- Summarisation of any document
- File reading and extraction
- Code explanation or annotation
- Draft writing and formatting
- Quick factual lookups
- Regex, simple scripting, boilerplate
- Any task estimated under 24,000 tokens
- Token conservation is priority

**Route to Epsilon (mid-tier, fast cloud) when:**
- Zeta validation score drops below 0.7
- Moderate coding tasks requiring cloud reasoning
- Structured multi-step logic beyond Zeta capability
- Speed is priority over depth
- Tasks estimated 24,000-100,000 tokens

**Route to Delta (heavy tier, maximum reasoning) when:**
- Complex system architecture decisions
- Multi-file codebase debugging
- Strategic planning and roadmapping
- Epsilon fails or returns low confidence
- Tasks requiring maximum reasoning depth
- Unanimous council vote required

### Epsilon Circuit Breaker
- If Epsilon confidence < 0.75, escalate to Delta automatically
- Maximum 2 Epsilon retry attempts before Delta escalation
- Log all Epsilon failures to council audit trail

### Zeta Circuit Breaker (Updated)
- Threshold remains 0.7 (validated against Gemma 4 capability profile)
- Zeta now routes to Epsilon first, not directly to Delta
- Escalation chain: Zeta  Epsilon  Delta  Rollback

### VRAM Protection Rules
- Only claude-3-5-sonnet:latest permitted in Ollama at any time
- No other models to be loaded or pulled without explicit council vote
- Maximum context: 24,576 tokens
- If VRAM exceeds 10,500 MiB, Zeta defers to Epsilon immediately

### Token Exhaustion Fail-Safe
- If Gemini (Alpha) API tokens are exhausted, resulting in a system lockout, Zeta immediately inherits the Architect orchestration privileges to preserve offline continuity.

## CLAUDE CODE OFFLINE ROUTING
To route Claude Code to the local Ollama instance without triggering Anthropic model whitelist validation errors, you MUST start the LiteLLM proxy via the Desktop shortcut \start-claude-offline.ps1\ or manually spin up LiteLLM on port 8000 using the generated config. council_mcp_server.py has been updated to automatically route to http://localhost:8000 internally.
