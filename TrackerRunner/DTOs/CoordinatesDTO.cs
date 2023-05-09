namespace TrackerRunner.DTOs
{
    public class CoordinatesDto
    {
        public CoordinatesDto(double lat, double lon, DateTime time)
        {
            Lat = lat;
            Lon = lon;
            Time = time;
        }

        public double Lat { get; set; }

        public double Lon { get; set; } 

        public DateTime Time { get; set; }

    }
}
