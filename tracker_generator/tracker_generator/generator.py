"""
Contains the route generator for RWK simulated trackers.
"""
import argparse
import os
import pickle
import uuid

import networkx
import numpy
import osmnx
from geopandas import GeoDataFrame
from networkx import MultiDiGraph
from osmnx import projection, settings, utils_geo
from shapely import LineString
from shapely.geometry import mapping


def run(region: str, count: int, sample_frequency: int):
    """
    Generate <count> routes for the given <region> and store to pickle files.
    """
    # Set up OSMNX with region map
    osmnx_map = init_osmnx(region)

    generated_routes = []
    while len(generated_routes) < count:
        try:
            shortest_route = generate_new_route(osmnx_map)

            gdf_edges = split_route_edges(osmnx_map, shortest_route, sample_frequency)

            # For the RWK route pricing:
            # Edge attributes for the route contain street name, type and distance, excellent for applying prices
            # route_edge_attributes = utils_graph.get_route_edge_attributes(graph,shortest_route)

            coordinates = convert_to_coordinates(gdf_edges)
        except networkx.NetworkXNoPath:
            continue

        generated_routes.append(coordinates)

    if not os.path.exists("out"):
        os.makedirs("out")
    identifier = str(uuid.uuid4())
    with open(f"out/routes-{identifier}.pickle", mode="wb") as file:
        pickle.dump(generated_routes, file)

    # TODO: Push pickles to storage so they can be loaded by generator
    # Loop:
    #   Generate two points
    #   Generate route between points
    #   Split route into coordinate list
    #   Store list


def convert_to_coordinates(gdf_edges):
    """
    Convert a GeoDataFrame of edges to a list of coordinate tuples.

    :param gdf_edges: GeoDataFrame containing the edges we want to convert.
    :return coordinates: List of coordinate tuples.
    """
    # Convert the dataframe of linestrings to a list of coordinate tuples
    coordinates = [mapping(linestring) for linestring in gdf_edges["geometry"]]
    coordinates = [
        (numpy.round(point[0], 7), numpy.round(point[1], 7))
        for coord in coordinates
        for point in coord["coordinates"]
    ]
    return coordinates


def split_route_edges(
        osmnx_map: MultiDiGraph, route: list, sample_frequency: int
) -> GeoDataFrame:
    """
    Generate a GeoDataFrame containing the edges of the given route with points on each edge based on the frequency.

    :param osmnx_map: OSMNX map containing the full route.
    :param route: The route to process.
    :param sample_frequency: The time between samples. Used with road speed to generate coordinates.
    :return gdf_edges: GeoDataFrame containing the edges we want to convert.
    """
    # Generate a dataframe containing the route geodata
    gdf_nodes, gdf_edges = osmnx.graph_to_gdfs(osmnx_map.subgraph(route))
    # Split the road_segments based on maximum speed on that edge
    for index, road_segment in gdf_edges.iterrows():
        seg_count = road_segment["travel_time"] / sample_frequency
        if seg_count <= 0:
            continue
        points = utils_geo.interpolate_points(
            road_segment["geometry"], road_segment["speed_kph"] / 3.6 * sample_frequency
        )
        road_segment["geometry"] = LineString(list(points))
    # Convert UTM/CRS back to lat/lng
    gdf_edges = projection.project_gdf(gdf_edges, to_latlong=True)
    return gdf_edges


def generate_new_route(osmnx_map: MultiDiGraph) -> list:
    """
    Generate a new route based on the shortest route between two random nodes on the map.

    :param osmnx_map: The OSMNX map to generate a route on.
    :return shortest_route: The route.
    """
    # Generate start and end points
    # Ignore the warning about undirected graphs, oversampling is not an issue for us
    start, end = list(utils_geo.sample_points(osmnx_map, 2))
    # Find the nodes nearest to those points
    start_node = osmnx.nearest_nodes(osmnx_map, start.x, start.y)
    end_node = osmnx.nearest_nodes(osmnx_map, end.x, end.y)
    # Weight options: 'length', 'travel_time', 'time'
    shortest_route = networkx.shortest_path(
        osmnx_map, start_node, end_node, weight="travel_time"
    )
    return shortest_route


def init_osmnx(region: str) -> MultiDiGraph:
    """
    Initialize OSMNX with configuration.

    :param region: The region for which to generate a map
    :return osmnx_map: The OSMNX map of the given region as a networkx multidimensional graph
    """
    # Configure osmnx, area and routing settings
    # For settings see https://osmnx.readthedocs.io/en/stable/osmnx.html?highlight=settings#module-osmnx.settings
    osmnx.config(log_console=True, use_cache=True)
    settings.log_console = True
    settings.use_cache = True

    # find the shortest route based on the mode of travel
    mode = "drive"  # 'drive', 'bike', 'walk'
    # create graph from OSM within the boundaries of some
    # geocodable place(s)
    osmnx_map = osmnx.graph_from_place(region, network_type=mode)
    osmnx_map = osmnx.projection.project_graph(osmnx_map)
    osmnx_map = osmnx.add_edge_speeds(osmnx_map)
    osmnx_map = osmnx.add_edge_travel_times(osmnx_map)
    return osmnx_map


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="RWK Route Generator",
        description="Generates a set of Routes for the given region and stores them in a pickle file as a list of "
                    "lists.",  # TODO: Where?
    )
    parser.add_argument(
        "region",
        type=str,
        help="The region in which the routes should be generated, in the OSM name format."
             "Example: 'Eindhoven, Noord-Brabant, Netherlands'"
             "Browse https://www.openstreetmap.org/relation/2323309 for options within the Netherlands.",
    )
    parser.add_argument(
        "count",
        type=int,
        help="Number of routes to generate.",
    )
    parser.add_argument(
        "--sample_frequency",
        type=int,
        help="The time between tracker samples. Used to determine points on longer roads.",
        default=1,
    )
    args = parser.parse_args()

    run(args.region, args.count, args.sample_frequency)
