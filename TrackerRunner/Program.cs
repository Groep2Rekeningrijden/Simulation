using System.Text;
using System.Text.Json;
using TrackerRunner.DTOs;

namespace TrackerRunner
{
    class Program
    {
        private static string _targetUrl = "";
        private static int _interval;
        private static int _batchSize;
        private static int _count;
        private static int _timeFactor;
        private static readonly Random Rnd = new Random();
        

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
            if (args.Count < 5)
            {
                throw new ArgumentException(
                    "Please provide count, interval, batchSize and timeFactor as integers, and the target url as a string");
            }

            _count = int.Parse(args[0]);
            _interval = int.Parse(args[1]);
            _batchSize = int.Parse(args[2]);
            _timeFactor = int.Parse(args[3]);
            _targetUrl = args[4];

            if (_count <= 0 || _interval <= 0 || _batchSize <= 0 || _timeFactor <= 0)
            {
                throw new ArgumentException(
                    "Invalid arguments: count, interval, batchSize and timeFactor must be positive integers");
            }
        }

        private static string[] GetFiles()
        {
            var files = Directory.GetFiles(@"/home/luna/Documents/rekeningrijden/Simulation/TrackerRunner/Routes",
                "*.json");

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
                var task = Task.Run(async () =>
                {
                    await RunBatch(_batchSize, httpClient, _interval, file);
                });

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
            var id = Guid.NewGuid().ToString();
            var coordinates = ReadCoordinatesFromFile(file);

            var result = new List<CoordinatesDto>();
            var timestamp = DateTime.UtcNow;

            foreach (var coord in coordinates)
            {
                result.Add(new CoordinatesDto(coord[0], coord[1], timestamp));
                timestamp = timestamp.AddSeconds(interval);
            }


            for (var j = 0; j < coordinates.Count; j += batchSize)
            {
                var batch = new RawInputDto(id, result.Skip(j).Take(batchSize).ToList());
                await SendCoordinatesAsync(httpClient, batch);
                await Task.Delay(_interval * _batchSize * 1000 / _timeFactor);
            }
        }

        private static async Task SendCoordinatesAsync(HttpClient httpClient, RawInputDto batch)
        {
            var content = new StringContent(JsonSerializer.Serialize(batch), Encoding.UTF8, "application/json");
            var response = await httpClient.PostAsync(_targetUrl, content);
            response.EnsureSuccessStatusCode();
        }
    }
}