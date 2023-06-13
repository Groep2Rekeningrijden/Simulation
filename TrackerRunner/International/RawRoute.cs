using System.Text.Json.Serialization;

namespace TrackerRunner.International
{
    public class RawRoute
    {

        [JsonPropertyName("vehicle")]
        public Vehicle Vehicle { get; set; }

        [JsonPropertyName("points")]
        public List<Point> Points { get; set; } 

        public RawRoute(Vehicle vehicle, List<Point> points)
        {
            Vehicle = vehicle;
            Points = points;
        }
    }
}
