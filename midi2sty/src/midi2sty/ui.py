"""Interactive recipe editor: `python -m midi2sty.ui song.mid [--port 8765] [--recipe r.json]`.

Stdlib-only localhost server (127.0.0.1) serving one self-contained HTML page (no CDNs).
API: GET /api/song, GET|POST /api/recipe, POST /api/suggest, POST /api/build, GET /download.sty.
arrange / sty_writer / validate / melody are imported lazily; a missing one gives a clear JSON error.
"""
from __future__ import annotations

import argparse
import base64
import importlib
import json
import math
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import model
from .recipe import Recipe

GM = ("Acoustic Grand Piano|Bright Acoustic Piano|Electric Grand Piano|Honky-tonk Piano|Electric Piano 1|"
      "Electric Piano 2|Harpsichord|Clavinet|Celesta|Glockenspiel|Music Box|Vibraphone|Marimba|Xylophone|"
      "Tubular Bells|Dulcimer|Drawbar Organ|Percussive Organ|Rock Organ|Church Organ|Reed Organ|Accordion|"
      "Harmonica|Tango Accordion|Nylon Guitar|Steel Guitar|Jazz Guitar|Clean Guitar|Muted Guitar|"
      "Overdriven Guitar|Distortion Guitar|Guitar Harmonics|Acoustic Bass|Finger Bass|Pick Bass|Fretless Bass|"
      "Slap Bass 1|Slap Bass 2|Synth Bass 1|Synth Bass 2|Violin|Viola|Cello|Contrabass|Tremolo Strings|"
      "Pizzicato Strings|Orchestral Harp|Timpani|String Ensemble 1|String Ensemble 2|Synth Strings 1|"
      "Synth Strings 2|Choir Aahs|Voice Oohs|Synth Voice|Orchestra Hit|Trumpet|Trombone|Tuba|Muted Trumpet|"
      "French Horn|Brass Section|Synth Brass 1|Synth Brass 2|Soprano Sax|Alto Sax|Tenor Sax|Baritone Sax|Oboe|"
      "English Horn|Bassoon|Clarinet|Piccolo|Flute|Recorder|Pan Flute|Blown Bottle|Shakuhachi|Whistle|Ocarina|"
      "Square Lead|Saw Lead|Calliope Lead|Chiff Lead|Charang Lead|Voice Lead|Fifths Lead|Bass+Lead|New Age Pad|"
      "Warm Pad|Polysynth Pad|Choir Pad|Bowed Pad|Metallic Pad|Halo Pad|Sweep Pad|Rain FX|Soundtrack FX|"
      "Crystal FX|Atmosphere FX|Brightness FX|Goblins FX|Echoes FX|Sci-Fi FX|Sitar|Banjo|Shamisen|Koto|Kalimba|"
      "Bagpipe|Fiddle|Shanai|Tinkle Bell|Agogo|Steel Drums|Woodblock|Taiko Drum|Melodic Tom|Synth Drum|"
      "Reverse Cymbal|Guitar Fret Noise|Breath Noise|Seashore|Bird Tweet|Telephone Ring|Helicopter|Applause|"
      "Gunshot").split("|")
NOTE = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]


class ApiError(Exception):
    def __init__(self, msg, status=500):
        super().__init__(msg)
        self.status = status


def _lazy(modname, attr):
    try:
        mod = importlib.import_module(f"midi2sty.{modname}")
        return getattr(mod, attr)
    except (ImportError, AttributeError) as e:
        raise ApiError(f"required function {modname}.{attr} is not available yet: {e}", 501)


def _optional(modname, attr):
    try:
        return getattr(importlib.import_module(f"midi2sty.{modname}"), attr)
    except (ImportError, AttributeError):
        return None


def bar_ticks(song) -> int:
    n, d = song.time_sig
    return model.TICKS_PER_BEAT * 4 * n // d


