"""То же правило для достройки сети: строка, исчезнувшая из CSV каталога, который в
этом месяце выдал файл, снимается из nvnet_* вместе со своими источниками.

Отдельный файл от tools/nveco_retire_test.py, потому что конвейеры разные: v2 грузит
CSV в базу и снимает оттуда, v3 собирает сеть из семени плюс достройки и пишет в
nvnet_* только достройку. Правило одно (`_retiring_agents` в nveco_ingest), проверять
его надо на обоих.

  python tools/nvnet_retire_test.py
"""

import csv
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="nvnet-retire-"))
os.environ["CAPITAL_DB"] = str(TMP / "test.db")

from engine import db, nveco, nvnet_ingest              # noqa: E402

db.RUNS_DIR = TMP / "runs"
MONTH = "2026-08"

EDGE_COLS = ["source", "target", "type", "strength", "note", "origin"]
SOURCE_COLS = ["owner_kind", "owner_key", "tier", "type", "title", "url", "quote"]

# Оба конца — из семени: достройка v3 и есть связи пивот↔пивот, которых в семени нет.
PAIRS = {"tsmc__asml__customer_of": ("tsmc", "asml", "customer_of"),
         "amd__tsmc__customer_of": ("amd", "tsmc", "customer_of")}


def _write(path, cols, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(rows)


def _month(by_agent):
    base = db.RUNS_DIR / MONTH
    if base.exists():
        shutil.rmtree(base)
    for agent, keys in by_agent.items():
        _write(base / agent / "edges.csv", EDGE_COLS,
               [[*PAIRS[k], 70, "связь достройки", "A1"] for k in keys])
        _write(base / agent / "sources.csv", SOURCE_COLS,
               [["edge", k, 2, "company_pr", "пресс-релиз",
                 f"https://pr.example.com/{k}", "стороны подтвердили поставку в совместном сообщении"]
                for k in keys])


def _run(by_agent):
    _month(by_agent)
    net = nvnet_ingest.build(MONTH)
    return nvnet_ingest.persist(MONTH, net)


def _ids(table):
    con = nveco.connect()
    out = {r[0] for r in con.execute(f"SELECT id FROM {table}")}
    con.close()
    return out


def _sources(owner):
    con = nveco.connect()
    n = con.execute("SELECT COUNT(*) FROM nvnet_source WHERE owner_kind='edge' AND owner_id=?",
                    (owner,)).fetchone()[0]
    con.close()
    return n


CHECKS = []


def check(name):
    def deco(fn):
        CHECKS.append((name, fn))
        return fn
    return deco


@check("связь, исчезнувшая из CSV, снята вместе с источником")
def _(log):
    _run({"nvnet-network": list(PAIRS)})
    assert _ids("nvnet_edge") == set(PAIRS), _ids("nvnet_edge")
    assert _sources("tsmc__asml__customer_of") == 1

    r = _run({"nvnet-network": ["amd__tsmc__customer_of"]})
    assert _ids("nvnet_edge") == {"amd__tsmc__customer_of"}, _ids("nvnet_edge")
    assert r["edges"] == ["tsmc__asml__customer_of"], r["edges"]
    assert _sources("tsmc__asml__customer_of") == 0, "источники снятой связи остались"
    log("снята одна связь из двух, её источник удалён")


@check("молчащий каталог ничего не теряет")
def _(log):
    _run({"nvnet-network": ["tsmc__asml__customer_of"],
          "nvnet-detail": ["amd__tsmc__customer_of"]})
    assert _ids("nvnet_edge") == set(PAIRS), _ids("nvnet_edge")
    r = _run({"nvnet-network": ["tsmc__asml__customer_of"]})
    assert _ids("nvnet_edge") == set(PAIRS), "снята связь молчавшего каталога"
    assert not r["edges"], r["edges"]
    log("обе связи на месте, снято 0")


@check("выдача, отвергнутая целиком, ничего не снимает")
def _(log):
    _run({"nvnet-network": list(PAIRS)})
    _month({"nvnet-network": list(PAIRS)})
    _write(db.RUNS_DIR / MONTH / "nvnet-network" / "edges.csv", EDGE_COLS,
           [["tsmc", "asml", "нет-такого-типа", 70, "брак", "A1"]])
    net = nvnet_ingest.build(MONTH)
    r = nvnet_ingest.persist(MONTH, net)
    assert _ids("nvnet_edge") == set(PAIRS), "снято по аварийной выдаче"
    assert r["broken"] == ["nvnet-network"], r["broken"]
    log("связи целы, каталог назван в broken")


def main():
    fails = 0
    for name, fn in CHECKS:
        if (TMP / "test.db").exists():
            (TMP / "test.db").unlink()
        try:
            fn(lambda m: print(f"        {m}"))
            print(f"  ok   {name}")
        except AssertionError as e:
            print(f"  FAIL {name}: {e}")
            fails += 1
    shutil.rmtree(TMP, ignore_errors=True)
    print(f"\n{'PASS' if not fails else 'FAIL'}: {len(CHECKS) - fails}/{len(CHECKS)} "
          f"проверок снятия с карты в достройке")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
