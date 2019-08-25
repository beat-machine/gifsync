import os
import subprocess
import tempfile
from typing import List

from PIL import Image
from pydub import AudioSegment


def to_frames(gif: Image.Image):
    """
    Converts a Pillow image into a sequence of its frames
    :param gif: Animated image to iterate over
    :return: A generator yielding copies of each of its frames
    """
    # noinspection PyUnresolvedReferences
    for i in range(gif.n_frames):
        gif.seek(i)
        yield gif.copy()


def render_indexed_frames(
    indices: List[int],
    frames: List[Image.Image],
    fps: int,
    final_audio: AudioSegment,
    output: str,
) -> None:
    """
    Uses ffmpeg to render reordered frames with background audio.

    :param indices: A list of indices in the `frames` parameter to return
    :param frames: A list of frames to re-index and render into a video
    :param fps: FPS of the resulting video
    :param final_audio: Audio track of the resulting video
    :param output: Output file (mp4 highly suggested, extension will be added if none is present)
    """
    result_frames = []
    for i in indices:
        result_frames.append(frames[i])

    frame_digits = len(str(len(result_frames)))
    filename_format = "{0:0" + str(frame_digits) + "d}.png"

    with tempfile.TemporaryDirectory() as d:
        for i, r in enumerate(result_frames):
            r.save(os.path.join(d, filename_format.format(i)))

        audio_filename = os.path.join(d, output + ".mp3")
        final_audio.export(audio_filename, format="mp3")

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
