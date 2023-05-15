"""
Contains the route generator for RWK simulated trackers.
"""
import argparse
import json
import logging
import os
import uuid

import networkx
import numpy
import osmnx
from geopandas import GeoDataFrame
from google.cloud import storage
from networkx import MultiDiGraph
from osmnx import projection, settings, utils_geo, utils_graph
from shapely import LineString
from shapely.geometry import mapping


def run(region: str, count: int, interval: int, debug: bool):
    """
    Generate <count> routes for the given <region> and store to pickle files.
    """
    # Set up OSMNX with region map
    osmnx_map = init_osmnx(region)
    if not os.path.exists("out"):
        os.makedirs("out")

    generated_routes = 0
    while generated_routes < count:
        try:
            shortest_route = generate_new_route(osmnx_map)
            identifier = str(uuid.uuid4())

            if debug:
                save_route_to_folium(osmnx_map, shortest_route, f"{identifier}-before-splitting")

            gdf_nodes, gdf_edges = split_route_edges(osmnx_map, shortest_route, interval)

            if debug:
                out = utils_graph.graph_from_gdfs(gdf_nodes, gdf_edges, None)
                save_graph_to_folium(out, f"{identifier}-after-splitting")

            route = convert_to_coordinates(gdf_edges)
        except networkx.NetworkXNoPath:
            continue
        try:
            write_to_file(route, identifier)
        except IOError as e:
            logging.error(e)

        generated_routes += 1

    # TODO: Push pickles to storage so they can be loaded by generator
    # Loop:
    #   Generate two points
    #   Generate route between points
    #   Split route into coordinate list
    #   Store list


def save_route_to_folium(osmnx_map, shortest_route, identifier):
    shortest_route_map = osmnx.plot_route_folium(
        osmnx.projection.project_graph(osmnx_map, to_crs="EPSG:4326"), shortest_route, tiles="openstreetmap"
    )
    shortest_route_map.save(outfile=f"{os.getcwd()}/out/{identifier}.html")


def save_graph_to_folium(graph, identifier):
    folium_map = osmnx.plot_graph_folium(graph, tiles="openstreetmap")
    folium_map.save(outfile=f"{os.getcwd()}/out/{identifier}.html")


def store_files_on_cloud():
    # Iterate over files in the out directory
    # TODO: Authentication
    storage_client = storage.Client()
    bucket_name = os.getenv('GC_BUCKET_NAME')
    for filename in os.listdir("out"):
        path = os.path.join("out", filename)
        # checking if it is a file
        if os.path.isfile(path):
            upload_blob(storage_client, bucket_name, filename, path)


def upload_blob(storage_client, bucket_name, source_file_name, path):
    """Uploads a file to the bucket."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_file_name)

    if blob.upload_from_filename(path):
        logging.info(f"File {source_file_name} uploaded to {blob}")


def write_to_file(route, identifier):
    """
    Write the generated routes to a JSON file.

    :param route: List of coordinates.
    :param identifier: Identifier for the route.
    """

    # Convert route to json and write to "<identifier>.json" in the out directory
    with open(f"{os.getcwd()}/out/{identifier}.json", mode="w") as file:
        file.write(json.dumps(route))


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
        osmnx_map: MultiDiGraph, route: list, interval: int
) -> tuple[GeoDataFrame, GeoDataFrame]:
    """
    Generate a GeoDataFrame containing the edges of the given route with points on each edge based on the frequency.

    :param osmnx_map: OSMNX map containing the full route.
    :param route: The route to process.
    :param interval: The time between samples. Used with road speed to generate coordinates.
    :return gdf_edges: GeoDataFrame containing the edges we want to convert.
    """
    # Generate a dataframe containing the route geodata
    gdf_nodes, gdf_edges = osmnx.graph_to_gdfs(osmnx_map.subgraph(route))
    gdf_edges = gdf_edges.reset_index()

    # We use the nodes in routes to find the next node in the route, and sort the edges based on this.
    # Then we can remove the rows that aren't part of the route.
    previous_node = None
    for index, node in enumerate(route):
        # Find next node and filter out backwards routes
        gdf_edges.loc[(gdf_edges["u"] == node) & ~(gdf_edges["v"] == previous_node), "order"] = index
        previous_node = node
    gdf_edges = gdf_edges.loc[~gdf_edges["order"].isnull()].sort_values(by=["order"])
    gdf_edges = gdf_edges.drop(columns=["order"]).set_index(["u", "v", "key"])

    # Split the road_segments based on maximum speed on that edge
    for index, road_segment in gdf_edges.iterrows():
        seg_count = road_segment["travel_time"] / interval
        if seg_count <= 1:
            continue
        points = utils_geo.interpolate_points(
            road_segment["geometry"], road_segment["speed_kph"] / 3.6 * interval
        )
        if road_segment["reversed"]:
            road_segment["geometry"] = LineString(list(points)[::-1])
        else:
            road_segment["geometry"] = LineString(list(points))

    # Convert UTM/CRS back to lat/lng
    gdf_nodes = projection.project_gdf(gdf_nodes, to_latlong=True)
    gdf_edges = projection.project_gdf(gdf_edges, to_latlong=True)

    return gdf_nodes, gdf_edges


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
             "Example: 'Eindhoven, Noord-Brabant, Netherlands' "
             "Browse https://www.openstreetmap.org/relation/2323309 for options within the Netherlands.",
    )
    parser.add_argument(
        "count",
        type=int,
        help="Number of routes to generate.",
    )
    parser.add_argument(
        "interval",
        type=int,
        help="The time between tracker samples. Used to determine points on longer roads.",
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Generate debug html graphs'
    )

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    run(args.region, args.count, args.interval, args.debug)
