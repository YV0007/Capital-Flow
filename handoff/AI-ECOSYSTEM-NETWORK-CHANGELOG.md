# СЕТЬ ИИ-ИНФРАСТРУКТУРЫ — v4.0-2026-08

108 сущностей (30 пивотов, 78 вторичных), 263 связей. Схема `ai-ecosystem-network/4`, сгенерировано 2026-08-29.

## Топология
- Плотность: **0.0353** · средняя степень: **3.78** · кластеризация: **0.4977**.
- Точек отказа найдено: **11**.
- Подграфов: **12** (0 вырожденных).

## Центральность — три меры, три разных вопроса

`degree` — со сколькими связан · `betweenness` — через кого идут пути · `pagerank` — на кого опираются те, на кого опираются сами.

### По betweenness — кто держит пути

| сущность | degree | betweenness | pagerank | пивот |
|---|---|---|---|---|
| NVIDIA | 74 | 0.831789 | 0.157531 | да |
| TSMC | 20 | 0.150539 | 0.020434 | да |
| Microsoft | 17 | 0.095878 | 0.00975 | да |
| OpenAI | 12 | 0.068172 | 0.01761 | да |
| Anthropic | 8 | 0.035807 | 0.00659 | да |
| Equinix | 6 | 0.034356 | 0.01669 | да |
| CUDA | 12 | 0.03306 | 0.017312 | да |
| vLLM | 8 | 0.022523 | 0.006409 | да |
| Samsung | 5 | 0.020234 | 0.007664 | да |
| Oracle | 5 | 0.019558 | 0.010192 | да |

### По pagerank — на кого опирается сеть

| сущность | degree | betweenness | pagerank | пивот |
|---|---|---|---|---|
| NVIDIA | 74 | 0.831789 | 0.157531 | да |
| TSMC | 20 | 0.150539 | 0.020434 | да |
| Fabrinet | 3 | 0.008029 | 0.017617 | — |
| OpenAI | 12 | 0.068172 | 0.01761 | да |
| Lam Research | 4 | 0.001716 | 0.017436 | — |
| CUDA | 12 | 0.03306 | 0.017312 | да |
| Equinix | 6 | 0.034356 | 0.01669 | да |
| Vertiv | 4 | 0.009081 | 0.01669 | да |
| Oklo | 2 | 8.8e-05 | 0.015867 | — |
| SoftBank | 4 | 0.004866 | 0.015825 | да |

## Точки отказа

