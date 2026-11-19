---
id: img-0104
title: Style test C2 — Painted storybook: читаемость силуэта (лягушка, меч, скелет, призрак)
category: image
provider: fal
model: fal-ai/flux/dev
size: 1024x576
seed: 20261117
status: test
files: docs/art/raw/20261117-style-test-c2.png
created: 2026-11-16
---
PROMPT:
2D game concept art, gouache storybook, chibi characters, soft 2–3 px dark ink outline, brush texture inside shapes, moonlit palette (teal, bone, pumpkin orange, blood red, violet), moonlight upper left, readable silhouette, no text, no watermark.

CAMERA: strict top-down game view, camera 55 degrees above the ground looking down, orthographic, no horizon, no sky, no background buildings; the ground fills the frame edge to edge. The frog knight is seen from above at a three-quarter top angle: head and shoulders visible, feet on the ground below him. No side view, no eye-level view, no portrait composition.

Frog knight, huge round head, two eye bumps, wide crooked mouth, rust-brown helmet and short cloak, bone-white belly. He holds a rusty sword in his right hand; the blade clearly extends past his body silhouette. Behind him a bone-white skeleton with a club. Right side: a legless violet hooded wraith, no lantern, empty hands. Old moonlit cemetery ground: leaning gravestones, sagging iron fence, two bare crooked trees, all seen from above.

Rendering: contour 2–3 px; gouache texture only inside shapes; crisp clean silhouette edges; low-contrast painterly background, high-contrast characters. No text.

NEGATIVE:
text, letters, watermark, logo, photorealistic, 3D render, PBR, realistic anatomy, extra limbs, deformed hands, blurry, busy background, neon, gradients, lens flare, lantern, hiding sword, side view, eye-level view, horizon, sky, portrait, cinematic composition, perspective distortion

NOTES:
**Результат:** камера снова не top-down — Flux нарисовал постановочную сцену с горизонтом и небом, несмотря на прямой запрет. Для проверки манеры C кадр годится (контур, гуашь, силуэты, меч виден), для проверки игровой камеры — нет. Ракурс в игре задаёт 3D-камера при рендере спрайтов, а не AI; этот файл не использовать как camera reference.

Уточняющий тест выбранного стиля C. Первый тест (img-0103) проверял, сколько живописи выдерживает игра; этот проверяет уже саму защиту от каши: останется ли силуэт читаемым, когда гуашь разрешена только внутри форм, а край фигуры чистый.

Что проверяем на картинке:
1. **320×180.** Уменьшить кадр и посмотреть заливкой: силуэт лягушки (круглая голова + два бугорка), скелета (череп + рёбра + дубина) и призрака (капля без ног) должны читаться по форме. Если на превью они сливаются с землёй или друг с другом — стиль не готов.
2. **Видимость меча.** Меч — часть силуэта героя и главный предмет игры. Он обязан явно выступать за тело, а не тонуть в плаще или в тени. Это прямая проверка `hiding sword` в NEGATIVE.
3. **Чистый край.** Контур 2–3 px должен быть непрерывным, а мазок — не вылезать за него. Смотрим шею, руку с мечом, низ плаща, край капюшона призрака: там гуашь чаще всего «мылит» силуэт.
4. **Не мылит ли гуашь силуэт.** Внутри форм фактура есть, снаружи её нет. Если фактура перетекает через край и фигура расплывается в фон — это провал теста, а не «живописность».
5. **Призрак без фонаря.** Фонарь — тёплый оранжевый акцент, и модель любит его дорисовывать. В этом кадре у призрака должны быть пустые руки: оранжевый в кадре принадлежит только луту и огню.
6. **Палитра.** Не больше 7 базовых цветов, без новых hue и неона: красный только как сигнал опасности, зелёный только на лягушке.

Технические заметки: это концепт стиля, не финальные спрайты — не просим у модели 8 направлений и не ждём пиксель-перфект контура. Модель `fal-ai/flux/dev`, 1024x576 (16:9). Сид 20261117 отличается от сида серии A/B/C намеренно: кадр другой, и повторять старую композицию смысла нет. Если генерация идёт через fal MCP с пресетами, бери `landscape_16_9` и запиши фактический размер в шапку.

Промт длиннее обычных 40–120 слов, потому что это тест стиля: половину длины занимает anchor, остальное — минимальный состав кадра и три технических требования (контур, гуашь только внутри, чистый край). Для боевых ассетов промт будет короче, а anchor — тот же.
