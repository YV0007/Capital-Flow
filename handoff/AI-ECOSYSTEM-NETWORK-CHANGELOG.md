# СЕТЬ ИИ-ИНФРАСТРУКТУРЫ — v2.0-2026-08

107 сущностей (27 пивотов, 80 вторичных), 262 связей. Схема `ai-ecosystem-network/2`, сгенерировано 2026-08-27.

## Топология
- Плотность: **0.0358** · средняя степень: **3.79** · кластеризация: **0.5066**.
- Точек отказа найдено: **10**.
- Подграфов: **12** (0 вырожденных).

## Центральность — три меры, три разных вопроса

`degree` — со сколькими связан · `betweenness` — через кого идут пути · `pagerank` — на кого опираются те, на кого опираются сами.

### По betweenness — кто держит пути

| сущность | degree | betweenness | pagerank | пивот |
|---|---|---|---|---|
| NVIDIA | 74 | 0.835431 | 0.158171 | да |
| TSMC | 20 | 0.134718 | 0.020517 | да |
| Microsoft | 17 | 0.096874 | 0.00979 | да |
| OpenAI | 12 | 0.068961 | 0.017681 | да |
| Anthropic | 8 | 0.036139 | 0.006617 | да |
| Equinix | 6 | 0.03468 | 0.016758 | — |
| CUDA | 12 | 0.03229 | 0.017382 | да |
| vLLM | 8 | 0.022773 | 0.006435 | да |
| Samsung | 5 | 0.02044 | 0.007695 | — |
| Oracle | 5 | 0.019751 | 0.010233 | — |

### По pagerank — на кого опирается сеть

| сущность | degree | betweenness | pagerank | пивот |
|---|---|---|---|---|
| NVIDIA | 74 | 0.835431 | 0.158171 | да |
| TSMC | 20 | 0.134718 | 0.020517 | да |
| Fabrinet | 3 | 0.008092 | 0.017689 | — |
| OpenAI | 12 | 0.068961 | 0.017681 | да |
| Lam Research | 4 | 0.001569 | 0.017507 | — |
| CUDA | 12 | 0.03229 | 0.017382 | да |
| Equinix | 6 | 0.03468 | 0.016758 | — |
| Vertiv | 4 | 0.009164 | 0.016758 | — |
| Oklo | 2 | 9e-05 | 0.015932 | — |
| SoftBank | 4 | 0.004898 | 0.015889 | — |

## Точки отказа

- **NVIDIA** (L10, betweenness 0.835431) — {'ru': 'убрать — и 2078 пар сущностей (37.3% связных пар) теряют путь друг к другу; сеть распадается на 22 части', 'en': 'remove it and 2078 pairs of entities (37.3% of connected pairs) lose their path to each other; the network breaks into 22 components'}
- **TSMC** (L3, betweenness 0.134718) — {'ru': 'убрать — и 613 пар сущностей (11.0% связных пар) теряют путь друг к другу; сеть распадается на 5 частей', 'en': 'remove it and 613 pairs of entities (11.0% of connected pairs) lose their path to each other; the network breaks into 5 components'}
- **Microsoft** (L9, betweenness 0.096874) — {'ru': 'убрать — и 209 пар сущностей (3.8% связных пар) теряют путь друг к другу; сеть распадается на 3 части', 'en': 'remove it and 209 pairs of entities (3.8% of connected pairs) lose their path to each other; the network breaks into 3 components'}
- **OpenAI** (L12, betweenness 0.068961) — {'ru': 'убрать — и 209 пар сущностей (3.8% связных пар) теряют путь друг к другу; сеть распадается на 3 части', 'en': 'remove it and 209 pairs of entities (3.8% of connected pairs) lose their path to each other; the network breaks into 3 components'}
- **Equinix** (L9, betweenness 0.03468) — {'ru': 'убрать — и 105 пар сущностей (1.9% связных пар) теряют путь друг к другу; сеть распадается на 2 части', 'en': 'remove it and 105 pairs of entities (1.9% of connected pairs) lose their path to each other; the network breaks into 2 components'}
- **vLLM** (L11, betweenness 0.022773) — {'ru': 'убрать — и 105 пар сущностей (1.9% связных пар) теряют путь друг к другу; сеть распадается на 2 части', 'en': 'remove it and 105 pairs of entities (1.9% of connected pairs) lose their path to each other; the network breaks into 2 components'}
- **Samsung** (L4, betweenness 0.02044) — {'ru': 'через узел проходит больше путей, чем через любого другого в слое L4 (betweenness 0.02044), но обходные маршруты сохраняются — связность сети он не держит', 'en': 'more paths run through this node than through any other in layer L4 (betweenness 0.02044), but detours survive — it does not hold the network together'}
- **Databricks** (L13, betweenness 0.018868) — {'ru': 'убрать — и 105 пар сущностей (1.9% связных пар) теряют путь друг к другу; сеть распадается на 2 части', 'en': 'remove it and 105 pairs of entities (1.9% of connected pairs) lose their path to each other; the network breaks into 2 components'}
- **Supermicro** (L5, betweenness 0.018868) — {'ru': 'убрать — и 105 пар сущностей (1.9% связных пар) теряют путь друг к другу; сеть распадается на 2 части', 'en': 'remove it and 105 pairs of entities (1.9% of connected pairs) lose their path to each other; the network breaks into 2 components'}
- **Arista Networks** (L8, betweenness 0.010974) — {'ru': 'через узел проходит больше путей, чем через любого другого в слое L8 (betweenness 0.010974), но обходные маршруты сохраняются — связность сети он не держит', 'en': 'more paths run through this node than through any other in layer L8 (betweenness 0.010974), but detours survive — it does not hold the network together'}

