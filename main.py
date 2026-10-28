
import json
import sys

from agent.executor import (
    build_agent,
    run_agent,
    extract_final_answer,
    extract_trace,
    REQUIRED_TOOLS,
)
from agent.prompts import DEMO_QUERY
from config.settings import get_settings
from evaluation.evaluator import evaluate_agent_run
from utils.logging_config import configure_logging


def show_trace(trace):
    for item in trace:
        if item["type"] == "ACTION":
            print(f"\n[ACTION] Tool: {item['tool']}")
            print(
                "Arguments:",
                json.dumps(item["arguments"], ensure_ascii=False),
            )
        else:
            print(f"\n[OBSERVATION] Tool: {item['tool']}")
            content = item["content"]
            print(content[:1800])

            if len(content) > 1800:
                print("...[observation truncated]...")


def main():
    configure_logging()

    try:
        settings = get_settings()
        agent = build_agent(settings)
    except Exception as exc:
        print(f"Initialization failed: {type(exc).__name__}: {exc}")
        sys.exit(1)

    print("\nMULTI-TOOL AUTONOMOUS AI AGENT")
    print(f"Model: {settings.model}")
    print("Tools: web_search | calculator | read_local_file")
    print("Commands: /demo, /evaluate, exit\n")

    history = []
    last_messages = None

    while True:
        try:
            query = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAgent stopped.")
            break

        if query.lower() in {"exit", "quit", "stop"}:
            print("Agent stopped.")
            break

        if not query:
            continue

        if query.lower() == "/evaluate":
            if last_messages is None:
                print("Run a query first.")
            else:
                print(json.dumps(
                    evaluate_agent_run(last_messages),
                    indent=2,
                    ensure_ascii=False,
                ))
            continue

        is_demo = query.lower() == "/demo"
        prompt = DEMO_QUERY if is_demo else query

        messages = history + [{"role": "user", "content": prompt}]

        print("\nAgent is working...\n")

        try:
            result = run_agent(agent, messages)
            last_messages = result["messages"]

            show_trace(extract_trace(last_messages))

            answer = extract_final_answer(last_messages)

            print("\n" + "=" * 60)
            print("FINAL ANSWER")
            print("=" * 60)
            print(answer)
            print("=" * 60)

            report = evaluate_agent_run(
                last_messages,
                REQUIRED_TOOLS if is_demo else set(),
            )

            print("\nEXECUTION EVALUATION")
            print(json.dumps(report, indent=2, ensure_ascii=False))

            history.extend([
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": answer},
            ])

        except Exception as exc:
            print(f"Agent execution failed: {type(exc).__name__}: {exc}")

        print()


if __name__ == "__main__":
    main()