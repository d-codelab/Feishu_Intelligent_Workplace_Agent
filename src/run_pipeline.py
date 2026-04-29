"""CLI entrypoint for the end-to-end todo pipeline."""

from todo_agent.config import DEFAULT_MOCK_TODOS_PATH, FALLBACK_MOCK_TODOS_PATH
from todo_agent.services.pipeline import run_pipeline
from todo_agent.utils.json_loader import load_todo_items


def load_default_todos() -> list[dict]:
    """Load mock todos from preferred fixture, with legacy fallback."""
    path = DEFAULT_MOCK_TODOS_PATH if DEFAULT_MOCK_TODOS_PATH.exists() else FALLBACK_MOCK_TODOS_PATH
    return load_todo_items(path)


if __name__ == "__main__":
    result = run_pipeline(load_default_todos())
    print(
        "Pipeline finished: "
        f"total={result['total']}, "
        f"write_success={result['write_success']}, "
        f"write_failed={result['write_failed']}, "
        f"summary_sent={result['summary_sent']}"
    )
