namespace TrackerRunner.DTOs
{
    public class RawInputDto
    {

        public string VehicleId { get; set; }

        public List<CoordinatesDto> Coordinates { get; set; } 

        public RawInputDto(string vehicleId, List<CoordinatesDto> coordinates)
        {
            VehicleId = vehicleId;
            Coordinates = coordinates;
        }
    }
}
