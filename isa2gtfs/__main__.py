import click

from isa2gtfs.converter import IsaGtfsConverter

@click.command
@click.option('--input', default='./input', help='input directory or ZIP file')
@click.option('--output', default='./output', help='output directory or ZIP file')
def main(input, output):
    converter = IsaGtfsConverter()
    converter.convert(input, output)

if __name__ == '__main__':
    main()