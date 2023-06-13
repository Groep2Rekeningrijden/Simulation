FROM mcr.microsoft.com/dotnet/runtime:7.0 AS base
WORKDIR /app

FROM mcr.microsoft.com/dotnet/sdk:7.0 AS build
WORKDIR /src
COPY ["TrackerRunner.csproj", "./"]
RUN dotnet restore "TrackerRunner.csproj"
COPY . .
WORKDIR "/src/"
RUN dotnet build "TrackerRunner.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "TrackerRunner.csproj" -c Release -o /app/publish /p:UseAppHost=false

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
COPY Routes/ /Routes
COPY pregen/ /pregen
ENTRYPOINT ["dotnet", "TrackerRunner.dll"]
