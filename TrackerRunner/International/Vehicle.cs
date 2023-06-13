using System.Text.Json.Serialization;

namespace TrackerRunner.International;

public class Vehicle
{
    public Vehicle(string id, string vehicleClassification, string fuelType)
    {
        Id = id;
        VehicleClassification = vehicleClassification;
        FuelType = fuelType;
    }

    [JsonPropertyName("id")]
    public string Id { get; set; }
    [JsonPropertyName("vehicleClassification")]
    public string VehicleClassification { get; set; }
    [JsonPropertyName("fuelType")]
    public string FuelType { get; set; }
}