# YouTube Downloader Pro

A Python/PySide6 desktop media download manager. v7 uses an analysis-first workflow, a managed queue, and local settings/history. Media extraction uses yt-dlp; conversion and merging use FFmpeg. Mutagen supplies cover-art metadata support.

**Use only for media you own or are authorized to download and store.** Respect platform terms, copyright, and applicable law. The application does not bypass DRM, paywalls, authentication, CAPTCHAs, or access controls.

This is a tested local release candidate, not a published release. See [the final feature audit](docs/FEATURE_AUDIT.md) for evidence, limitations and release blockers.

## Screenshots

A screenshot of the current Windows interface is included in [docs/screenshots/home.png](docs/screenshots/home.png). Additional platform screenshots can be added after native testing.

## Features

- Turkish and English interfaces, including standard Qt controls. Language persists and changes after restart. Dark, light, and system themes; Home, Downloads, History, Settings, and About pages.
- Paste or drop a URL, analyze it without downloading, then review title, uploader, duration, available formats, subtitles, and a thumbnail where supplied.
- Video resolution discovery, Best Available, MP4/WebM, and a custom yt-dlp format selector.
- Actual FFmpeg audio conversion to MP3, M4A, OPUS, FLAC, or WAV. Lossy audio supports 128/192/256/320 kbps; lossless formats ignore bitrate.
- A queue with 1–5 concurrent downloads, 1–8 fragments per download, speed limits, progress, speed, ETA, cancellation, retry, search, and status filtering.
- Three-attempt retries for temporary network failures, with 2- and 4-second backoff. Permanent errors are not retried automatically.
- Playlist selection in pages of up to 100 entries. Selections persist while moving between pages.
- Manual/automatic subtitles, preferred or selected language codes, and SRT/VTT conversion where FFmpeg is available.
- Optional metadata, chapters, descriptions, cover artwork, and thumbnail files, subject to container support.
- Persistent settings, SQLite history with title/status/type/date/format filters and 100-row pagination, and an optional verified download archive.
- Optional clipboard detection with Analyze/Dismiss actions, tray notifications, scheduled queue starts, and a floating Mini Mode.
- Cross-platform FFmpeg detection, rotating logs, About/version information, and an explicit read-only engine version check.

## Download / Windows

When the owner publishes a tested Windows x64 release:

