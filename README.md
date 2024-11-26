# isa2gtfs
This repository provides a lightweight converter for timetable information data in IVU Standard ASCII (ISA) format to GTFS. ISA is a data exchange format for timetable information data between different systems.

## Usage
We recommend running the converter in a virtual environment with all dependencies installed. To run the converter, use the following command:

```shell
python -m isa2gtfs -i ./input.zip -o ./output.zip [-c ./isa2gtfs.yaml]
```

The file input.zip can be either a ZIP file or a directory containing your ISA input data. The output.zip can also be either a ZIP file or directory where the GTFS output files are written to. By specifying an additional config YAML file, you can modify the behaviour of the converter. See the next section for details.

## Configuration
By using an additional YAML file, you can set some preferences for the converter. The YAML file *must have* the following structure in order to work properly:

```yaml
config:
  extract_zone_ids: true
default:
  agency_url: "https://gtfs.org"
  agency_timezone: "Europe/Berlin"
  agency_lang: "de-DE"
mapping:
  station_id: "[stationInternationalId]_Parent"
  stop_id: "[stopInternationalId]"
  service_id: "service-[serviceId]"
  agency_id: "agency-[agencyId]"
  route_id: "[routeInternationalId]"
  trip_id: "[tripRouteId][tripId]"
```

The configurations will take following effect:

- config.extract_zone_ids Whether to extract zone IDs and write them to zone_id in stops.txt or not
- default.agency_url Default URL for agencies, if no agency URL is available
- default.agency_timezone Default timezone for agencies, if no timezone is available
- mapping.station_id The template for generating station IDs (location type 1 in GTFS)
- mapping.stop_id The template for generating stop IDs (location type 0 or emtpy in GTFS)
- mapping.service_id The templatr for generating service IDs
- mapping.agency_id The template for generating agency IDs
- mapping.route_id The template for generating route IDs 
- mapping.trip_id The template for generating trip IDs

All templates can use several placeholders in their context. Following placeholders are available:

- [stationId] for stations, maps to the internal station ID
- [stationInternationalId] for stations, maps to the international station ID (IFOPT)
- [stopId] for stops, maps to the internal stop ID
- [stopInternationalId] for stops, maps to the international stop ID (IFOPT)
- [agencyId] for agencies, maps to the internal agency ID
- [routeId] for lines, maps to the internal line or route ID
- [routeInternationalId] for lines, maps to the international line or route ID (DLID/DTID)
- [tripRouteId] for trips, maps to the corresponding route ID created previously of a trip
- [tripId] for trips, maps to the internal trip ID
- [tripInternationalId] for trips, maps to thr international trip ID (DFID)

See the example above for an example configuration.

## Different Implementations
Since data exchange interfaces provide many different ways to build up a data model, the exact data modelling can vary from system to system. Therefore, this converter is built upon so-called dialects which contain the exact converter implementation. Currently, there following dialects implemented:

    - init51 - ISA 5.1 exported by MOBILE.PLAN (INIT) with support for line versions

If your desired dialect is missing here, feel free to open an issue or a PR with an implementation approach.

# License
This project is licensed under the Apache 2.0 license. See ![LICENSE.md](LICENSE.md) for details.
