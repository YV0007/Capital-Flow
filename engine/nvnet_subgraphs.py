"""Подграфы сети — ПРАВИЛОМ по role/sector/layer, а не руками собранным списком.

Разница принципиальная. Список узлов, набранный вручную, всегда выглядит содержательно:
что положил, то и увидел. Правило может дать пустой или вырожденный подграф — и это
результат исследования, а не сбой. Если у группы нет самостоятельного ландшафта, движок
обязан это показать, а не подогнать состав.

Правила лежат в конфиге ниже, а не в коде, чтобы их можно было оспорить, не читая Python.

Пять способов набрать состав. Все они — правила над данными, ни один не перечисляет
узлы «потому что они там уместны»:

  sectors     — сектор сущности входит в набор (положение в стеке)
  layers      — основной слой сущности входит в набор (то же, но грубее)
  ids         — якорь: сущность, вокруг которой группа и строится. Держать коротким:
                чем длиннее список, тем ближе правило к ручной выборке.
  edge_types  — ОБА конца каждой связи перечисленных типов. Так набирается группа,
                которая определена не положением узлов, а видом отношения между ними
                («кто кого шлюзует», «кто кому угрожает»).
  linked_to   — соседи конкретного узла по перечисленным типам связей (точечно).
  grow        — ОДИН шаг наружу от уже набранного ядра по перечисленным типам связей.
                Ядро задаёт «кто это», grow добавляет «с кем это работает».

Ребро относится к подграфу, если ОБА его конца в нём: подграф — это срез сети, а не
набор узлов с торчащими наружу связями.

Порядок в RULES — порядок в файле передачи: от самых полных и самостоятельных групп к
частным. Дашборд рисует их в этом порядке.
"""

