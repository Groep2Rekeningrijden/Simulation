using System.Text;
using Newtonsoft.Json;
using TrackerRunner.DTOs;
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


    static async Task Main(string[] args)
    {
        ProcessArgs(args);

        var files = GetFiles();

        var httpClient = new HttpClient();
        var tasks = new List<Task>();

        CreateTasks(files, httpClient, tasks);

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

        if (_count <= 0 || _interval <= 0 || _batchSize <= 0 || _timeFactor <= 0 || _statusInterval <= 0)
        {
            throw new ArgumentException(
                "Invalid arguments: count, interval, batchSize, timeFactor and statusInterval must be positive integers");
        }
    }

    private static string[] GetFiles()
    {
        var files = Directory.GetFiles("/Routes");

        if (files.Length == 0)
        {
            throw new Exception("No route files found");
        }

        return files;
    }

    private static void CreateTasks(IReadOnlyList<string> files, HttpClient httpClient, ICollection<Task> tasks)
    {
        for (var i = 0; i < _count; i++)
        {
            var file = files[Rnd.Next(files.Count)];
            var task = Task.Run(async () => { await RunBatch(_batchSize, httpClient, _interval, file); });

            tasks.Add(task);
        }
    }

    private static List<List<double>> ReadCoordinatesFromFile(string file)
    {
        var json = File.ReadAllText(file);
        var coordinates = JsonSerializer.Deserialize<List<List<double>>>(json);
        return coordinates ?? throw new InvalidDataException($"Coordinate file {file} failed to read.");
    }

    private static async Task RunBatch(int batchSize, HttpClient httpClient, int interval, string file)
    {
        var id = await GetRandomVehicle(httpClient);
        var coordinates = ReadCoordinatesFromFile(file);

        var result = new List<CoordinatesDto>();
        var timestamp = DateTime.UtcNow;

        foreach (var coord in coordinates)
        {
            result.Add(new CoordinatesDto(coord[0], coord[1], timestamp));
            timestamp = timestamp.AddSeconds(interval);
        }

        var batchesPerStatus = _statusInterval / (_batchSize * _interval);
        var ticksSinceStatus = batchesPerStatus;

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

        await SendStatusAsync(httpClient, new StatusDto(id, 1));
    }

    private static async Task<string> GetRandomVehicle(HttpClient httpClient)
    {
        var response = await httpClient.GetStringAsync($"{_carUrl}random");
        return JsonConvert.DeserializeObject<VehicleDTO>(response)!.Id;
    }

    private static async Task SendCoordinatesAsync(HttpClient httpClient, RawInputDto batch)
    {
        var content = new StringContent(JsonSerializer.Serialize(batch), Encoding.UTF8, "application/json");
        var response = await httpClient.PostAsync($"{_targetUrl}raw", content);
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