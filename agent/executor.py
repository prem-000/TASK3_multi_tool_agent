
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, ToolMessage

from agent.prompts import SYSTEM_PROMPT
from config.settings import Settings
from tools.calculator import calculator
from tools.file_reader import read_local_file
from tools.web_search import web_search


REQUIRED_TOOLS = {
    "web_search",
    "calculator",
    "read_local_file",
}


def build_agent(settings: Settings):
    """Build the Gemini-powered LangChain agent."""
    model = ChatGoogleGenerativeAI(
        model=settings.model,
        temperature=0,
        timeout=120,
        max_retries=1,
        google_api_key=settings.api_key,
    )

    return create_agent(
        model=model,
        tools=[
            web_search,
            calculator,
            read_local_file,
        ],
        system_prompt=SYSTEM_PROMPT,
    )


def run_agent(agent, messages):
    """Execute the agent and return its messages and tool trace."""
    if not messages:
        raise ValueError("At least one message is required.")

    return agent.invoke(
        {"messages": messages},
        config={"recursion_limit": 15},
    )


def content_to_text(content) -> str:
    """Convert model content into displayable text."""
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("text"):
                parts.append(item["text"])
            else:
                parts.append(str(item))
        return "\n".join(parts)

    return str(content)


def extract_final_answer(messages) -> str:
    """Extract the final assistant response."""
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            if not (getattr(message, "tool_calls", None) or []):
                answer = content_to_text(message.content).strip()
                if answer:
                    return answer

    return "No final answer was returned."


def extract_trace(messages) -> list:
    """Return visible tool actions and observations."""
    trace = []

    for message in messages:
        calls = getattr(message, "tool_calls", None) or []

        for call in calls:
            trace.append({
                "type": "ACTION",
                "tool": call.get("name", "unknown"),
                "arguments": call.get("args", {}),
            })

        if isinstance(message, ToolMessage):
            trace.append({
                "type": "OBSERVATION",
                "tool": getattr(message, "name", "unknown"),
                "content": content_to_text(message.content),
            })

    return trace
