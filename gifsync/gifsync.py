import os
import subprocess
import tempfile
import warnings
from typing import List, Union

import PIL.Image
import librosa
import numpy as np
import scipy.signal
import soundfile

import gifsync.effects as fx

warnings.filterwarnings("ignore", category=UserWarning, module='librosa')


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
        frames: List[PIL.Image.Image], audio_y: np.ndarray, audio_sr: int, fps: int, output: str
):
    with tempfile.TemporaryDirectory() as d:
        audio_filename = os.path.join(d, output + ".wav")
        soundfile.write(audio_filename, audio_y, audio_sr)

        p = subprocess.Popen(
            [
                # fmt: off
                "ffmpeg",
                "-hide_banner",
                "-loglevel", "panic",
                "-y",
                "-f", "image2pipe",
                "-vcodec", "mjpeg",
                "-r", str(fps),
                "-i", "-",
                "-i", audio_filename,
                "-acodec", "aac",
                "-pix_fmt", "yuv420p",
                "-vcodec", "libx264",
                "-crf", "25",
                output + (".mp4" if len(output.split(".")) <= 1 else ""),
                # fmt: on
            ],
            stdin=subprocess.PIPE
        )

        for f in frames:
            f.convert('RGB').save(p.stdin, 'JPEG')

        p.stdin.close()
        p.wait()


# Best guess at attribution: https://github.com/andi611/CS-Tacotron-Pytorch/blob/master/src/utils/data.py
def high_pass(y, sr, filter_pass_freq):
    nyquist_rate = sr / 2.
    desired = (0, 0, 1, 1)
    bands = (0, 70, filter_pass_freq, nyquist_rate)
    filter_coefs = scipy.signal.firls(1001, bands, desired, nyq=nyquist_rate)
    filtered_audio = scipy.signal.filtfilt(filter_coefs, [1], y)

    return filtered_audio


def process_files(
        audio: str,
        gif: Union[PIL.Image.Image],
        effects: List[fx.AVEffect],
        output: str,
        output_fps: int = 24,
        high_pass_hz: int = 800,
        smoothing_window: int = 3
):
    print('load audio')
    y, sr = librosa.load(audio)
    y /= np.max(np.abs(y), axis=0)
    audio_length = librosa.get_duration(y, sr)

    print('load image')
    if type(gif) is str:
        gif = PIL.Image.open(gif)

    print('norm image')
    # To make ffmpeg happy, we want our frames to have even dimensions.
    w, h = gif.size
    if w % 2 != 0:
        w -= 1
    if h % 2 != 0:
        h -= 1

    print('x frames')
    frames = [f.resize((w, h)) for f in to_frames(gif)]

    print('calc energies')
    energy_by_frame = high_pass(y, sr, high_pass_hz)
    frame_splits = np.array_split(energy_by_frame, int(audio_length * output_fps))
    energy_by_frame = np.array([np.max(librosa.feature.rms(y=s)) for s in frame_splits])
    energy_by_frame = scipy.signal.medfilt(energy_by_frame, kernel_size=smoothing_window)
    energy_by_frame /= np.max(np.abs(energy_by_frame), axis=0)

    print('apply fx')
    reordered_frames = list(fx.apply_effects(frames, energy_by_frame, *effects))

    print('render')
    render_video(reordered_frames, y, sr, output_fps, output)
