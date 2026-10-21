import base64
import json
import sys
import threading
import types
import urllib.error
import urllib.request

import pytest

from midi2sty import model, ui
from midi2sty.recipe import Recipe, SectionPlan, TrackPlan


def synth_song(bars=16):
    bt = 1920
    drums = model.Track("Drums", 9, None, [model.Note(b * bt + k * 480, 100, 36 + (k % 2) * 2, 90)
                                           for b in range(bars) for k in range(4)], True, 0)
    bass = model.Track("Bass", 0, 33, [model.Note(b * bt, 960, 36 + (b % 4), 90) for b in range(bars)], False, 1)
    mel = model.Track("Lead", 1, 73, [model.Note(b * bt + 480, 240, 72 + (b % 5), 90) for b in range(bars)], False, 2)
    return model.Song([drums, bass, mel], 120.0, (4, 4), bars * bt, 0, False)


def install_stubs(monkeypatch):
    arrange = types.ModuleType("midi2sty.arrange")
    arrange.suggest_recipe = lambda song: Recipe(
        name="stub", tracks=[TrackPlan(0, "RHY1", "drums"), TrackPlan(1, "BASS", "mono, low"),
                             TrackPlan(2, "exclude", "melody: mono, high, sparse")],
        sections=[SectionPlan("Main A", "song", 0, 4)])

    def build_style(song, recipe):
        secs = [model.StyleSection(n, 1920 * 4, [model.StyleChannel("RHY1", None, [model.Note(0, 10, 36, 90)])])
                for n in model.SECTIONS]
        return model.Style(120, (4, 4), secs)
    arrange.build_style = build_style
    w = types.ModuleType("midi2sty.sty_writer"); w.write_sty = lambda st: b"MThd-stub"
    v = types.ModuleType("midi2sty.validate"); v.validate_sty = lambda b: ["stub warning"]
    m = types.ModuleType("midi2sty.melody")
    m.classify_parts = lambda song: [{"index": 2, "tier": "melody", "score": 0.9, "reason": "mono, high"}]
    for k, mod in (("arrange", arrange), ("sty_writer", w), ("validate", v), ("melody", m)):
        monkeypatch.setitem(sys.modules, f"midi2sty.{k}", mod)


@pytest.fixture
def server(monkeypatch):
    install_stubs(monkeypatch)
    srv = ui.make_server(synth_song(), port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown(); srv.server_close()


def call(base, path, body=None):
    req = urllib.request.Request(base + path, data=None if body is None else json.dumps(body).encode(),
                                 method="GET" if body is None else "POST")
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def test_page_and_song(server):
    st, body = call(server, "/")
    assert st == 200 and b"<title>midi2sty</title>" in body
    assert b"cdn" not in body.lower() and b"https://" not in body
    s = json.loads(call(server, "/api/song")[1])
    assert s["bars"] == 16 and s["time_sig"] == [4, 4] and len(s["tracks"]) == 3
    assert s["tracks"][1]["program_name"] == "Finger Bass" and s["tracks"][2]["part"]["tier"] == "melody"
    assert s["tracks"][0]["poly"] == 1 and len(s["tracks"][0]["density"]) == 16
    assert len(s["roots"]) == 16


def test_recipe_roundtrip_and_build(server):
    r = json.loads(call(server, "/api/recipe")[1])
    assert r["name"] == "stub"
    r["tracks"][2]["role"] = "PHR1"
    assert call(server, "/api/recipe", r)[0] == 200
    assert json.loads(call(server, "/api/recipe")[1])["tracks"][2]["role"] == "PHR1"
    st, body = call(server, "/api/build", r)
    j = json.loads(body)
    assert st == 200 and len(j["sections"]) == 15 and j["sections"][0]["bars"] == 4.0
    assert j["warnings"] == ["stub warning"] and j["channels"][2]["tracks"] == ["Bass"]
    assert base64.b64decode(j["sty_b64"]) == b"MThd-stub"
    assert call(server, "/download.sty") == (200, b"MThd-stub")


def test_bad_recipe(server):
    r = json.loads(call(server, "/api/recipe")[1])
    r["tracks"][0]["role"] = "BOGUS"
    st, body = call(server, "/api/recipe", r)
    assert st == 400 and "unknown role" in json.loads(body)["error"]


def test_missing_module_gives_clear_error(monkeypatch):
    for k in ("arrange", "sty_writer", "validate", "melody"):
        monkeypatch.setitem(sys.modules, f"midi2sty.{k}", None)   # forces ImportError
    srv = ui.make_server(synth_song(), port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    try:
        st, body = call(base, "/api/build", {})
        assert st == 501 and "arrange.suggest_recipe" in json.loads(body)["error"]
        assert call(base, "/api/song")[0] == 200
    finally:
        srv.shutdown(); srv.server_close()
