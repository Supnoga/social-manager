"""Plánovanie na týždeň jedným klikom (0 tokenov) a opakovanie úspešných videí.

- Každý účet dostane videá svojho projektu a jazyka, ktoré na ňom ešte neboli (najlepšie nápady prvé).
- Časy: najlepšie hodiny daného účtu (stats.best_hours), s malým náhodným posunom.
- Úspešné videá: pôvodné video ide na účty, kde ešte nebolo, a k víťazom vzniknú 2 nové variácie
  (jedno malé lacné AI volanie pre všetkých víťazov naraz).
"""
import datetime as dt
import json
import random

from . import ai, db, stats


def _fmt(t):
    return t.strftime("%Y-%m-%d %H:%M:%S")


def _candidates(acc, platforms_of):
    """Hotové videá pre účet, ktoré na ňom ešte neboli (ani naplánované). Jedno video na nápad."""
    rows = db.q("""SELECT v.*, COALESCE(i.score,0) score, s.idea_id, i.source isrc, COALESCE(i.due_date,'') due,
                   COALESCE(i.markets,'') markets, COALESCE(i.format,'short') fmt, COALESCE(i.pillar,'') pillar,
                   COALESCE(i.parent_id,0) parent FROM videos v
                   LEFT JOIN scripts s ON s.id=v.script_id LEFT JOIN ideas i ON i.id=s.idea_id
                   WHERE v.status='ready' AND NOT EXISTS (SELECT 1 FROM posts p WHERE p.video_id=v.id AND p.account_id=?
                         AND p.status!='failed')
                   ORDER BY v.id DESC""", (acc["id"],))
    used_ideas = {r["idea_id"] for r in db.q("""SELECT s.idea_id FROM posts p JOIN videos v ON v.id=p.video_id
                   JOIN scripts s ON s.id=v.script_id WHERE p.account_id=? AND p.status!='failed'""", (acc["id"],))}
    out, seen = [], set()
    for v in rows:
        if acc["project_id"] and v["project_id"] != acc["project_id"]:
            continue
        if acc["platform"] not in platforms_of.get(v["project_id"], [acc["platform"]]):
            continue
        if acc["lang"] and v["lang"] and acc["lang"] != v["lang"]:
            continue
        if v["markets"]:
            ms = v["markets"].split(",")
            if acc.get("country") and any(m.isupper() for m in ms):
                if acc["country"] not in ms:  # sviatok len v niektorých krajinách
                    continue
            elif acc["lang"] and acc["lang"] not in ms:
                continue
        if v["due"] and v["due"] < dt.date.today().isoformat():
            continue
        if v["idea_id"] and (v["idea_id"] in used_ideas or v["idea_id"] in seen):
            continue
        seen.add(v["idea_id"] or -v["id"])
        out.append(v)
    win = {w["idea_id"]: w["ratio"] for p in {v["project_id"] for v in out} for w in stats.winners(p)}
    out.sort(key=lambda v: (-(win.get(v["idea_id"], 0)), -v["score"], v["id"]))
    return out


def project_plan(pid):
    """Vlastný rytmus projektu: {"days":[0..6] (0 = pondelok), "hours":[12,18,22], "long_hours":[15]}.
    hours = krátke videá, long_hours = dlhé videá na šírku. Bez neho platí spoločné nastavenie."""
    pp = (db.get_setting("plan_projects", {}) or {}).get(str(pid)) if pid else None
    if not pp or not pp.get("days") or not (pp.get("hours") or pp.get("long_hours")):
        return None
    return {"days": [int(d) for d in pp["days"]], "hours": sorted(int(h) for h in pp.get("hours") or []),
            "long_hours": sorted(int(h) for h in pp.get("long_hours") or []),
            "long_every": int(pp.get("long_every") or 0), "offset": int(pp.get("offset") or 0)}


def long_day(own, day):
    """Striedanie (Oliver 14.11.): dlhé video len každý long_every-ty deň, kanály posunuté o offset."""
    return not own.get("long_every") or (day.toordinal() + own.get("offset", 0)) % own["long_every"] == 0


