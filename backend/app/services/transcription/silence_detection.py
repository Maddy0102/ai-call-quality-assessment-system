import re
import subprocess


def detect_silence(audio_path, noise="-35dB", min_duration=0.5):
    """
    Detect silent intervals using FFmpeg.
    Returns intervals in seconds.
    """

    command = [
        "ffmpeg",
        "-hide_banner",
        "-i", str(audio_path),
        "-af", f"silencedetect=noise={noise}:d={min_duration}",
        "-f", "null",
        "-"
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg silence detection failed: {result.stderr[-1000:]}"
        )

    output = result.stderr

    starts = re.findall(
        r"silence_start:\s*([\d.]+)",
        output
    )

    ends = re.findall(
        r"silence_end:\s*([\d.]+)",
        output
    )

    intervals = []

    for index, start in enumerate(starts):
        start_time = float(start)

        if index < len(ends):
            end_time = float(ends[index])
        else:
            end_time = None

        intervals.append({
            "start": start_time,
            "end": end_time
        })

    return intervals


def analyze_segment_silence(segment, silence_intervals):
    """
    Calculate the percentage of a transcript segment
    that overlaps detected silence.
    """

    start = float(segment["start"])
    end = float(segment["end"])

    duration = end - start

    if duration <= 0:
        return {
            "silence_ratio": 0,
            "overlaps_silence": False,
            "mostly_silence": False
        }

    silent_duration = 0

    for interval in silence_intervals:
        silence_start = interval["start"]

        silence_end = (
            interval["end"]
            if interval["end"] is not None
            else end
        )

        overlap_start = max(start, silence_start)
        overlap_end = min(end, silence_end)

        if overlap_end > overlap_start:
            silent_duration += overlap_end - overlap_start

    ratio = min(silent_duration / duration, 1.0)

    return {
        "silence_ratio": round(ratio, 3),
        "overlaps_silence": ratio >= 0.20,
        "mostly_silence": ratio >= 0.50
    }
