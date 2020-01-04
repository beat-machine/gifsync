import click
from .gifsync import process_files
from .effects import index_by_amplitude, cas_and_index_by_amplitude


def validate_smoothing_window(_ctx, _param, value):
    if value % 2 == 0:
        raise click.BadParameter('smoothing window must be odd')


@click.command()
@click.option('--audio', '-a', type=click.Path(exists=True, dir_okay=False), required=True)
@click.option('--gif', '-g', type=click.Path(exists=True, dir_okay=False), required=True)
@click.option('--fps', '-f', type=int, default=24)
@click.option('--high-pass-hz', '-h', type=int, default=800)
@click.option('--smoothing', '-s', type=int, default=3, callback=validate_smoothing_window)
@click.option('--cas', '-c', is_flag=True)
@click.option('--output', '-o', type=click.Path(exists=False), required=True)
def main(audio, gif, fps, high_pass_hz, smoothing, cas, output):
    effects = [index_by_amplitude]

    if cas:
        effects = [cas_and_index_by_amplitude]

    process_files(audio, gif, effects, output, fps, high_pass_hz, smoothing)


if __name__ == "__main__":
    main()
