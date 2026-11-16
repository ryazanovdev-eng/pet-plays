# MCP-серверы

Документ описывает, какие MCP-серверы подключены, как их запускать и как проверять. MCP — это протокол, по которому Kilo получает инструменты внешних программ.

## 1. Что подключено

| Сервер | Назначение | Статус |
|---|---|---|
| `blender` | 3D-сцена, low-poly, материалы, рендеры, импорт ассетов | включён, проверен на живой сцене |
| `godot` | запуск редактора и проекта, debug-вывод, сцены и узлы | включён, проверен |
| `fal` | изображения, видео, музыка, аудио через fal.ai | проверен: изображение и 18 инструментов |

Конфиг: `kilo.json` в корне проекта. Секреты в проектный конфиг не кладём — только в глобальный `C:\Users\Dima\.config\kilo\kilo.jsonc`.

## 2. Blender MCP

Требования:

- Blender 5.3;
- аддон `blender_mcp.py` в `%APPDATA%\Blender Foundation\Blender\5.3\scripts\addons`;
- `uvx.exe` по пути из `kilo.json`.

Порядок запуска:

1. Открыть Blender.
2. **Edit → Preferences → Add-ons** → включить **Interface: MCP for Blender**.
3. В 3D-вьюпорте нажать `N` → вкладка **MCP for Blender** → **Start MCP Server** (порт 9876).
4. Перезагрузить окно VS Code, если менялся `kilo.json`.
5. Проверить `/mcps`.

Проверка без Kilo:

```powershell
python tools\mcp_probe.py --name blender --call get_scene_info `
  "C:\Users\Dima\AppData\Local\Microsoft\WinGet\Packages\astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe\uvx.exe" `
  --python 3.11 mcp-for-blender
```

Если Blender закрыт, сервер запустится, но инструменты не смогут подключиться к сцене. Это нормально.

Проверено 15.11.2026: сервер `MCP for Blender 1.30.0`, аддон 2.0, протокол 16, Blender 5.3.0. Сервер поднимается автоматически при открытии Blender, порт 9876 слушается. `get_scene_info` вернул Cube, Light, Camera; `look` вернул скриншот viewport.

Кнопка **Start MCP Server** нужна только если сервер остановлен вручную. В обычном запуске она не требуется.

### Где найти панель

- В 3D-вьюпорте нажать `N` — откроется боковая панель.
- Вкладки находятся вертикально у правого края: ищи **MCP** или **MCP for Blender**.
- Если вкладки не видно: убедись, что активен именно 3D Viewport, а не Outliner/Properties, и расширь панель мышью.
- Настройки и кнопка запуска: **Edit → Preferences → Add-ons → Interface: MCP for Blender**.

Библиотеки Poly Haven, Sketchfab, Poly Pizza и генераторы Tripo/Meshy/Hunyuan3D/Rodin сейчас выключены. Они включаются в панели аддона, когда понадобятся.

Безопасность:

- `BLENDER_MCP_SAFE_MODE=1` проверяет скрипты перед выполнением.
- `DISABLE_TELEMETRY=true` выключает телеметрию.
- Порт 9876 не выставлять наружу: у него нет авторизации.
- Перед экспериментами сохранить `.blend` и закоммитить проект.

## 3. Godot MCP

Требования:

- Node.js 18+ (у нас 26);
- `GODOT_PATH` указывает на `Godot_v4.7.2-stable_win64.exe`;
- первый запуск `npx` скачивает пакет, нужен интернет.

Проверка без Kilo:

```powershell
python tools\mcp_probe.py --name godot --call get_godot_version -- cmd /c npx -y @coding-solo/godot-mcp
```

Что умеет: запускать редактор и проект, читать debug-вывод, создавать сцены и узлы, работать с UID.

Проверено 15.11.2026: `godot-mcp 0.1.0`, 14 инструментов. `get_godot_version` вернул `4.7.2.stable.official.ed1daf0bf`, `get_project_info` увидел проект `pet-plays`, `create_scene` + `add_node` создали сцену с `Label` (после проверки сцена удалена).

Практическая деталь: `create_scene` принимает `res://game/scene.tscn`, а `add_node` ждёт путь относительно проекта — `game/scene.tscn`. Если передать `res://`, инструмент ответит «Scene file does not exist».

Осторожно: сервер может менять `.tscn`. Перед изменениями сцен делать коммит. Источник правды по сборке — `.\tools\check.cmd`.

## 4. Пробник MCP

`tools/mcp_probe.py` запускает любой stdio-MCP-сервер, делает `initialize`, `tools/list` и при желании вызывает инструмент.

```powershell
python tools\mcp_probe.py --name godot -- cmd /c npx -y @coding-solo/godot-mcp
python tools\mcp_probe.py --name godot --call get_godot_version -- cmd /c npx -y @coding-solo/godot-mcp
```

Вывод: имя сервера, версия протокола, список инструментов и результат вызова. Скрипт не зависит от Kilo и подходит для диагностики.

## 4.1. Проверка в Kilo

