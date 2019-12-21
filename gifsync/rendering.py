import os
import subprocess
import tempfile
from typing import List

from PIL import Image
from pydub import AudioSegment


def render_video(
    frames: List[Image.Image], fps: int, audio: AudioSegment, output: str
) -> None:
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
