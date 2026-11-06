from pathlib import Path
import numpy as np
import soundfile as sf

from app.services.transcription.silence_detection import detect_silence


def _db(value):
    return round(20 * np.log10(max(float(value), 1e-10)), 2)


def analyze_voice_channel(audio_path, speaker):
    """
    Local audio measurements for one speaker channel.
    No external API calls and no database writes.
    """

    path = Path(audio_path)

    if not path.is_file():
        raise FileNotFoundError(f"Audio file not found: {path}")

    audio, sample_rate = sf.read(path, dtype="float32")

    if audio.ndim == 2:
        audio = np.mean(audio, axis=1)

    if len(audio) == 0:
        raise ValueError("Audio file is empty")

    duration = len(audio) / sample_rate

    # Measure short-time RMS using 20 ms frames.
    frame_size = max(1, int(sample_rate * 0.020))
    usable_length = (len(audio) // frame_size) * frame_size

    frames = audio[:usable_length].reshape(-1, frame_size)
    rms_values = np.sqrt(np.mean(np.square(frames), axis=1))

    frame_db = 20 * np.log10(np.maximum(rms_values, 1e-10))

    # Silence detection is independent for each speaker channel.
    silence_intervals = detect_silence(
        path,
        noise="-35dB",
        min_duration=0.5
    )

    total_silence = 0.0
    pauses = []

    for interval in silence_intervals:
        start = max(0.0, float(interval["start"]))
        end = (
            duration
            if interval["end"] is None
            else min(duration, float(interval["end"]))
        )

        silence_duration = max(0.0, end - start)
        total_silence += silence_duration

        pauses.append({
            "start": round(start, 2),
            "end": round(end, 2),
            "duration": round(silence_duration, 2)
        })

    total_silence = min(total_silence, duration)
    speech_activity = max(0.0, duration - total_silence)

    # Approximate low-energy floor, not a calibrated noise measurement.
    low_energy_floor = float(np.percentile(frame_db, 10))
    median_level = float(np.median(frame_db))

    peak_amplitude = float(np.max(np.abs(audio)))
    clipping_samples = int(np.sum(np.abs(audio) >= 0.999))

    result = {
        "speaker": speaker,
        "duration_seconds": round(duration, 2),
        "sample_rate": int(sample_rate),
        "measurements": {
            "speech_activity_seconds": round(speech_activity, 2),
            "silence_seconds": round(total_silence, 2),
            "speech_activity_percent": round(
                speech_activity / duration * 100, 2
            ),
            "silence_percent": round(
                total_silence / duration * 100, 2
            ),
            "pause_count": len(pauses),
            "longest_pause_seconds": round(
                max((p["duration"] for p in pauses), default=0), 2
            ),
            "average_frame_level_dbfs": _db(np.mean(rms_values)),
            "median_frame_level_dbfs": round(median_level, 2),
            "low_energy_floor_dbfs": round(low_energy_floor, 2),
            "peak_level_dbfs": _db(peak_amplitude),
            "clipping_sample_count": clipping_samples,
            "clipping_percent": round(
                clipping_samples / len(audio) * 100, 5
            ),
        },
        "pauses": pauses,
        "limitations": [
            "Silence is measured independently on this speaker channel.",
            "Low-energy floor is an approximate audio indicator, not a calibrated noise measurement.",
            "These measurements do not establish pronunciation accuracy, confidence, or professionalism.",
        ],
    }

    return result


def analyze_call_voice_quality(executive_audio, customer_audio):
    executive = analyze_voice_channel(
        executive_audio, "EXECUTIVE"
    )
    customer = analyze_voice_channel(
        customer_audio, "CUSTOMER"
    )

    return {
        "analysis_type": "local_audio_measurements",
        "provider": "local",
        "executive": executive,
        "customer": customer,
    }
