from agents.research_agent import create_agent


def main():
    print("=" * 70)
    print("AI Research Assistant")
    print("Type 'exit' to quit.")
    print("=" * 70)

    agent = create_agent()

    while True:
        query = input("\nYou: ").strip()

        if not query:
            continue

        if query.lower() in {"exit", "quit"}:
            break

        print("\nAssistant:\n")

        try:
            answer = agent.run(query)
            print(answer)

        except KeyboardInterrupt:
            print("\nInterrupted.")

        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    main()