RULES = {
    # ── два среза пилота, оставлены без изменений ─────────────────────────────
    "gpu-ecosystem": {
        "label": "GPU-стек",
        "label_en": "GPU stack",
        "description_en": "Training and inference on GPUs: the accelerators, the programming "
                           "environment, the libraries and the hyperscalers buying them",
        "description": "Обучение и инференс на GPU: ускорители, среда программирования, "
                       "библиотеки и покупатели-гиперскейлеры",
        "sectors": {"gpu_platform", "ml_framework", "compiler", "inference_engine",
                    "model_hub", "hyperscaler", "neocloud"},
        "ids": {"nvidia", "amd", "cuda", "pytorch", "vllm"},
        # Кто заперт средой программирования — тот в GPU-стеке по определению.
        "linked_to": {"cuda": {"locks_in_developers", "locks_in_platforms",
                               "path_dependent_on", "standardizes_on", "is_alternative_to"}},
    },
    "infrastructure-backbone": {
        "label": "Хребет инфраструктуры",
        "label_en": "Infrastructure backbone",
        "description_en": "The manufacturing and geopolitics common to both stacks: fabs, tools, "
                           "design software, jurisdictions and capital",
        "description": "Производство и геополитика, общие для обоих стеков: фабрики, "
                       "станки, софт проектирования, юрисдикции и капитал",
        "sectors": {"foundry", "fab_equipment", "eda", "chip_ip", "packaging",
                    "materials", "jurisdiction", "export_authority", "policy",
                    "generation", "grid_power", "venture", "strategic_capital"},
    },

    # ── срезы v1.2: конкретные потоки, цепочки и подэкосистемы ────────────────
    "export-control": {
        "label": "Экспортный контроль",
        "label_en": "Export control",
        "description_en": "Who decides, and through which instrument, that advanced chips may be "
                           "sold and bought",
        "description": "Кто и через какой документ решает, кому разрешено продавать и "
                       "покупать передовые чипы",
        # Группа определена ВИДОМ отношения, а не положением узлов: шлюз — это связь,
        # а не слой. Поэтому ядро набирается по типам связей хребта control, а сектора
        # добавляют сами инстанции власти, включая те, что пока никого не шлюзуют.
        "sectors": {"jurisdiction", "export_authority", "policy", "standards"},
        "edge_types": {"controls_access_to", "export_controlled_by",
                       "subject_to_restriction", "geopolitically_dependent"},
    },
    "power-and-cooling": {
        "label": "Энергия и охлаждение",
        "label_en": "Power and cooling",
        "description_en": "The physical datacenter build-out: generation, transmission, cooling "
                           "and rack power — and everyone drawing on it",
        "description": "Физическая стройка дата-центра: генерация, передача тока, "
                       "охлаждение и питание стоек — и кто всё это потребляет",
        "sectors": {"generation", "grid_power", "cooling", "thermal_materials",
                    "rack_power"},
        # Один шаг по поставке наружу: без потребителя слои L6 и L7 распадаются на
        # список несвязанных подрядчиков — проверено, 15 узлов при 6 внутренних связях.
        "grow": {"supplies", "strategic_partner", "integrates", "delivers_to"},
    },
    "labs-and-clouds": {
        "label": "Лаборатории и их облака",
        "label_en": "Labs and their clouds",
        "description_en": "Whose compute each frontier lab trains on, and what it pays for the "
                           "privilege",
        "description": "На чьей мощности обучается каждая передовая лаборатория и чем "
                       "она за это платит",
        "sectors": {"frontier_lab", "open_model"},
        "grow": {"supplies", "customer_of", "strategic_partner", "enables"},
    },
    "lithography-chain": {
        "label": "Цепочка литографии",
        "label_en": "Lithography chain",
        "description_en": "Who physically cannot be replaced in making a leading-edge die — from "
                           "the tool and the wafer through to packaging",
        "description": "Кого физически нельзя заменить при изготовлении передового "
                       "кристалла — от станка и пластины до упаковки",
        "sectors": {"fab_equipment", "materials", "foundry", "packaging"},
        # Цепочка кончается упакованным кристаллом, поэтому один шаг по упаковке:
        # иначе Amkor и ASE висят в группе вовсе без связей.
        "grow": {"packages"},
    },
    "open-stack-vs-cuda": {
        "label": "Открытый стек против CUDA",
        "label_en": "Open stack versus CUDA",
        "description_en": "How real the exit from NVIDIA's programming environment is: what "
                           "replaces it, and what stands in the way",
        "description": "Насколько реален выход из среды программирования NVIDIA: чем "
                       "именно её замещают и что этому мешает",
        "sectors": {"ml_framework", "compiler", "inference_engine", "model_hub"},
        "ids": {"cuda", "nvidia", "amd"},
        "edge_types": {"is_alternative_to", "could_disrupt"},
    },
    "build-capital": {
        "label": "Капитал стройки",
        "label_en": "Capital behind the build",
        "description_en": "Who pays for the stack — venture and strategic capital — and what the "
                           "money bought",
        "description": "Кто оплачивает стек — венчур и стратегический капитал — и что "
                       "именно куплено на эти деньги",
        "sectors": {"venture", "strategic_capital"},
        "grow": {"invests_in", "funded_by", "board_seat", "hedges_against"},
    },
    "network-fabric": {
        "label": "Сети и оптика",
        "label_en": "Networking and optics",
        "description_en": "The other half of a datacenter: the switching, interconnect and optics "
                           "that bind accelerators into a cluster",
        "description": "Вторая половина дата-центра: коммутация, межсоединения и "
                       "оптика, связывающие ускорители в кластер",
        "sectors": {"switching", "interconnect", "optics"},
        "grow": {"supplies", "co_designs"},
    },
    "hyperscaler-silicon": {
        "label": "Свой чип у покупателя",
        "label_en": "Customers building silicon",
        "description_en": "Buyers who started designing accelerators themselves, and what that "
                           "costs their supplier",
        "description": "Покупатели, которые сами стали проектировать ускорители, и чем "
                       "это грозит их поставщику",
        "sectors": {"hyperscaler"},
        "ids": {"meta", "broadcom", "marvell"},
        # Угроза — это связь, а не свойство узла: тип `threatens` и есть тот самый
        # разворот «клиент становится конкурентом», ради которого группа существует.
        "edge_types": {"threatens"},
    },
    "tpu-ecosystem": {
        "label": "TPU-стек",
        "label_en": "TPU stack",
        "description_en": "Google's vertical end to end: who designs and prints its accelerator, "
                           "who computes on it, and who it still has to buy from",
        "description": "Вертикаль Google целиком: кто проектирует и печатает её "
                       "ускоритель, кто на нём считает и у кого она при этом покупает",
        "ids": {"google", "google-cloud", "google-deepmind", "jax"},
        # Правило пилота обрывалось на четырёх узлах одного владельца и помечалось
        # вырожденным. Причина была в самом правиле: оно набирало только СОБСТВЕННОСТЬ.
        # Стек TPU держится на чужих руках — Broadcom проектирует, TSMC печатает,
        # Anthropic считает, — и эти рёбра в данных есть.
        "linked_to": {"google": {"co_designs", "manufactures", "customer_of", "supplies"},
                      "google-cloud": {"supplies", "customer_of", "enables"},
                      "google-deepmind": {"enables", "supplies"}},
    },
    "memory-hbm": {
        "label": "Память и HBM",
        "label_en": "Memory and HBM",
        "description_en": "The fast-memory triopoly: who makes it, on whose tools, and what it "
                           "feeds",
        "description": "Триополия быстрой памяти: кто её делает, на каких станках и "
                       "кого она кормит",
        "sectors": {"hbm", "dram", "storage"},
        "grow": {"supplies", "co_designs"},
    },
}

