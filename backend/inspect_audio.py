import soundfile as sf
import numpy as np

audio_path = "uploads/0126eb3d-6aa7-4449-b68a-3986ea9221ce.mp3"

audio, sample_rate = sf.read(audio_path)

print("========== AUDIO DETAILS ==========")
print("Sample rate:", sample_rate)
print("Shape:", audio.shape)
print("Duration:", len(audio) / sample_rate)

print("Minimum amplitude:", np.min(audio))
print("Maximum amplitude:", np.max(audio))
print("Average amplitude:", np.mean(np.abs(audio)))
print("RMS amplitude:", np.sqrt(np.mean(audio ** 2)))
