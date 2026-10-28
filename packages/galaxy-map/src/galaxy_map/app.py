from pathlib import Path
import re
import sys
from flask import Flask, render_template

app = Flask(__name__, instance_relative_config=True)
app.config["TEMPLATES_AUTO_RELOAD"] = True


def load_map_data(path: Path) -> dict:
    stars = []
    with path.open("r") as f:
        for line in f:
            if not line or not line.strip():
                continue
            match = re.match(
                r"!\[\[se-(.+)\.png\]\] at coordinates \\\[SV ([0-9.-]+), ([0-9.-]+), ([0-9.-]+)\]",
                line,
            )
            if not match:
                raise ValueError(f"Line does not match expected format: {line}")
            name, x, y, z = match.groups()
            x, y, z = map(float, (x, y, z))
            stars.append({"name": name, "x": x, "y": y, "z": z})
    return {"stars": stars}


if len(sys.argv) < 2:
    raise ValueError("Please provide the path to the map data file as an argument.")
map_data_path = sys.argv[1]
map_data = load_map_data(Path(map_data_path))


@app.route("/")
def index():
    return render_template("index.html", mapdata=map_data)


# app.config.from_object('config')