1. Command Palette → **Developer: Reload Window**.
2. Открыть `/mcps`, если команда доступна. В VS Code-расширении её может не быть: `/mcps` — команда CLI/TUI. Тогда проверяй по факту: доступны ли инструменты `blender_*`, `godot_*`, `fal_*`.
3. Godot: попросить «Получи версию Godot через Godot MCP».
4. Blender: открыть Blender, включить аддон и сервер, затем попросить «Покажи информацию о сцене Blender».
5. Если инструменты не появились — проверить пробником из раздела 4 и посмотреть вывод MCP в Kilo.

## 4.2. Пробная цепочка ассета

15.11.2026 проверена полная цепочка: промт → изображение → low-poly модель в Blender через MCP → `.glb` → импорт в Godot. Результат: `assets/models/probe_character.glb`, 592 полигона, ~1032 треугольника, сцена `game/probe/probe_character.tscn`, headless-запуск без ошибок. Подробности — `docs/qa/2026-11-15-m0-mcp.md`.

AI-генераторы 3D в аддоне выключены: Tripo, Meshy, Hunyuan3D, Rodin требуют ключей или Premium. Для теста модель собрана процедурно из примитивов.

## 5. Windows-нюансы

- `uvx` и `npx` — это `.cmd`/`.exe`. Если Kilo не находит команду, используй полный путь или обёртку `cmd /c`.
- VS Code наследует PATH при запуске. После установки uv **полностью закрой и открой VS Code**, обычный reload не поможет.
- После правки `kilo.json`: Command Palette → **Developer: Reload Window**.
- Проверить серверы: `/mcps`.

## 6. Выключить сервер

В `kilo.json`:

```json
"enabled": false
```

Или через `/mcps` в интерфейсе. Держи включёнными только те серверы, которые нужны сейчас: каждый добавляет инструменты в контекст.

## 7. fal.ai

Статус: сервер проверен с настоящим ключом. Пакет `fal-mcp-server` 1.18.0, 18 инструментов. Сгенерировано изображение скелета-солдата: 512x512, `fal-ai/flux/schnell`, ≈$0.0008.

### Куда класть токен

Токен уже вставлен в глобальный `C:\Users\Dima\.config\kilo\kilo.jsonc`, поле `mcp.fal.environment.FAL_KEY`. Сервер включён. В проектном `kilo.json` ключей нет и быть не должно.

Если нужно сменить токен: открыть этот файл, заменить значение `FAL_KEY`, сохранить и выполнить Command Palette → **Developer: Reload Window**. Если инструменты не появились — полностью закрыть и открыть VS Code.

### Команда запуска

```json
"fal": {
  "type": "local",
  "command": [
    "C:\\Users\\Dima\\AppData\\Local\\Microsoft\\WinGet\\Packages\\astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe\\uvx.exe",
    "--python", "3.11",
    "--from", "fal-mcp-server",
    "--with", "mcp<2",
    "fal-mcp"
  ],
  "environment": {
    "UV_PYTHON_PREFERENCE": "only-managed",
    "FAL_KEY": "<твой токен>"
  },
  "enabled": true,
  "timeout": 600000
}
```

`--with "mcp<2"` обязателен: без него сервер падает на `mcp 2.x` с `AttributeError: 'Server' object has no attribute 'list_tools'`.

### Что умеет

18 инструментов: генерация и редактирование изображений, видео, музыка, аудио, `get_pricing`, `get_usage`, `upload_file`, `list_models`.

Проверено: `generate_image` с `fal-ai/flux/schnell`, 512x512, seed 424242. Изображение скачано в `docs/art/raw/fal-skeleton-soldier-424242.png`.

3D-генерации в этом MCP нет. 3D остаётся за Blender MCP: процедурные модели, Poly Pizza/Poly Haven или встроенные Tripo/Meshy/Hunyuan/Rodin.

### Бюджет

Лимит проекта — **$5 на fal.ai** (ADR-001). Перед платной генерацией вызывай `fal_get_pricing`, после — `fal_get_usage`. Дорогие модели (видео, Meshy) — только с явного согласования. Если в кабинете fal есть жёсткий лимит, поставь его там: это единственная гарантия, не зависящая от агента.

Потрачено на первый тест: **≈$0.0008** (512x512, flux/schnell). `fal_get_usage` требует admin-ключ; с обычным ключом возвращает `Access denied`, поэтому расход считается по прайсу и проверяется в кабинете fal.

### Ограничение

Глобальный конфиг действует на все проекты. Если нужно, чтобы fal был только в pet-plays, позже переедем на локальный `.env` и обёртку `tools/fal-mcp.cmd`.

## 8. Правила

- Один сервер — одна зона ответственности. Не давать Blender и Godot MCP править одни и те же сцены одновременно.
- Все MCP-инструменты в `permission` стоят на `ask`.
- Не коммитить ключи.
- После изменений через MCP всегда запускать `.\tools\check.cmd`.
- Если сервер сломался, сначала проверить его пробником, потом лезть в Kilo.