# Ниже этого числа узлов подграф считается вырожденным и помечается — но НЕ достраивается.
DEGENERATE_BELOW = 5


def _members(rule, entities, edges):
    sectors = rule.get("sectors") or set()
    layers = rule.get("layers") or set()
    ids = set(rule.get("ids") or ())

    for e in entities:
        if e.get("sector") in sectors or e.get("primaryLayer") in layers:
            ids.add(e["id"])

    for x in edges:
        if x["type"] in (rule.get("edge_types") or set()):
            ids.add(x["source"])
            ids.add(x["target"])

    for hub, types in (rule.get("linked_to") or {}).items():
        for x in edges:
            if x["type"] not in types:
                continue
            if x["source"] == hub:
                ids.add(x["target"])
            elif x["target"] == hub:
                ids.add(x["source"])

    # Ровно ОДИН шаг: ядро фиксируется до расширения, иначе группа расползлась бы по
    # всей сети и перестала отвечать на свой вопрос.
    grow = rule.get("grow") or set()
    if grow:
        core = set(ids)
        for x in edges:
            if x["type"] not in grow:
                continue
            if x["source"] in core:
                ids.add(x["target"])
            if x["target"] in core:
                ids.add(x["source"])

    return (ids - set(rule.get("exclude_ids") or ())) & {e["id"] for e in entities}


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
        # Узел без единой внутренней связи виден на карте как одинокая точка. Правило
        # его привело — значит, по положению он в группе; но читателю честнее сказать.
        inside = set(edge_ids)
        touched = set()
        for x in edges:
            if x["id"] in inside:
                touched.add(x["source"])
                touched.add(x["target"])
        isolated = [i for i in node_ids if i not in touched]
        if isolated:
            notes.append(f"{sid}: без внутренних связей — {', '.join(isolated)}")
        out.append({"id": sid, "label": rule["label"],
                    "label_en": rule.get("label_en"),
                    "description": rule["description"],
                    "description_en": rule.get("description_en"),
                    "nodeIds": node_ids, "edgeIds": edge_ids,
                    "degenerate": degenerate})
    return {"subgraphs": out, "notes": notes}
