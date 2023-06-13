using System.Text.Json.Serialization;
using TrackerRunner.DTOs;

namespace TrackerRunner.International
{
    public class Point
    {
        public Point(double lat, double lon, DateTime time)
        {
            Lat = lat;
            Lon = lon;
            Time = time;
        }

        public Point(CoordinatesDto coordinatesDto)
        {
            Lat = coordinatesDto.Lat;
            Lon = coordinatesDto.Lon;
            Time = coordinatesDto.Time;
        }

        [JsonPropertyName("lat")] public double Lat { get; set; }
        [JsonPropertyName("lon")] public double Lon { get; set; }

        [JsonPropertyName("time")] public DateTime Time { get; set; }
    }
}