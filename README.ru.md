# speech2md

**Аудио → читаемые Markdown-заметки. Локально, на вашей видеокарте, без облака.**

speech2md распознаёт речь (русский, английский и 90+ других языков) моделью
[Whisper large-v3](https://huggingface.co/openai/whisper-large-v3) и сохраняет результат как
аккуратный Markdown-документ: заголовок, строка метаданных и текст, разбитый на абзацы по
естественным паузам в речи. Готово для Obsidian, Notion или git-репозитория.

[Read in English](README.md)

## Зачем, если есть whisper-ctranslate2 и whisper.cpp?

Они выдают плоский текст или субтитры и отлично подходят для видеопайплайнов. speech2md — про
**заметки, которые можно читать**: часовая запись превращается в структурированный документ, а
не в стену текста. Плюс GPU на Windows работает после одного `pip install` — без установки
CUDA Toolkit.

## Требования

- Python 3.10+
- ~2 ГБ на диске для модели (скачивается при первом запуске)
- Опционально: NVIDIA GPU с 4+ ГБ VRAM (драйвер CUDA 12). Без GPU работает на CPU, медленнее.
- FFmpeg не нужен — mp3, wav, m4a, mp4, ogg, flac и другие форматы декодируются из коробки.

## Установка

**Windows (PowerShell):**

```powershell
git clone https://github.com/Arshont/speech2md
cd speech2md
.\install.ps1
```

**Любая ОС (pip):**

```bash
pip install -e .          # CPU
pip install -e .[cuda]    # NVIDIA GPU (cuBLAS/cuDNN ставятся pip-пакетами)
```

## Использование

```powershell
speech2md запись.mp3                           # автоопределение языка → запись.md
speech2md meeting.m4a --language ru            # язык вручную
speech2md lecture.mp4 --timestamps             # метки [00:01:23] у абзацев
speech2md talk.wav --format md,srt             # несколько форматов сразу
speech2md .\records\*.m4a                      # пакетная обработка по маске
speech2md long.mp3 --model large-v3-turbo      # в ~5 раз быстрее, качество чуть ниже
```

На Windows есть обёртка: `.\transcribe.ps1 запись.mp3 -Language ru -Timestamps`.

Форматы вывода: `md` (по умолчанию), `txt`, `srt`, `vtt`.

## Выбор модели

При первом запуске speech2md опрашивает железо (VRAM, RAM, CPU), показывает таблицу моделей
с пометками «влезает/нет» и предлагает рекомендуемую: Enter — согласиться, либо введите имя
другой. Выбор сохраняется. Посмотреть или изменить:

```powershell
speech2md models            # таблица моделей + что влезает в ваш ПК
speech2md models --setup    # заново запустить интерактивный выбор
speech2md models --set large-v3-turbo
```

Ориентир: 4+ ГБ VRAM → `large-v3`; 2.5–4 ГБ → `large-v3-turbo`; только CPU → `large-v3-turbo`
при 8+ ГБ RAM, иначе `small`. Внимание: `distil-large-v3` — **только английский**.
Полная таблица со ссылками — в [README.md](README.md#choosing-a-model).

## Настройки

Дефолты хранятся в JSON (`%APPDATA%\speech2md\config.json` на Windows,
`~/.config/speech2md/config.json` в остальных ОС); файл создаётся диалогом первого запуска.
Флаги командной строки всегда важнее конфига. Ключи: `model`, `language`, `format`,
`timestamps`, `device`.

## Скорость

На GTX 1060 6GB (INT8, с VAD): ~6x от реального времени на коротких записях; на длинных
ожидайте 1.5–3x с `large-v3` и в разы быстрее с `large-v3-turbo`. На CPU c `large-v3` будет
медленнее реального времени — берите `distil-large-v3` или `medium`.

## Лицензии

Код speech2md — MIT. Утилита скачивает и запускает
[whisper-large-v3](https://huggingface.co/openai/whisper-large-v3) (© OpenAI, Apache 2.0) в
[CTranslate2-конвертации Systran](https://huggingface.co/Systran/faster-whisper-large-v3) (MIT).
