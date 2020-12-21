import copy
import math
import multiprocessing
import os
import time
from multiprocessing import connection
from typing import Any, Dict, List, Optional, Tuple, Union, overload
from xml.etree import ElementTree

import numpy as np

from .. import error
from .. import poker
from . import viewer


class GraphicViewer(viewer.PokerViewer):
    def __init__(
        self,
        num_players: int,
        num_hole_cards: int,
        num_community_cards: int,
        port: int = 23948,
        **kwargs,
    ):
        super(GraphicViewer, self).__init__(
            num_players, num_hole_cards, num_community_cards
        )

        self.port = port

        self.svg_table = SVGTable(
            self.num_players, self.num_hole_cards, self.num_community_cards
        )

        self.socket: Optional[connection.Connection] = None
        self.process = multiprocessing.Process(target=self._run_flask, daemon=True)
        self.process.start()

    def _run_flask(self):
        from gevent import monkey

        monkey.patch_all()
        import flask_socketio

        import flask

        config = {}
        dir_path = os.path.dirname(os.path.realpath(__file__))
        templates_path = os.path.join(dir_path, "resources", "templates")
        static_path = os.path.join(dir_path, "resources", "static")
        app = flask.Flask(
            "clubs", template_folder=templates_path, static_folder=static_path
        )
        socketio = flask_socketio.SocketIO(app)

        @socketio.on("connect")
        def connect():
            socketio.emit("config", config)

        @app.route("/")
        def index():
            svg = str(self.svg_table.generate())
            return flask.render_template("index.html", svg=flask.Markup(svg))

        def listener():
            nonlocal config
            socket = connection.Listener(("localhost", self.port + 1))
            conn = socket.accept()
            while True:
                if conn.poll():
                    message: Dict[str, Any] = conn.recv()
                    if message["content"] == "close":
                        conn.close()
                        break
                    else:
                        config = message["content"]
                        socketio.emit("config", config, broadcast=True)
                socketio.sleep(0.01)
            socket.close()

        socketio.start_background_task(listener)

        socketio.run(app, port=self.port)

    def render(self, config: dict, sleep: float = 0, **kwargs) -> None:
        """Render the table based on the table configuration

        Parameters
        ----------
        config : dict
            game configuration dictionary,
                config = {
                    'action': int - position of active player,
                    'active': List[bool] - list of active players,
                    'all_in': List[bool] - list of all in players,
                    'community_cards': List[Card] - list of community
                                       cards,
                    'dealer': int - position of dealer,
                    'done': bool - list of done players,
                    'hole_cards': List[List[Card]] - list of hole cards,
                    'pot': int - chips in pot,
                    'payouts': List[int] - list of chips won for each
                               player,
                    'prev_action': Tuple[int, int, int] - last
                                   position bet and fold,
                    'street_commits': List[int] - list of number of
                                      chips added to pot from each
                                      player on current street,
                    'stacks': List[int] - list of stack sizes,
                }
        """
        tries = 0
        while True:
            if self.socket is not None:
                break
            try:
                self.socket = connection.Client(("localhost", self.port + 1))
            except ConnectionRefusedError:
                tries += 1
                if tries == 5:
                    raise error.RenderInitializationError(
                        "unable to reach flask process"
                    )
                time.sleep(1)
        self.socket.send({"content": jsonify(config)})
        if sleep:
            time.sleep(sleep)


def convert_hands(hands: List[List[poker.Card]]) -> List[List[str]]:
    _hands = []
    for hand in hands:
        _cards = []
        for card in hand:
            _cards.append(str(card))
        _hands.append(_cards)
    return _hands


def jsonify(config: Union[Dict[str, Any]]) -> Dict[str, Any]:
    _config: Dict[str, Any] = {}
    for key, value in config.items():
        if isinstance(value, dict):
            _config[key] = jsonify(value)
        elif isinstance(value, np.ndarray):
            _config[key] = value.tolist()
        elif isinstance(value, list):
            community = key == "community_cards"
            if community:
                value = [value]
            cards = convert_hands(value)
            if community:
                _config[key] = cards[0]
            else:
                _config[key] = cards
        elif isinstance(value, float):
            _config[key] = float(value)
        elif isinstance(value, int):
            _config[key] = int(value)
    return _config


