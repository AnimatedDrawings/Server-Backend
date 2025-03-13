import logging
import os
from zero import ZeroServer
from animated_drawings import render  # type: ignore


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
def render_start(mvc_cfg_file_path: str) -> dict:
    try:
        render.start(mvc_cfg_file_path)
        return {"status": "success"}
    except Exception as e:
        logging.error(f"render_start failed: {e}")
        return {"status": "fail", "message": str(e)}


"""
rpc_server > render_start called with argument: workspace/files/result_exmaple1/mvc_cfg.yaml
config > Using user-specified mvc config file located at /app/AnimatedDrawings/workspace/files/result_exmaple1/mvc_cfg.yaml


rpc_server > render_start called, argument: workspace/files/result_exmaple1/mvc_cfg.yaml
config > Using user-specified mvc config file located at /app/AnimatedDrawings/animated_drawings/app/workspace/files/result_exmaple1/mvc_cfg.yaml
rpc_server > render_start failed: [Errno 2] No such file or directory: '/app/AnimatedDrawings/animated_drawings/app/workspace/files/result_exmaple1/mvc_cfg.yaml'
"""


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s"
    )
    logging.info(f"ZeroRPC server started, listening on port : {internal_port}")
    app.run()
