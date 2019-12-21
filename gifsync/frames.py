from PIL import Image


def to_frames(gif: Image.Image):
    """
    Converts a Pillow image into a sequence of its frames
    :param gif: Animated image to iterate over
    :return: A generator yielding copies of each of its frames
    """

    # noinspection PyUnresolvedReferences
    try:
        if not gif.is_animated:
            yield gif.copy()
            return
    except AttributeError:
        yield gif.copy()
        return

    # noinspection PyUnresolvedReferences
    for i in range(gif.n_frames):
        gif.seek(i)
        yield gif.copy()
