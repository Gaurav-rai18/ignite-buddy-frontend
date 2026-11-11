import pytest
from server import commands
from server.commands import parse
from server.domain import router


def tools(text):
    r = parse(text)
    assert r and r["intent"] == "command", (text, r)
    return [s["tool"] for s in r["steps"]]


@pytest.mark.parametrize("text,expected", [
    ("open the react assignment 3 in vs code and run the install.bat file", ["find_folder", "open_in_app", "run_file"]),
    ("open the react assignment 3 in vs code and run install dot bat", ["find_folder", "open_in_app", "run_file"]),
    ("open chrome and search the web for django channels tutorial", ["open_target", "web_search"]),
    ("run install.bat", ["find_file", "run_file"]),
    ("run install.bat in react assignment 3", ["find_folder", "run_file"]),
    ("open resume.pdf", ["find_file", "open_file"]),
    ("open the react assignment folder", ["find_folder", "open_folder"]),
    ("open github.com", ["open_url"]),
    ("launch chrome", ["open_app"]),
    ("set a timer for 10 minutes", ["set_timer"]),
    ("set a 10 minute timer for pasta", ["set_timer"]),
    ("set a timer for 5 minutes and remind me to stretch in 10 minutes", ["set_timer", "set_reminder"]),
    ("remind me to buy milk and eggs tomorrow at 5pm", ["set_reminder"]),
    ("can you please remind me to call mom at 6pm", ["set_reminder"]),
    ("note: viva and exam on friday", ["add_note"]),
    ("search the web for salt and pepper recipes", ["web_search"]),
    ("search my notes for deadline", ["search_notes"]),
    ("delete today's activity", ["delete_activity"]),
    ("how much time did I spend in VS Code today", ["activity_time"]),
    ("pause tracking for 30 minutes", ["pause_tracking"]),
    ("wipe all my data", ["wipe_all_data"]),
    ("what data do you store about me", ["data_report"]),
])
def test_grammar(text, expected):
    assert tools(text) == expected


def test_args_are_exact():
    p = parse("remind me every day at 9am to log my hours")["steps"][0]["args"]
    assert p == {"text": "log my hours", "when": "at 9am", "repeat": "daily"}
    p = parse("note: Buy MILK")["steps"][0]["args"]
    assert p == {"text": "Buy MILK"}                                      # case preserved
    s = parse("open the react assignment 3 in vs code and run install.bat")["steps"]
    assert s[1]["args"] == {"app": "vs code", "path": "$1.path"} and s[2]["args"] == {"file": "install.bat", "cwd": "$1.path"}
    s = parse("run install.bat")["steps"]
    assert s[1]["args"] == {"file": "$1.name", "cwd": "$1.parent"}


def test_clarify_and_refuse():
    assert parse("run the file")["intent"] == "clarify"
    assert parse("remind me to call mom")["intent"] == "clarify"
    assert parse("delete activity")["intent"] == "clarify"
    assert parse("open chrome and remind me to stretch")["intent"] == "clarify"
    for t in ("delete all my files", "format the disk", "edit the registry"):
        assert parse(t)["intent"] == "refuse"


@pytest.mark.parametrize("text", ["what is a closure", "explain error handling in python", "how do I open a file in python",
                                  "hello there", "open source licences explained in detail for beginners please now"])
def test_not_commands(text):
    assert parse(text) is None


def test_deterministic():
    t = "open the react assignment 3 in vs code and run install.bat"
    assert parse(t) == parse(t)


def test_every_rule_example_parses_and_validates():
    for r in commands.RULES:
        for ex in r.examples:
            plan = parse(ex)
            assert plan, ex
            if plan["intent"] == "command":
                commands.validate(plan)


def test_validate_rejects_bad_plans():
    bad = [{"steps": [{"id": 1, "tool": "rm_rf", "args": {}}]},
           {"steps": [{"id": 1, "tool": "set_timer", "args": {"nope": "1"}}]},
           {"steps": [{"id": 1, "tool": "open_folder", "args": {"path": "$2.path"}}]},
           {"steps": []}]
    for p in bad:
        with pytest.raises(commands.PlanError):
            commands.validate(p)


@pytest.mark.parametrize("text,kind", [
    ("what's this error", "screen"), ("summarize my day", "summary"), ("what was I doing this morning", "activity"),
    ("ask what are the deadlines", "rag"), ("search leave policy", "rag"),
    ("/ask python tutorial", "rag"), ("/search ignite timetable", "rag"),
    ("explain recursion", "browser"),
    ("open the thing", "command"), ("remind me", "clarify"), ("delete all my folders", "refuse"), ("delete the folder x", "command"),
    ("run the unknown thing", "clarify")])
def test_router(text, kind):
    assert router.route(text).kind == kind
