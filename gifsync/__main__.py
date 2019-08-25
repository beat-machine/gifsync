import argparse

import halo
from PIL import Image
from pydub import AudioSegment

from gifsync.frames import to_frames, render_indexed_frames
from gifsync.volume import median_filter, normalize, to_loudness_ratios


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-audio", "-a", required=True, help="input audio file")
    parser.add_argument("--input-gif", "-g", required=True, help="input gif file")
    parser.add_argument(
        "--silence-threshold",
        "-t",
        type=int,
        default=-30,
        help="silence threshold (activity below this level is cut from the original audio, set lower if experiencing "
        "random cuts, max is 0)",
    )
    parser.add_argument(
        "--fps",
        "-f",
        type=int,
        default=30,
        help="fps of the resulting video (does not affect audio)",
    )
    parser.add_argument(
        "--high-pass-hz",
        "-p",
        type=int,
        default=800,
        help="cutoff frequency of high pass used when mapping frames to amplitude (used to get a more defined result, "
        "not audible in final product)",
    )
    parser.add_argument(
        "--smoothing",
        "-s",
        type=int,
        default=2,
        help="smoothing window to use (increase if result is jittery, decrease if lacking definition)",
    )
    parser.add_argument(
        "--show-amplitude-graph",
        action="store_true",
        help="shows a graph of the audio's amplitude (after processing, before mapping to frames) before rendering",
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="output filename (extension defaults to mp4)",
    )
    args = parser.parse_args()

    with halo.Halo(text="Processing audio") as spinner:
        original_audio = (
            AudioSegment.from_file(args.input_audio)
            .normalize()
            .remove_dc_offset()
            .strip_silence(silence_thresh=args.silence_threshold)
        )

        # To get a more defined output (instead of just having the gif jitter around in the middle third of its frames),
        # we use a high pass and compressor to bring out as much definition as we can.
        processed_audio = (
            original_audio.high_pass_filter(args.high_pass_hz)
            .compress_dynamic_range()
            .normalize()
        )

        spinner.succeed()

    with halo.Halo("Processing image") as spinner:
        gif = Image.open(args.input_gif)

        if not gif.is_animated or gif.n_frames <= 1:
            spinner.fail("Image only has 1 frame")
            exit(1)

        # Make sure both width and height are even to prevent ffmpeg from freaking out
        w, h = gif.size
        if w % 2 != 0:
            w += 1
        if h % 2 != 0:
            h += 1

        ms_per_frame = 1000 // args.fps
        frames = [f.resize((w, h)) for f in to_frames(gif)]

        spinner.succeed()

    with halo.Halo("Selecting frames") as spinner:
        ratios = list(to_loudness_ratios(processed_audio, ms_per_frame))
        smoothed_ratios = median_filter(list(normalize(ratios)), window=args.smoothing)

        frame_indices = [int((len(frames) - 1) * r) for r in smoothed_ratios]

        if args.show_amplitude_graph:
            import matplotlib.pyplot as plt

            spinner.info("Displaying graph")

            plt.plot(smoothed_ratios)
            plt.show()

        spinner.succeed()

    with halo.Halo(f"Rendering video to {args.output}") as spinner:
        render_indexed_frames(
            frame_indices, frames, args.fps, original_audio, args.output
        )
        spinner.succeed()

    print("Done!")


if __name__ == "__main__":
    main()
