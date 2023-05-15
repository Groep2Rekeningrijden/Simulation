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

With htlm map output:

```shell
poetry run python tracker_generator/generator.py "Eindhoven, Noord-Brabant, Netherlands" 10 3 --debug
```
