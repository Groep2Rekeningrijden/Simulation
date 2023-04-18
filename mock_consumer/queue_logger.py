"""
Contains the mock consumer for testing the mock tracker of the RWK project.
"""
import argparse
import logging
import os
import sys

import pika


def run(args):
    """
    Run the logger.

    :param args: Console arguments from argparse
    :return:
    """
    connection = pika.BlockingConnection(pika.ConnectionParameters(args.target))
    channel = connection.channel()
    channel.queue_declare(queue=args.queue)
    channel.basic_consume(queue=args.queue, auto_ack=True, on_message_callback=callback)
    logging.info(" [*] Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()


def callback(ch, method, properties, body):
    """
    Log the body of the consumed message.

    :param ch: channel
    :param method: method
    :param properties: properties
    :param body: body
    :return:
    """
    logging.info(" [x] Received %r" % body)


if __name__ == "__main__":
    """
    Main entrypoint for the script.
    """
    parser = argparse.ArgumentParser(
        prog="Car Tracker Queue Logger",
        description="Serves as a Rabbitmq consumer that logs received messages.",
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
    try:
        run(parser.parse_args())
    except KeyboardInterrupt:
        logging.error("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
