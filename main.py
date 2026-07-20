import sys
from agents.research_agent import create_agent
from config.model import validate_model_connection
from utils import get_logger

logger = get_logger(__name__)


def main():
    print("=" * 70)
    print("AI Research Assistant")
    print("Type 'exit' or 'quit' to exit.")
    print("=" * 70)

    logger.info("Performing model connection pre-flight check...")
    is_valid, msg = validate_model_connection()
    if not is_valid:
        logger.warning(f"Validation Warning: {msg}")
        print(f"\n⚠️  [Model Pre-flight Warning]: {msg}\n")
    else:
        logger.info(f"✅ {msg}")

    logger.info("Initializing Research Agent...")
    try:
        agent = create_agent()
        logger.info("Research Agent Ready.")
    except Exception as e:
        logger.error(f"Failed to build Research Agent: {e}")
        sys.exit(1)

    while True:
        try:
            query = input("\nYou: ").strip()

            if not query:
                continue

            if query.lower() in {"exit", "quit"}:
                logger.info("Shutting down.")
                break

            print("\nAssistant:\n")
            answer = agent.run(query)
            print(f"\n{answer}\n")

        except KeyboardInterrupt:
            print("\n")
            logger.warning("Interrupted by user.")
            break

        except Exception as err:
            err_str = str(err)
            if "Timeout" in err_str or "timed out" in err_str.lower():
                logger.error("Connection timed out. Check your model provider response speed or context size.")
            elif "RateLimit" in err_str or "429" in err_str:
                logger.error("Rate limit hit or quota exceeded. Verify API key limits or wait before retrying.")
            elif "Authentication" in err_str or "401" in err_str or "403" in err_str:
                logger.error("Authentication error. Check your GEMINI_API_KEY or MODEL_API_KEY in .env.")
            else:
                logger.exception("An error occurred during query execution")


if __name__ == "__main__":
    main()