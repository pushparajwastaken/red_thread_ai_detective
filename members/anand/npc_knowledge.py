"""NPC knowledge context builder.

This module intentionally uses permissive parsing so it can work with a variety
of case-state shapes while still enforcing the contract: exact NPC ID lookup,
fact authorization filtering, progression gating, and read-only handling of the
input case.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Mapping


class UnknownNPCError(KeyError):
    """Raised when the requested NPC does not exist in the case state."""


class NPCContext(dict):
    """Mapping-like container for an NPC's current context.

    The implementation behaves like a dictionary and also exposes attributes for
    ergonomic access in tests and downstream consumers.
    """

    def __init__(
        self,
        npc_id: str | None = None,
        known_facts: Iterable[Any] | None = None,
        suspected_facts: Iterable[Any] | None = None,
        cover_story: Iterable[Any] | None = None,
        **extras: Any,
    ) -> None:
        payload = {
            "npc_id": npc_id,
            "known_facts": list(known_facts or []),
            "suspected_facts": list(suspected_facts or []),
            "cover_story": list(cover_story or []),
        }
        payload.update(extras)
        super().__init__(payload)
        self.__dict__.update(payload)

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as exc:  # pragma: no cover - defensive fallback
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


def _as_mapping(value: Any) -> Mapping[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, Mapping):
        return value
    if hasattr(value, "__dict__"):
        return vars(value)
    return None


def _read(obj: Any, *names: str, default: Any = None) -> Any:
    if obj is None:
        return default
    mapping = _as_mapping(obj)
    if mapping is not None:
        for name in names:
            if name in mapping:
                return mapping[name]
            alt = name.lower()
            for key, val in mapping.items():
                if isinstance(key, str) and key.lower() == alt:
                    return val
    for name in names:
        if hasattr(obj, name):
            return getattr(obj, name)
        alt = name.lower()
        for attr_name in dir(obj):
            if attr_name.lower() == alt:
                return getattr(obj, attr_name)
    return default


def _case_list(case: Any, *keys: str) -> list[Any]:
    for key in keys:
        value = _read(case, key)
        if value is None:
            continue
        if isinstance(value, (list, tuple, set)):
            return list(value)
        if isinstance(value, dict):
            return list(value.values())
        mapping = _as_mapping(value)
        if mapping is not None:
            return list(mapping.values())
    return []


def _make_fact_id(fact: Any) -> Any:
    if fact is None:
        return None
    for key in ("fact_id", "id", "factId", "uuid"):
        value = _read(fact, key)
        if value is not None:
            return value
    return None


def _make_npc_id(npc: Any) -> Any:
    if npc is None:
        return None
    for key in ("npc_id", "id", "npcId", "character_id"):
        value = _read(npc, key)
        if value is not None:
            return value
    return None


def _fact_auth_ids(fact: Any, npc_id: str) -> bool:
    if fact is None:
        return False

    for key in (
        "authorized_for",
        "authorized_npcs",
        "authorized_players",
        "knowledge_for",
        "knowers",
        "npc_ids",
        "npcs",
        "owner_ids",
        "owners",
    ):
        value = _read(fact, key, default=None)
        if value is None:
            continue
        items = value if isinstance(value, (list, tuple, set)) else [value]
        for item in items:
            if item == npc_id:
                return True
            if isinstance(item, Mapping):
                if _read(item, "npc_id", "id", "character_id") == npc_id:
                    return True
    for key in ("npc_id", "owner", "owner_id", "character_id"):
        value = _read(fact, key, default=None)
        if value == npc_id:
            return True
    if "permissions" in _as_mapping(fact) or hasattr(fact, "permissions"):
        perms = _read(fact, "permissions", default={})
        if isinstance(perms, Mapping):
            if npc_id in perms:
                return True
            for scope in perms.values():
                if isinstance(scope, (list, tuple, set)) and npc_id in scope:
                    return True

    return False


def _has_global_fact_access(case: Any, npc_id: str) -> set[Any]:
    permissions = _read(case, "permissions", "npc_permissions", "access", "authorization", default={})
    permissions_map = _as_mapping(permissions)
    if permissions_map is None:
        return set()

    access = set()
    for key, value in permissions_map.items():
        if key == npc_id:
            access |= set(value if isinstance(value, (list, tuple, set)) else [value])
        value_map = _as_mapping(value)
        if value_map is not None:
            inner = value_map.get("facts")
            if inner is not None:
                access |= set(inner if isinstance(inner, (list, tuple, set)) else [inner])
    return access


def _progression_state(case: Any) -> Mapping[str, Any]:
    for key in ("progress", "state", "investigation", "case_state", "progression"):
        value = _read(case, key, default=None)
        mapping = _as_mapping(value)
        if mapping is not None:
            return mapping
    return {}


def _is_available(case: Any, fact: Any) -> bool:
    if fact is None:
        return False

    for key in ("available", "is_available", "visible", "enabled"):
        value = _read(fact, key, default=None)
        if value is not None:
            return bool(value)

    state = _progression_state(case)
    any_triggers = [
        "required_discovery",
        "required_fact",
        "requires",
        "unlocks_after",
        "unlocked_by",
        "discoveries",
        "required_facts",
        "progression",
    ]
    for name in any_triggers:
        required = _read(fact, name, default=None)
        if required is None:
            continue
        if isinstance(required, str):
            required = [required]
        elif not isinstance(required, (list, tuple, set)):
            required = [required]
        required_ids = {item for item in required if isinstance(item, (str, int))}
        discovered = set()
        for key in ("discovered_facts", "discovered", "found_facts", "unlocked_facts"):
            value = _read(state, key, default=None)
            if value is not None:
                discovered = set(value if isinstance(value, (list, tuple, set)) else [value])
                break
        if isinstance(state, Mapping):
            for nested_key in ("discovered_facts", "fact_ids", "unlocked"):
                nested = state.get(nested_key)
                if nested is not None:
                    discovered |= set(nested if isinstance(nested, (list, tuple, set)) else [nested])
        if required_ids and not required_ids.issubset(discovered):
            return False

    for key in ("requires_progress", "required_progress", "min_progress", "threshold"):
        required = _read(fact, key, default=None)
        if required is None:
            continue
        progress = _read(state, "progress", "level", "investigation", "stage", default=0)
        if isinstance(progress, Mapping):
            progress = progress.get("value", progress.get("level", 0))
        if isinstance(progress, (int, float)) and float(progress) < float(required):
            return False

    return True


def _fact_category(fact: Any, npc: Any) -> str:
    for key in ("category", "type", "status"):
        value = _read(fact, key, default=None)
        if value is not None:
            value = str(value).lower()
            if value in {"suspect", "suspected", "suspicion", "rumor", "rumour"}:
                return "suspected"
            if value in {"lie", "cover_story", "cover story", "false", "misdirection"}:
                return "cover_story"

    npc_map = _as_mapping(npc)
    if npc_map is not None and "suspicions" in npc_map:
        suspicion_ids = npc_map["suspicions"]
        if suspicion_ids and isinstance(suspicion_ids, (list, tuple, set)):
            fact_id = _make_fact_id(fact)
            if fact_id in suspicion_ids:
                return "suspected"

    for key in ("suspected_facts", "suspicions", "rumors", "rumours"):
        value = _read(npc, key, default=None)
        if value is not None:
            fact_id = _make_fact_id(fact)
            seq = value if isinstance(value, (list, tuple, set)) else [value]
            if fact_id in seq:
                return "suspected"

    for key in ("cover_story", "lies", "lie", "misdirection"):
        value = _read(npc, key, default=None)
        if value is not None:
            seq = value if isinstance(value, (list, tuple, set)) else [value]
            if _make_fact_id(fact) in seq or fact in seq:
                return "cover_story"

    return "known"


def build_npc_context(case: Any, npc_id: str) -> NPCContext:
    """Build the authorized knowledge context for a single NPC.

    The implementation uses exact matching for NPC ids and intentionally does not
    mutate the input case object. Returned collections are independent copies.
    """

    if npc_id is None:
        raise UnknownNPCError("NPC id is required")

    npc_map = _as_mapping(case)
    if npc_map is None:
        raise UnknownNPCError(f"Unknown NPC: {npc_id}")

    npcs = _case_list(case, "npcs", "characters", "actors")
    if not npcs:
        mapping = _read(case, "npc_lookup", "npcs_by_id", default={})
        if isinstance(mapping, Mapping):
            npcs = list(mapping.values())

    npc = None
    for candidate in npcs:
        candidate_id = _make_npc_id(candidate)
        if candidate_id == npc_id:
            npc = candidate
            break

    if npc is None:
        npc_lookup = _read(case, "npc_lookup", "npcs_by_id", default={})
        if isinstance(npc_lookup, Mapping) and npc_id in npc_lookup:
            npc = npc_lookup[npc_id]

    if npc is None:
        raise UnknownNPCError(f"Unknown NPC: {npc_id}")

    facts = _case_list(case, "facts", "case_facts", "knowledge")
    if not facts:
        fact_lookup = _read(case, "fact_lookup", "facts_by_id", default={})
        if isinstance(fact_lookup, Mapping):
            facts = list(fact_lookup.values())

    known: list[Any] = []
    suspected: list[Any] = []
    cover_story: list[Any] = []

    fact_ids = set()
    for fact in facts:
        fact_id = _make_fact_id(fact)
        if fact_id is not None:
            fact_ids.add(fact_id)

    global_access = _has_global_fact_access(case, npc_id)
    for fact in facts:
        fact_id = _make_fact_id(fact)
        if not _is_available(case, fact):
            continue

        if not (
            _fact_auth_ids(fact, npc_id)
            or (fact_id in global_access)
            or _fact_auth_ids(fact, str(npc_id))
        ):
            continue

        category = _fact_category(fact, npc)
        if category == "suspected":
            suspected.append(deepcopy(fact))
        elif category == "cover_story":
            cover_story.append(deepcopy(fact))
        else:
            known.append(deepcopy(fact))

    if not known and not suspected and not cover_story:
        # Some case states embed permissions in NPC records; preserve the contract
        # by checking those records even when the fact list is empty.
        for key in ("known_facts", "facts_known", "knowledge"):
            value = _read(npc, key, default=None)
            if isinstance(value, (list, tuple, set)):
                for item in value:
                    if item is not None:
                        known.append(deepcopy(item))
                break

    return NPCContext(
        npc_id=str(npc_id),
        known_facts=known,
        suspected_facts=suspected,
        cover_story=cover_story,
    )
