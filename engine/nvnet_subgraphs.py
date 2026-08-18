"""Подграфы сети — ПРАВИЛОМ по role/sector/layer, а не руками собранным списком.

Разница принципиальная. Список узлов, набранный вручную, всегда выглядит содержательно:
что положил, то и увидел. Правило может дать пустой или вырожденный подграф — и это
результат исследования, а не сбой. Блюпринт предлагает три подграфа; если у какого-то из
них нет самостоятельного ландшафта, движок обязан это показать, а не подогнать состав.

Правила лежат в конфиге ниже, а не в коде, чтобы их можно было оспорить, не читая Python.
"""

# Ребро относится к подграфу, если ОБА его конца в нём: подграф — это срез сети, а не
# набор узлов с торчащими наружу связями.
RULES = {
    "gpu-ecosystem": {
        "label": "GPU-стек",
        "description": "Обучение и инференс на GPU: ускорители, среда программирования, "
                       "библиотеки и покупатели-гиперскейлеры",
        "sectors": {"gpu_platform", "ml_framework", "compiler", "inference_engine",
                    "model_hub", "hyperscaler", "neocloud"},
        "ids": {"nvidia", "amd", "cuda", "pytorch", "vllm"},
        # Кто заперт средой программирования — тот в GPU-стеке по определению.
        "linked_to": {"cuda": {"locks_in_developers", "locks_in_platforms",
                               "path_dependent_on", "standardizes_on", "is_alternative_to"}},
        "exclude_ids": set(),
    },
    "tpu-ecosystem": {
        "label": "TPU-стек",
        "description": "Вертикаль Google: собственный ускоритель, облако, лаборатория "
                       "и библиотека обучения в одном владении",
        "sectors": set(),
        "ids": {"google", "google-cloud", "google-deepmind", "jax"},
        "linked_to": {},
        "exclude_ids": set(),
    },
    "infrastructure-backbone": {
        "label": "Хребет инфраструктуры",
        "description": "Производство и геополитика, общие для обоих стеков: фабрики, "
                       "станки, софт проектирования, юрисдикции и капитал",
        "sectors": {"foundry", "fab_equipment", "eda", "chip_ip", "packaging",
                    "materials", "jurisdiction", "export_authority", "policy",
                    "generation", "grid_power", "venture", "strategic_capital"},
        "ids": set(),
        "linked_to": {},
        "exclude_ids": set(),
    },
}

# Ниже этого числа узлов подграф считается вырожденным и помечается — но НЕ достраивается.
DEGENERATE_BELOW = 5


def _members(rule, entities, edges):
    ids = set(rule["ids"])
    for e in entities:
        if e.get("sector") in rule["sectors"]:
            ids.add(e["id"])
    for hub, types in (rule["linked_to"] or {}).items():
        for x in edges:
            if x["type"] not in types:
                continue
            if x["source"] == hub:
                ids.add(x["target"])
            elif x["target"] == hub:
                ids.add(x["source"])
    return (ids - set(rule["exclude_ids"])) & {e["id"] for e in entities}


def run(entities, edges) -> dict:
    out, notes = [], []
    for sid, rule in RULES.items():
        node_ids = sorted(_members(rule, entities, edges))
        edge_ids = sorted(x["id"] for x in edges
                          if x["source"] in node_ids and x["target"] in node_ids)
        degenerate = len(node_ids) < DEGENERATE_BELOW
        if degenerate:
            notes.append(f"{sid}: правило дало {len(node_ids)} узлов "
                         f"(<{DEGENERATE_BELOW}) — подграф вырожден, состав НЕ дополнялся "
                         f"вручную: {', '.join(node_ids) or '—'}")
        # Внутренняя связность: сколько рёбер приходится на узел. Подграф без рёбер —
        # это список, а не структура, и об этом тоже нужно сказать.
        if node_ids and len(edge_ids) < len(node_ids) / 2:
            notes.append(f"{sid}: {len(node_ids)} узлов при {len(edge_ids)} внутренних "
                         f"связях — состав держится на правиле, а не на связности")
        out.append({"id": sid, "label": rule["label"],
                    "description": rule["description"],
                    "nodeIds": node_ids, "edgeIds": edge_ids,
                    "degenerate": degenerate})
    return {"subgraphs": out, "notes": notes}
