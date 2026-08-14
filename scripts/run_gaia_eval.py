import json
import logging
import os
import sys
from pathlib import Path
from datasets import load_dataset
from huggingface_hub import login

# Add the parent directory to sys.path so we can import from agents
sys.path.append(str(Path(__file__).resolve().parent.parent))

from agents.research_agent import ResearchAgent
from utils import get_logger

logger = get_logger(__name__)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run GAIA Evaluation")
    parser.add_argument("--split", type=str, default="test", choices=["validation", "test"],
                        help="The GAIA dataset split to evaluate on. 'validation' has answers, 'test' is for leaderboard.")
    parser.add_argument("--output", type=str, default="gaia_submission.jsonl",
                        help="Path to the output JSONL file.")
    parser.add_argument("--max-tasks", type=int, default=None,
                        help="Maximum number of tasks to process (useful for debugging).")
    args = parser.parse_args()

    # Step 1: Ensure Hugging Face authentication
    hf_token = os.environ.get("HF_TOKEN")
    if hf_token:
        logger.info("Found HF_TOKEN in environment. Logging in...")
        login(token=hf_token)
    else:
        logger.warning(
            "No HF_TOKEN found in environment. If you haven't run `huggingface-cli login` "
            "you might not be able to access the gated GAIA dataset."
        )

    # Step 2: Load the dataset
    logger.info(f"Loading GAIA dataset (split: {args.split})...")
    try:
        ds = load_dataset("gaia-benchmark/GAIA", "2023_all", split=args.split)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        logger.error("Please ensure you have accepted the dataset terms on Hugging Face and are authenticated.")
        sys.exit(1)

    logger.info(f"Loaded {len(ds)} tasks from the {args.split} split.")

    # Step 3: Initialize the Agent
    logger.info("Initializing Research Agent...")
    agent = ResearchAgent()
    
    output_file = Path(args.output)
    
    # Check what tasks we've already done if resuming
    completed_task_ids = set()
    if output_file.exists():
        with open(output_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        completed_task_ids.add(data.get("task_id"))
                    except:
                        pass
        logger.info(f"Found {len(completed_task_ids)} already completed tasks in {output_file}.")

    # Step 4: Run Evaluation
    tasks_processed = 0
    with open(output_file, "a", encoding="utf-8") as f:
        for row in ds:
            task_id = row["task_id"]
            if task_id in completed_task_ids:
                logger.info(f"Skipping already completed task {task_id}")
                continue
                
            question = row["question"]
            file_name = row.get("file_name")
            file_path = row.get("file_path") # datasets might provide the local path automatically if it downloads attachments
            
            logger.info(f"Processing Task ID: {task_id}")
            
            prompt = f"Task: {question}"
            if file_name and file_path:
                # If datasets downloaded it to a local cache, provide that path
                prompt += f"\n\nAttached File Path (you may need to analyze this file): {file_path}"
            elif file_name:
                prompt += f"\n\nNote: This task requires a file named '{file_name}', but the local path wasn't automatically resolved."

            logger.info(f"Prompt:\n{prompt}")
            
            try:
                # Use plan_and_run which utilizes the Intelligent Planning Engine
                answer = agent.plan_and_run(prompt)
                # The agent might return an object, cast it to string
                model_answer = str(answer).strip()
            except Exception as e:
                logger.error(f"Error processing task {task_id}: {e}")
                model_answer = f"Error: {e}"

            # Step 5: Save Result
            # The schema requires exactly one JSON object per line with task_id and model_answer
            result = {
                "task_id": task_id,
                "model_answer": model_answer
            }
            f.write(json.dumps(result) + "\n")
            f.flush()
            logger.info(f"Saved result for task {task_id}")
            
            tasks_processed += 1
            if args.max_tasks and tasks_processed >= args.max_tasks:
                logger.info(f"Reached max_tasks limit ({args.max_tasks}). Stopping.")
                break
                
    logger.info(f"Evaluation complete. Results saved to {output_file}")


if __name__ == "__main__":
    main()