class _RoundedRectangle:
    def __init__(self, x: float, y: float, width: float, height: float) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.center_x = width * 0.5
        self.center_y = height * 0.5

    def edge(self, frac: float) -> Tuple[float, float]:
        frac = frac % 1
        x, y = 0.0, 0.0
        perimeter_frac = frac * self.perimeter
        if perimeter_frac < self.straight_width * 0.5:
            x = -perimeter_frac
            y = self.radius_height
        elif perimeter_frac < self.straight_width * 0.5 + self.circle_perimeter * 0.5:
            circle_frac = (perimeter_frac - self.straight_width * 0.5) / (
                self.circle_perimeter * 0.5
            )
            angle = math.pi * 0.5 + math.pi * circle_frac
            x = self.radius_height * math.cos(angle) - self.straight_width * 0.5
            y = self.radius_height * math.sin(angle)
        elif perimeter_frac < self.straight_width * 1.5 + self.circle_perimeter * 0.5:
            straight_frac = (
                perimeter_frac - self.straight_width * 0.5 - self.circle_perimeter * 0.5
            ) / self.straight_width
            x = (straight_frac - 0.5) * self.straight_width
            y = -self.radius_height
        elif perimeter_frac < self.straight_width * 1.5 + self.circle_perimeter:
            circle_frac = (
                perimeter_frac - self.straight_width * 1.5 + self.circle_perimeter * 0.5
            ) / (self.circle_perimeter * 0.5)
            angle = math.pi * 1.5 + math.pi * circle_frac
            x = self.radius_height * math.cos(angle) + self.straight_width * 0.5
            y = self.radius_height * math.sin(angle)
        elif frac <= 1:
            straight_frac = (
                perimeter_frac - self.straight_width * 1.5 - self.circle_perimeter
            ) / self.straight_width
            x = (-straight_frac + 0.5) * self.straight_width
            y = self.radius_height
        x += self.center_x + self.x
        y += self.center_y + self.y
        return round(x, 2), round(y, 2)

    @property
    def radius_height(self):
        return float(self.height * 0.5)

    @property
    def circle_perimeter(self):
        return float(math.pi * self.height)

    @property
    def straight_width(self):
        return float(self.width - self.height)

    @property
    def perimeter(self):
        return float(self.straight_width * 2 + 2 * math.pi * self.radius_height)


