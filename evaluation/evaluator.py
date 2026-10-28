
from langchain_core.messages import AIMessage, ToolMessage

from agent.executor import content_to_text


def evaluate_agent_run(messages, required_tools=None) -> dict:
    """Evaluate execution and tool usage for a completed agent run."""
    required = set(required_tools or [])
    tool_calls = []
    observations = []
    final_answer = ""

    for message in messages:
        calls = getattr(message, "tool_calls", None) or []

        for call in calls:
            name = call.get("name")
            if name:
                tool_calls.append(name)

        if isinstance(message, ToolMessage):
            observations.append({
                "tool": getattr(message, "name", "unknown"),
                "content": content_to_text(message.content),
            })

        if isinstance(message, AIMessage) and not calls:
            text = content_to_text(message.content).strip()
            if text:
                final_answer = text

    tools_used = sorted(set(tool_calls))
    missing_tools = sorted(required - set(tools_used))

    tool_errors = [
        {
            "tool": item["tool"],
            "error": item["content"],
        }
        for item in observations
        if item["content"].strip().startswith("ERROR:")
    ]

    passed = bool(final_answer) and not missing_tools and not tool_errors

    return {
        "tool_calls": tool_calls,
        "tools_used": tools_used,
        "missing_required_tools": missing_tools,
        "tool_errors": tool_errors,
        "final_answer_present": bool(final_answer),
        "passed_execution_checks": passed,
        "note": (
            "Execution checks only. Review factual accuracy and source "
            "quality separately."
        ),
    }