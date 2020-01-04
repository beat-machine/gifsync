import click
from .gifsync import apply_av_effects
from .effects import index_by_amplitude, cas_and_index_by_amplitude

@click.command()
@click.option('--audio', '-a', type=click.Path(exists=True, dir_okay=False), required=True)
@click.option('--gif', '-g', type=click.Path(exists=True, dir_okay=False), required=True)
@click.option('--fps', '-f', type=int, default=24)
@click.option('--high-pass-hz', '-h', type=int, default=800)
@click.option('--smoothing', '-s', type=int, default=2)
@click.option('--cas', '-c', is_flag=True)
@click.option('--output', '-o', type=click.Path(exists=False), required=True)
def main(audio, gif, fps, high_pass_hz, smoothing, cas, output):
    effects = [index_by_amplitude]

    if cas:
        effects = [cas_and_index_by_amplitude]

    
    start = timer()
    apply_av_effects(audio, gif, effects, output, fps, high_pass_hz, smoothing)
    end = timer()
    print(end - start)


if __name__ == "__main__":
    main()
