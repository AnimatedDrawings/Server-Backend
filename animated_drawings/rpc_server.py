import zerorpc
from animated_drawings.render import start


def ping(n):
    return f"animated_drawings connection successful! Received: {n}"


functions = {
    "render_start": start,
    "ping": ping,
}


if __name__ == "__main__":
    zeroServer = zerorpc.Server(functions)
    zeroServer.bind("tcp://0.0.0.0:8001")
    zeroServer.run()
