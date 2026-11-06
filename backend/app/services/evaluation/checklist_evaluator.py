from app.services.checklist_loader import load_checklist
from app.services.openai_provider import OpenAIEvaluationProvider
from app.schemas.checklist import ChecklistEvaluation


class ChecklistEvaluator:

    def __init__(self):
        self.provider = OpenAIEvaluationProvider()

    def evaluate(self, transcript_segments, checklist_name="sales_call"):

        # 1. Load checklist
        checklist = load_checklist(checklist_name)

        results = []

        yes_count = 0
        no_count = 0
        partial_count = 0
        not_clear_count = 0

        total_weight = 0
        achieved_weight = 0

        # 2. Process each checklist category
        for category in checklist["categories"]:

            category_name = category["category_name"]

            for item in category["questions"]:

                question_id = item["id"]
                question = item["question"]
                expected_behavior = item.get(
                    "expected_behavior",
                    question
                )
                weight = float(item["weight"])

                print(f"Evaluating: {question_id} - {question}")

                # 3. Evaluate using local AI
                evaluation = self.provider.evaluate_question(
                    question=question,
                    expected_behavior=expected_behavior,
                    transcript_segments=transcript_segments
                )

                status = evaluation["status"]

                # 4. Count individual results
                if status == "YES":
                    yes_count += 1
                    achieved_weight += weight

                elif status == "NO":
                    no_count += 1

                elif status == "PARTIAL":
                    partial_count += 1
                    achieved_weight += weight * 0.5

                elif status == "NOT_CLEAR":
                    not_clear_count += 1

                # NOT_CLEAR is excluded from the scoring denominator.
                if status != "NOT_CLEAR":
                    total_weight += weight

                # 5. Save question result
                results.append({
                    "question_id": question_id,
                    "question": question,
                    "category": category_name,
                    "status": status,
                    "explanation": evaluation["explanation"],
                    "evidence": evaluation["evidence"],
                    "review_required": evaluation["review_required"],
                    "review_reason": evaluation["review_reason"],
                    "weight": weight
                })

        # 6. Calculate compliance percentage
        compliance_percentage = None

        if total_weight > 0:
            compliance_percentage = round(
                (achieved_weight / total_weight) * 100,
                2
            )

        # 7. Build final report
        report = ChecklistEvaluation(
            checklist_id=checklist["checklist_id"],
            checklist_name=checklist["checklist_name"],
            total_questions=len(results),
            yes_count=yes_count,
            no_count=no_count,
            partial_count=partial_count,
            not_clear_count=not_clear_count,
            compliance_percentage=compliance_percentage,
            results=results
        )

        return report
