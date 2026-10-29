from collections import Counter, defaultdict
import pprint
from math import sqrt, atan2, acos

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
        # print (f"{name}\t| {' '.join(sorted(map(str, clns.values())))}")

    # pprint.pprint(colocated_names)
                

def run_comparisons(data: list[dict[str, dict[str, list[ str]]]]):
    comparisons = []
    for entry1 in data:
        for entry2 in data:
            name1, details1 = next(iter(entry1.items()))
            name2, details2 = next(iter(entry2.items()))
            if name1 == name2:
                continue

            if not 'coords' in details1 or not 'coords' in details2:
                continue

            coords1 = details1['coords']
            coords2 = details2['coords']
            assert len(coords1) == 3, f"Name '{name1}' has unexpected number of coordinates"
            assert len(coords2) == 3, f"Name '{name2}' has unexpected number of coordinates"
            if (coords1[0] != coords2[0] and coords1[1] != coords2[1] and coords1[2] != coords2[2]):
                continue

            names1 = set(details1['parts'])
            names2 = set(details2['parts'])
            namesdiff1 = (f"+{n}" for n in names2 - names1)
            namesdiff2 = (f"-{n}" for n in names1 - names2)
            namesdiff = list(namesdiff1) + list(namesdiff2)
            coordsdiff = [c2 - c1 for c1, c2 in zip(coords1, coords2)]
            comparisons.append(f"{' '.join(map(str, sorted(namesdiff)))} | {coordsdiff} | {name2} - {name1}")
    comparisons.sort()
    for comparison in comparisons:
        print(comparison)

    polar_coords = []

    for entry in data:
        name, details = next(iter(entry.items()))
        if 'coords' not in details:
            continue
        coords = details['coords']
        rho = sqrt(pow(coords[0], 2) + pow(coords[1], 2) + pow(coords[2], 2))
        rho = round(rho, 3)
        theta = atan2(coords[1], coords[0])
        theta = round(theta, 3)
        phi = acos(coords[2] / rho)
        phi = round(phi, 3)
        polar_coords.append((rho, theta, phi))
    polar_coords.sort()
    for polar_coord in polar_coords:
        print(polar_coord)

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: check-star-data <file>")
        return

    file_path = sys.argv[1]

    with open(file_path, "r") as f:
        data = yaml.safe_load(f)
    
    run_checks(data)
    run_comparisons(data)
    
