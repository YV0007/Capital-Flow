# ЭКОСИСТЕМА NVIDIA — 2026-08

Якорь: **nvidia**. 106 сущностей, 243 связей, 146 контуров, 10 тех-узлов. Сгенерировано 2026-08-23, схема `nvidia-ecosystem/2`.

## Состояние
- Подтверждённых связей: **224** из 243 (92%).
- С первичным источником (тир 1–3): **243** (100%).
- Мёртвых ссылок: **0**.
- Блёкнущих сущностей: **0**.

## Связи по хребтам
| хребет | связей |
|---|---|
| physical | 92 |
| capital | 59 |
| moat | 45 |
| rivalry | 27 |
| control | 20 |

## Добавлено (7)
- **edge** `eu__eu-ai-act__standardizes_on` — Регламент — инструмент, которым блок задаёт правила для рынка ИИ.
- **edge** `microsoft__blackrock__funded_by` — Инфраструктурный капитал финансирует площадки и энергию под облачные мощности.
- **edge** `nventures__nvidia__funded_by` — Венчурное подразделение якоря: инструмент управления собственным риском, а не портфель ради доходности.
- **edge** `nvidia__kubernetes__standardizes_on` — Отраслевой стандарт запуска контейнеров: совместимость с ним обязательна для любого поставщика ускорителей.
- **edge** `pytorch__meta__funded_by` — Библиотеку создала компания-покупатель ускорителей и передала независимому фонду.
- **edge** `tsmc__arm__standardizes_on` — Более 350 миллиардов выпущенных чипов используют эту архитектуру — общий знаменатель для фабрик.
- **edge** `usa__chips-act__standardizes_on` — Закон — инструмент, которым юрисдикция возвращает производство внутрь страны.

## Отвалилось (7)
- **edge** `arm__tsmc__standardizes_on` — связь больше не заявлена
- **edge** `blackrock__microsoft__funded_by` — связь больше не заявлена
- **edge** `chips-act__usa__standardizes_on` — связь больше не заявлена
- **edge** `eu-ai-act__eu__standardizes_on` — связь больше не заявлена
- **edge** `kubernetes__nvidia__standardizes_on` — связь больше не заявлена
- **edge** `meta__pytorch__funded_by` — связь больше не заявлена
- **edge** `nvidia__nventures__funded_by` — связь больше не заявлена

## Изменилось
— ничего.

## Замкнутые контуры
- `c1` **lockin** — cuda → pytorch → nvidia → cuda
- `c2` **lockin** — cuda → nvidia → microsoft → cuda
- `c3` **financing** — microsoft → nvidia → openai → microsoft
- `c4` **sales** — coreweave → nvidia → microsoft → coreweave
- `c5` **lockin** — cuda → nvidia → tsmc → cuda
- `c6` **sales** — broadcom → nvidia → tsmc → broadcom
- `c7` **financing** — nvidia → openai → oracle → nvidia
- `c8` **sales** — astera-labs → nvidia → tsmc → astera-labs
- `c9` **sales** — broadcom → google → nvidia → broadcom
- `c10` **lockin** — cuda → huggingface → nvidia → cuda
- `c11` **lockin** — cuda → huggingface → pytorch → cuda
- `c12` **lockin** — cuda → pytorch → meta → cuda