def _plan_rot(a, own, cand, days, now, status, jit, dry):
    """Každý deň 1 krátke video, dlhé každý long_every-ty deň (najprv dlhé, krátke až po ňom).
    Krátke patria k poslednému dlhému videu účtu: 3 krátke = 3 dni, kým nepríde ďalšie dlhé."""
    lh = (own["long_hours"] or [14])[0]
    sh = (own["hours"] or [18])[0]
    last = db.one("""SELECT s.idea_id FROM posts p JOIN videos v ON v.id=p.video_id JOIN scripts s ON s.id=v.script_id
                     JOIN ideas i ON i.id=s.idea_id WHERE p.account_id=? AND p.status IN ('queued','review','uploading','done')
                     AND i.format='long' AND p.scheduled_at<=? ORDER BY p.scheduled_at DESC LIMIT 1""", (a["id"], _fmt(now)))
    cur = last["idea_id"] if last else None
    n = total = 0
    for d in range(days + 1):
        day = (now + dt.timedelta(days=d)).date()
        if day.weekday() not in own["days"]:
            continue
        iso = day.isoformat()
        there = db.q("""SELECT p.scheduled_at, s.idea_id, COALESCE(i.format,'short') fmt FROM posts p JOIN videos v ON v.id=p.video_id
                        LEFT JOIN scripts s ON s.id=v.script_id LEFT JOIN ideas i ON i.id=s.idea_id
                        WHERE p.account_id=? AND p.status IN ('queued','review','uploading','done') AND substr(p.scheduled_at,1,10)=?""",
                     (a["id"], iso))
        has_long = next((r["idea_id"] for r in there if r["fmt"] == "long"), None)
        has_short = any(r["fmt"] != "long" for r in there)
        if has_long:
            cur = has_long
        slots = ([("long", lh)] if long_day(own, day) and not has_long else []) + ([("short", sh)] if not has_short else [])
        for kind, h in slots:
            if dt.datetime.combine(day, dt.time(h)) <= now + dt.timedelta(minutes=20):
                continue
            total += 1
            if kind == "long":
                pool = [v for v in cand if v["fmt"] == "long" and (not v["due"] or v["due"] == iso)]
                kids = {}
                for v in cand:
                    if v["fmt"] != "long" and v["parent"]:
                        kids[v["parent"]] = kids.get(v["parent"], 0) + 1
                pool.sort(key=lambda v: (v["due"] != iso, -min(kids.get(v["idea_id"], 0), 3)))
            else:
                pool = [v for v in cand if v["fmt"] != "long" and cur and v["parent"] == cur]
                if not pool:   # krátke k inému dlhému, ktoré už na účte bolo; inak hocijaké hotové krátke
                    pool = [v for v in cand if v["fmt"] != "long" and not (v["due"] and v["due"] != iso)]
            if not pool:
                continue
            v = pool[0]
            cand.remove(v)
            if kind == "long":
                cur = v["idea_id"]
            when = dt.datetime.combine(day, dt.time(h)) + dt.timedelta(minutes=random.randint(0, jit) if jit else 0)
            if not dry:
                db.run("INSERT INTO posts(video_id,account_id,scheduled_at,privacy,status) VALUES(?,?,?,?,?)",
                       (v["id"], a["id"], _fmt(when), "public", status))
            n += 1
    return n, total


