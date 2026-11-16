# Библиотека промтов

Каждый промт — отдельный файл. Файл самодостаточен: по нему можно повторить генерацию без переписки с AI.

## Правила

- Промт — по-английски, заметки — по-русски.
- Один файл — один ассет или одна задача.
- Обязательно: style anchor, модель, размер, сид.
- Имя файла: `<category>-<краткий-slug>.md`, например `image-hero-idle.md`.
- Статусы: `draft`, `approved`, `rejected`.
- После генерации обнови `files` и `seed` в шапке файла.

## Как запустить

```powershell
python tools\gen_image.py --prompt-file docs\prompts\image-hero-idle.md
python tools\gen_image.py --prompt-file docs\prompts\image-hero-idle.md --seed 777 --count 4
```

Скрипт читает из шапки `model`, `size`, `seed`, из секций — `PROMPT` и `NEGATIVE`. Явные аргументы командной строки важнее значений из файла.

## Индекс

| ID | Файл | Что генерирует | Статус |
|---|---|---|---|
| img-0001 | [image-demo-test.md](image-demo-test.md) | Проверка пайплайна: кот-курьер | test |
| img-0002 | [image-probe-character.md](image-probe-character.md) | ProbeBot: робот для теста 3D | test |
| img-0003 | [image-probe-skeleton-soldier.md](image-probe-skeleton-soldier.md) | Скелет-солдат для теста fal и анимации | test |
