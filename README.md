## Stroke triage inputs ##

This repo provides python 3 scripts to generate input data for simulations of a [stroke triage model](https://github.com/eschenfeldt/stroke). Specifically, it can be used to generate a set of locations in any state or states, randomly distributed by population (according to the 2010 census), and then can use [Google maps](https://github.com/googlemaps/google-maps-services-python) to compute travel times between those points and nearby stroke-certified hospitals.

### Random locations ###

Generate a CSV of locations using the script `population.py`, which accepts states as command line arguments. For example, running

```
python3 population.py Illinois IN -p 5000
```

generates a file `data/points/IL_IN_n=5000.csv` containing 5000 random locations in Illinois and Indiana. The first time you use a particular state the [census data](https://www.census.gov/geo/maps-data/data/tiger-line.html) for that state will be downloaded and stored in `data/census`. States can be listed by name, abbreviation, or [FIPS state code](https://en.wikipedia.org/wiki/Federal_Information_Processing_Standard_state_code), with some flexibility in the matching provided by the [`us` package](https://github.com/unitedstates/python-us). Details on command line options available via `python3 population.py --help`.

The script wraps the function `population.generate_points`, which can be used as part of a larger workflow.
