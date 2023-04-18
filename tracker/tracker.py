"""
Contains the mock tracker for the RWK project.
"""
import argparse
import json
import multiprocessing
import time
import uuid

import networkx as nx
import numpy
import osmnx as ox
import pika
from osmnx import projection, utils_geo
from shapely import LineString
from shapely.geometry import mapping


def run(args):
    """
    Run the tracker.

    :param args: Console arguments from argparse
    :return:
    """
    graph, optimizer = setup_osmnx()

    processes = []
    while True:
        if len(processes) < args.count:
            processes.append(
                multiprocessing.Process(
                    target=run_tracker, args=(args, graph, optimizer)
                )
            )
            processes[-1].start()


def run_tracker(args, graph, optimizer):
    """
    Run an instance of the tracker.

    :param args: Console arguments from argparse
    :param graph: The graph to use as map
    :param optimizer: Optimizer type to use
    :return:
    """
    # TODO: If running with multiprocessing the UUIDs are different but they somehow share the route/coordinates list
    # For now just run the script multiple times with '-c 1'
    while True:
        identifier = str(uuid.uuid4())
        coords = generate_coordinates(args, graph, optimizer)

        # Establish connection and start sending
        connection = pika.BlockingConnection(pika.ConnectionParameters(args.target))
        channel = connection.channel()
        # channel.queue_declare(args.queue)
        for coordinate in coords:
            out = json.dumps({"id": identifier, "x": coordinate[0], "y": coordinate[1]})
            channel.basic_publish(
                exchange="", routing_key=args.queue, body=bytes(out, encoding="utf8")
            )
            time.sleep(args.frequency)
        connection.close()


def generate_coordinates(args, graph, optimizer):
    """
    Generate the coordinates for a route.

    :param args: Console arguments from argparse
    :param graph: The graph to use as map
    :param optimizer: Optimizer type to use
    :return:
    """
    shortest_route = generate_base_route(graph, optimizer)
    linestring_series = generate_points_for_route(args, graph, shortest_route)
    # Edge attributes for the route contain street name, type and distance, excellent for applying prices
    # route_edge_attributes = utils_graph.get_route_edge_attributes(graph,shortest_route)
    coords = [mapping(linestring) for linestring in linestring_series]
    coords = [
        (numpy.round(point[0], 7), numpy.round(point[1], 7))
        for coord in coords
        for point in coord["coordinates"]
    ]
    # save_route_map(graph, shortest_route)
    return coords


def generate_points_for_route(args, graph, shortest_route):
    """
    Generate a series of points for a route.

    :param args: Console arguments from argparse
    :param graph: The graph to use as map
    :param shortest_route: The shortest route graph
    :return:
    """
    # Generate a graph that only contains the route
    subgraph = graph.subgraph(shortest_route)
    # Convert it to dataframe
    gdf_nodes, gdf_edges = ox.graph_to_gdfs(subgraph)
    # Convert lat/lng to UTM CRS
    gdf_edges = projection.project_gdf(gdf_edges)
    for index, edge in gdf_edges.iterrows():
        seg_count = edge["travel_time"] / args.frequency
        if seg_count > 0:
            points = utils_geo.interpolate_points(
                edge["geometry"], edge["speed_kph"] / 3.6 * args.frequency
            )
            edge["geometry"] = LineString(list(points))
    gdf_edges = projection.project_gdf(gdf_edges, to_latlong=True)
    return gdf_edges["geometry"]


def save_route_map(graph, shortest_route):
    """
    Save the route and map to output files.

    :param graph: The graph to use as map
    :param shortest_route: The shortest route graph
    :return:
    """
    ox.plot_graph(graph, save=True, filepath="../out/out.png")
    shortest_route_map = ox.plot_route_folium(
        graph, shortest_route, tiles="openstreetmap"
    )
    shortest_route_map.save(outfile=f"out/route_{shortest_route[0]}.html")


def generate_base_route(graph, optimizer):
    """
    Generate the base route.

    :param graph: The graph to use as map
    :param optimizer: The optimizer to use
    :return:
    """
    # generate two points on the given graph
    start, end = list(utils_geo.sample_points(graph, 2))

    # TODO: Nearest point on edge https://stackoverflow.com/questions/64104884/osmnx-project-point-to-street-segments

    # find the nearest node to the start location
    orig_node = ox.nearest_nodes(graph, start.x, start.y)
    # find the nearest node to the end location
    dest_node = ox.nearest_nodes(graph, end.x, end.y)
    #  find the shortest path
    return nx.shortest_path(graph, orig_node, dest_node, weight=optimizer)


def setup_osmnx():
    """
    Initialize OSMNX with configuration.

    :return:
    """
    # Configure osmnx, area and routing settings
    ox.config(log_console=True, use_cache=True)
    # location where you want to find your route
    place = "Eindhoven, Noord-Brabant, Netherlands"
    # find the shortest route based on the mode of travel
    mode = "drive"  # 'drive', 'bike', 'walk'
    # find the shortest path based on distance or time
    optimizer = "travel_time"  # 'length','travel_time', 'time'
    # create graph from OSM within the boundaries of some
    # geocodable place(s)
    graph = ox.graph_from_place(place, network_type=mode)
    graph = ox.add_edge_speeds(graph)
    graph = ox.add_edge_travel_times(graph)
    return graph, optimizer


if __name__ == "__main__":
    """
    Main entrypoint for the script.
    """
    parser = argparse.ArgumentParser(
        prog="Car Tracker Mock",
        description="Generates a set of mock car trackers that drive around Eindhoven, sending data to the given "
        "Rabbitmq address.",
    )
    parser.add_argument(
        "-f",
        "--frequency",
        type=int,
        help="The time between the tracker recording coordinates.",
        default=1,
    )
    parser.add_argument(
        "-c",
        "--count",
        type=int,
        help="Number of simultaneous mock trackers to run.",
        default=2,
    )
    parser.add_argument(
        "-t",
        "--target",
        type=str,
        help="The address of the Rabbitmq server.",
        default="localhost",
    )
    parser.add_argument(
        "-q",
        "--queue",
        type=str,
        help="The queue to use on the Rabbitmq server.",
        default="demoQueueJson",
    )

    run(parser.parse_args())
