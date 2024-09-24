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
def main(input, output):
    converter = IsaGtfsConverter()
    converter.convert(input, output)

if __name__ == '__main__':
    main()