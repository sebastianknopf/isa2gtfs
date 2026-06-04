import click
import logging

from isa2gtfs.converter import IsaGtfsConverter

logging.basicConfig(
    level=logging.INFO, 
    format= '[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)

@click.command
@click.option('--input', '-i', default='./input', help='input directory or ZIP file')
@click.option('--output', '-o', default='./output', help='output directory or ZIP file')
@click.option('--config', '-c', default=None, help='additional config file')
@click.option('--dialect', '-d', default='init51', help='name of the implementation used for conversion')
def main(input, output, config, dialect):
    converter = IsaGtfsConverter(config, dialect)
    converter.convert(input, output)

if __name__ == '__main__':
    main()