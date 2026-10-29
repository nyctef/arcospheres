from pathlib import Path
import sys
import yaml
from flask import Flask, render_template

app = Flask(__name__, instance_relative_config=True)
app.config["TEMPLATES_AUTO_RELOAD"] = True


def load_map_data(path: Path) -> dict:
    with path.open("r") as f:
        data = yaml.safe_load(f)

    entries: dict[str, dict] = {}
    for entry in data:
        for name, details in entry.items():
            entries[str(name)] = details

    stars = []
    for name, details in entries.items():
        if coords := details.get("coords"):
            x, y, z = map(float, coords)
            stars.append({"name": name, "x": x, "y": y, "z": z})

    # draw a line between two entries when each lists the other as one of its parts
    lines = []
    for name, details in entries.items():
        for part in map(str, details.get("parts", [])):
            if name < part and name in map(str, entries.get(part, {}).get("parts", [])):
                lines.append({"source": name, "target": part})

    return {"stars": stars, "lines": lines}


if len(sys.argv) < 2:
    raise ValueError("Please provide the path to the map data file as an argument.")
map_data_path = sys.argv[1]
map_data = load_map_data(Path(map_data_path))


@app.route("/")
def index():
    return render_template("index.html", mapdata=map_data)


# app.config.from_object('config')
