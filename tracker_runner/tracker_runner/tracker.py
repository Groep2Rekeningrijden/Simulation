import argparse
import json
import pickle
import random
import time

import pika


def run(target: str, batch_time: int, id: str, route_file: str):
    with open(f"routes/{route_file}", "rb") as file:
        route = pickle.load(file)

    coord_queue = "coordinates"
    in_progress_queue = "in_progress"

    with pika.BlockingConnection(pika.ConnectionParameters(target)) as connection:
        channel = connection.channel(random.randint(0,100000))
        channel.queue_declare(coord_queue)
        channel.queue_declare(in_progress_queue)

        # assume 1 second between coordinates
        batches = [route[x : x + batch_time] for x in range(0, len(route), batch_time)]

        # Assume we send in_progress every 2 min = 120 sec
        time_between_in_progress = 120
        time_since_in_progress = 0

        while len(batches) > 0:
            batch_out = json.dumps({"id": id, "batch": batches.pop(0)})
            channel.basic_publish(
                exchange="",
                routing_key=coord_queue,
                body=bytes(batch_out, encoding="utf8"),
            )

            time.sleep(batch_time)

            time_since_in_progress += batch_time
            if time_since_in_progress >= time_between_in_progress:
                channel.basic_publish(
                    exchange="",
                    routing_key=in_progress_queue,
                    body=bytes(
                        json.dumps({"id": id, "in_progress": True}), encoding="utf8"
                    ),
                )
        # Send end-of-ride
        channel.basic_publish(
            exchange="",
            routing_key=in_progress_queue,
            body=bytes(json.dumps({"id": id, "in_progress": False}), encoding="utf8"),
        )
        channel.close()


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
