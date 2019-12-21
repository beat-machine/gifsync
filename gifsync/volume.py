from typing import List

from pydub import AudioSegment


def to_loudness_ratios(audio: AudioSegment, step_ms: int):
    """
    Converts a pydub AudioSegment to a list of loudness ratios.
    :param audio: Audio to convert
    :param step_ms: Chunk size to use
    :return: A generator yielding loudness ratios of each chunk
    """
    for i in range(step_ms, len(audio), step_ms):
        clip = audio[i : i + step_ms]
        yield clip.rms / clip.max_possible_amplitude


def normalize(values: List[float], coeff: int = 1):
    """
    Normalizes a list of floats to be within the range [0, coeff].
    :param values: List of floats to normalize
    :param coeff: Coefficient (max value) of result
    :return: A generator yielding normalized values
    """
    x_min = min(values)
    x_max = max(values)

    for x_i in values:
        yield coeff * (x_i - x_min) / (x_max - x_min)


def median_filter(values: List[float], window: int = 1) -> List[float]:
    """
    Applies a median filter to each value with sufficient padding.
    :param values: List of floats to filter
    :param window: Radius of window to determine values of each element
    :return: A filtered list
    """
    filtered = [0.0] * len(values)

    for i in range(window):
        filtered[i] = values[i]
        filtered[-i] = values[-i]

    for i in range(window, len(values) - window):
        segment = values[i - window : i + window]
        filtered[i] = list(sorted(segment))[len(segment) // 2]

    return filtered
