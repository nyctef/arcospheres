clear;
uv run python rotate.py;
# dot -Kneato -Tsvg -o scratch/graph.svg scratch/graph_output.txt
for f in scratch/strategy_*.dot; do
    dot -Kneato -Tsvg -o "${f%.dot}.svg" "$f";
done