def _max_poly(notes) -> int:
    ev = sorted([(n.start, 1) for n in notes] + [(n.start + n.dur, -1) for n in notes],
                key=lambda e: (e[0], e[1]))
    cur = best = 0
    for _, d in ev:
        cur += d
        best = max(best, cur)
    return best


class State:
    def __init__(self, song, recipe=None, title="song"):
        self.song = song
        self.title = title
        self.recipe = recipe
        self.last_build = None
        self.lock = threading.Lock()

    # ---- JSON builders -------------------------------------------------
    def song_json(self) -> dict:
        s = self.song
        bt = bar_ticks(s)
        nbars = max(1, math.ceil(s.length_ticks / bt))
        parts = {}
        cp = _optional("melody", "classify_parts")
        warn = None
        if cp:
            try:
                parts = {p["index"]: p for p in cp(s)}
            except Exception as e:  # noqa: BLE001
                warn = f"melody.classify_parts failed: {e}"
        else:
            warn = "melody.classify_parts not available"
        tracks = []
        for t in s.tracks:
            dens = [0] * nbars
            for n in t.notes:
                b = min(nbars - 1, n.start // bt)
                dens[b] += 1
            ps = [n.pitch for n in t.notes]
            prog = None if t.program is None else t.program
            tracks.append({
                "index": t.index, "name": t.name, "channel": t.channel, "program": prog,
                "program_name": "Drum Kit" if t.is_drums else (GM[prog] if prog is not None and prog < 128 else "-"),
                "is_drums": t.is_drums, "notes": len(t.notes),
                "lo": min(ps) if ps else None, "hi": max(ps) if ps else None,
                "poly": _max_poly(t.notes), "density": dens, "part": parts.get(t.index),
            })
        return {"title": self.title, "tempo": round(s.tempo_bpm, 1), "time_sig": list(s.time_sig),
                "bars": nbars, "bar_ticks": bt, "key": f"{NOTE[s.key_root % 12]} {'minor' if s.key_minor else 'major'}",
                "key_root": s.key_root, "key_minor": s.key_minor, "tracks": tracks,
                "roots": self.detect_roots(nbars, bt), "sections": model.SECTIONS,
                "roles": list(model.STYLE_CHANNELS), "warning": warn}

    def detect_roots(self, nbars, bt):
        """Per-bar chord root guess (lowest note in the bar of the bass-role track, else lowest pitched track)."""
        r = self.recipe
        if r is not None and r.bar_roots:
            return list(r.bar_roots)[:nbars] + [None] * max(0, nbars - len(r.bar_roots))
        cands = [t for t in self.song.tracks if r and r.role_of(t.index) == "BASS"]
        if not cands:
            cands = [t for t in self.song.tracks if not t.is_drums]
        out = []
        for b in range(nbars):
            lo = None
            for t in cands:
                for n in t.notes:
                    if b * bt <= n.start < (b + 1) * bt and (lo is None or n.pitch < lo):
                        lo = n.pitch
            out.append(None if lo is None else lo % 12)
        return out

    def recipe_json(self) -> dict:
        if self.recipe is None:
            self.recipe = self.suggest()
        return json.loads(self.recipe.to_json())

    def suggest(self) -> Recipe:
        return _lazy("arrange", "suggest_recipe")(self.song)

    def set_recipe(self, d: dict):
        try:
            r = Recipe.from_json(json.dumps(d))
        except (TypeError, ValueError, KeyError) as e:
            raise ApiError(f"bad recipe: {e}", 400)
        bad = r.validate()
        if bad:
            raise ApiError("invalid recipe: " + "; ".join(bad), 400)
        self.recipe = r

    def build(self) -> dict:
        if self.recipe is None:
            self.recipe = self.suggest()
        build_style = _lazy("arrange", "build_style")
        write_sty = _lazy("sty_writer", "write_sty")
        validate_sty = _lazy("validate", "validate_sty")
        style = build_style(self.song, self.recipe)
        data = write_sty(style)
        warnings = list(validate_sty(data))
        bt = bar_ticks(self.song)
        secs, chans = [], {}
        by_name = {s.name: s for s in style.sections}
        for name in model.SECTIONS:
            s = by_name.get(name)
            if s is None:
                secs.append({"name": name, "bars": 0, "present": False})
                continue
            secs.append({"name": name, "bars": round(s.length_ticks / bt, 2), "present": True,
                         "channels": {c.role: len(c.notes) for c in s.channels if c.notes}})
            for c in s.channels:
                chans[c.role] = chans.get(c.role, 0) + len(c.notes)
        feeds = {}
        for tp in self.recipe.tracks:
            if tp.role in model.STYLE_CHANNELS:
                tr = next((t for t in self.song.tracks if t.index == tp.index), None)
                feeds.setdefault(tp.role, []).append(tr.name if tr else f"#{tp.index}")
        channels = [{"role": r, "channel": model.STYLE_CHANNELS[r] + 1, "tracks": feeds.get(r, []),
                     "notes": chans.get(r, 0)} for r in model.STYLE_CHANNELS]
        self.last_build = data
        return {"sections": secs, "channels": channels, "warnings": warnings, "size": len(data),
                "filename": (self.recipe.name or "midi2sty") + ".sty",
                "sty_b64": base64.b64encode(data).decode("ascii")}


class Handler(BaseHTTPRequestHandler):
    server_version = "midi2sty-ui"

    def log_message(self, *a):  # quiet
        pass

    def _send(self, code, body: bytes, ctype="application/json", extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj).encode("utf-8"))

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b""
        try:
            return json.loads(raw.decode("utf-8")) if raw else {}
        except ValueError:
            raise ApiError("request body is not valid JSON", 400)

    def _run(self, fn):
        try:
            with self.server.state.lock:
                fn(self.server.state)
        except ApiError as e:
            self._json({"error": str(e)}, e.status)
        except Exception as e:  # noqa: BLE001
            self._json({"error": f"{type(e).__name__}: {e}"}, 500)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            self._send(200, HTML.encode("utf-8"), "text/html; charset=utf-8")
        elif path == "/favicon.ico":
            self._send(204, b"", "image/x-icon")
        elif path == "/api/song":
            self._run(lambda st: self._json(st.song_json()))
        elif path == "/api/recipe":
            self._run(lambda st: self._json(st.recipe_json()))
        elif path == "/download.sty":
            def f(st):
                if st.last_build is None:
                    st.build()
                self._send(200, st.last_build, "application/octet-stream",
                           {"Content-Disposition": f'attachment; filename="{(st.recipe.name or "style")}.sty"'})
            self._run(f)
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        path = self.path.split("?")[0]
        if path == "/api/recipe":
            def f(st):
                st.set_recipe(self._body())
                self._json({"ok": True})
            self._run(f)
        elif path == "/api/suggest":
            def f(st):
                st.recipe = st.suggest()
                self._json(json.loads(st.recipe.to_json()))
            self._run(f)
        elif path == "/api/build":
            def f(st):
                body = self._body()
                if body:
                    st.set_recipe(body)
                self._json(st.build())
            self._run(f)
        else:
            self._json({"error": "not found"}, 404)