- **NVIDIA** (L10, betweenness 0.831789) — {'ru': 'убрать — и 2100 пар сущностей (37.0% связных пар) теряют путь друг к другу; сеть распадается на 22 части', 'en': 'remove it and 2100 pairs of entities (37.0% of connected pairs) lose their path to each other; the network breaks into 22 components'}
- **TSMC** (L3, betweenness 0.150539) — {'ru': 'убрать — и 717 пар сущностей (12.6% связных пар) теряют путь друг к другу; сеть распадается на 5 частей', 'en': 'remove it and 717 pairs of entities (12.6% of connected pairs) lose their path to each other; the network breaks into 5 components'}
- **Microsoft** (L9, betweenness 0.095878) — {'ru': 'убрать — и 211 пар сущностей (3.7% связных пар) теряют путь друг к другу; сеть распадается на 3 части', 'en': 'remove it and 211 pairs of entities (3.7% of connected pairs) lose their path to each other; the network breaks into 3 components'}
- **OpenAI** (L12, betweenness 0.068172) — {'ru': 'убрать — и 211 пар сущностей (3.7% связных пар) теряют путь друг к другу; сеть распадается на 3 части', 'en': 'remove it and 211 pairs of entities (3.7% of connected pairs) lose their path to each other; the network breaks into 3 components'}
- **Equinix** (L9, betweenness 0.034356) — {'ru': 'убрать — и 106 пар сущностей (1.9% связных пар) теряют путь друг к другу; сеть распадается на 2 части', 'en': 'remove it and 106 pairs of entities (1.9% of connected pairs) lose their path to each other; the network breaks into 2 components'}
- **vLLM** (L11, betweenness 0.022523) — {'ru': 'убрать — и 106 пар сущностей (1.9% связных пар) теряют путь друг к другу; сеть распадается на 2 части', 'en': 'remove it and 106 pairs of entities (1.9% of connected pairs) lose their path to each other; the network breaks into 2 components'}
- **Samsung** (L4, betweenness 0.020234) — {'ru': 'через узел проходит больше путей, чем через любого другого в слое L4 (betweenness 0.020234), но обходные маршруты сохраняются — связность сети он не держит', 'en': 'more paths run through this node than through any other in layer L4 (betweenness 0.020234), but detours survive — it does not hold the network together'}
- **ASML** (L1, betweenness 0.018692) — {'ru': 'убрать — и 106 пар сущностей (1.9% связных пар) теряют путь друг к другу; сеть распадается на 2 части', 'en': 'remove it and 106 pairs of entities (1.9% of connected pairs) lose their path to each other; the network breaks into 2 components'}
- **Databricks** (L13, betweenness 0.018692) — {'ru': 'убрать — и 106 пар сущностей (1.9% связных пар) теряют путь друг к другу; сеть распадается на 2 части', 'en': 'remove it and 106 pairs of entities (1.9% of connected pairs) lose their path to each other; the network breaks into 2 components'}
- **Supermicro** (L5, betweenness 0.018692) — {'ru': 'убрать — и 106 пар сущностей (1.9% связных пар) теряют путь друг к другу; сеть распадается на 2 части', 'en': 'remove it and 106 pairs of entities (1.9% of connected pairs) lose their path to each other; the network breaks into 2 components'}
- **Arista Networks** (L8, betweenness 0.010857) — {'ru': 'через узел проходит больше путей, чем через любого другого в слое L8 (betweenness 0.010857), но обходные маршруты сохраняются — связность сети он не держит', 'en': 'more paths run through this node than through any other in layer L8 (betweenness 0.010857), but detours survive — it does not hold the network together'}

## Подграфы

- **{'ru': 'GPU-стек', 'en': 'GPU stack'}**: 22 узлов, 65 внутренних связей. {'ru': 'Обучение и инференс на GPU: ускорители, среда программирования, библиотеки и покупатели-гиперскейлеры', 'en': 'Training and inference on GPUs: the accelerators, the programming environment, the libraries and the hyperscalers buying them'}.
- **{'ru': 'Хребет инфраструктуры', 'en': 'Infrastructure backbone'}**: 45 узлов, 26 внутренних связей. {'ru': 'Производство и геополитика, общие для обоих стеков: фабрики, станки, софт проектирования, юрисдикции и капитал', 'en': 'The manufacturing and geopolitics common to both stacks: fabs, tools, design software, jurisdictions and capital'}.
- **{'ru': 'Экспортный контроль', 'en': 'Export control'}**: 23 узлов, 44 внутренних связей. {'ru': 'Кто и через какой документ решает, кому разрешено продавать и покупать передовые чипы', 'en': 'Who decides, and through which instrument, that advanced chips may be sold and bought'}.
- **{'ru': 'Энергия и охлаждение', 'en': 'Power and cooling'}**: 21 узлов, 42 внутренних связей. {'ru': 'Физическая стройка дата-центра: генерация, передача тока, охлаждение и питание стоек — и кто всё это потребляет', 'en': 'The physical datacenter build-out: generation, transmission, cooling and rack power — and everyone drawing on it'}.
- **{'ru': 'Лаборатории и их облака', 'en': 'Labs and their clouds'}**: 17 узлов, 64 внутренних связей. {'ru': 'На чьей мощности обучается каждая передовая лаборатория и чем она за это платит', 'en': 'Whose compute each frontier lab trains on, and what it pays for the privilege'}.
- **{'ru': 'Цепочка литографии', 'en': 'Lithography chain'}**: 16 узлов, 30 внутренних связей. {'ru': 'Кого физически нельзя заменить при изготовлении передового кристалла — от станка и пластины до упаковки', 'en': 'Who physically cannot be replaced in making a leading-edge die — from the tool and the wafer through to packaging'}.
- **{'ru': 'Открытый стек против CUDA', 'en': 'Open stack versus CUDA'}**: 13 узлов, 33 внутренних связей. {'ru': 'Насколько реален выход из среды программирования NVIDIA: чем именно её замещают и что этому мешает', 'en': "How real the exit from NVIDIA's programming environment is: what replaces it, and what stands in the way"}.
- **{'ru': 'Капитал стройки', 'en': 'Capital behind the build'}**: 17 узлов, 41 внутренних связей. {'ru': 'Кто оплачивает стек — венчур и стратегический капитал — и что именно куплено на эти деньги', 'en': 'Who pays for the stack — venture and strategic capital — and what the money bought'}.
- **{'ru': 'Сети и оптика', 'en': 'Networking and optics'}**: 12 узлов, 25 внутренних связей. {'ru': 'Вторая половина дата-центра: коммутация, межсоединения и оптика, связывающие ускорители в кластер', 'en': 'The other half of a datacenter: the switching, interconnect and optics that bind accelerators into a cluster'}.
- **{'ru': 'Свой чип у покупателя', 'en': 'Customers building silicon'}**: 11 узлов, 25 внутренних связей. {'ru': 'Покупатели, которые сами стали проектировать ускорители, и чем это грозит их поставщику', 'en': 'Buyers who started designing accelerators themselves, and what that costs their supplier'}.
- **{'ru': 'TPU-стек', 'en': 'TPU stack'}**: 8 узлов, 23 внутренних связей. {'ru': 'Вертикаль Google целиком: кто проектирует и печатает её ускоритель, кто на нём считает и у кого она при этом покупает', 'en': "Google's vertical end to end: who designs and prints its accelerator, who computes on it, and who it still has to buy from"}.
- **{'ru': 'Память и HBM', 'en': 'Memory and HBM'}**: 8 узлов, 12 внутренних связей. {'ru': 'Триополия быстрой памяти: кто её делает, на каких станках и кого она кормит', 'en': 'The fast-memory triopoly: who makes it, on whose tools, and what it feeds'}.
  - infrastructure-backbone: без внутренних связей — a16z, amkor, ase, blackrock, blackstone, bloom-energy, china, eaton, ge-vernova, lightspeed, nventures, oklo, schneider, sequoia, siemens-eda, siemens-energy, singapore, south-korea, thrive

