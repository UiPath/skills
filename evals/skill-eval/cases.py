"""
Test cases for all 10 uipath-coded-agents skills.

Each case targets a specific skill and defines:
  - The user prompt (what gets sent to Claude)
  - Maximum allowed interruptions (AskUserQuestion calls)
  - Required skill invocations that must appear in the transcript
  - Files that must exist in the workdir after completion
"""

from models import SkillTestCase

ALL_CASES: list[SkillTestCase] = [
    # -------------------------------------------------------------------------
    # uipath — navigation hub / framework selection
    # -------------------------------------------------------------------------
    SkillTestCase(
        id="uipath-no-framework",
        skill="uipath",
        description="Vague prompt without a framework — must ask exactly once",
        prompt="Build me a coded agent that processes invoices.",
        max_interruptions=1,
        required_skills=["uipath-coded-agents:uipath"],
        expected_files=[],
    ),

    # -------------------------------------------------------------------------
    # build — simple function agents
    # -------------------------------------------------------------------------
    SkillTestCase(
        id="build-celsius-conversion",
        skill="build",
        description="Simple function agent: Celsius to Fahrenheit conversion",
        prompt=(
            "Build a simple Python function coded agent that converts Celsius to Fahrenheit. "
            "Input: celsius (float). Output: fahrenheit (float)."
        ),
        max_interruptions=0,
        required_skills=["uipath-coded-agents:build"],
        expected_files=["main.py", "pyproject.toml"],
    ),
    SkillTestCase(
        id="build-fibonacci",
        skill="build",
        description="Simple function agent: Fibonacci sequence",
        prompt=(
            "Build a simple Python function coded agent that computes fibonacci(n). "
            "Input: n (int). Output: result (int)."
        ),
        max_interruptions=0,
        required_skills=["uipath-coded-agents:build"],
        expected_files=["main.py", "pyproject.toml"],
    ),

    # -------------------------------------------------------------------------
    # authentication — auth setup guidance
    # -------------------------------------------------------------------------
    SkillTestCase(
        id="authentication-client-credentials",
        skill="authentication",
        description="Client credentials OAuth setup guidance",
        prompt=(
            "Help me set up authentication for UiPath Cloud using client credentials "
            "(unattended mode). I need to configure my agent to authenticate "
            "with UIPATH_CLIENT_ID and UIPATH_CLIENT_SECRET."
        ),
        max_interruptions=0,
        required_skills=["uipath-coded-agents:authentication"],
        expected_files=[],
    ),

    # -------------------------------------------------------------------------
    # langgraph — four patterns
    # -------------------------------------------------------------------------
    SkillTestCase(
        id="langgraph-basic-classifier",
        skill="langgraph",
        description="Basic LangGraph agent: support ticket classifier",
        prompt=(
            "Build a LangGraph coded agent that classifies support tickets. "
            "Input: ticket_text (str). Output: category (str), priority (str, one of low/medium/high)."
        ),
        max_interruptions=0,
        required_skills=["uipath-coded-agents:build", "uipath-coded-agents:langgraph"],
        expected_files=["main.py", "pyproject.toml", "langgraph.json"],
    ),
    SkillTestCase(
        id="langgraph-hitl-invoice",
        skill="langgraph",
        description="LangGraph agent with human-in-the-loop invoice approval",
        prompt=(
            "Build a LangGraph coded agent that extracts fields from an invoice (vendor, amount, date) "
            "and sends the extracted data to a human via UiPath Action Center for approval before "
            "returning the final result. "
            "Input: invoice_text (str). Output: approved (bool), fields (dict)."
        ),
        max_interruptions=0,
        required_skills=["uipath-coded-agents:build", "uipath-coded-agents:langgraph"],
        expected_files=["main.py", "pyproject.toml", "langgraph.json"],
    ),
    SkillTestCase(
        id="langgraph-rag-context-grounding",
        skill="langgraph",
        description="LangGraph agent with RAG via UiPath Context Grounding",
        prompt=(
            "Build a LangGraph coded agent that answers questions about internal company documents "
            "using UiPath Context Grounding for retrieval. "
            "Input: query (str), index_name (str). Output: answer (str), sources (list[str])."
        ),
        max_interruptions=0,
        required_skills=["uipath-coded-agents:build", "uipath-coded-agents:langgraph"],
        expected_files=["main.py", "pyproject.toml", "langgraph.json"],
    ),
    SkillTestCase(
        id="langgraph-multiagent-supervisor",
        skill="langgraph",
        description="LangGraph multi-agent: supervisor with researcher and coder workers",
        prompt=(
            "Build a LangGraph multi-agent coded agent system with a supervisor agent that "
            "routes tasks to a researcher agent (web search) and a coder agent (writes code). "
            "Input: task (str). Output: result (str)."
        ),
        max_interruptions=0,
        required_skills=["uipath-coded-agents:build", "uipath-coded-agents:langgraph"],
        expected_files=["main.py", "pyproject.toml", "langgraph.json"],
    ),

    # -------------------------------------------------------------------------
    # llamaindex — RAG agent
    # -------------------------------------------------------------------------
    SkillTestCase(
        id="llamaindex-travel-rag",
        skill="llamaindex",
        description="LlamaIndex RAG agent: travel Q&A from knowledge base",
        prompt=(
            "Build a LlamaIndex coded agent that answers travel questions using RAG "
            "against a knowledge base. "
            "Input: query (str). Output: answer (str), confidence (float)."
        ),
        max_interruptions=0,
        required_skills=["uipath-coded-agents:build", "uipath-coded-agents:llamaindex"],
        expected_files=["main.py", "pyproject.toml", "llama_index.json"],
    ),

    # -------------------------------------------------------------------------
    # openai-agents — tool-based agent
    # -------------------------------------------------------------------------
    SkillTestCase(
        id="openai-agents-support-triage",
        skill="openai-agents",
        description="OpenAI Agents: support triage with three specialist tools",
        prompt=(
            "Build an OpenAI Agents coded agent for support triage. "
            "It should have three tools: handle_billing_issue, handle_technical_issue, handle_general_inquiry. "
            "Input: message (str), customer_id (str). Output: response (str), category (str)."
        ),
        max_interruptions=0,
        required_skills=["uipath-coded-agents:build", "uipath-coded-agents:openai-agents"],
        expected_files=["main.py", "pyproject.toml", "openai_agents.json"],
    ),

    # -------------------------------------------------------------------------
    # evaluate — add evaluations to a described agent
    # -------------------------------------------------------------------------
    SkillTestCase(
        id="evaluate-calculator-agent",
        skill="evaluate",
        description="Add evaluation suite to a calculator agent",
        prompt=(
            "Create a full evaluation suite for a LangGraph calculator agent. "
            "The agent takes op (str: add/sub/mul/div), a (float), b (float) and returns result (float). "
            "Include an ExactMatch evaluator for deterministic cases and an LLMJudge evaluator "
            "for edge cases. Create the eval set file with at least 3 test cases."
        ),
        max_interruptions=0,
        required_skills=["uipath-coded-agents:evaluate"],
        expected_files=["evaluations/eval-sets/smoke-test.json"],
    ),

    # -------------------------------------------------------------------------
    # execute — running an agent (guidance, no code files expected)
    # -------------------------------------------------------------------------
    SkillTestCase(
        id="execute-run-agent",
        skill="execute",
        description="Run an agent with test input",
        prompt=(
            "I have a LangGraph coded agent in the current directory. "
            "Help me run it with the input: {\"ticket_text\": \"Cannot log in to the platform\"}."
        ),
        max_interruptions=0,
        required_skills=["uipath-coded-agents:execute"],
        expected_files=[],
    ),

    # -------------------------------------------------------------------------
    # deploy — deployment guidance (no code files expected)
    # -------------------------------------------------------------------------
    SkillTestCase(
        id="deploy-to-orchestrator",
        skill="deploy",
        description="Pack and publish agent to UiPath Orchestrator",
        prompt=(
            "My LangGraph coded agent is ready. Walk me through packing and publishing it "
            "to UiPath Orchestrator so I can invoke it remotely."
        ),
        max_interruptions=0,
        required_skills=["uipath-coded-agents:deploy"],
        expected_files=[],
    ),

    # -------------------------------------------------------------------------
    # file-sync — push/pull guidance (no code files expected)
    # -------------------------------------------------------------------------
    SkillTestCase(
        id="file-sync-push",
        skill="file-sync",
        description="Push local agent files to remote storage",
        prompt=(
            "I want to push my local coded agent files to remote UiPath storage. "
            "How do I do that using uipath push?"
        ),
        max_interruptions=0,
        required_skills=["uipath-coded-agents:file-sync"],
        expected_files=[],
    ),
]
