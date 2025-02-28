import zerorpc
import logging
from pathlib import Path
import os
from animated_drawings.render import start  # type: ignore


class RPCService:
    def ping(self, n):
        logging.info(f"ping called with argument: {n}")
        return f"animated_drawings connection successful! Received: {n}"

    def render_start(self, mvc_cfg_file_path: str):
        return start(mvc_cfg_file_path)


def get_internal_port():
    internal_port = os.environ.get("INTERNAL_PORT")
    if internal_port is None:
        raise ValueError("INTERNAL_PORT is not set.")
    return internal_port


if __name__ == "__main__":
    internal_port = get_internal_port()
    my_url = f"tcp://0.0.0.0:{internal_port}"

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s"
    )
    logging.info(f"ZeroRPC server started, listening on {my_url}")

    service = RPCService()
    zeroServer = zerorpc.Server(service)
    zeroServer.bind(my_url)
    zeroServer.run()
