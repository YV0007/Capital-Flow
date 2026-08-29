# ЭКОСИСТЕМА ИИ-ИНФРАСТРУКТУРЫ — 2026-08

107 сущностей, 270 связей, 197 контуров, 10 тех-узлов. Сгенерировано 2026-08-29, схема `nvidia-ecosystem/4`.

## Состояние
- Подтверждённых связей: **232** из 270 (86%).
- С первичным источником (тир 1–3): **270** (100%).
- Мёртвых ссылок: **0**.
- Блёкнущих сущностей: **0**.

## Связи по хребтам
| хребет | связей |
|---|---|
| physical | 97 |
| capital | 66 |
| moat | 47 |
| rivalry | 40 |
| control | 20 |

## Добавлено (5)
- **edge** `amd__hpe__supplies` — Названа HPE поставщиком процессоров x86 наравне с Intel.
- **edge** `broadcom__hpe__supplies` — Названа HPE поставщиком стандартных микросхем и единственным источником для рынка целиком.
- **edge** `ge-vernova__crusoe__supplies` — Газовая турбина LM2500XPRESS питает дата-центр Crusoe как быстрый резервный источник.
- **edge** `intel__hpe__supplies` — Названа HPE поставщиком процессоров x86 и одновременно единственным источником для рынка целиком.
- **edge** `sandisk__kioxia__strategic_partner` — Совместное предприятие Flash Ventures: пока оно работает, обе стороны не вправе выпускать флеш-память с третьими лицами.

## Отвалилось
— ничего.

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
