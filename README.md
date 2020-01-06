# gifsync
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

Maps frames of a gif to audio based on its amplitude.

## Usage

As with many multimedia programs, **[ffmpeg](https://ffmpeg.org/) is required**. Here are a
[couple](https://github.com/adaptlearning/adapt_authoring/wiki/Installing-FFmpeg)
[guides](https://video.stackexchange.com/questions/20495/how-do-i-set-up-and-use-ffmpeg-in-windows).

You'll also want ImageMagick installed if you plan on using the liquid rescale
("content-aware scale") effect.

### Setup

Gifsync currently isn't on PyPI since it's in an early state, but it can be run like a typical Python app. After
cloning the repo:

```sh
pip install poetry  # if you don't already have it
poetry install
```

It's also worth making sure that you have `ffmpeg` in your PATH.

```sh
$ ffmpeg -version
ffmpeg version 3.4.6-0ubuntu0.18.04.1 Copyright (c) 2000-2019 the FFmpeg developers
<...>
```

### Usage

For more info on tweaking the result, use the `--help`/`-h` flag. Basic usage is illustrated below.

```
poetry run python -m gifsync \
    -a in_audio.mp3 \
    -g in_gif.gif \
    -o out_video.mp4
```
