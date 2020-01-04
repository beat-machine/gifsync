import functools
import io
import tempfile
from typing import Callable, Iterable, List

import numpy as np
import wand.image
from PIL import Image

AVEffect = Callable[[List[Image.Image], np.ndarray], Iterable[Image.Image]]


def index_by_amplitude(
    frames: List[Image.Image], energy: np.ndarray
) -> Iterable[Image.Image]:
    frame_indices = (len(frames) - 1) * energy

    for i in frame_indices:
        yield frames[int(i)]


def cas_by_amplitude(
    frames: List[Image.Image], amplitudes: List[float]
) -> Iterable[Image.Image]:
    factors = [1 - a for a in amplitudes]
    frame = frames[0]

    frame_filename = tempfile.mktemp(suffix=".png")
    frame.save(frame_filename)

    with wand.image.Image(filename=frame_filename) as base_image:
        for f in factors:
            with base_image.clone() as i:
                original_width, original_height = i.size
                i.liquid_rescale(int(f * original_width), int(f * original_height))
                i.resize(original_width, original_height)

                out = io.BytesIO()
                i.save(out)
                out.seek(0)
                yield Image.open(out)


def _cas(frame: Image.Image, f: float) -> Image.Image:
    frame_filename = tempfile.mktemp(suffix=".png")
    frame.save(frame_filename)

    with wand.image.Image(filename=frame_filename) as base_image:
        with base_image.clone() as i:
            original_width, original_height = i.size
            i.liquid_rescale(int(f * original_width), int(f * original_height))
            i.resize(original_width, original_height)

            out = io.BytesIO()
            i.save(out)
            out.seek(0)
            return Image.open(out)


def cas_and_index_by_amplitude(
    frames: List[Image.Image], amplitudes: List[float]
) -> Iterable[Image.Image]:
    indexed_frames = list(index_by_amplitude(frames, amplitudes))
    frame_indices = [int((len(frames) - 1) * r) for r in amplitudes]
    factors = [max(0.1, 1 - a) for a in amplitudes]
    frame_cache = {}

    for (idx, f) in zip(frame_indices, factors):
        if idx not in frame_cache:
            frame_cache[idx] = _cas(indexed_frames[idx], f)

        yield frame_cache[idx]


def apply_effects(
    frames: List[Image.Image], energy: np.ndarray, *effects: AVEffect
) -> Iterable[Image.Image]:
    return functools.reduce(
        lambda effect_frames, f: list(f(effect_frames, energy)), effects, frames
    )
