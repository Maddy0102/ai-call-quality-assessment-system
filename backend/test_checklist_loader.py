
from app.services.checklist_loader import (
    load_checklist,
    list_checklists
)

print("\n========== CHECKLIST LOADER TEST ==========")

# List available checklists
available = list_checklists()

print("\nAvailable checklists:")
for name in available:
    print("-", name)

# Load sales checklist
checklist = load_checklist("sales_call")

print("\nChecklist:", checklist["checklist_name"])
print("Version:", checklist["version"])

total_questions = 0
total_weight = 0

for category in checklist["categories"]:

    print("\nCategory:", category["category_name"])

    for question in category["questions"]:
        total_questions += 1
        total_weight += question["weight"]

        print(
            question["id"],
            "-",
            question["question"],
            "| Weight:",
            question["weight"]
        )

print("\nTotal questions:", total_questions)
print("Total weight:", total_weight)
print("\nTEST COMPLETED")
