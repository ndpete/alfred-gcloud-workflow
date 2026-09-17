import json

from src.models import Feedback, Item, Modifier


def test_item_serialization():
    item = Item(
        title="Test Title",
        subtitle="Test Subtitle",
        arg="https://example.com",
        valid=True,
        icon="icon.png",
        uid="unique-id",
        autocomplete="autoc",
    )
    d = item.to_dict()
    assert d["title"] == "Test Title"
    assert d["subtitle"] == "Test Subtitle"
    assert d["arg"] == "https://example.com"
    assert d["valid"] is True
    assert d["icon"] == {"path": "icon.png"}
    assert d["uid"] == "unique-id"
    assert d["autocomplete"] == "autoc"


def test_item_with_modifier():
    item = Item(title="Item", arg="base")
    item.mods["cmd"] = Modifier(arg="cmd-arg", subtitle="Cmd subtitle")
    d = item.to_dict()
    assert "mods" in d
    assert d["mods"]["cmd"]["arg"] == "cmd-arg"
    assert d["mods"]["cmd"]["subtitle"] == "Cmd subtitle"


def test_feedback_serialization():
    fb = Feedback()
    fb.add_item(Item(title="Item 1", arg="arg1"))
    fb.add_item(Item(title="Item 2", arg="arg2"))
    json_str = fb.to_json()
    data = json.loads(json_str)
    assert len(data["items"]) == 2
    assert data["items"][0]["title"] == "Item 1"
    assert data["items"][1]["title"] == "Item 2"
