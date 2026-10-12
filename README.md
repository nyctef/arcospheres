reference for arcosphere names/recipes:

(internal SE names are relevant when dumping debug information out via lua)

|     |         |     |                 |
| --- | ------- | --- | --------------- |
| γ   | gamma   | G   | se-arcosphere-g |
| ε   | epsilon | E   | se-arcosphere-e |
| ζ   | zeta    | Z   | se-arcosphere-c |
| θ   | theta   | T   | se-arcosphere-d |
| λ   | lambda  | L   | se-arcosphere-a |
| ξ   | xi      | X   | se-arcosphere-b |
| φ   | phi     | P   | se-arcosphere-f |
| ω   | omega   | O   | se-arcosphere-h |

```
X G -> Z L | se-arcosphere-fold-b
X Z -> P T | se-arcosphere-fold-c
Z P -> G E | se-arcosphere-fold-f
G P -> X O | se-arcosphere-fold-g

O E -> L G | se-arcosphere-fold-h
L O -> T X | se-arcosphere-fold-a
T L -> E Z | se-arcosphere-fold-d
E T -> O P | se-arcosphere-fold-e
```

```
L X E P -> Z T G O | se-arcosphere-fold-out
Z T G O -> L X E P | se-arcosphere-fold-in
```

## Recovery policies

Run the six-sphere `LXZ -> PET / POG` policy search with:

```sh
uv run --package arcospheres-cli python -m arcospheres_cli.rotate
```

The search targets every production-ready inventory in each maximal end component,
rather than selecting an arbitrary small strategy first. Shortest-path recovery
provides an initial policy. A simplification pass removes clauses, weakens their
extra-sphere requirements, and swaps recipe priorities only when exhaustive
simulation still recovers safely from both production outcomes at every ready
inventory. Production guards are simplified using the same check.

Each policy is a priority list: produce first when its guard matches; otherwise
run the first applicable recipe whose guard matches. Recipe inputs must always be
available, including for rules printed as `(always)`.

For the current configuration:

| Family | Ready inventories | Fold clauses | Production clauses | Maximum recovery folds |
| --- | ---: | ---: | ---: | ---: |
| First MEC | 48 | 20 | 7 | 13 |
| Second MEC | 46 | 19 | 5 | 15 |

The previous smallest-strategy policies covered 17 and 16 ready inventories and
needed 34 and 38 total clauses, respectively. The broader policies need 27 and 24.
They may take longer paths, but validation rejects loops, stuck states, missed
production, and production outside the ready family. Closure under both outcomes
means the checked policies can sustain repeated production from those inventories.

These are locally simplified policies, not proven minimum-rule solutions or a
general proof for other inventory sizes. An unconditional recipe priority list
was not sufficient in the sampled searches.

Run the regression tests with:

```sh
uv run --package arcospheres-cli python -m unittest discover -s packages/arcospheres-cli/tests -v
```
