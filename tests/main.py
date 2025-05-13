from gevent import monkey
from gevent.pywsgi import WSGIServer

monkey.patch_all()

from app import create_app
import settings

app = create_app()


if __name__ == "__main__":
    host = settings.hostname
    port = settings.hostport

    print("* Running on http://%s:%s/ (Press CTRL+C to quit)" % (str(host), str(port)))
    server = WSGIServer((host, port), app)
    server.serve_forever()
