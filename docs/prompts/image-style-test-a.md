---
id: img-0101
title: Style test A — Cult ink: лягушка-рыцарь на кладбище
category: image
provider: fal
model: fal-ai/flux/dev
size: 1024x576
seed: 20261116
status: test
files: docs/art/raw/20261116-style-test-a.png
created: 2026-11-16
---
PROMPT:
2D game concept art, top-down 3/4 view, fixed orthographic camera at 55 degrees, 16:9. A chubby chibi frog knight: huge round head half his height, two eye bumps, wide crooked mouth, rust-brown helmet and short cloak, bone-white belly, rusty sword in his right hand. Old moonlit cemetery: three leaning gravestones, sagging iron fence, two bare crooked trees, a bone-white skeleton with a club behind him, a legless violet hooded wraith floating to the right. Moonlight upper left, soft baked shadows to the lower right. Seven-color palette: #16232B night, #3A3B33 ground, #7FA75C frog, #EDE3CC bone, #F0A23C lantern glow, #8874B0 wraith, #141210 outlines. Low-contrast painterly background, high-contrast characters, every silhouette readable as one flat color, no text. MANNER: thick even black ink outline, 4-5 px, constant weight around every shape; flat single-tone fills, no gradients, no brush texture on characters, clean vector-like shapes with one flat shadow tone; background gouache reduced to flat color patches.

NEGATIVE:
text, letters, watermark, logo, photorealistic, 3D render, PBR, realistic anatomy, extra limbs, deformed hands, blurry, busy background, neon, gradients, lens flare

NOTES:
Подвариант A, «Cult ink». Отличие: контур одной толщины по всему периметру фигуры, внутри — одна плоская заливка и один плоский теневой тон, гуашь в фоне сведена к плоским пятнам. Что проверяем: даёт ли максимально графичная манера самый чистый силуэт в игровом масштабе и не выглядит ли кадр «дешёвым» при живописном фоне.

Риск читаемости в толпе: минимальный — это самый защищённый вариант. Равномерная толстая линия держит форму даже на 320×180 и не даёт персонажам сливаться. Обратная сторона: мало фактуры, тепло «книжной» иллюстрации почти пропадает, а на 16 врагах кадр может стать плоским и однообразным. Если A выигрывает по читаемости, но проигрывает по настроению — смотреть в сторону B.

Технические заметки: это концепт стиля, не финальный спрайт. Модель fal-ai/flux/dev, 1024x576 (16:9, 0.59 МП; если нужен ~1 МП — 1536x864 тем же кадром). Сид 20261116 общий для A/B/C: меняется только секция MANNER, всё остальное в промте идентично, поэтому разница на картинках — это разница манеры, а не сюжета. Если генерация идёт через fal MCP с пресетами, бери landscape_16_9 и запиши фактический размер в шапку. Названия игр в промт не вставлялись намеренно: описываем признаки, а не бренды.
