# YouTube Downloader Pro

A modern desktop media download manager built with Python, PySide6, yt-dlp and FFmpeg.
Analyze a link, choose video or audio, and manage downloads through a desktop queue with local history and settings.

## Features

- **Media analysis:** inspect the title, uploader, duration, available qualities, subtitle languages and thumbnail when the source provides them.
- **Video and audio:** MP4/WebM video downloads and actual MP3, M4A, OPUS, FLAC and WAV audio conversion.
- **Source-based quality choices:** Best, 4K and other discovered resolutions; advanced users can supply a custom yt-dlp format selector.
- **Playlists:** select individual entries across paginated results before adding them to the queue.
- **Download management:** queue search and status filtering, 1–5 parallel downloads, speed limits, progress, speed and ETA when available, cancellation and retry.
- **History:** local SQLite records with search, status/type/date/format filters, pagination, retry, Open File and Open Folder actions.
- **Media options:** manual or automatic subtitles, metadata, chapters, descriptions, thumbnail files and cover artwork where supported by the source and output format.
- **Preferences:** persistent settings, immediate Turkish/English switching, and Dark, Light and System themes.
- **Desktop helpers:** Mini Mode, optional clipboard link suggestions, scheduled queue starts while the app remains open, and optional system-tray notifications where the desktop supports them.

