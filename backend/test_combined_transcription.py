from app.services.transcription.channel_transcription import transcribe_call

result = transcribe_call(
    left_audio_path="uploads/left_16k.wav",
    right_audio_path="uploads/right_16k.wav"
)

print("\n========== COMBINED TRANSCRIPTION ==========")

print("Model:", result["model"])
print("Executive language:", result["executive_language"])
print("Customer language:", result["customer_language"])

print("\nTotal segments:", len(result["segments"]))

for segment in result["segments"]:
    print(
        f"\n[{segment['start']}s - {segment['end']}s]"
        f" [{segment['speaker']}]"
    )
    print("Text:", segment["text"])
