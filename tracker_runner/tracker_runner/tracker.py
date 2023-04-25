import argparse
import json
import pickle
import requests
import time

from google.cloud import storage

# We load the route file from the routes directory
# We assume that the route file is a pickle file
# We take random routes from the route file
# For each route fetch an identifier from the /get_vehicle endpoint
# We send the identifier and a batch of coordinates to the /coordinates endpoint
# We also send a keep_alive signal to the /keep_alive endpoint

# Generate a function to fetch a route file from a remote storage
def load_routes(route_file: str):
    """
    Load the routes from a file.
    :param route_file: The name of the route file.
    :return: The routes.
    """
    with open(f"routes/{route_file}", "rb") as file:
        routes = pickle.load(file)
    return routes

def get_identifier(target: str):
    """
    Get an identifier from the target server.
    :param target: The url of the target server.
    :return: The identifier.
    """
    r = requests.get(f"{target}/get_vehicle")
    return r.json()["identifier"]


def generate_batches(route: list, coordinate_count: int):
    """
    Generate batches of coordinates from a route.
    :param route: The route.
    :param coordinate_count: The number of coordinates per batch.
    :return: The batches.
    """
    batches = [route[x: x + coordinate_count] for x in range(0, len(route), coordinate_count)]
    return batches

# TODO: Pull files from gcloud, fetch vehicles from endpoint (just fake that for now), then combine batches with id's and send


# def run(target: str, batch_time: int, id: str, route_file: str):
#     with open(f"routes/{route_file}", "rb") as file:
#         route = pickle.load(file)
#
#         # assume 1 second between coordinates
#         batches = [route[x: x + batch_time] for x in range(0, len(route), batch_time)]
#
#         # Assume we send in_progress every 2 min = 120 sec
#         time_between_in_progress = 120
#         time_since_in_progress = 0
#
#         while len(batches) > 0:
#             batch_out = json.dumps({"id": id, "batch": batches.pop(0)})
#             channel.basic_publish(
#                 exchange="",
#                 routing_key=coord_queue,
#                 body=bytes(batch_out, encoding="utf8"),
#             )
#
#             time.sleep(batch_time)
#
#             time_since_in_progress += batch_time
#             if time_since_in_progress >= time_between_in_progress:
#                 channel.basic_publish(
#                     exchange="",
#                     routing_key=in_progress_queue,
#                     body=bytes(
#                         json.dumps({"id": id, "in_progress": True}), encoding="utf8"
#                     ),
#                 )
#         # Send end-of-ride
#         channel.basic_publish(
#             exchange="",
#             routing_key=in_progress_queue,
#             body=bytes(json.dumps({"id": id, "in_progress": False}), encoding="utf8"),
#         )
#         channel.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="RWK Tracker Sim",
        description="Run a fake tracker with the given parameters.",
    )
    parser.add_argument(
        "target",
        type=str,
        help="The url of the target Rabbitmq server.",
    )
    parser.add_argument(
        "batch_time",
        type=int,
        help="Timespan of a single batch of coordinates.",
    )
    parser.add_argument(
        "id",
        type=str,
        help="The identifier to use.",
    )
    parser.add_argument(
        "route_file",
        type=str,
        help="The route file to use.",
    )

    args = parser.parse_args()

    run(args.target, args.batch_time, args.id, args.route_file)