Media processing is covered by tests using locally generated files and real yt-dlp/FFmpeg. Support for a particular website, format or remote playlist depends on the source and extractor. Desktop notification delivery depends on the OS/session. See [Testing](#testing) for validation coverage and limits.

## Screenshots

| Page | Screenshot status |
| --- | --- |
| Home | [Existing capture](docs/screenshots/home.png); needs refreshing to show the final visual polish. |
| Downloads | Screenshot pending: `docs/screenshots/downloads.png`. |
| Settings | Screenshot pending: `docs/screenshots/settings.png`. |

## Languages

- Türkçe
- English

Choose a language in **Settings → General** and save. The running interface switches immediately, without restarting or interrupting downloads. The selected language persists after closing and reopening the app. Missing translations fall back to English.

Media titles, uploader names, paths and source format identifiers retain their original text.

## Download / Windows

For a published Windows build:

1. Open [GitHub Releases](https://github.com/Can-Ozan/Youtube-Downloader-Pro-v6.0/releases).
2. Download the latest Windows x64 ZIP asset.
3. Extract the **entire ZIP** to a folder.
4. Open the extracted application folder and run **YouTube Downloader Pro.exe**.

Keep the `_internal` folder beside the EXE. The packaged application includes Python and its Python/Qt dependencies; **users do not need to install Python**. FFmpeg is separate in the current default package; see [FFmpeg](#ffmpeg).

If no Windows ZIP is listed, a packaged release is not available there yet. GitHub Actions build artifacts are separate from published releases.

## Usage

1. Paste or drop a media URL into **Home**.
2. Click **Analyze** to load the media details.
3. Choose **Video** or **Audio**.
4. Select the available quality and output format.
5. If needed, change the download folder in **Settings → General**, save, then return to Home.
6. Click **Start Download**.
7. Monitor progress and use Cancel or Retry in **Downloads**.
8. Find previous attempts and open completed files from **History**.

For a playlist, use **Select playlist videos** after analysis. Selections remain available as you move between pages.

**Advanced** on Home contains bitrate, additional audio formats, subtitle and metadata options, and Custom mode. **Add to queue** defers starting; use **Start now** in Downloads or expand **Schedule** and enter a local 24-hour time such as `18:30`. A time already passed schedules the next day. The app must remain open.

Cancel stops the current job and cleans up its temporary files. Retry starts a new attempt. Pause/resume, live streams, and restoring the live queue or schedule after an application restart are not supported.

## Supported Formats

| Output | Supported choices | Behavior |
| --- | --- | --- |
| Video | MP4, WebM | Downloads compatible source streams; FFmpeg merges separate video/audio streams when required. |
| Audio | MP3, M4A, OPUS | FFmpeg extracts/converts audio. Bitrate choices are available under Advanced. |
| Audio | FLAC, WAV | FFmpeg produces lossless output; bitrate selection does not apply. Lossless output cannot restore detail absent from the source. |
| Subtitles | SRT, VTT | Downloads available subtitles; FFmpeg converts them when necessary. |

Audio output uses yt-dlp's FFmpeg postprocessing pipeline, not a renamed file extension. MP3 and M4A are the standard Audio choices; OPUS, FLAC and WAV are available under Advanced. Custom mode accepts source-specific format selectors and must produce one final media file per queue item.

Embedded artwork is not supported for WAV or WebM. Other artwork and metadata options depend on the container, source data and available processing tools.

## Quality

Single-media analysis populates the quality list from the resolutions reported by the source. **Best** selects the best compatible available streams. **4K** represents 2160p; other choices, such as 1440p, 1080p or 720p, appear when discovered.

A selected resolution is an **upper limit**, not a promise that the source has that exact quality. MP4/WebM selection also constrains compatible streams. If no compatible format is available, the job reports an error.

Playlists offer standard resolution limits because entries are analyzed individually when their jobs start. Neither choosing a higher resolution nor converting to a different format improves the original source quality.

## FFmpeg

FFmpeg handles audio conversion, merging separate video/audio streams, subtitle conversion, and supported metadata, chapter and artwork processing. Full processing requires both **FFmpeg and ffprobe**. Without them, compatible video files containing both audio and video can still download.

The application probes candidates in this order and uses the first working pair:

1. Bundled `ffmpeg/` or `ffmpeg/bin/` under the application resource directory. In Windows ONEDIR builds, this is inside `_internal/`.
2. `ffmpeg/bin/` under the default application data directory, such as `%LOCALAPPDATA%\YouTubeDownloaderPro\ffmpeg\bin` on Windows.
3. System `PATH`, with ffprobe beside the detected FFmpeg executable.

**The current local Windows package and default build do not bundle FFmpeg.** Install a trusted FFmpeg/ffprobe pair separately and make it discoverable through one of these locations. The app does not download or install these binaries. About displays the detected version, source and ffprobe status. Restart the app after changing the installation or `PATH`; this is separate from language changes, which apply immediately.

Optional bundling requires an explicitly supplied, verified distribution and its provenance/notices. See [Windows build documentation](docs/WINDOWS_BUILD.md#ffmpeg-distribution).

## Running From Source

The Windows example uses Python 3.12:

```powershell
git clone https://github.com/Can-Ozan/Youtube-Downloader-Pro-v6.0.git
cd Youtube-Downloader-Pro-v6.0
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m youtube_downloader_pro
```

On macOS/Linux, after cloning and entering the repository, use a supported Python interpreter:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m youtube_downloader_pro
```

If shell activation is unavailable, invoke the virtual environment's Python directly: `.\.venv\Scripts\python.exe` on Windows or `.venv/bin/python` on macOS/Linux.

`youtube_indirici.py` remains a compatibility launcher for the same modular application; it is not a separate legacy download engine.

## Requirements

- **Python 3.11 or newer** for source use, as declared in [pyproject.toml](pyproject.toml). CI targets Python 3.11 and 3.12.
- A desktop environment supported by PySide6. Windows x64 has the dedicated distribution pipeline; macOS/Linux source support also has CI configuration.
- FFmpeg and ffprobe for full media processing.
- Network access to the requested media source and enough writable disk space for output and temporary processing files.

Dependency versions and development extras are defined in `pyproject.toml`.

## Project Structure

```text
youtube_downloader_pro/
    main.py, __main__.py    Application startup and module entry point
    core/                  Download manager, yt-dlp workers, FFmpeg detection,
                           scheduling and clipboard validation
    models/                Download items, states and settings
    services/              Settings, SQLite history/archive, notifications,
                           read-only engine version checks
    ui/                    Main window, pages, widgets and themes
    i18n/                  Turkish/English catalogs and translation support
    utils/                 Paths, resources, logging and output validation
youtube_indirici.py         Compatibility launcher
tests/                     Unit, UI and generated-media integration tests
scripts/                   Build, package, cleanup and UI benchmark tools
build/windows.spec         Windows ONEDIR source specification
docs/                      Audits, build notes and screenshots
assets/                    Optional application assets
.github/workflows/         Cross-platform checks and Windows build workflow
```

The Qt interface receives worker events rather than running downloads on the UI thread. Progress updates are batched and update affected rows; history queries and media work run in background tasks. The application version has one source: `youtube_downloader_pro/__init__.py`.

## Development

Inside the activated virtual environment:

```text
python -m pip install -e ".[dev]"
python -m pytest
ruff check .
python -m compileall youtube_downloader_pro
```

For a startup/import smoke check with isolated local settings and history:

```text
python -m youtube_downloader_pro --smoke-test --data-dir .test-artifacts/startup --smoke-report .test-artifacts/startup-report.json
```

For headless checks, set `QT_QPA_PLATFORM=offscreen` first: `$env:QT_QPA_PLATFORM='offscreen'` in PowerShell, or `export QT_QPA_PLATFORM=offscreen` on macOS/Linux. Smoke mode initializes the application, checks resources/persistence and spawned engine imports, then exits gracefully.

The existing synthetic UI benchmark measures startup, progress-event batching, timer responsiveness, idle CPU and shutdown:

```text
python scripts/benchmark_ui.py --output .test-artifacts/ui-benchmark/after.json
```

The benchmark uses local synthetic rows and makes no media network requests. Results depend on the machine and workload.

## Windows Build

Use Windows x64 and an existing virtual environment created with Python 3.12 x64 as above. From the repository root:

```powershell
.\scripts\build_windows.ps1 -InstallDependencies
.\scripts\package_release.ps1
```

The build script finds `.venv` automatically. `-InstallDependencies` explicitly installs the project's development dependencies there; omit it for subsequent builds with dependencies already installed.

The build runs pytest, Ruff, compileall and source smoke checks, creates the PyInstaller **ONEDIR** application, audits the distribution and runs a packaged startup smoke test. Packaging requires successful smoke evidence matching the current distribution files and creates a ZIP, SHA256 checksum and validation report.

| Artifact | Output path |
| --- | --- |
| EXE | `dist/YouTube Downloader Pro/YouTube Downloader Pro.exe` |
| ZIP | `release/YouTube-Downloader-Pro-v<version>-Windows-x64.zip` |
| Checksum | The ZIP path followed by `.sha256` |
| Validation report | The ZIP path followed by `.validation.json` |

The version is read from the package. Distribute the complete ONEDIR folder, including `_internal`, rather than the EXE alone.

The build performs scoped cleanup automatically. To preview or run cleanup separately:

```powershell
.\scripts\clean_build.ps1 -WhatIf
.\scripts\clean_build.ps1
```

Cleanup removes generated `build/.work/`, `build/.cache/` and `dist/`. It preserves `build/windows.spec` and existing release archives; `-IncludeRelease` additionally removes `release/`.

The [Windows GitHub Actions workflow](.github/workflows/windows-build.yml) runs this pipeline on `windows-latest` and uploads build artifacts. It does not publish a GitHub Release. See [Windows build documentation](docs/WINDOWS_BUILD.md) for FFmpeg bundling, optional icons, diagnostics and distribution checks. Rebuild and validate from the current source before distributing an updated ZIP.

## Testing

- **Pytest:** validation, queue transitions, cancellation, retry, settings/history persistence and UI-to-engine integration.
- **Real media processing:** locally generated audio/video served over loopback HTTP, converted or merged with yt-dlp/FFmpeg, then decoded to check the output. Includes subtitle, metadata and artwork cases. FFmpeg-dependent cases skip if FFmpeg is unavailable; `YDP_TEST_FFMPEG` can select a trusted test executable.
- **UI validation:** live TR ↔ EN switching, persistence, dynamically created widgets, all themes, layout constraints and progress batching. Recent arrow checks also exercised simulated 100–200% DPI scaling.
- **Static/startup checks:** Ruff, compileall, source smoke tests and packaged resource/import/persistence checks.

The [CI configuration](.github/workflows/ci.yml) targets Windows, Ubuntu and macOS. Configured CI jobs are not proof that every platform has passed. Offscreen Qt checks do not replace native testing, physical monitor/DPI changes, notification delivery, or clean-machine Windows acceptance. Remote media downloads and remote YouTube playlists are not covered by the local generated-media tests. [Feature audit](docs/FEATURE_AUDIT.md) records additional evidence and release limitations; dated results refer to their respective snapshots.

## Troubleshooting

| Issue | What to check |
| --- | --- |
| FFmpeg not found | Ensure both FFmpeg and ffprobe are installed together in a detected location, then restart. Check About for detection status. |
| Unavailable or unsupported media | Check the URL and source availability. Private, protected and live content is unsupported. The app supplies no credentials or access-control bypasses. JavaScript runtimes and remote challenge components are disabled, which can limit some YouTube formats. |
| Network or extraction errors | Check connectivity and retry. Temporary failures receive bounded automatic retries. About can check the installed engine against PyPI; it does not install updates. Packaged engine updates require a newer build. |
| Format unavailable | Analyze again and try Best or another container. Available source formats determine what can be downloaded. |
| Output folder or disk errors | Choose a writable folder, free disk space and shorten the folder/template if needed. Temporary processing needs additional space. |
| SmartScreen warning | Unsigned builds may trigger reputation warnings. Verify the release source and published SHA256, investigate the warning and contact the publisher if uncertain. |
| Schedule or notification missing | Scheduling requires the app to remain open. Notifications require the setting to be enabled and a desktop session that supports system-tray messages. |

## Privacy

Settings, history, the optional download archive and logs are stored locally. Default locations come from `platformdirs`, outside the application installation directory:

| Data | Typical Windows location |
| --- | --- |
| Settings, history and archive | `%LOCALAPPDATA%\YouTubeDownloaderPro` |
| Logs | `%LOCALAPPDATA%\YouTubeDownloaderPro\Logs` |
| Downloads | The user's Downloads folder / `YouTube Downloader Pro` |

macOS/Linux use their platform-specific application data and log locations. `--data-dir` explicitly overrides settings/history/archive and log storage for tests or portable use.

History stores source URLs, titles, output paths and download options. It can be disabled or cleared; clearing history does not remove downloaded media or the independent archive. Logs rotate and redact URLs and common credential-like fields, but should still be reviewed before sharing.

Analysis, downloads and thumbnail previews contact media hosts. The explicit engine version check contacts PyPI. Clipboard monitoring is off by default; enabling it shows suggestions for recognized media URLs and does not start downloads automatically. The application does not load browser cookies or provide account sign-in.

## Legal Notice

YouTube Downloader Pro is intended for downloading media that you own or are authorized to download. Users are responsible for complying with applicable copyright laws and platform terms.

## License

No project `LICENSE` file has been added, and no project license is claimed here. The repository owner must select the license. Dependencies retain their own licenses; see [third-party notes](docs/THIRD_PARTY.md) and complete the applicable distribution requirements before publishing binaries.

## Author

**Yusuf Can Ozan** · GitHub: [Can-Ozan](https://github.com/Can-Ozan)

[Project repository](https://github.com/Can-Ozan/Youtube-Downloader-Pro-v6.0)