class SVGElement:

    SVGS_PATH = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "resources", "static", "images"
    )

    def __init__(self, name: str, svg: Optional[ElementTree.Element] = None) -> None:
        if svg is None:
            svg_path = os.path.join(self.SVGS_PATH, f"{name}.svg")
            if not os.path.exists:
                raise FileNotFoundError(f"SVG {name}.svg does not exist")
            with open(svg_path, "r") as file:
                svg_str = file.read()
            self.svg = ElementTree.fromstring(svg_str)
        else:
            self.svg = svg
        self.name = name

    def __str__(self) -> str:
        string = ElementTree.tostring(self.svg, encoding="utf8", method="xml")
        string = string.decode("utf8")
        return string

    def __repr__(self) -> str:
        return f"SVGElement<name={self.name}, id={id(self)}>"

    def get_sub_svg(self, name: str, attr_name: Optional[str] = None) -> "SVGElement":
        if attr_name is not None:
            xpath = f".//*[@{attr_name}='{name}']"
        else:
            xpath = f".//{name}"
        svg = self.svg.find(xpath)
        if svg is None:
            raise KeyError(f"unable to find sub svg with arguments {name}")
        return SVGElement(name, svg)

    def get_sub_svgs(
        self, name: str, attr_name: Optional[str] = None
    ) -> List["SVGElement"]:
        if attr_name is not None:
            xpath = f".//*[@{attr_name}='{name}']"
        else:
            xpath = f".//{name}"
        svgs = self.svg.findall(xpath)
        if not svgs:
            raise KeyError(f"unable to find sub svg with arguments {name}")
        return [SVGElement(name, svg) for svg in svgs]

    def get_svg_attr(self, tag_name: str) -> Optional[str]:
        return self.svg.get(tag_name, None)

    def set_svg_attr(self, tag_name: str, value: str) -> "SVGElement":
        self.svg.set(tag_name, value)
        return self

    @property
    def x(self) -> float:
        value = self.get_svg_attr("x")
        if value is None:
            return 0
        return float(value)

    @x.setter
    def x(self, x: float):
        self.set_svg_attr("x", str(x))

    @property
    def y(self) -> float:
        value = self.get_svg_attr("y")
        if value is None:
            return 0
        return float(value)

    @y.setter
    def y(self, y: float):
        self.set_svg_attr("y", str(y))

    @property
    def width(self) -> float:
        value = self.get_svg_attr("width")
        if value is None:
            return 0
        return float(value)

    @width.setter
    def width(self, width: float):
        self.set_svg_attr("width", str(width))

    @property
    def height(self) -> float:
        value = self.get_svg_attr("height")
        if value is None:
            return 0
        return float(value)

    @height.setter
    def height(self, height: float):
        self.set_svg_attr("height", str(height))

    @property
    def id(self) -> Optional[str]:
        return self.get_svg_attr("id")

    @id.setter
    def id(self, id: str):
        self.set_svg_attr("id", str(id))

    @property
    def view_box(self) -> Optional[str]:
        return self.get_svg_attr("viewBox")

    @view_box.setter
    def view_box(self, view_box: str):
        self.set_svg_attr("viewBox", view_box)

    @property
    def view_box_x(self) -> Optional[float]:
        view_box = self.view_box
        if view_box is None:
            return view_box
        return float(view_box.split(" ")[0])

    @view_box_x.setter
    def view_box_x(self, view_box_x: float):
        if self.view_box is not None:
            split_view_box = self.view_box.split(" ")
            split_view_box[0] = str(view_box_x)
            view_box = " ".join(split_view_box)
            self.set_svg_attr("viewBox", view_box)

    @property
    def view_box_y(self) -> Optional[float]:
        view_box = self.view_box
        if view_box is None:
            return view_box
        return float(view_box.split(" ")[1])

    @view_box_y.setter
    def view_box_y(self, view_box_y: float):
        if self.view_box is not None:
            split_view_box = self.view_box.split(" ")
            split_view_box[1] = str(view_box_y)
            view_box = " ".join(split_view_box)
            self.set_svg_attr("viewBox", view_box)

    @property
    def view_box_width(self) -> Optional[float]:
        view_box = self.view_box
        if view_box is None:
            return view_box
        return float(view_box.split(" ")[2])

    @view_box_width.setter
    def view_box_width(self, view_box_width: float):
        if self.view_box is not None:
            split_view_box = self.view_box.split(" ")
            split_view_box[2] = str(view_box_width)
            view_box = " ".join(split_view_box)
            self.set_svg_attr("viewBox", view_box)

    @property
    def view_box_height(self) -> Optional[float]:
        view_box = self.view_box
        if view_box is None:
            return view_box
        return float(view_box.split(" ")[3])

    @view_box_height.setter
    def view_box_height(self, view_box_height: float):
        if self.view_box is not None:
            split_view_box = self.view_box.split(" ")
            split_view_box[3] = str(view_box_height)
            view_box = " ".join(split_view_box)
            self.set_svg_attr("viewBox", view_box)

    def center_x(
        self, other: Optional["SVGElement"] = None, x: Optional[float] = None
    ) -> "SVGElement":
        if other is not None:
            if other.view_box_width is not None:
                other_width = other.view_box_width
            else:
                other_width = other.width
            self.x = (other_width - self.width) / 2
        if x is not None:
            self.x = x - self.width / 2
        return self

    def center_y(
        self, other: Optional["SVGElement"] = None, y: Optional[float] = None
    ) -> "SVGElement":
        if other is not None:
            if other.view_box_height is not None:
                other_height = other.view_box_height
            else:
                other_height = other.height
            self.y = (other_height - self.height) / 2
        if y is not None:
            self.y = y - self.height / 2
        return self

    def center(
        self,
        other: Optional["SVGElement"] = None,
        x: Optional[float] = None,
        y: Optional[float] = None,
    ) -> "SVGElement":
        self.center_x(other, x)
        self.center_y(other, y)
        return self

    def append(self, other: Union["SVGElement", ElementTree.Element]) -> "SVGElement":
        if isinstance(other, SVGElement):
            other = other.svg
        self.svg.append(other)
        return self

    def remove(self, other: "SVGElement") -> "SVGElement":
        self.svg.remove(other.svg)
        return self