def _plan_own(a, own, cand, days, now, status, jit, dry):
    """Účet projektu s vlastným rytmom. Keď má projekt dlhé aj krátke hodiny, každý deň je jeden balík:
    najprv 1 dlhé video a v krátkych hodinách len Shorts vystrihnuté z TOHO dlhého videa (Oliver 14.11.).
    Deň bez dlhého videa ostane prázdny. Projekty len s krátkymi hodinami plánujú Shorts ako doteraz."""
    bundle = bool(own["long_hours"]) and bool(own["hours"])
    slots_def = [(h, "long") for h in sorted(own["long_hours"])] + [(h, "short") for h in sorted(own["hours"])]
    n = total = 0
    for d in range(days + 1):
        day = (now + dt.timedelta(days=d)).date()
        if day.weekday() not in own["days"]:
            continue
        iso = day.isoformat()
        there = db.q("""SELECT p.scheduled_at, COALESCE(i.pillar,'') pillar, s.idea_id, COALESCE(i.format,'short') fmt
                        FROM posts p JOIN videos v ON v.id=p.video_id
                        LEFT JOIN scripts s ON s.id=v.script_id LEFT JOIN ideas i ON i.id=s.idea_id
                        WHERE p.account_id=? AND p.status IN ('queued','review','uploading','done')
                        AND substr(p.scheduled_at,1,10)=?""", (a["id"], iso))
        taken = {int(r["scheduled_at"][11:13]) for r in there}
        used = {r["pillar"] for r in there if r["pillar"]}
        day_long = next((r["idea_id"] for r in there if r["fmt"] == "long" and r["idea_id"]), None)
        for h, kind in slots_def:
            if dt.datetime.combine(day, dt.time(h)) <= now + dt.timedelta(minutes=20):
                continue
            total += 1
            if h in taken:
                continue
            if kind == "long":
                if day_long:
                    continue
                pool = [v for v in cand if v["fmt"] == "long" and (not v["due"] or v["due"] == iso)]
                if bundle:  # dlhé video s hotovými Shorts má prednosť, aby deň bol celý
                    kids = {}
                    for v in cand:
                        if v["fmt"] != "long" and v["parent"]:
                            kids[v["parent"]] = kids.get(v["parent"], 0) + 1
                    pool.sort(key=lambda v: (v["due"] != iso, -min(kids.get(v["idea_id"], 0), len(own["hours"])), v["pillar"] in used))
                else:
                    pool.sort(key=lambda v: (v["due"] != iso, v["pillar"] in used))
            else:
                if bundle:
                    if not day_long:
                        continue  # bez dlhého videa v ten deň žiadne Shorts
                    pool = [v for v in cand if v["fmt"] != "long" and v["parent"] == day_long]
                else:
                    pool = [v for v in cand if v["fmt"] != "long" and (not v["due"] or v["due"] == iso)]
                    pool.sort(key=lambda v: (v["due"] != iso, v["pillar"] in used))
            if not pool:
                continue
            v = pool[0]
            cand.remove(v)
            if v["pillar"]:
                used.add(v["pillar"])
            if kind == "long":
                day_long = v["idea_id"]
            when = dt.datetime.combine(day, dt.time(h)) + dt.timedelta(minutes=random.randint(0, jit) if jit else 0)
            if not dry:
                db.run("INSERT INTO posts(video_id,account_id,scheduled_at,privacy,status) VALUES(?,?,?,?,?)",
                       (v["id"], a["id"], _fmt(when), "public", status))
            n += 1
    return n, total


def plan_week(project_ids=None, days=7, per_day=None, dry=False):
    per_day = int(per_day or db.get_setting("plan_per_day", 1) or 1)
    base_per_day = per_day
    status = "review" if db.get_setting("require_approval", True) else "queued"
    jit = int(db.get_setting("jitter_min", 10) or 0)
    platforms_of = {p["id"]: json.loads(p["platforms"] or "[]") or ["youtube", "tiktok", "instagram", "facebook"]
                    for p in db.q("SELECT id, platforms FROM projects")}
    accs = db.q("SELECT * FROM accounts")
    if project_ids:
        accs = [a for a in accs if not a["project_id"] or a["project_id"] in project_ids]
    now = dt.datetime.now()
    created, per_acc, empty, short = 0, [], [], []
    base_status = status
    for a in accs:
        cand = _candidates(a, platforms_of)
        if project_ids:
            cand = [v for v in cand if v["project_id"] in project_ids]
        own = project_plan(a["project_id"])
        if own:  # projekt má vlastné dni a hodiny
            n, slots_total = (_plan_rot if own.get("long_every") else _plan_own)(a, own, cand, days, now, status, jit, dry)
            created += n
            per_acc.append({"account": a["name"], "platform": a["platform"], "posts": n,
                            "hours": sorted(own["hours"] + own["long_hours"]), "how": "plán projektu"})
            if n == 0:
                empty.append(a["name"])
            elif n < slots_total:
                short.append(a["name"])
            continue
        per_day = base_per_day
        hours, how = stats.best_hours(a, max(per_day, 1))
        hours = sorted(hours[:per_day])
        n, used_days, slots_total = 0, 0, 0
        for d in range(days + 1):
            day = (now + dt.timedelta(days=d)).date()
            slots = [h for h in hours if dt.datetime.combine(day, dt.time(h)) > now + dt.timedelta(minutes=20)]
            if not slots:
                continue
            used_days += 1
            if used_days > days:
                break
            slots_total += len(slots)
            have = db.one("""SELECT COUNT(*) n FROM posts WHERE account_id=? AND status IN ('queued','review','uploading','done')
                             AND substr(scheduled_at,1,10)=?""", (a["id"], day.isoformat()))["n"]
            dated = [v for v in cand if v["due"] == day.isoformat()]
            for v in dated:  # video k udalosti: presne v jej deň (aj nad bežný počet)
                cand.remove(v)
                h = slots[0]
                when = dt.datetime.combine(day, dt.time(h)) + dt.timedelta(minutes=random.randint(0, jit) if jit else 0)
                if not dry:
                    db.run("INSERT INTO posts(video_id,account_id,scheduled_at,privacy,status) VALUES(?,?,?,?,?)",
                           (v["id"], a["id"], _fmt(when), "public", status))
                n += 1
                have += 1
            for h in slots[have:]:
                cand = [v for v in cand if not v["due"] or v["due"] > day.isoformat()]
                undated = [v for v in cand if not v["due"]]
                if not undated:
                    break
                v = undated[0]
                cand.remove(v)
                when = dt.datetime.combine(day, dt.time(h)) + dt.timedelta(minutes=random.randint(0, jit) if jit else 0)
                if not dry:
                    db.run("INSERT INTO posts(video_id,account_id,scheduled_at,privacy,status) VALUES(?,?,?,?,?)",
                           (v["id"], a["id"], _fmt(when), "public", status))
                n += 1
        created += n
        per_acc.append({"account": a["name"], "platform": a["platform"], "posts": n, "hours": hours, "how": how})
        if n == 0:
            empty.append(a["name"])
        elif n < per_day * days:
            short.append(a["name"])
    return {"created": created, "accounts": per_acc, "empty": empty, "short": short, "review": base_status == "review",
            "per_day": base_per_day}