## Изменения по десяти категориям блюпринта

| категория | записей |
|---|---|
| новые узлы | 1 |
| удалённые узлы | 0 |
| связи + | 1 |
| связи − | 0 |
| связи ~ | 72 |
| сдвиг критичности >5 | 35 |
| смена фазы | 0 |
| эскалация риска | 0 |
| новые источники | 0 |
| смена слоя | 0 |
| вход/выход из ядра | 23 |

## Вход и выход из ядра (13 / 10)

Ядро вычисляется, а не назначается: top-30 by integration. Движение состава — такая же находка карты, как новая связь.

**Вошли.**

- `broadcom` — интеграция 12
- `coreweave` — интеграция 11
- `crusoe` — интеграция 9
- `databricks` — интеграция 9
- `digital-realty` — интеграция 10
- `equinix` — интеграция 12
- `nventures` — интеграция 11
- `oracle` — интеграция 13
- `samsung` — интеграция 12
- `sk-hynix` — интеграция 10
- `softbank` — интеграция 11
- `usa` — интеграция 9
- `vertiv` — интеграция 12

**Вышли.**

- `amd` — интеграция 8, опустился ниже порога ядра
- `asml` — интеграция 6, опустился ниже порога ядра
- `bis` — интеграция 7, опустился ниже порога ядра
- `brookfield` — интеграция 8, опустился ниже порога ядра
- `cadence` — интеграция 7, опустился ниже порога ядра
- `google-cloud` — интеграция 7, опустился ниже порога ядра
- `jax` — интеграция 7, опустился ниже порога ядра
- `synopsys` — интеграция 9, опустился ниже порога ядра
- `taiwan` — интеграция 8, опустился ниже порога ядра
- `xai` — интеграция 5, опустился ниже порога ядра

## Добавленные связи (1)

- `zeiss-smt__asml__supplies` — {'ru': 'Единственный поставщик оптики для станков, с эксклюзивным соглашением. Ограничение лежит выше самого производителя станков.', 'en': 'The sole supplier of optics for the machines, under an exclusive agreement. The constraint sits above the machine maker itself.'}
