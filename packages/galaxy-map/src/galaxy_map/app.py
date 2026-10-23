from pathlib import Path
import re
from flask import Flask, render_template

app = Flask(__name__, instance_relative_config=True)
app.config["TEMPLATES_AUTO_RELOAD"] = True

def load_map_data(path: Path) -> dict:
    stars = []
    with path.open("r") as f:
        for line in f:
            if not line or not line.strip():
                continue
            match = re.match(r"at coordinates \[SV ([0-9.-]+), ([0-9.-]+), ([0-9.-]+)\]", line)
            if match:
                x, y, z = map(float, match.groups())
                stars.append({"x": x, "y": y, "z": z})
    return {"stars": stars}

map_data = load_map_data(Path(__file__).parent.parent.parent /  "map.txt")

@app.route('/')
def index():
    return render_template("index.html", mapdata=map_data)

# app.config.from_object('config')