# Style anchor

- **Статус:** не заполнен
- **Заполняется на этапе:** `/art-style`

## Зачем

Style anchor — это один и тот же блок текста, который добавляется в начало каждого промта. Он держит стиль одинаковым, пока меняются сюжет, поза и композиция.

## Шаблон

```
STYLE ANCHOR:
<2D or 3D game concept art>, <technique>, <shape language>, <palette of 3-5 colors>,
<lighting>, <level of detail>, <camera>, clean readable silhouette, no text, no watermark
```

## Правила

- Не больше 40 слов.
- Только то, что должно повторяться в каждом кадре.
- Не добавляй сюда сюжет и конкретных персонажей.
- При смене стиля обнови этот файл и зафиксируй решение в `docs/decisions/`.

## Текущий anchor

_Пока не выбран._
