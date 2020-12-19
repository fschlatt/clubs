import os

import flask
import flask_socketio

dir_path = os.path.dirname(os.path.realpath(__file__))
templates_path = os.path.join(dir_path, "resources", "templates")
static_path = os.path.join(dir_path, "resources", "static")
app = flask.Flask("clubs", template_folder=templates_path, static_folder=static_path)
socketio = flask_socketio.SocketIO(app)

connections = 0


def updater():
    timestamp = 0
    while True:
        if config["timestamp"] > timestamp:
            socketio.emit("config", config)
            timestamp = time.time()
        if event.is_set():
            break
        time.sleep(0.001)


@app.route("/")
def index():
    svg = str(self.svg_table.generate())
    return flask.render_template("index.html", svg=flask.Markup(svg))


if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=self.port, debug=True)
