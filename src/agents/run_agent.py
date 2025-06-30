import sys
import time
import os
from src.agents.analyzer_agent import compiled_graph
from langchain_core.messages import HumanMessage


def main():
    print("Infrastructure Monitoring Agent")
    print("=" * 50)

    is_interactive = sys.stdin.isatty()

    if is_interactive:
        print("Type 'exit' to quit")
        print()

        state = {"messages": []}

        while True:
            user_input = input("You: ")

            if user_input.lower() in ['exit', 'quit', 'q']:
                print("Exiting...")
                break

            state["messages"].append(HumanMessage(content=user_input))

            print("Processing...")
            result = compiled_graph.invoke(state)

            state = result

            agent_message = result["messages"][-1]
            print("\nAgent:", agent_message.content)
            print()
    else:
        print("Running in non-interactive mode")
        print("Use 'docker exec -it <container_name> python agent/run_agent.py' to run in interactive mode")
        print()

        print("Agent is ready and waiting for interactive commands.")
        print("No automatic analysis will be performed.")
        print()

        while True:
            time.sleep(60)
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Agent is running. Metrics file exists: {os.path.exists('data/outputs/realtime_metrics.json')}")


if __name__ == "__main__":
    main()
