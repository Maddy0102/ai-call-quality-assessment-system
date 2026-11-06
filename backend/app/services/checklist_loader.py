
import json

from pathlib import Path


CHECKLIST_DIR = (
    Path(__file__).resolve().parents[1] / "checklists"
)


def list_checklists():
    """
    Return available checklist names.
    """

    return sorted(
        file.stem
        for file in CHECKLIST_DIR.glob("*.json")
        if file.is_file()
    )


def load_checklist(checklist_name="sales_call"):
    """
    Load a checklist JSON configuration dynamically.
    """

    # Prevent directory traversal
    if (
        not checklist_name
        or Path(checklist_name).name != checklist_name
        or checklist_name in {".", ".."}
    ):
        raise ValueError("Invalid checklist name")

    checklist_path = CHECKLIST_DIR / f"{checklist_name}.json"

    if not checklist_path.is_file():
        raise FileNotFoundError(
            f"Checklist '{checklist_name}' was not found"
        )

    with checklist_path.open("r", encoding="utf-8") as file:
        checklist = json.load(file)

    if not isinstance(checklist.get("categories"), list):
        raise ValueError("Invalid checklist: categories must be a list")

    question_ids = set()

    for category in checklist["categories"]:

        questions = category.get("questions")

        if not isinstance(questions, list):
            raise ValueError("Invalid checklist category: questions must be a list")

        for question in questions:

            question_id = question.get("id")
            weight = question.get("weight")

            if not question_id or question_id in question_ids:
                raise ValueError(
                    f"Missing or duplicate question ID: {question_id}"
                )

            if (
                isinstance(weight, bool)
                or not isinstance(weight, (int, float))
                or weight <= 0
            ):
                raise ValueError(
                    f"Invalid weight for question: {question_id}"
                )

            question_ids.add(question_id)

    return checklist
