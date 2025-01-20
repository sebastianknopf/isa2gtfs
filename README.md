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
  extract_zone_ids: false
  extract_platform_codes: true
  generate_feed_info: true
  generate_feed_start_date: true
  generate_feed_end_date: true
  write_feed_id: false
default:
  agency_url: "https://gtfs.org"
  agency_timezone: "Europe/Berlin"
  agency_lang: "de-DE"
  feed_info:
    feed_publisher_name: "YourCompanyName"
    feed_publisher_url: "https://yourdomain.dev"
    feed_contact_url: "https://yourdomain.dev/contact"
    feed_contact_email: "contact@yourdomain.dev"
    feed_version: "%Y%m%d%H%M%S"
    feed_lang: "de-DE"
    default_lang: "de-DE"
mapping:
  feed_id: "COM"
  station_id: "[stationInternationalId]_Parent"
  stop_id: "[stopInternationalId]"
  service_id: "service-[serviceId]"
  agency_id: "agency-[agencyId]"
  route_id: "[routeInternationalId]"
  trip_id: "[tripRouteId][tripId]"
```

The configurations will take following effect:

- config.extract_zone_ids Whether to extract zone IDs and write them to zone_id in stops.txt or not
- config.extract_platform_codes Whether to extract platform codes from ATTRIBUT.ASC and HSTATTRI.ASC or not
- config.generate_feed_info Whether to generate the feed_info.txt file or not
- config.generate_feed_start_date Whether to generate feed_start_date in feed_info.txt or not
- config.generate_feed_end_date Whether to generate feed_end_date in feed_info.txt or not
- config.write_feed_id Whether to write the column feed_id (unofficial!) in feed_info.txt or not; this column might be used by systems like OpenTripPlanner
- default.agency_url Default URL for agencies, if no agency URL is available
- default.agency_timezone Default timezone for agencies, if no timezone is available
- default.feed_info.feed_publisher_name Feed publisher name for feed_info.txt
- default.feed_info.feed_publisher_url Feed publisher URL for feed_info.txt
- default.feed_info.feed_contact_url Feed contact URL for feed_info.txt; should point to a contact page
- default.feed_info.feed_contact_email Feed contact email address for feed_info.txt; should point to a mail address which can be used for issue tracking
- default.feed_info.feed_version Version template; the version is being generated based on the current date/time, the value must be a valid strftime format string
- default.feed_info.feed_lang Feed language for feed_info.txt which is used as default language for agencies
- default.feed_info.default_lang Feed language for feed_info.txt which ist used by the GTFS consumer if the the langauge of the rider is not known
- mapping.feed_id The feed ID used in systems like OpenTripPlanner
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
