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
                   COALESCE(i.markets,'') markets FROM videos v
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
    """Vlastný rytmus projektu: {"days":[0..6] (0 = pondelok), "hours":[18]}. Bez neho platí spoločné nastavenie."""
    pp = (db.get_setting("plan_projects", {}) or {}).get(str(pid)) if pid else None
    if not pp or not pp.get("days") or not pp.get("hours"):
        return None
    return {"days": [int(d) for d in pp["days"]], "hours": sorted(int(h) for h in pp["hours"])}


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
    for a in accs:
        cand = _candidates(a, platforms_of)
        if project_ids:
            cand = [v for v in cand if v["project_id"] in project_ids]
        own = project_plan(a["project_id"])
        if own:  # projekt má vlastné dni a hodiny
            hours, how, per_day = own["hours"], "plán projektu", len(own["hours"])
        else:
            per_day = base_per_day
            hours, how = stats.best_hours(a, max(per_day, 1))
            hours = sorted(hours[:per_day])
        n, used_days, slots_total = 0, 0, 0
        for d in range(days + 1):
            day = (now + dt.timedelta(days=d)).date()
            if own and day.weekday() not in own["days"]:
                continue
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
        elif n < (slots_total if own else per_day * days):
            short.append(a["name"])
    return {"created": created, "accounts": per_acc, "empty": empty, "short": short, "review": status == "review",
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
    """Voliteľne: každú nedeľu večer naplánuje ďalší týždeň sám (nastavenie auto_plan_week)."""
    now = dt.datetime.now()
    if not db.get_setting("auto_plan_week", False) or now.weekday() != 6 or now.hour < 18:
        return
    if db.get_setting("auto_plan_last", "") == now.date().isoformat():
        return
    db.set_setting("auto_plan_last", now.date().isoformat())
    plan_week()
