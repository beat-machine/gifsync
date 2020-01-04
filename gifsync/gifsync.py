import os
import subprocess
import tempfile
from typing import List, Union, Iterable

import PIL.Image
import pydub

import gifsync.effects as fx


def to_rms_array(audio: pydub.AudioSegment, step_ms: int):
    return [audio[i: i + step_ms].rms for i in range(step_ms, len(audio), step_ms)]


def normalize(values: Iterable[float]):
    values = list(values)

    x_min = min(values)
    x_max = max(values)

    for x_i in values:
        yield (x_i - x_min) / (x_max - x_min)


def median_filter(values: Iterable[float], window: int = 1) -> List[float]:
    values = list(values)

    filtered = [0.0] * len(values)

    for i in range(window):
        filtered[i] = values[i]
        filtered[-i] = values[-i]

    for i in range(window, len(values) - window):
        segment = values[i - window: i + window]
        filtered[i] = list(sorted(segment))[len(segment) // 2]

    return filtered


def to_frames(gif: PIL.Image.Image):
    try:
        if not gif.is_animated:
            yield gif.copy()
            return
    except AttributeError:
        yield gif.copy()
        return

    for i in range(gif.n_frames):
        gif.seek(i)
        yield gif.copy()


def render_video(
        frames: List[PIL.Image.Image], audio: pydub.AudioSegment, fps: int, output: str
):
    frame_digits = len(str(len(frames)))
    filename_format = "{0:0" + str(frame_digits) + "d}.png"

    with tempfile.TemporaryDirectory() as d:
        for i, r in enumerate(frames):
            r.save(os.path.join(d, filename_format.format(i)))

        audio_filename = os.path.join(d, output + ".mp3")
        audio.export(audio_filename, format="mp3")

        subprocess.check_call(
            [
                # fmt: off
                "ffmpeg",
                "-hide_banner",
                "-loglevel", "panic",
                "-y",
                "-r", str(fps),
                "-f", "image2",
                "-i", os.path.join(d, f"%0{frame_digits}d.png"),
                "-i", audio_filename,
                "-pix_fmt", "yuv420p",
                "-vcodec", "libx264",
                "-acodec", "aac",  # Using MP3 makes some websites act up when uploading
                "-crf", "25",
                output + (".mp4" if len(output.split(".")) <= 1 else ""),
                # fmt: on
            ]
        )


def apply_av_effects(
        audio: Union[pydub.AudioSegment, str],
        gif: Union[PIL.Image.Image],
        effects: List[fx.AVEffect],
        output: str,
        output_fps: int = 24,
        high_pass_hz: int = 800,
        smoothing_window: int = 2
):
    if type(audio) is str:
        audio = pydub.AudioSegment.from_file(audio)

    if type(gif) is str:
        gif = PIL.Image.open(gif)

    # To make ffmpeg happy, we want our frames to have even dimensions.
    w, h = gif.size
    if w % 2 != 0:
        w -= 1
    if h % 2 != 0:
        h -= 1

    frames = [f.resize((w, h)) for f in to_frames(gif)]
    processed_audio = audio.high_pass_filter(high_pass_hz).compress_dynamic_range().normalize()

    ms_per_frame = 1000 // output_fps
    gif_time_curve = list(
        normalize(
            median_filter(
                to_rms_array(processed_audio, ms_per_frame), window=smoothing_window
            )
        )
    )

    reordered_frames = list(fx.apply_effects(frames, gif_time_curve, *effects))
    audio = audio[: ms_per_frame * len(reordered_frames)]

    render_video(reordered_frames, audio, output_fps, output)
