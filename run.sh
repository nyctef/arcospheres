clear;
uv run --package arcospheres-cli python -m profiling.sampling run --flamegraph -o scratch/profile.html -m arcospheres_cli.rotate
# dot -Kneato -Tsvg -o scratch/graph.svg scratch/graph_output.txt
for f in scratch/strategy_*.dot; do
    dot -Kneato -Tsvg -o "${f%.dot}.svg" "$f";
done
