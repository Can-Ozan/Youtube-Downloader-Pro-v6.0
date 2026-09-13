# Changelog

## 7.0.0 — development

### Architecture and correctness

- Replace the single-file Tkinter implementation with a Python package and PySide6 desktop UI.
- Keep `youtube_indirici.py` as a compatibility launcher for the same new application.
- Add typed options, download states, a central bounded manager, and Qt signal delivery.
- Isolate yt-dlp in processes so cancellation can stop network work and FFmpeg children.
- Verify postprocessed output, stage downloads separately, and publish without overwriting files.
- Bound temporary-error retries with exponential backoff; distinguish permanent failures.
- Validate URL schemes, output paths, filename templates, settings, and schedule times.
- Remove unchecked FFmpeg downloads and in-app dependency installation.

### Desktop features

- Add sidebar navigation, dark/light/system themes, media analysis and preview, and URL drag/drop.
- Discover source formats, resolution choices, and manual/automatic subtitle languages.
- Support MP4/WebM video and FFmpeg conversion to MP3/M4A/OPUS/FLAC/WAV.
- Add per-download progress, speed, ETA, cancellation, retries, context actions, and queue filters.
- Add playlist selection in bounded pages, an optional clipboard banner, and a floating Mini Mode.
- Retain speed limits, fragment concurrency, subtitles, chapters, artwork, and metadata options.
- Add atomic settings, SQLite history, an optional completion archive, and rotating redacted logs.
- Add optional tray notifications, FFmpeg/engine status, About, and a read-only version check.

### Engineering

- Declare runtime/development dependencies and one application version source.
- Add mocked unit tests, headless Qt tests, and generated-media integration tests.
- Add Windows/Linux/macOS CI checks and a Windows PyInstaller build check.
- Add standalone build configuration with optional explicitly supplied FFmpeg binaries.
- Replace inaccurate documentation; leave license selection to the repository owner.

### Current boundaries

- No pause/resume, background OS service, persistent live queue, or translated UI yet.
- Scheduled starts require the application to remain open; English is the available UI language.
- No DRM, paywall, authentication, CAPTCHA, or access-control bypass.
- Extractor availability depends on the source platform; remote challenge components are disabled.
- Signing, notarization, installers, and publishing releases remain owner-controlled work.
