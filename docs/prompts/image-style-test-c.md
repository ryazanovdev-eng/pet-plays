---
id: img-0103
title: Style test C — Painted storybook: лягушка-рыцарь на кладбище
category: image
provider: fal
model: fal-ai/flux/dev
size: 1024x576
seed: 20261116
status: test
files: docs/art/raw/20261116-style-test-c.png
created: 2026-11-16
---
PROMPT:
2D game concept art, top-down 3/4 view, fixed orthographic camera at 55 degrees, 16:9. A chubby chibi frog knight: huge round head half his height, two eye bumps, wide crooked mouth, rust-brown helmet and short cloak, bone-white belly, rusty sword in his right hand. Old moonlit cemetery: three leaning gravestones, sagging iron fence, two bare crooked trees, a bone-white skeleton with a club behind him, a legless violet hooded wraith floating to the right. Moonlight upper left, soft baked shadows to the lower right. Seven-color palette: #16232B night, #3A3B33 ground, #7FA75C frog, #EDE3CC bone, #F0A23C lantern glow, #8874B0 wraith, #141210 outlines. Low-contrast painterly background, high-contrast characters, every silhouette readable as one flat color, no text. MANNER: thin 1-2 px contour, characters painted in loose gouache like a storybook plate, soft blended edges, rich visible texture across sky, ground and figures, gentle color variation inside each shape, gentle value transitions instead of hard shadow steps.

NEGATIVE:
text, letters, watermark, logo, photorealistic, 3D render, PBR, realistic anatomy, extra limbs, deformed hands, blurry, busy background, neon, gradients, lens flare

NOTES:
Подвариант C, «Painted storybook». Отличие от A и B: контур почти исчезает (1–2 px), персонажи написаны той же гуашью, что и фон, края мягкие, фактура богатая по всему кадру. Что проверяем: сколько живописи выдерживает игра, не теряя главный приём — толстый контур как защиту от каши. Это вариант «самый красивый на скриншоте», и его надо честно проверить на 320×180, а не любоваться в полном размере.

Риск читаемости в толпе: высокий. Тонкая линия и мягкие края означают, что персонаж перестаёт отделяться от фона контрастом техники: при 16 врагах силуэты начнут слипаться, а тёмная лягушка на тёмной земле потребует постоянной светлой кромки. Если C выбирают, контур героя всё равно придётся вернуть к 4–5 px — то есть C тестирует не толщину линии, а степень живописности фона и персонажа.

Технические заметки: это концепт стиля, не финальные спрайты. Модель fal-ai/flux/dev, 1024x576 (16:9, 0.59 МП; альтернатива ~1 МП — 1536x864). Сид 20261116 общий для A/B/C, меняется только секция MANNER. Если генерация идёт через fal MCP с пресетами, бери landscape_16_9 и запиши фактический размер в шапку. У C самый большой риск, что модель уйдёт в «иллюстрацию без контура вообще» — это тоже результат теста, его фиксируем, а не перегенерируем до победного.
