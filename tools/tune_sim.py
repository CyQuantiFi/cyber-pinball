#!/usr/bin/env python3
"""Rough Monte Carlo of Threat Tide games, for tuning before playtesting.

Reads technique cards and tuning values straight from table/tt_config.vbs so
there is one source of truth. The player model is deliberately simple: each
shot either hits the lit stage, hits some other stage, or misses; drains and
slings happen at fixed rates. Use it to compare settings, not to predict
exact scores. Real numbers come from cabinet playtests (docs/acceptance.md).

    python3 tools/tune_sim.py                 # 5,000 games per player profile
    python3 tools/tune_sim.py --games 20000 --seed 7
"""
import argparse
import pathlib
import random
import re
import statistics

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = ROOT / "table" / "tt_config.vbs"

STAGES = ["ST_RECON", "ST_INITIAL_ACCESS", "ST_EXECUTION", "ST_PERSISTENCE",
          "ST_PRIV_ESC", "ST_LATERAL", "ST_IMPACT"]

# Player profiles. accuracy = chance a shot at the lit stage hits it.
# ball_seconds = average time a ball survives. stray = chance a missed shot
# still hits some other (unlit) stage.
PROFILES = {
    "first-timer": dict(accuracy=0.20, ball_seconds=60, stray=0.45, shot_seconds=4.0),
    "average":     dict(accuracy=0.32, ball_seconds=80, stray=0.45, shot_seconds=3.5),
    "expert":      dict(accuracy=0.55, ball_seconds=140, stray=0.35, shot_seconds=3.0),
}
SLING_PER_SHOT = 0.35
ASSET_PER_SHOT = 0.08


def load_config():
    text = CONFIG.read_text(encoding="utf-8")
    consts = {}
    for m in re.finditer(r"^\s*Const\s+(\w+)\s*=\s*([-\d.]+)", text, re.M):
        consts[m.group(1)] = float(m.group(2))
    for m in re.finditer(r"^\s*Dim\s+(\w+)\s*:\s*\w+\s*=\s*(True|False|[-\d.]+)", text, re.M):
        v = m.group(2)
        consts[m.group(1)] = (v == "True") if v in ("True", "False") else float(v)
    cards = {i: [] for i in range(7)}
    for m in re.finditer(r'Array\((ST_\w+),\s*"([^"]+)",\s*"(T\d+)",\s*([\d.]+)\)', text):
        cards[STAGES.index(m.group(1))].append((m.group(2), m.group(3), float(m.group(4))))
    assert all(cards.values()), "every stage needs at least one card"
    return consts, cards


def play_game(c, cards, prof, rng):
    score = 0.0
    impact = c["TT_IMPACT_START"]
    paths = 0
    extra = 0
    extra_given = False
    seconds = 0.0
    balls_left = int(c["TT_BallsPerGame"])
    worst = 0.0
    while balls_left > 0:
        balls_left -= 1
        done = [None] * 7  # stage value when collected
        mult = c["TT_PATH_MULT_START"]
        t = 0.0
        last_stage_t = 0.0
        saved = False
        next_patch = c["TT_PATCH_TUESDAY_MS"] / 1000
        p_drain = prof["shot_seconds"] / prof["ball_seconds"]
        while True:
            t += prof["shot_seconds"] * rng.uniform(0.6, 1.4)
            if c["TT_PatchTuesdayOn"] and t >= next_patch:
                next_patch += c["TT_PATCH_TUESDAY_MS"] / 1000
                lit = [i for i in range(6) if done[i] is not None]
                if lit:
                    done[rng.choice(lit)] = None
            if rng.random() < SLING_PER_SHOT:
                done = [v * (1 - c["TT_EDR_CUT"]) if v is not None else None for v in done]
            if rng.random() < ASSET_PER_SHOT:
                impact += c["TT_IMPACT_STEP"]
            if rng.random() < p_drain:
                if t < c["TT_BALLSAVE_MS"] / 1000 and not saved:
                    saved = True
                    continue
                score += min(int(t - last_stage_t) * c["TT_DWELL_PER_SEC"], c["TT_DWELL_CAP"])
                break
            nxt = next(i for i in range(7) if done[i] is None)
            if rng.random() < prof["accuracy"]:
                stage, lit = nxt, True
            elif rng.random() < prof["stray"]:
                stage, lit = rng.choice([i for i in range(7) if i != nxt]), False
            else:
                continue
            _, _, prob = rng.choice(cards[stage])
            value = round(prob * impact * (1 if lit else c["TT_UNLIT_SHARE"]))
            score += value
            last_stage_t = t
            if lit:
                done[stage] = value
                if stage == 6:
                    award = round(sum(done) * mult)
                    score += award
                    worst = max(worst, award)
                    paths += 1
                    mult = min(mult + c["TT_PATH_MULT_STEP"], c["TT_PATH_MULT_MAX"])
                    done = [None] * 7
                    if paths == c["TT_EXTRA_BALL_AT_PATH"] and not extra_given:
                        extra_given = True
                        extra += 1
        seconds += t
        if extra:
            extra -= 1
            balls_left += 1
    return score, paths, seconds, worst


def money(v):
    if v >= 1e9:
        return f"${v / 1e9:,.1f}B"
    if v >= 1e7:
        return f"${v / 1e6:,.1f}M"
    return f"${v:,.0f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()
    c, cards = load_config()
    rng = random.Random(args.seed)
    print(f"Threat Tide tuning sim - {args.games} games per profile, "
          f"{int(c['TT_BallsPerGame'])} balls, Patch Tuesday {'on' if c['TT_PatchTuesdayOn'] else 'off'}\n")
    print(f"{'profile':<12} {'median':>12} {'p90':>12} {'mins':>6} {'1+ path':>8} "
          f"{'path in 3':>10} {'3+ paths':>9}")
    for name, prof in PROFILES.items():
        games = [play_game(c, cards, prof, rng) for _ in range(args.games)]
        scores = sorted(g[0] for g in games)
        p_path = sum(1 for g in games if g[1] >= 1) / len(games)
        p_three = sum(1 for g in games if g[1] >= c["TT_WIZARD_AT_PATHS"]) / len(games)
        mins = statistics.mean(g[2] for g in games) / 60
        print(f"{name:<12} {money(statistics.median(scores)):>12} "
              f"{money(scores[int(len(scores) * 0.9)]):>12} {mins:>6.1f} {p_path:>8.0%} "
              f"{1 - (1 - p_path) ** 3:>10.0%} {p_three:>9.0%}")
    print("\nTargets (spec): first-timer completes a Path within 3 games; games last 3-5 minutes.")


if __name__ == "__main__":
    main()
