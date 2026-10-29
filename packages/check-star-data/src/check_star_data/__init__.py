from collections import Counter, defaultdict
import pprint

import yaml
import sys

def run_checks(data: list[dict[str, dict[str, list[ str]]]]):
    assert isinstance(data, list)

    names: set[str] = set()

    for entry in data:
        assert isinstance(entry, dict)
        for name, details in entry.items():
            assert isinstance(name, str)
            assert isinstance(details, dict)
            assert len(details['parts']) == 11, f"Name '{name}' has unexpected number of parts"
            names.add(name)

    referenced_names = set(p for entry in data for x in entry.values() for p in x['parts'])
    referenced_names_counter = Counter(p for entry in data for x in entry.values() for p in x['parts'])
    for refname in referenced_names:
        assert refname in names, f"Referenced name '{refname}' not found in names"
        assert referenced_names_counter[refname] == 11, f"Referenced name '{refname}' has unexpected count"

    assert len(names)== 60, f"Expected 60 names, found {len(names)}"
    assert len(referenced_names) == 60, f"Expected 60 referenced names, found {len(referenced_names)}"

    colocated_names: dict[str, dict[str, int]] = defaultdict(dict)
    for entry in data:
        for name, details in entry.items():
            for part1 in details['parts']:
                for part2 in details['parts']:
                    if part1 == part2:
                        continue
                    if part2 not in colocated_names[part1]:
                        colocated_names[part1][part2] = 0
                    colocated_names[part1][part2] += 1

    for name, clns in colocated_names.items():
        assert len(clns) == 29, f"Name '{name}' has unexpected colocated count"
        # print(f"{name} | {''.join(f'{other}:{count} ' for other, count in clns.items())}")
        print (f"{name}\t| {' '.join(sorted(map(str, clns.values())))}")

    # pprint.pprint(colocated_names)
                

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: check-star-data <file>")
        return

    file_path = sys.argv[1]

    with open(file_path, "r") as f:
        data = yaml.safe_load(f)
    
    run_checks(data)
    
