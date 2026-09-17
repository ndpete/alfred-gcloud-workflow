from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Modifier:
    arg: str
    subtitle: str
    valid: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "arg": self.arg,
            "subtitle": self.subtitle,
            "valid": self.valid,
        }


@dataclass
class Item:
    title: str
    subtitle: str = ""
    arg: str = ""
    valid: bool = True
    icon: str | None = None
    uid: str | None = None
    autocomplete: str | None = None
    variables: dict[str, str] = field(default_factory=dict)
    mods: dict[str, Modifier] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "title": self.title,
            "subtitle": self.subtitle,
            "arg": self.arg,
            "valid": self.valid,
        }
        if self.icon:
            d["icon"] = {"path": self.icon}
        if self.uid:
            d["uid"] = self.uid
        if self.autocomplete is not None:
            d["autocomplete"] = self.autocomplete
        if self.variables:
            d["variables"] = self.variables
        if self.mods:
            d["mods"] = {k: v.to_dict() for k, v in self.mods.items()}
        return d


@dataclass
class Feedback:
    items: list[Item] = field(default_factory=list)
    variables: dict[str, str] = field(default_factory=dict)

    def add_item(self, item: Item) -> None:
        self.items.append(item)

    def to_dict(self) -> dict[str, Any]:
        res: dict[str, Any] = {"items": [item.to_dict() for item in self.items]}
        if self.variables:
            res["variables"] = self.variables
        return res

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def emit(self) -> None:
        sys.stdout.write(self.to_json())
        sys.stdout.write("\n")
        sys.stdout.flush()
