using System.Text;
using Newtonsoft.Json;
using TrackerRunner.DTOs;
using TrackerRunner.International;
using JsonSerializer = System.Text.Json.JsonSerializer;

namespace TrackerRunner;

class Program
{
    private static string _targetUrl = "";
    private static string _carUrl = "";
    private static int _interval;
    private static int _batchSize;
    private static int _count;
    private static int _timeFactor;
    private static int _statusInterval;
    private static readonly Random Rnd = new();
    private static bool _international;
    private static string _routesSource = "";
    private static string _cc = "";


    static async Task Main(string[] args)
    {
        ProcessArgs(args);

        var files = GetFiles();

        var httpClient = new HttpClient();
        var tasks = new List<Task>();

        await CreateTasks(files, httpClient, tasks);

        await Task.WhenAll(tasks);
    }

    private static void ProcessArgs(IReadOnlyList<string> args)
    {
        _count = Convert.ToInt32(Environment.GetEnvironmentVariable("COUNT") ??
                                 throw new ArgumentException("ENV variable COUNT is not defined"));
        _interval = Convert.ToInt32(Environment.GetEnvironmentVariable("INTERVAL") ??
                                    throw new ArgumentException("ENV variable INTERVAL is not defined"));
        _batchSize = Convert.ToInt32(Environment.GetEnvironmentVariable("BATCH_SIZE") ??
                                     throw new ArgumentException("ENV variable BATCH_SIZE is not defined"));
        _timeFactor = Convert.ToInt32(Environment.GetEnvironmentVariable("TIME_FACTOR") ??
                                      throw new ArgumentException("ENV variable TIME_FACTOR is not defined"));
        _statusInterval = Convert.ToInt32(Environment.GetEnvironmentVariable("STATUS_INTERVAL") ??
                                          throw new ArgumentException(
                                              "ENV variable STATUS_INTERVAL is not defined"));
        _targetUrl = Environment.GetEnvironmentVariable("TARGET_URL") ??
                     throw new ArgumentException("ENV variable TARGET_URL is not defined");
        _carUrl = Environment.GetEnvironmentVariable("CAR_URL") ??
                  throw new ArgumentException("ENV variable CAR_URL is not defined");
        _international = bool.Parse(Environment.GetEnvironmentVariable("INTERNATIONAL") ?? "false");
        _routesSource = Environment.GetEnvironmentVariable("ROUTES_SOURCE") ?? "/Routes";
        _cc = Environment.GetEnvironmentVariable("CC") ?? "BE";

        if (_count <= 0 || _interval <= 0 || _batchSize <= 0 || _timeFactor <= 0 || _statusInterval <= 0)
        {
            throw new ArgumentException(
                "Invalid arguments: count, interval, batchSize, timeFactor and statusInterval must be positive integers");
        }
    }

    private static string[] GetFiles()
    {
        var files = Directory.GetFiles(_routesSource);

        if (files.Length == 0)
        {
            throw new Exception("No route files found");
        }

        return files;
    }

    private static async Task CreateTasks(IReadOnlyList<string> files, HttpClient httpClient, ICollection<Task> tasks)
    {
        var vehicles = await GetRandomVehicles(httpClient);
        for (var i = 0; i < _count; i++)
        {
            var file = files[Rnd.Next(files.Count)];
            // var file = files[i];
            var vehicle = vehicles[i];
            var task = Task.Run(async () => { await RunBatch(_batchSize, httpClient, _interval, file, vehicle); });

            tasks.Add(task);
        }
    }

    private static List<List<double>> ReadCoordinatesFromFile(string file)
    {
        var json = File.ReadAllText(file);
        var coordinates = JsonSerializer.Deserialize<List<List<double>>>(json);
        return coordinates ?? throw new InvalidDataException($"Coordinate file {file} failed to read.");
    }

    private static async Task RunBatch(int batchSize, HttpClient httpClient, int interval, string file, VehicleDTO vehicle)
    {
        var coordinates = ReadCoordinatesFromFile(file);

        var result = new List<CoordinatesDto>();
        var timestamp = DateTime.UtcNow;

        foreach (var coord in coordinates)
        {
            result.Add(new CoordinatesDto(coord[1], coord[0], timestamp));
            timestamp = timestamp.AddSeconds(interval);
        }

        if (_international)
        {
            // Console.WriteLine(JsonSerializer.Serialize(vehicle));
            var outVehicle = new Vehicle(vehicle.Id, vehicle.VehicleClassification, vehicle.FuelType);
            var outPoints = result.Select(coordinatesDto => new Point(coordinatesDto)).ToList();
            var raw = new RawRoute(vehicle: outVehicle, points: outPoints);
            // Console.WriteLine("Writing to " + file);
            // await File.WriteAllTextAsync(file.Replace("/pregen", "/rawPregen"),
            //     JsonSerializer.Serialize(raw));
            // return;
            await SendRawAsync(httpClient: httpClient, route: raw);
            return;
        }

        var batchesPerStatus = _statusInterval / (_batchSize * _interval);
        var ticksSinceStatus = batchesPerStatus;
        var id = vehicle.Id;
        for (var j = 0; j < coordinates.Count; j += batchSize)
        {
            if (ticksSinceStatus >= batchesPerStatus)
            {
                await SendStatusAsync(httpClient, new StatusDto(id, 0));
                ticksSinceStatus = 0;
            }

            var batch = new RawInputDto(id, result.Skip(j).Take(batchSize).ToList());
            await SendCoordinatesAsync(httpClient, batch);
            await Task.Delay(_interval * _batchSize * 1000 / _timeFactor);
            ticksSinceStatus++;
        }

        // Small wait so the coordinate service is likely to have processed the coordinates.
        await Task.Delay(3000);

        await SendStatusAsync(httpClient, new StatusDto(id, 1));
    }

    private static async Task<List<VehicleDTO>> GetRandomVehicles(HttpClient httpClient)
    {
        var response = await httpClient.GetStringAsync($"{_carUrl}get-n?n={_count}");
        return JsonConvert.DeserializeObject<List<VehicleDTO>>(response)!;
    }

    private static async Task SendCoordinatesAsync(HttpClient httpClient, RawInputDto batch)
    {
        var content = new StringContent(JsonSerializer.Serialize(batch), Encoding.UTF8, "application/json");
        var response = await httpClient.PostAsync($"{_targetUrl}raw", content);
        response.EnsureSuccessStatusCode();
    }

    private static async Task SendRawAsync(HttpClient httpClient, RawRoute route)
    {
        // Console.WriteLine("--------------------------------------");
        // Console.WriteLine(JsonSerializer.Serialize(route));
        var content = new StringContent(JsonSerializer.Serialize(route), Encoding.UTF8, "application/json");
        var response = await httpClient.PostAsync($"{_targetUrl}submit-raw?cc={_cc}", content);
        // Console.WriteLine("--------------------------------------");
        // Console.WriteLine(content);
        // Console.WriteLine("--------------------------------------");
        // Console.Write(response);
        // Console.WriteLine("--------------------------------------");
        // Console.Write(response.RequestMessage);
        // Console.WriteLine("--------------------------------------");
        response.EnsureSuccessStatusCode();
    }


    private static async Task SendStatusAsync(HttpClient httpClient, StatusDto status)
    {
        // 0 if en route, 1 if ready
        var content = new StringContent(JsonSerializer.Serialize(status), Encoding.UTF8, "application/json");
        var response = await httpClient.PostAsync($"{_targetUrl}status", content);
        response.EnsureSuccessStatusCode();
    }
}