class SVGTable:
    def __init__(
        self, num_players: int, num_hole_cards: int, num_community_cards: int
    ) -> None:
        self.num_players = num_players
        self.num_hole_cards = num_hole_cards
        self.num_community_cards = num_community_cards
        self.base_svg = self._base_svg()

    def _base_svg(self) -> "SVGElement":
        base = SVGElement("base")
        table = SVGElement("table")
        player = SVGElement("player")
        card = SVGElement("card")
        button = SVGElement("button")
        for pattern in SVGElement("patterns").get_sub_svgs("pattern"):
            base.append(pattern)

        table.center(other=base)
        base.append(table)

        player_rectangle = _RoundedRectangle(
            table.x, table.y, table.width, table.height
        )
        player_rectangle.width += 100
        player_rectangle.height += 60
        button_rectangle = _RoundedRectangle(
            table.x, table.y, table.width, table.height
        )
        button_rectangle.width -= 200
        button_rectangle.height -= 160

        player.width = max(
            0 if player.width is None else player.width,
            card.width * self.num_hole_cards + 20,
        )

        player_background = player.get_sub_svg("player-background", attr_name="class")
        player_background.width = player.width - 10
        player_background.height = player_background.height - 10

        cards = player.get_sub_svg("cards", attr_name="class")
        cards.width = self.num_hole_cards * card.width
        cards.center_x(player)

        card_background = card.get_sub_svg("card-background", attr_name="class")
        card_background.set_svg_attr("fill", "url(#card-back)")

        chips = player.get_sub_svg("chips", attr_name="class")
        chips.width = player.width - 20
        chips.center_x(player)

        for player_idx in range(self.num_players):
            x, y = player_rectangle.edge(player_idx / (self.num_players))
            new_player = self._new_player(
                player, f"player-{player_idx}", card, self.num_hole_cards
            )
            new_player.center(x=x, y=y)
            base.append(new_player)
            x, y = button_rectangle.edge(player_idx / (self.num_players))
            new_button = copy.deepcopy(button)
            new_button.id = f"button-{player_idx}"
            new_button.center(x=x, y=y)
            base.append(new_button)

        player.width = card.width * (self.num_community_cards + 1) + 20

        player_background = player.get_sub_svg("player-background", "class")
        player.remove(player_background)

        cards = player.get_sub_svg("cards", "class")
        cards.width = player.width
        cards.center_x(player)

        card_background = card.get_sub_svg("card-background", "class")
        card_background.set_svg_attr("fill", "url(#card-blank)")

        chips = player.get_sub_svg("chips", "class")
        chips.width = player.width - 60
        chips.center_x(player)
        chips.set_svg_attr("id", "pot")
        chips.get_sub_svg("chips-text", "class").set_svg_attr("id", "pot-text")

        community = self._new_player(
            player, "community", card, self.num_community_cards + 1
        )
        community.set_svg_attr("class", "community")
        community.center(other=table)
        card_0 = community.get_sub_svg("card-community-0", "id")
        card_0.get_sub_svg("card-background", "class").set_svg_attr(
            "fill", "url(#card-back)"
        )
        card_0.x -= 10
        community.x += table.x
        community.y += table.y - 40
        base.append(community)
        return base

    def _new_player(
        self, player: SVGElement, label: str, card: SVGElement, num_cards: int
    ) -> SVGElement:
        new_player = copy.deepcopy(player)
        new_player.id = label
        card_width = card.width
        if card_width is None:
            card_width = 0
        cards = new_player["cards", "class"]
        if cards is not None:
            for card_idx in range(num_cards):
                new_card = copy.deepcopy(card)
                new_card.center_x(cards)
                offset = (-card_width * num_cards / 2) + card_width * (card_idx + 0.5)
                new_card.x += offset
                new_card.id = f"card-{label}-{card_idx}"
                cards.append(new_card)
        return new_player

    def generate(self):
        return self.base_svg
