# Running it

## Generator

Setup

```shell
poetry shell
poetry install
```

```shell
poetry run python tracker_generator/generator.py <region> <count> <interval>
```

```shell
poetry run python tracker_generator/generator.py "Eindhoven, Noord-Brabant, Netherlands" 10 3
```

```shell
poetry run python tracker_generator/generator.py '{"south": 51.075920, "west": 3.180542, "north": 51.522416, "east": 5.907898}' 10 3 --type BBOX
```

With htlm map output:

```shell
poetry run python tracker_generator/generator.py "Eindhoven, Noord-Brabant, Netherlands" 10 3 --debug
```

For testing OUR international api - Dutch border:

```shell
poetry run python tracker_generator/generator.py '{"south": 51.243865, "west": 4.446716, "north": 51.391494, "east": 5.034485}' 10 3 --type BBOX
```

For testing OUR international api - Luxembourg border:

```shell
poetry run python tracker_generator/generator.py '{"south": 49.661406, "west": 5.548096, "north": 50.006856, "east":5.733490}' 10 3 --type BBOX
```

For testing THEIR international api - Dutch border:

```shell
poetry run python tracker_generator/generator.py '{"south": 51.337476, "west": 5.173187, "north": 51.735534, "east": 5.795288}' 10 3 --type BBOX
```

For testing THEIR international api - Luxembourg border:

```shell
poetry run python tracker_generator/generator.py '{"south": 49.572431, "west": 5.921974, "north": 49.793012, "east": 6.072693}' 10 3 --type BBOX
```