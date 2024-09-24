import click
import logging

from isa2gtfs.converter import IsaGtfsConverter

logging.basicConfig(
    level=logging.INFO, 
    format= '[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)

@click.command
@click.option('--input', default='./input', help='input directory or ZIP file')
@click.option('--output', default='./output', help='output directory or ZIP file')
@click.option('--config', default=None, help='additional config file')
def main(input, output, config):
    converter = IsaGtfsConverter(config)
    converter.convert(input, output)

if __name__ == '__main__':
    main()