# type: ignore # unfortunately draftsman types seem kinda scuffed
from .arco_types import Or
from draftsman.blueprintable import Blueprint
from draftsman.classes.entity_list import EntityList
from draftsman.entity import DeciderCombinator
from draftsman.constants import Direction

signal_map: dict[str, str] = {
    "G": "se-arcosphere-g",
    "E": "se-arcosphere-e",
    "Z": "se-arcosphere-c",
    "T": "se-arcosphere-d",
    "L": "se-arcosphere-a",
    "X": "se-arcosphere-b",
    "P": "se-arcosphere-f",
    "O": "se-arcosphere-h",
}


def _to_bp_one(index: int, output_signal: str, or_clauses: Or) -> DeciderCombinator:

    combi = DeciderCombinator(
        # draftsman bug? it ends up trying to create an entity with name "aai-filter" if we don't do this
        name="decider-combinator",
        tile_position=(0, index),
        direction=Direction.EAST,
    )
    conditions = []
    for and_clause in or_clauses.clauses:
        is_first_in_and_clause = True
        for clause in and_clause.clauses:
            condi = DeciderCombinator.Condition(
                first_signal=signal_map[clause.leftsignal],
                comparator=clause.comparison,
                constant=clause.rightconstant,
            )
            if is_first_in_and_clause:
                conditions = conditions | condi
                is_first_in_and_clause = False
            else:
                conditions = conditions & condi
    combi.conditions = conditions
    combi.outputs = [
        DeciderCombinator.Output(
            signal=output_signal, copy_count_from_input=False, constant=1
        )
    ]
    return combi


def to_bp(combis: dict[Recipe, Or]) -> Blueprint:
    entities = EntityList()
    for i, (recipe, or_clauses) in enumerate(combis.items()):
        combi = _to_bp_one(i, recipe.internal_name, or_clauses)
        entities.append(combi)
    return Blueprint(entities=entities)
