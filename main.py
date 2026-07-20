from agents.research_agent import create_agent
from utils import get_logger

logger = get_logger(__name__)


def main():
    print("=" * 70)
    print("AI Research Assistant")
    print("Type 'exit' to quit.")
    print("=" * 70)

    logger.info("Initializing Research Agent...")

    agent = create_agent()

    logger.info("Research Agent Ready.")

    while True:
        query = input("\nYou: ").strip()

        if not query:
            continue

        if query.lower() in {"exit", "quit"}:
            logger.info("Shutting down.")
            break

        print("\nAssistant:\n")

        try:
            answer = agent.run(query)
            print(answer)

        except KeyboardInterrupt:
            logger.warning("Interrupted by user.")

        except Exception:
            logger.exception("Unhandled exception")


if __name__ == "__main__":
    main()