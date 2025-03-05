import logging
import os
from zero import ZeroServer
from animated_drawings.render import start  # type: ignore


def get_internal_port():
    internal_port = os.environ.get("INTERNAL_PORT")
    if internal_port is None:
        raise ValueError("INTERNAL_PORT is not set.")
    return internal_port


internal_port = get_internal_port()
app = ZeroServer(port=int(internal_port))


@app.register_rpc
def ping(n: int) -> str:
    logging.info(f"ping called with argument: {n}")
    return f"animated_drawings connection successful! Received: {n}"


@app.register_rpc
def render_start(mvc_cfg_file_path: str) -> str:
    return start(mvc_cfg_file_path)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s"
    )
    logging.info(f"ZeroRPC server started, listening on port : {internal_port}")
    app.run()
