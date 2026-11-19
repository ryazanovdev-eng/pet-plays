---
id: img-0102
title: Style test B — Ink & gouache: лягушка-рыцарь на кладбище
category: image
provider: fal
model: fal-ai/flux/dev
size: 1024x576
seed: 20261116
status: test
files: docs/art/raw/20261116-style-test-b.png
created: 2026-11-16
---
PROMPT:
2D game concept art, top-down 3/4 view, fixed orthographic camera at 55 degrees, 16:9. A chubby chibi frog knight: huge round head half his height, two eye bumps, wide crooked mouth, rust-brown helmet and short cloak, bone-white belly, rusty sword in his right hand. Old moonlit cemetery: three leaning gravestones, sagging iron fence, two bare crooked trees, a bone-white skeleton with a club behind him, a legless violet hooded wraith floating to the right. Moonlight upper left, soft baked shadows to the lower right. Seven-color palette: #16232B night, #3A3B33 ground, #7FA75C frog, #EDE3CC bone, #F0A23C lantern glow, #8874B0 wraith, #141210 outlines. Low-contrast painterly background, high-contrast characters, every silhouette readable as one flat color, no text. MANNER: ink contour of varying weight, heaviest on the outer silhouette, thinner inside; light gouache breaking through the character fills; soft two-tone shadows; warm storybook feel; background gouache with visible 6-12 px brush strokes and blended edges.

NEGATIVE:
text, letters, watermark, logo, photorealistic, 3D render, PBR, realistic anatomy, extra limbs, deformed hands, blurry, busy background, neon, gradients, lens flare

NOTES:
Подвариант B, «Ink & gouache». Отличие от A: контур живой, переменной толщины — снаружи толще, внутри тоньше; внутри форм видна лёгкая гуашь, тени двухтоновые и мягкие, в фоне читается мазок. Что проверяем: сохраняется ли читаемость, если линия перестаёт быть равномерной, и появляется ли при этом «книжное» тепло, которого не хватает варианту A.

Риск читаемости в толпе: средний. Переменная линия может «похудеть» в узких местах (шея, рука с мечом, ноги), и на 320×180 эти участки начнут растворяться. Второй риск — гуашевая фактура внутри фигуры на маленьком масштабе превращается в шум и спорит с правилом «силуэт читается одной заливкой». Проверять именно места сужения силуэта и лицо лягушки на 320×180.

Технические заметки: это концепт стиля, не финальный спрайт. Модель fal-ai/flux/dev, 1024x576 (16:9, 0.59 МП; альтернатива ~1 МП — 1536x864). Сид 20261116 общий для A/B/C, меняется только секция MANNER. Если генерация идёт через fal MCP с пресетами, бери landscape_16_9 и запиши фактический размер в шапку. Если B выигрывает, в финальном якоре надо будет явно ограничить фактуру внутри персонажа, иначе при рендере 3D-спрайтов она не воспроизведётся.
