```shell
 dotnet run TrackerRunner.csproj 1 3 5 1000 localhost:5099/raw
```

```shell
1 3 5 10 https://router.kind.cluster/
```

```shell
cd bin/Debug/net7.0/
dotnet TrackerRunner.dll 1 3 5 10 
```


COUNT=10
INTERVAL=3
CAR_URL=http://car-service/
INTERNATIONAL=true
TARGET_URL=http://localhost:5060/
ROUTES_SOUCE=/pregen/dutch_border_belgium_side 
BATCH_SIZE=5
TIME_FACTOR=1
STATUS_INTERVAL=120