## Подграфы

- **{'ru': 'GPU-стек', 'en': 'GPU stack'}**: 22 узлов, 65 внутренних связей. {'ru': 'Обучение и инференс на GPU: ускорители, среда программирования, библиотеки и покупатели-гиперскейлеры', 'en': 'Training and inference on GPUs: the accelerators, the programming environment, the libraries and the hyperscalers buying them'}.
- **{'ru': 'Хребет инфраструктуры', 'en': 'Infrastructure backbone'}**: 44 узлов, 25 внутренних связей. {'ru': 'Производство и геополитика, общие для обоих стеков: фабрики, станки, софт проектирования, юрисдикции и капитал', 'en': 'The manufacturing and geopolitics common to both stacks: fabs, tools, design software, jurisdictions and capital'}.
- **{'ru': 'Экспортный контроль', 'en': 'Export control'}**: 23 узлов, 44 внутренних связей. {'ru': 'Кто и через какой документ решает, кому разрешено продавать и покупать передовые чипы', 'en': 'Who decides, and through which instrument, that advanced chips may be sold and bought'}.
- **{'ru': 'Энергия и охлаждение', 'en': 'Power and cooling'}**: 21 узлов, 42 внутренних связей. {'ru': 'Физическая стройка дата-центра: генерация, передача тока, охлаждение и питание стоек — и кто всё это потребляет', 'en': 'The physical datacenter build-out: generation, transmission, cooling and rack power — and everyone drawing on it'}.
- **{'ru': 'Лаборатории и их облака', 'en': 'Labs and their clouds'}**: 17 узлов, 64 внутренних связей. {'ru': 'На чьей мощности обучается каждая передовая лаборатория и чем она за это платит', 'en': 'Whose compute each frontier lab trains on, and what it pays for the privilege'}.
- **{'ru': 'Цепочка литографии', 'en': 'Lithography chain'}**: 15 узлов, 29 внутренних связей. {'ru': 'Кого физически нельзя заменить при изготовлении передового кристалла — от станка и пластины до упаковки', 'en': 'Who physically cannot be replaced in making a leading-edge die — from the tool and the wafer through to packaging'}.
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
| новые узлы | 0 |
| удалённые узлы | 0 |
| связи + | 0 |
| связи − | 0 |
| связи ~ | 0 |
| сдвиг критичности >5 | 0 |
| смена фазы | 0 |
| эскалация риска | 0 |
| новые источники | 0 |
| смена слоя | 0 |
