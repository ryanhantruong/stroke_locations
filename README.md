# Stroke triage inputs #

This repo provides Python 3 scripts to generate input data for simulations of a [stroke triage model](https://github.com/eschenfeldt/stroke). Specifically, it can be used to generate a set of locations in any state or states, randomly distributed by population (according to the 2010 census), and then can use [Google maps](https://github.com/googlemaps/google-maps-services-python) to compute travel times between those points and nearby stroke-certified hospitals.

## Random locations ##

Generate a CSV of locations using the script `population.py`, which accepts states as command line arguments. For example, running

```
python3 population.py Illinois IN -p 5000
```

generates a file `data/points/IL_IN_n=5000.csv` containing 5000 random locations in Illinois and Indiana. The first time you use a particular state the [census data](https://www.census.gov/geo/maps-data/data/tiger-line.html) for that state will be downloaded and stored in `data/census`. States can be listed by name, abbreviation, or [FIPS state code](https://en.wikipedia.org/wiki/Federal_Information_Processing_Standard_state_code), with some flexibility in the matching provided by the [`us` package](https://github.com/unitedstates/python-us). Details on command line options available via `python3 population.py --help`.

The script wraps the function `population.generate_points`, which can be used as part of a larger workflow.

#### Visualization ####

The points generated above can be visualized using the `visualization.py` script, either as individual points or a heatmap. Note that this requires Google maps configuration. Plotting of hospital locations may not work by default on Windows machines, see [this issue](https://github.com/vgm64/gmplot/issues/63).

## Hospitals ##

The `hospitals` module defines functions for generating a simple list of stroke-certified hospitals, determining their locations, and identifying transfer destinations for all primary centers. Because the latter two steps involve a large number of Google maps API calls, there is no script interface. Call `hospitals.master_list()` to generate an initial list of Joint Commission certified [primary](https://www.jointcommission.org/certification/primary_stroke_centers.aspx) and [comprehensive](https://www.jointcommission.org/certification/advanced_certification_comprehensive_stroke_centers.aspx) stroke centers.<sup>[1](#footnote1)</sup>

The function `hospitals.update_locations()`  calls the Google maps [Places API](https://developers.google.com/places/web-service/intro) to give a best guess address and geographic coordinates for a hospital based on the information proveded by the Joint Commission. The function `hospitals.update_transfer_destinations()` calls the [Distance Matrix API](https://developers.google.com/maps/documentation/distance-matrix/start) to determine which of the comprehensive centers is closest by travel time to each primary center, designating that as the default transfer destination. Both functions update the master list, which is stored as a CSV at `data/hospitals/all.csv`, and neither will change any data already stored in that file. Thus manual addresses, locations, and transfer destinations can be added by editing the CSV. This file also has empty columns for door to needle and door to puncture distributions for each hospital, defined by median and interquartile range, which can be filled in as available.

## Travel times ##

Once a set of points has been generated and a list of hospitals exists, travel times from the points to nearby hospitals can be generated with the `travel_times.py` script. This accepts a single command line argument `point_file` with the path to the file of points (formatted like those generated by `population.py` above), and uses the master list of hospitals to identify those that are nearby (see below) and uses the [Google Maps Distance Matrix API](https://developers.google.com/maps/documentation/distance-matrix/start) to compute travel times to those hospitals. These travel times are stored in a CSV where each row represents a point and columns are hospitals, with a hospital being included only if it is nearby at least one of the points.

#### "Nearby" hospitals ####

To limit the number of Google Maps API calls, travel times are computed only for hospitals close to the point in question. The determination of nearby hospitals is performed separately for PSCs and CSCs. First, geographic distance is computed between the point and all hospitals, and the closest hospital is identified. We let `m` be the distance to this closest hospital in miles, and define a cutoff distance as `max(m * 1.5, m + 30)`, and consider any hospital within this cutoff to be "nearby". All such hospitals get computed travel times and are included in the resulting output file. Note that no further thresholding is done on actual travel times, so this may result in the inclusion of some unrealistic hospitals in [the model](https://github.com/eschenfeldt/stroke), which considers all hospitals that have computed travel times available.

## Anonymization ##

The `anonymize.py` script will convert the travel times computed by `travel_times.py` into the format required to run [the model](https://github.com/eschenfeldt/stroke), which primarily involves removing the specific location information and identifying hospital information. The generated hospital file will also include only hospitals needed for the locations used. These anonymized files can be used as inputs to the visualization script, though they will fail if non-anonymized versions of the data are no longer available.

## Setup ##

Dependencies are recorded in `stroke_locations.yml`.

To use any of the Google Maps functionality, an API key needs to be entered into `config/google_maps.cfg`. The format is specified in `config/google_maps.cfg.example`. The project associated with the key needs to have the Distance Matrix, Places, and [Maps JavaScript](https://developers.google.com/maps/documentation/javascript/tutorial) APIs activated.

Fully processing hospitals will generally use one Places API call per hospital and 2-5 Distance Matrix elements per primary center (depending on how many comprehensive centers are nearby). Generating travel times will use at least 2 and up to 50 Distance Matrix elements per point, depending on the number of nearby hospitals for each point. For densely populated areas this will often be in the 10-25 range. To avoid accidental charges the `travel_times.py` script requires the `allow_large` flag to run on more than 10 points.

----
<a name="footnote1">1</a>: For the moment [thrombectomy-capable](https://www.jointcommission.org/certification/certification_for_thrombectomycapable_stroke_centers.aspx) stroke centers are treated as primary centers.
