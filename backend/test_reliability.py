
from app.services.transcription.reliability import (
    assess_transcription_reliability
)

sample_segments = [
    {
        "speaker": "EXECUTIVE",
        "text": "வணக்கம்",
        "avg_logprob": -0.2,
        "no_speech_prob": 0.01
    },
    {
        "speaker": "CUSTOMER",
        "text": "என்ன budget?",
        "avg_logprob": -0.7,
        "no_speech_prob": 0.05
    },
    {
        "speaker": "EXECUTIVE",
        "text": "சரி",
        "avg_logprob": -1.5,
        "no_speech_prob": 0.1
    }
]

result = assess_transcription_reliability(sample_segments)

print("\n========== RELIABILITY TEST ==========")

print("Total:", result["total_segments"])
print("Reliable:", result["reliable_segments"])
print("Needs Review:", result["needs_review_segments"])
print("Uncertain:", result["uncertain_segments"])

for segment in result["segments"]:
    print("\nSpeaker:", segment["speaker"])
    print("Text:", segment["text"])
    print("Reliability:", segment["reliability"]["status"])
    print("Reasons:", segment["reliability"]["reasons"])
