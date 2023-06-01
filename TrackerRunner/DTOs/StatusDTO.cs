namespace TrackerRunner.DTOs;

public class StatusDto
{
    public string VehicleID { get; set; }

    public int Status { get; set; }

    public StatusDto(string vehicleId, int status)
    {
        VehicleID = vehicleId;
        Status = status;
    }
}