1. Download the Windows x64 ZIP from [GitHub Releases](https://github.com/Can-Ozan/Youtube-Downloader-Pro-v6.0/releases).
2. Extract the entire ZIP to a folder.
3. Double-click **YouTube Downloader Pro.exe** inside that folder.

Keep the `_internal` folder beside the EXE. Normal users do not need Python,
pip, Qt, yt-dlp or a terminal. A v7 release has not been published by this work.
Default test builds do not include FFmpeg; full conversion/merging requires a
verified bundled or installed FFmpeg/ffprobe pair. Check the release notes.

Unsigned applications can trigger Windows SmartScreen or antivirus reputation
warnings. Verify the download source and published checksum and investigate
warnings; do not blindly bypass Windows security protections.

## Source requirements

- Python **3.11 or newer** supported by the declared dependencies; CI targets 3.11 and 3.12.
- Windows, macOS, or a desktop Linux environment supported by PySide6. Native Windows startup/build tests were performed locally; other platforms have CI configuration and mocked OS helper tests.
- FFmpeg **and ffprobe** for full processing support. Without them, compatible combined audio/video formats can still download; high-resolution merging, conversion, and artwork need FFmpeg.
- Sufficient free disk space. Known estimates receive a preflight check; temporary transfer/processing files also require space. Estimates are not guarantees.

The dependency ranges in `pyproject.toml` are the authoritative requirements. The application version is defined only in `youtube_downloader_pro/__init__.py`; the UI, package, and build read it.

## Installation and running from source

Clone this repository, then create an isolated environment:

```powershell
git clone https://github.com/Can-Ozan/Youtube-Downloader-Pro-v6.0.git
cd Youtube-Downloader-Pro-v6.0
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m youtube_downloader_pro
```

On macOS/Linux, use `python3 -m venv .venv` and `source .venv/bin/activate` instead. For a runtime-only installation, use `python -m pip install -e .`.

All three entry points run the same application:

```text
python -m youtube_downloader_pro
python youtube_indirici.py
youtube-downloader-pro
```

`youtube_indirici.py` is a compatibility launcher; it does not contain a second download engine. The original implementation is preserved in Git history.

## FFmpeg

Install FFmpeg/ffprobe through your OS package manager or a trusted distribution linked from the [official FFmpeg download page](https://ffmpeg.org/download.html). Verify the distributor's checksums/signatures before using manually downloaded binaries. Do not download executable files from untrusted mirrors.

Detection order:

1. Bundled `ffmpeg/` inside the resource directory (`_internal/` in Windows ONEDIR); legacy source `ffmpeg/bin/` is also supported.
2. `<application data>/ffmpeg/bin/` for an explicitly managed installation.
3. System `PATH`, using `shutil.which()` and bounded version probes.

Place both `ffmpeg` and `ffprobe` in the selected directory (`.exe` on Windows). Restart after changing installation or `PATH`. About displays the detected version/source and ffprobe status. The GUI never downloads binaries or runs a package installer.

## Usage

1. Paste or drag a complete HTTP/HTTPS media URL into Home, then click **Analyze**.
2. For a playlist, open **Select playlist videos**. Select individual rows or all rows on the current page, then use Next/Previous to load more. Nothing is automatically enqueued during analysis.
3. Choose Video, Audio, or Custom. Video resolutions are upper limits; the engine selects a matching available format. MP4/WebM choices constrain both container and compatible source streams; unavailable choices fail visibly rather than silently increasing resolution or changing the format.
4. Configure subtitles and advanced options. Playlist entries are analyzed individually when they start; preferred languages are useful when a flat playlist has no subtitle metadata.
5. Click **Start Download** to enqueue and start immediately. For deferred downloads, click **Add to queue**, then **Start now**, or enter a valid local 24-hour time such as `18:30` and choose **Start at…**. A time already passed runs the next day. A new schedule replaces the previous one. The app must stay open.
6. Use queue actions or the context menu to cancel, retry, remove, open outputs/folders, or copy URLs. Double-click a row for error details. Use **Download again anyway** to override the archive.
7. History retains completed/failed/cancelled attempts that reached the manager's worker, with retry options. Clearing history leaves media files and the separate archive intact.

Cancel stops the current media process and its children. Partial job files are cleaned up. Retry starts a fresh attempt; pause/resume and retaining partial files across application restarts are not implemented. Completion requires a nonempty final media file after all requested processing and publication.

## Settings, history, and privacy

Default locations come from `platformdirs`, never an arbitrary working directory:

| Data | Location |
| --- | --- |
| Settings/history/archive | OS application data directory for `YouTubeDownloaderPro` |
| Logs | OS log directory for `YouTubeDownloaderPro` |
| Downloads | OS Downloads directory / `YouTube Downloader Pro` |

Typical data directories are `%LOCALAPPDATA%\YouTubeDownloaderPro` on Windows, `~/Library/Application Support/YouTubeDownloaderPro` on macOS, and `~/.local/share/YouTubeDownloaderPro` on Linux. `platformdirs` honors applicable OS/XDG settings. `--data-dir PATH` explicitly overrides settings/history/archive and logging for tests or portable use.

Settings include folder, theme, default quality/container/audio codec, audio bitrate, concurrency, speed limit, subtitle preferences, metadata/artwork, filename template, history/archive, clipboard, notifications, auto-open, and Mini Mode preference. Turkish and English are available; the first launch follows the system UI language when supported, otherwise English. Changing language requires a restart. Missing translations fall back to English. Save applies defaults to new queue entries; queued items retain their own settings. Parallelism changes require an idle queue.

The default template is `%(title)s [%(id)s].%(ext)s`. Supported fields are `title`, `id`, `uploader`, `channel`, `playlist`, `playlist_index`, and `ext`, with up to two safe subfolders. Presets are available. Unsafe characters/reserved names are sanitized, and colliding files receive numbered suffixes; existing files are never overwritten. Extremely long Windows paths are rejected with a clear message.

History stores source URLs, titles, final paths, format/quality, size, state/date, duration, thumbnail URL, and the options needed to retry. Disable history if you do not want those records. The optional archive independently stores source URLs and yt-dlp media identities, and exports `download-archive.txt` in yt-dlp's archive format. A media-identity match can recognize alternate URLs after analysis. The SQLite ledger is authoritative; enabling the archive does not import external archive text files.

No telemetry, passwords, browser cookies, tokens, or session credentials are collected. Clipboard monitoring is off by default and only suggests recognized media hosts. Thumbnail loading and media analysis contact the relevant media hosts. The explicit version-check button contacts PyPI; it does not install anything. Logs redact URLs and credential-like fields and rotate at 2 MB with three backups. Review logs before sharing them.

## Architecture and project structure

```text
youtube_indirici.py                 Compatibility launcher
pyproject.toml                     Package/dependency/tool configuration
build/windows.spec                Windows ONEDIR source specification
scripts/build_windows.ps1          Windows build and validation
scripts/package_release.ps1        Runtime ZIP and SHA256
scripts/clean_build.ps1            Safe generated-output cleanup
youtube_downloader_pro/
    __init__.py                    Single application version source
    main.py, __main__.py            Startup and command-line options
    core/                          Queue manager, yt-dlp adapter, process runner,
                                   errors, FFmpeg detection, schedule, clipboard
    models/                        Download items, states, immutable settings/options
    services/                      Settings, SQLite history/archive, notifications,
                                   read-only version checks
    i18n/                          Matched UTF-8 Turkish/English catalogs and fallback
    ui/                            Main window, themes, five pages, reusable widgets
    utils/                         Validation, formatting, paths, staged output, logs
tests/                             Unit, UI, generated-media integration tests
docs/AUDIT.md                      Findings from the original implementation
.github/workflows/ci.yml            Cross-platform validation
.github/workflows/windows-build.yml Windows build, smoke, ZIP and checksum
scripts/benchmark_ui.py            Opt-in local UI benchmark
```

The manager owns queue state behind a lock. A bounded `ThreadPoolExecutor` supervises isolated spawned media processes. The Qt UI receives snapshots through queued signals; workers never manipulate widgets. A separate bounded executor handles history, version checks, settings writes, and FFmpeg probing. The scheduler uses one low-frequency Qt timer. Qt network requests handle bounded thumbnail loading; image decoding/scaling runs in a two-thread pool. UI progress is coalesced at 125 ms, with state changes delivered immediately. Only affected virtual rows repaint; searches are debounced and history queries run in the background.

Each download has a private staging directory on the destination filesystem. The parent verifies and publishes media and sidecars without overwrites, using atomic hard links where supported and exclusive streaming copies elsewhere. Cancellation rolls back files created during incomplete publication. Disk/network/processing failures are distinct from completion. On close the application cancels work, waits asynchronously, joins workers, and shuts down its executors.

## Development and testing

Inside the activated virtual environment:

```text
python -m pip install -e ".[dev]"
python -m pytest
ruff check .
ruff format --check .
python -m compileall youtube_downloader_pro
python -c "from youtube_downloader_pro.ui.main_window import MainWindow"
python -m youtube_downloader_pro --smoke-test --data-dir .test-artifacts/startup
```

For headless startup set `QT_QPA_PLATFORM=offscreen`. The tests configure this automatically. Native screenshots can be captured with `--screenshot PATH`. GUI smoke mode exits after initialization and graceful shutdown.

Unit tests mock external behavior. Integration tests generate their own tone/video and serve it over loopback HTTP, then exercise real yt-dlp and decode converted output with FFmpeg. No copyrighted third-party media is downloaded. Conversion tests skip when FFmpeg is missing; set `YDP_TEST_FFMPEG` to a trusted executable to run them. Linux CI installs the Qt system libraries needed for headless tests. OS file/folder launch commands are mocked on platforms not running locally.

For source dependency maintenance, update within the project virtual environment and rerun tests:

```text
python -m pip install --upgrade -e ".[dev]"
```

This is a developer action, not application behavior. Packaged engines are updated by rebuilding the application. The CI workflow runs checks on Windows, Ubuntu, and macOS and builds Windows; the Windows workflow uploads test artifacts without publishing a GitHub Release. Successful local tests do not imply that the remote CI matrix has already run.

The final local verification record and remaining blockers are in [docs/FEATURE_AUDIT.md](docs/FEATURE_AUDIT.md). Earlier reports are historical. Run `python scripts/benchmark_ui.py --output .test-artifacts/ui-benchmark/after.json` for the opt-in synthetic benchmark.

## Windows standalone builds

On Windows, create a Python 3.12 x64 virtual environment and run:

```powershell
py -3.12 -m venv .venv
./scripts/build_windows.ps1 -InstallDependencies
./scripts/package_release.ps1
```

The production ONEDIR output is `dist/YouTube Downloader Pro/YouTube Downloader Pro.exe`.
The versioned ZIP and SHA256 are written to `release/`. All supporting files must
stay with the EXE. The build uses the same application entry point as source.
No UPX, installer, automatic release publishing or onefile build is enabled.

See [Windows build instructions](docs/WINDOWS_BUILD.md) for resource paths,
FFmpeg provenance, icon placement, debugging, cleanup, CI and release validation.
Build, native/offscreen startup results and exact artifact hashes are recorded in
the [final feature audit](docs/FEATURE_AUDIT.md). Earlier Windows validation reports
refer to earlier artifacts. Clean-machine Windows 10/11 acceptance and distribution
licensing remain release tasks.

## Troubleshooting and current limits

- **FFmpeg unavailable:** ensure both executables are discoverable and runnable, then restart. Audio conversion and separate video/audio merging require them.
- **Unavailable/private/protected media or verification prompts:** open the source platform normally. This app does not supply access-control workarounds or credentials.
- **YouTube/site extraction failures:** platform behavior changes. Review the logs and the installed engine version. Remote JavaScript challenge components and runtime auto-discovery are disabled; media requiring them may not be available through this application. Live analysis returned 49 formats for the Blender Foundation’s Big Buck Bunny video during the final pass. Remote media downloads were not validated; automated download tests use locally generated media.
- **Format unavailable:** analyze again, choose Best Available, another container, or a source format in Custom mode. A custom selector producing multiple outputs is rejected because one queue item must map to one verified output.
- **Artwork failures:** WAV/WebM artwork embedding is rejected; other codec/artwork combinations still depend on FFmpeg/yt-dlp support.
- **Disk/permission/path error:** free space or choose a writable, shorter folder/template. Size estimates can be absent or wrong. Staging folders left by a power loss can be removed when no application instance is running.
- **No thumbnail/subtitles/size:** sources do not always provide these fields. Thumbnail requests are size-limited, and redirects are not followed; downloads still work without preview artwork.
- **Schedule did not run:** the app must stay running. Schedules and the live queue do not persist across restart. Desktop sleep/time-zone changes may delay local schedules; no background OS service is installed.
- **No notification:** tray availability and notification support depend on the OS/session; banners remain available.
- **UI language:** Turkish/English application messages and standard Qt controls are translated. Media titles, uploader names, paths, format IDs and upstream technical diagnostics retain their original text; technical diagnostics are available in logs.
- **Live streams:** not supported; use a finished recording. Pause/resume is not exposed because it cannot be implemented reliably across the transfer/postprocessing pipeline here.

## Security and licensing

URL input accepts HTTP/HTTPS only and rejects embedded credentials. Filename templates cannot traverse out of the chosen folder. Media/plugin update payloads are never executed. Third-party yt-dlp plugin discovery is disabled. Subprocesses use argument lists, and opening files is restricted to media/text/image types. FFmpeg detection executes only the detected installed/bundled/managed tool. There is no binary downloader or archive extractor in the application.

This repository does **not** include a project LICENSE. No MIT or other project license is claimed; the repository owner must choose one. Dependencies have their own licenses.

Developer: **Yusuf Can Ozan / Can-Ozan**. [Repository](https://github.com/Can-Ozan/Youtube-Downloader-Pro-v6.0).
