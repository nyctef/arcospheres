clear;
# fixed hash seed so set ordering (and so every tie-break) is reproducible
PYTHONHASHSEED=9 uv run --package arcospheres-cli python -m profiling.sampling run --flamegraph -o scratch/profile.html -m arcospheres_cli
# dot -Kneato -Tsvg -o scratch/graph.svg scratch/graph_output.txt
for f in scratch/strategy_*.dot; do
    dot -Kneato -Tsvg -o "${f%.dot}.svg" "$f";
done