def repeat_winners(pid, variations=True):
    """Úspešné videá: 2 nové variácie ku každému víťazovi (do schránky Nápadov). Pôvodné víťazné videá
    plánovanie dáva na účty, kde ešte neboli, ako prvé."""
    win = stats.winners(pid)[:5]
    if not win:
        return {"winners": 0, "ideas": 0}
    done = {r["source_ref"] for r in db.q("SELECT source_ref FROM ideas WHERE project_id=? AND source='repeat'", (pid,))}
    fresh = [w for w in win if str(w["idea_id"]) not in done]
    created = 0
    if variations and fresh:
        p = db.one("SELECT * FROM projects WHERE id=?", (pid,))
        from . import languages
        items = "\n".join(f'- id {w["idea_id"]}: "{w["title"]}" | hook: {w["hook"]} | {w["ratio"]}x normal views' for w in fresh)
        data = ai.ask(f"""Project: {p['name']}. {p.get('strategy_short') or p.get('description', '')[:300]}
These videos performed far above normal:
{items}
For each, write 2 NEW videos that repeat what worked (same topic/format/emotion) but with a fresh hook and angle, not a copy.
Return JSON: {{"ideas":[{{"of":0,"title":"","hook":"exact first sentence","angle":"","why":"what we reuse from the winner"}}]}}
Write in {languages.english(p['source_lang'])}.""", "repeat", "cheap")
        for it in (data or {}).get("ideas", []):
            src = next((w for w in fresh if w["idea_id"] == it.get("of")), None)
            if not src or not it.get("title"):
                continue
            pillar = (db.one("SELECT pillar FROM ideas WHERE id=?", (src["idea_id"],)) or {}).get("pillar", "")
            db.run("""INSERT INTO ideas(project_id,title,hook,angle,pillar,format,why,score,status,source,source_ref)
                      VALUES(?,?,?,?,?,'short',?,8,'inbox','repeat',?)""",
                   (pid, it["title"][:300], it.get("hook", ""), it.get("angle", ""), pillar,
                    f"Variácia úspešného videa ({src['ratio']}x): {it.get('why', '')}", str(src["idea_id"])))
            created += 1
    return {"winners": len(win), "ideas": created}


def weekly_auto():
    """Voliteľne: každú nedeľu večer naplánuje ďalší týždeň sám (nastavenie auto_plan_week).
    Projekty s vlastným plánom (plan_projects) a dennou výrobou sa dopĺňajú každú hodinu, aby hotové videá nečakali mimo plánu."""
    now = dt.datetime.now()
    hour = now.strftime("%Y-%m-%d %H")
    if db.get_setting("auto_plan_hour", "") != hour:
        db.set_setting("auto_plan_hour", hour)
        own = {int(k) for k in (db.get_setting("plan_projects", {}) or {})} & {int(k) for k in (db.get_setting("auto_produce", {}) or {})}
        if own:
            try:
                plan_week(sorted(own))
            except Exception as e:
                print("hodinové plánovanie:", e)
    if not db.get_setting("auto_plan_week", False) or now.weekday() != 6 or now.hour < 18:
        return
    if db.get_setting("auto_plan_last", "") == now.date().isoformat():
        return
    db.set_setting("auto_plan_last", now.date().isoformat())
    plan_week()
