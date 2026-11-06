from app.services.evaluation.checklist_evaluator import ChecklistEvaluator


transcript_segments = [
    {
        "speaker": "EXECUTIVE",
        "channel": "left",
        "start": 0.0,
        "end": 4.0,
        "text": "Good morning, this is Arun, sales manager calling from ABC Properties.",
        "reliability": {"status": "reliable"}
    },
    {
        "speaker": "CUSTOMER",
        "channel": "right",
        "start": 4.5,
        "end": 8.0,
        "text": "I am looking for a three bedroom apartment in Chennai.",
        "reliability": {"status": "reliable"}
    },
    {
        "speaker": "EXECUTIVE",
        "channel": "left",
        "start": 8.5,
        "end": 15.0,
        "text": "Sure. Could you tell me your preferred location and budget?",
        "reliability": {"status": "reliable"}
    },
    {
        "speaker": "CUSTOMER",
        "channel": "right",
        "start": 15.5,
        "end": 20.0,
        "text": "My budget is around 80 lakhs. I prefer Anna Nagar.",
        "reliability": {"status": "reliable"}
    },
    {
        "speaker": "EXECUTIVE",
        "channel": "left",
        "start": 20.5,
        "end": 29.0,
        "text": "Understood. We have three bedroom apartments in Anna Nagar within your budget. They include covered parking, security and a gym.",
        "reliability": {"status": "reliable"}
    },
    {
        "speaker": "CUSTOMER",
        "channel": "right",
        "start": 29.5,
        "end": 33.0,
        "text": "That sounds interesting. What happens next?",
        "reliability": {"status": "reliable"}
    },
    {
        "speaker": "EXECUTIVE",
        "channel": "left",
        "start": 33.5,
        "end": 40.0,
        "text": "I will share the property details and arrange a site visit. Thank you for your time. Have a great day.",
        "reliability": {"status": "reliable"}
    }
]


if __name__ == "__main__":

    evaluator = ChecklistEvaluator()

    print("\n========== CHECKLIST EVALUATION ==========\n")

    report = evaluator.evaluate(
        transcript_segments=transcript_segments,
        checklist_name="sales_call"
    )

    print("\n========== FINAL REPORT ==========\n")

    print(report.model_dump_json(indent=2))

    print("\n========== SUMMARY ==========\n")

    print("Total Questions:", report.total_questions)
    print("YES:", report.yes_count)
    print("NO:", report.no_count)
    print("PARTIAL:", report.partial_count)
    print("NOT CLEAR:", report.not_clear_count)
    print("Compliance:", report.compliance_percentage)