def make_server(song, recipe=None, port=8765, title="song") -> ThreadingHTTPServer:
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    srv.state = State(song, recipe, title)
    return srv


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="midi2sty.ui", description="Interactive midi2sty recipe editor.")
    ap.add_argument("input", help=".mid file")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--recipe", help="recipe .json to start from")
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args(argv)
    from .analyze import load_song
    try:
        song = load_song(a.input)
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    recipe = None
    if a.recipe:
        with open(a.recipe, encoding="utf-8") as f:
            recipe = Recipe.from_json(f.read())
    import os
    srv = make_server(song, recipe, a.port, os.path.basename(a.input))
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    print(f"midi2sty UI at {url}  (Ctrl+C to stop)")
    if not a.no_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>midi2sty</title>
<style>
:root{--bg:#f6f7f9;--fg:#1c2128;--mut:#667085;--card:#fff;--bd:#d8dce3;--acc:#2563eb;--accfg:#fff;--warn:#b45309;--err:#b91c1c;--hm:37,99,235}
@media(prefers-color-scheme:dark){:root{--bg:#0f1318;--fg:#e6e9ee;--mut:#98a2b3;--card:#181d24;--bd:#2c3440;--acc:#4f8cff;--accfg:#0b1020;--warn:#f0a35a;--err:#f87171;--hm:79,140,255}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.4 system-ui,Segoe UI,sans-serif}
main{max-width:1200px;margin:0 auto;padding:12px 16px 60px}
h1{font-size:20px;margin:8px 0}h2{font-size:15px;margin:0 0 8px}
section{background:var(--card);border:1px solid var(--bd);border-radius:8px;padding:12px;margin:12px 0}
.info{display:flex;flex-wrap:wrap;gap:6px 18px}.info b{color:var(--mut);font-weight:500;margin-right:4px}
.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%}
th,td{text-align:left;padding:4px 8px;border-bottom:1px solid var(--bd);vertical-align:middle;white-space:nowrap}
th{color:var(--mut);font-weight:500;font-size:12px}tr.dim td{opacity:.45}tr.dim td:last-child{opacity:1}
.reason{color:var(--mut);font-size:12px;white-space:normal;min-width:150px}
button,select,input{font:inherit;color:var(--fg);background:var(--card);border:1px solid var(--bd);border-radius:6px;padding:5px 9px}
button{cursor:pointer}button.pri{background:var(--acc);color:var(--accfg);border-color:var(--acc)}
input[type=number]{width:70px}.bar{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}
.strip{display:flex;align-items:flex-end;height:18px;width:160px;gap:0}.strip i{flex:1;min-width:1px;background:rgb(var(--hm));display:block}
.hm{overflow-x:auto;user-select:none;touch-action:pan-x}.row{display:flex;align-items:center;height:18px}
.row>label{position:sticky;left:0;width:64px;flex:none;background:var(--card);font-size:11px;color:var(--mut);z-index:1}
.cell{width:12px;height:16px;flex:none;margin-right:1px;border-radius:2px;background:rgba(var(--hm),var(--a,0))}
.num{width:13px;flex:none;font-size:8px;color:var(--mut);text-align:center;overflow:visible;white-space:nowrap}
.sel{outline:2px solid var(--acc);outline-offset:-2px}.rt{font-size:8px;width:13px;flex:none;text-align:center;color:var(--fg)}
.sec{width:12px;height:16px;margin-right:1px;flex:none;font-size:8px;overflow:hidden;text-align:center}
.warn{color:var(--warn)}.err{color:var(--err);font-weight:600}.mut{color:var(--mut)}
@media(max-width:600px){main{padding:8px}.strip{width:100px}}
</style></head><body><main>
<h1>midi2sty <span class="mut" id="ttl"></span></h1>
<div id="msg" class="err"></div>
<section><h2>Song</h2><div class="info" id="info"></div></section>
<section><h2>Tracks</h2><div class="scroll"><table id="tracks"></table></div></section>
<section><h2>Section map</h2>
<div class="bar"><label><input type="checkbox" id="roots"> show chord roots per bar</label>
<span class="mut">Drag over bars to select, then assign:</span>
<span id="selinfo" class="mut">none</span>
<select id="assign"></select><button id="doassign">Assign selection</button></div>
<div class="hm" id="hm"></div>
<div class="scroll" style="margin-top:10px"><table id="secs"></table></div></section>
<section><h2>Actions</h2><div class="bar">
<button id="resuggest">Re-suggest</button><button id="save">Save recipe (.json)</button>
<button id="loadb">Load recipe</button><input type="file" id="loadf" accept=".json" hidden>
<button class="pri" id="build">Build &amp; download .sty</button></div>
<div id="report"></div></section>
</main>
<script>
const $=s=>document.querySelector(s);
let SONG=null,R=null,SUG=null,SEL=null,sel=[null,null];
const ROLES=["RHY1","RHY2","BASS","CHD1","CHD2","PAD","PHR1","PHR2","exclude"];
const NN=["C","C#","D","Eb","E","F","F#","G","Ab","A","Bb","B"];
const pn=p=>p==null?"-":NN[p%12]+(Math.floor(p/12)-1);
const esc=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
function err(m){$("#msg").textContent=m||""}
async function api(path,body){
  const r=await fetch(path,body===undefined?{}:{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
  const j=await r.json().catch(()=>({error:"bad response"}));
  if(!r.ok)throw new Error(j.error||r.status);return j}
function normRecipe(){
  const have={};(R.sections||[]).forEach(s=>have[s.name]=s);
  R.sections=SONG.sections.map(n=>have[n]||{name:n,source:"auto",start_bar:null,n_bars:null,derive_from:null});
  const th={};(R.tracks||[]).forEach(t=>th[t.index]=t);
  R.tracks=SONG.tracks.map(t=>th[t.index]||{index:t.index,role:"exclude",reason:""})}
function renderInfo(){
  const s=SONG;$("#ttl").textContent=s.title;
  $("#info").innerHTML=`<span><b>Tempo</b>${s.tempo} bpm</span><span><b>Time</b>${s.time_sig[0]}/${s.time_sig[1]}</span>
  <span><b>Bars</b>${s.bars}</span><span><b>Key</b>${esc(s.key)}</span><span><b>Tracks</b>${s.tracks.length}</span>`+
  (s.warning?`<span class="warn">${esc(s.warning)}</span>`:"")}
function strip(d){const m=Math.max(1,...d);return `<div class="strip">`+d.map(v=>`<i style="height:${Math.round(100*v/m)}%"></i>`).join("")+`</div>`}
function renderTracks(){
  let h=`<tr><th>#</th><th>Track</th><th>GM program</th><th>Notes</th><th>Range</th><th>Poly</th><th>Density/bar</th><th>Suggested</th><th>Role</th></tr>`;
  SONG.tracks.forEach(t=>{
    const tp=R.tracks.find(x=>x.index==t.index),sg=SUG&&SUG.tracks.find(x=>x.index==t.index);
    const part=t.part?`${t.part.tier}: ${t.part.reason||""}`:"";
    const sr=sg?`<b>${esc(sg.role)}</b> ${esc(sg.reason||"")}`:"";
    h+=`<tr class="${tp.role=="exclude"?"dim":""}"><td>${t.index}</td><td>${esc(t.name)} <span class="mut">ch${t.channel+1}</span></td>
    <td>${esc(t.program_name)}</td><td>${t.notes}</td><td>${t.is_drums?"drums":pn(t.lo)+"-"+pn(t.hi)}</td><td>${t.poly}</td>
    <td>${strip(t.density)}</td><td class="reason">${sr}${part?`<div>${esc(part)}</div>`:""}</td>
    <td><select data-t="${t.index}">${ROLES.map(r=>`<option${r==tp.role?" selected":""}>${r}</option>`).join("")}</select></td></tr>`});
  $("#tracks").innerHTML=h;
  $("#tracks").querySelectorAll("select").forEach(s=>s.onchange=()=>{
    R.tracks.find(x=>x.index==s.dataset.t).role=s.value;renderTracks();renderMap()})}
function rowVals(f){const n=SONG.bars,o=new Array(n).fill(0);
  SONG.tracks.forEach(t=>{if(f(t,R.tracks.find(x=>x.index==t.index).role))t.density.forEach((v,i)=>o[i]+=v)});return o}
function renderMap(){
  const n=SONG.bars;
  const rows=[["drums",rowVals((t,r)=>t.is_drums||r=="RHY1"||r=="RHY2")],
   ["bass",rowVals((t,r)=>r=="BASS")],["chords",rowVals((t,r)=>["CHD1","CHD2","PAD"].includes(r))],
   ["melody",rowVals((t,r)=>!t.is_drums&&(r=="exclude"||r=="PHR1"||r=="PHR2"||(t.part&&t.part.tier=="melody")))]];
  let h=`<div class="row"><label>bar</label>`+Array.from({length:n},(_,i)=>`<div class="num">${(i+1)%4==1||n<24?i+1:""}</div>`).join("")+`</div>`;
  rows.forEach(([nm,v])=>{const m=Math.max(1,...v);
    h+=`<div class="row"><label>${nm}</label>`+v.map((x,i)=>`<div class="cell" data-b="${i}" style="--a:${(x/m).toFixed(2)}" title="bar ${i+1}: ${x}"></div>`).join("")+`</div>`});
  if($("#roots").checked)h+=`<div class="row"><label>root</label>`+SONG.roots.map(r=>`<div class="rt">${r==null?"":NN[r]}</div>`).join("")+`</div>`;
  const lab=new Array(n).fill("");R.sections.forEach(s=>{if(s.source=="song"&&s.start_bar!=null){
    const len=s.n_bars||4;for(let i=s.start_bar;i<s.start_bar+len&&i<n;i++)lab[i]=lab[i]||s.name.replace(/^(\w)\w* ?(\w+)?.*$/,"$1$2")}});
  h+=`<div class="row"><label>sections</label>`+lab.map(l=>`<div class="sec" title="${l}">${l[0]||""}${l[1]||""}</div>`).join("")+`</div>`;
  $("#hm").innerHTML=h;paintSel()}
function paintSel(){
  const a=Math.min(sel[0]??-1,sel[1]??-1),b=Math.max(sel[0]??-1,sel[1]??-1);
  document.querySelectorAll(".cell").forEach(c=>c.classList.toggle("sel",sel[0]!=null&&+c.dataset.b>=a&&+c.dataset.b<=b));
  $("#selinfo").textContent=sel[0]==null?"none":`bars ${a+1}-${b+1} (${b-a+1})`}
let drag=false;
function bar(e){const el=document.elementFromPoint(e.clientX,e.clientY);return el&&el.dataset&&el.dataset.b!=null?+el.dataset.b:null}
$("#hm").addEventListener("pointerdown",e=>{const b=bar(e);if(b==null)return;drag=true;sel=[b,b];paintSel();e.preventDefault()});
$("#hm").addEventListener("pointermove",e=>{if(!drag)return;const b=bar(e);if(b!=null){sel[1]=b;paintSel()}});
addEventListener("pointerup",()=>drag=false);
$("#doassign").onclick=()=>{
  if(sel[0]==null){err("select bars first");return}err("");
  const a=Math.min(...sel),b=Math.max(...sel),s=R.sections.find(x=>x.name==$("#assign").value);
  Object.assign(s,{source:"song",start_bar:a,n_bars:b-a+1,derive_from:null});renderSecs();renderMap()};
function renderSecs(){
  let h=`<tr><th>Section</th><th>Source</th><th>Derive from</th><th>Start bar</th><th>Bars</th><th></th></tr>`;
  R.sections.forEach((s,i)=>{
    h+=`<tr data-i="${i}"><td>${s.name}</td>
    <td><select data-f="source">${["song","derive","auto"].map(o=>`<option${o==s.source?" selected":""}>${o}</option>`).join("")}</select></td>
    <td><select data-f="derive_from" ${s.source=="derive"?"":"disabled"}><option value=""></option>${SONG.sections.filter(n=>n!=s.name).map(o=>`<option${o==s.derive_from?" selected":""}>${o}</option>`).join("")}</select></td>
    <td><input type="number" min="1" max="${SONG.bars}" data-f="start_bar" value="${s.start_bar==null?"":s.start_bar+1}" ${s.source=="song"?"":"disabled"}></td>
    <td><input type="number" min="1" data-f="n_bars" placeholder="default" value="${s.n_bars==null?"":s.n_bars}"></td>
    <td><button data-sug="1">suggest</button></td></tr>`});
  $("#secs").innerHTML=h;
  $("#secs").querySelectorAll("[data-f]").forEach(el=>el.onchange=()=>{
    const s=R.sections[el.closest("tr").dataset.i],f=el.dataset.f;let v=el.value;
    if(f=="start_bar")v=v===""?null:Math.max(0,+v-1);else if(f=="n_bars")v=v===""?null:Math.max(1,+v);else if(v==="")v=null;
    s[f]=v;if(f=="source"){if(v!="derive")s.derive_from=null;if(v=="song"&&s.start_bar==null)s.start_bar=0}
    renderSecs();renderMap()});
  $("#secs").querySelectorAll("[data-sug]").forEach(el=>el.onclick=()=>{
    const i=el.closest("tr").dataset.i,d=SUG&&SUG.sections.find(x=>x.name==R.sections[i].name);
    R.sections[i]=d?{...d}:{name:R.sections[i].name,source:"auto",start_bar:null,n_bars:null,derive_from:null};renderSecs();renderMap()})}
function renderAll(){normRecipe();renderInfo();renderTracks();renderSecs();renderMap()}
async function suggest(){
  try{err("");SUG=await api("/api/suggest",{});R=JSON.parse(JSON.stringify(SUG));SONG=await api("/api/song");renderAll()}catch(e){err("Suggest failed: "+e.message)}}
$("#resuggest").onclick=suggest;
$("#roots").onchange=renderMap;
function dl(name,data,type){const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([data],{type}));a.download=name;document.body.appendChild(a);a.click();a.remove()}
$("#save").onclick=()=>dl((R.name||"recipe")+".recipe.json",JSON.stringify(R,null,2),"application/json");
$("#loadb").onclick=()=>$("#loadf").click();
$("#loadf").onchange=async e=>{const f=e.target.files[0];if(!f)return;
  try{R=JSON.parse(await f.text());await api("/api/recipe",R);normRecipe();renderAll();err("")}catch(x){err("Load failed: "+x.message)}e.target.value=""};
$("#build").onclick=async()=>{
  try{err("");$("#report").innerHTML="building...";const j=await api("/api/build",R);
    const bin=atob(j.sty_b64),u=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)u[i]=bin.charCodeAt(i);
    dl(j.filename,u,"application/octet-stream");
    let h=`<p>${esc(j.filename)}: ${j.size} bytes</p><div class="scroll"><table><tr><th>Section</th><th>Bars</th></tr>`+
      j.sections.map(s=>`<tr><td>${s.name}</td><td>${s.present?s.bars:'<span class="mut">not built</span>'}</td></tr>`).join("")+`</table></div>
      <div class="scroll"><table><tr><th>Channel</th><th>Style ch</th><th>Fed by</th><th>Notes</th></tr>`+
      j.channels.map(c=>`<tr><td>${c.role}</td><td>${c.channel}</td><td>${esc(c.tracks.join(", ")||"-")}</td><td>${c.notes}</td></tr>`).join("")+`</table></div>`;
    h+=j.warnings.length?`<p class="warn"><b>Validation warnings</b></p><ul>`+j.warnings.map(w=>`<li class="warn">${esc(w)}</li>`).join("")+`</ul>`:`<p>validate_sty: no warnings</p>`;
    $("#report").innerHTML=h}catch(e){$("#report").innerHTML="";err("Build failed: "+e.message)}};
(async()=>{
  const aso=document.createElement("select");
  try{SONG=await api("/api/song");R=await api("/api/recipe");
    SUG=JSON.parse(JSON.stringify(R));
    $("#assign").innerHTML=SONG.sections.map(n=>`<option>${n}</option>`).join("");renderAll()}
  catch(e){err("Could not load: "+e.message);
    if(SONG){$("#assign").innerHTML=SONG.sections.map(n=>`<option>${n}</option>`).join("");
      R={tracks:[],sections:[]};renderAll()}}
})();
</script></body></html>
"""

if __name__ == "__main__":
    sys.exit(main())
