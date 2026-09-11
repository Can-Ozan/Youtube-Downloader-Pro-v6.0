"""yt-dlp adapter. This module has no Qt dependency and runs inside isolated workers."""

import os
import time
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path

import yt_dlp
from yt_dlp.postprocessor.common import PostProcessor

from youtube_downloader_pro.core.errors import DownloadError
from youtube_downloader_pro.models.download_item import DownloadOptions
from youtube_downloader_pro.models.settings import Settings
from youtube_downloader_pro.services.archive_service import ArchiveService
from youtube_downloader_pro.utils.logger import redact
from youtube_downloader_pro.utils.paths import (
    check_disk_space,
    contained_file,
    ensure_output_dir,
    sanitize_filename,
)
from youtube_downloader_pro.utils.validators import validate_url

EventSink = Callable[[dict], None]
PAGE_SIZE = 100


class EngineLogger:
    def __init__(self, emit: EventSink) -> None:
        self.emit = emit

    def debug(self, message: str) -> None:
        # yt-dlp also routes ordinary informational output through debug.
        if not message.startswith("[debug]"):
            self.emit({"type": "log", "message": redact(message)[:2000]})

    def info(self, message: str) -> None:
        self.debug(message)

    def warning(self, message: str) -> None:
        self.emit({"type": "log", "message": redact(message)[:2000]})

    def error(self, message: str) -> None:
        self.warning(message)


def base_options(emit: EventSink) -> dict:
    # Never discover third-party executable plugins from user/system directories.
    os.environ["YTDLP_NO_PLUGINS"] = "1"
    return {
        "quiet": True,
        "no_warnings": False,
        "logger": EngineLogger(emit),
        "ignoreerrors": False,
        "socket_timeout": 15,
        "retries": 0,
        "fragment_retries": 0,
        "extractor_retries": 0,
        "file_access_retries": 0,
        "skip_unavailable_fragments": False,
        "cachedir": False,
        "windowsfilenames": True,
        "restrictfilenames": False,
        "noprogress": True,
        "geo_bypass": False,
        # No user configuration, credentials, plugins, or remote JS components are loaded.
        "js_runtimes": {},
        "remote_components": set(),
    }


def compact_media(info: dict, fallback_url: str, index: int | None = None) -> dict:
    url = info.get("webpage_url") or info.get("url") or fallback_url
    if index is not None and url == fallback_url:
        # Generic HTML playlists can share one webpage while each entry has a direct source.
        direct = info.get("url")
        if not direct:
            candidates = info.get("formats") or []
            direct = next(
                (
                    f.get("url")
                    for f in reversed(candidates)
                    if str(f.get("url", "")).startswith(("http://", "https://"))
                ),
                None,
            )
        if direct:
            url = direct
    if not str(url).startswith(("http://", "https://")):
        url = fallback_url
    formats = []
    for fmt in info.get("formats") or []:
        if fmt.get("has_drm") or fmt.get("vcodec") == "none" and fmt.get("acodec") == "none":
            continue
        formats.append(
            {
                key: fmt.get(key)
                for key in (
                    "format_id",
                    "ext",
                    "height",
                    "width",
                    "fps",
                    "vcodec",
                    "acodec",
                    "abr",
                    "filesize",
                    "filesize_approx",
                    "format_note",
                )
            }
        )
    return {
        "url": validate_url(url),
        "title": info.get("title") or "Untitled media",
        "id": info.get("id", ""),
        "uploader": info.get("uploader") or info.get("channel") or "",
        "duration": info.get("duration"),
        "thumbnail": info.get("thumbnail") or "",
        "estimated_size": info.get("filesize") or info.get("filesize_approx"),
        "formats": formats,
        "subtitles": sorted((info.get("subtitles") or {}).keys()),
        "automatic_captions": sorted((info.get("automatic_captions") or {}).keys()),
        "playlist_index": info.get("playlist_index") or index,
    }


def analyze(url: str, emit: EventSink, start: int = 1) -> dict:
    url = validate_url(url)
    if not 1 <= start <= 100_000:
        raise ValueError("Invalid playlist page")
    opts = base_options(emit) | {
        "extract_flat": "in_playlist",
        "lazy_playlist": True,
        "playlist_items": f"{start}:{start + PAGE_SIZE - 1}",
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    if not info:
        raise DownloadError("unavailable", "No media was found at this URL.")
    if "entries" not in info:
        return compact_media(info, url) | {"is_playlist": False}
    entries = []
    for index, entry in enumerate(info["entries"], start):
        if entry:
            entries.append(compact_media(entry, url, index))
        if index >= start + PAGE_SIZE - 1:
            break
    count = info.get("playlist_count") or info.get("n_entries")
    return {
        "url": url,
        "title": info.get("title") or "Playlist",
        "is_playlist": True,
        "entries": entries,
        "count": count,
        "start": start,
        "has_more": (start + PAGE_SIZE <= count) if count else len(entries) == PAGE_SIZE,
    }


def build_options(options: DownloadOptions, staging: Path, ffmpeg: str, emit: EventSink) -> dict:
    options.validate()
    settings = options.settings
    opts = base_options(emit) | {
        "paths": {"home": str(staging)},
        "outtmpl": settings.filename_template,
        "noplaylist": True,
        "continuedl": True,
        "overwrites": False,
        "trim_file_name": 160,
        "concurrent_fragment_downloads": settings.fragment_concurrency,
        "ratelimit": settings.speed_limit or None,
        "postprocessors": [],
        "writedescription": settings.write_description,
        "writethumbnail": settings.download_thumbnail or settings.embed_thumbnail,
        "updatetime": False,
    }
    if ffmpeg:
        opts["ffmpeg_location"] = ffmpeg
    pp = opts["postprocessors"]
    if options.mode == "audio":
        if not ffmpeg:
            raise DownloadError("ffmpeg", "Install FFmpeg and ffprobe to convert audio.")
        opts["format"] = "bestaudio/best"
        pp.append(
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": settings.audio_format,
                "preferredquality": str(settings.audio_bitrate),
            }
        )
    elif options.mode == "custom":
        opts["format"] = options.custom_format
    else:
        height = "" if options.quality == "Best Available" else f"[height<={options.quality[:-1]}]"
        container = options.container
        audio_ext = "m4a" if container == "mp4" else "webm"
        combined = f"best[ext={container}]{height}"
        opts["format"] = (
            f"bestvideo[ext={container}]{height}+bestaudio[ext={audio_ext}]/{combined}"
            if ffmpeg
            else combined
        )
        opts["merge_output_format"] = container
    if settings.subtitle_mode != "none":
        opts.update(
            {
                "writesubtitles": settings.manual_subtitles,
                "writeautomaticsub": settings.automatic_subtitles,
                "subtitleslangs": list(settings.subtitle_languages),
                "subtitlesformat": f"{settings.subtitle_format}/best",
            }
        )
        if ffmpeg:
            pp.append({"key": "FFmpegSubtitlesConvertor", "format": settings.subtitle_format})
        else:
            opts["subtitlesformat"] = settings.subtitle_format
    if (settings.embed_metadata or settings.preserve_chapters) and ffmpeg:
        pp.append(
            {
                "key": "FFmpegMetadata",
                "add_metadata": settings.embed_metadata,
                "add_chapters": settings.preserve_chapters,
            }
        )
    if settings.embed_thumbnail:
        if not ffmpeg:
            raise DownloadError("ffmpeg", "Install FFmpeg to embed thumbnail artwork.")
        if options.mode == "audio" and settings.audio_format == "wav":
            raise DownloadError(
                "format", "WAV does not support cover artwork. Disable Embed thumbnail."
            )
        if options.mode == "video" and options.container == "webm":
            raise DownloadError("format", "WebM does not support embedded cover artwork.")
        pp.extend(
            [
                {"key": "FFmpegThumbnailsConvertor", "format": "png", "when": "before_dl"},
                {"key": "EmbedThumbnail", "already_have_thumbnail": settings.download_thumbnail},
            ]
        )
    return opts


class SafeYoutubeDL(yt_dlp.YoutubeDL):
    def __init__(self, options: dict, staging: Path) -> None:
        self.staging = staging.resolve()
        super().__init__(options)

    def prepare_filename(self, info_dict, dir_type="", *, outtmpl=None, warn=False):
        value = super().prepare_filename(info_dict, dir_type, outtmpl=outtmpl, warn=warn)
        if not value:
            return value
        path = contained_file(self.staging, value)
        relative = path.relative_to(self.staging)
        parts = [sanitize_filename(part, 120) for part in relative.parts[:-1]]
        name = Path(relative.name)
        parts.append(sanitize_filename(name.stem, 160) + name.suffix)
        safe = self.staging.joinpath(*parts)
        if os.name == "nt" and len(str(safe).encode("utf-16-le")) // 2 > 245:
            raise DownloadError(
                "path", "The output path is too long. Choose a shorter folder/template."
            )
        return str(safe)


class FinalPathCollector(PostProcessor):
    """Collect only after all postprocessors and the final move have succeeded."""

    def __init__(self, downloader) -> None:
        super().__init__(downloader)
        self.paths: list[str] = []

    def run(self, info: dict):
        if info.get("filepath"):
            self.paths.append(info["filepath"])
        return [], info


def download(payload: dict, emit: EventSink) -> dict:
    data = dict(payload["options"])
    data["settings"] = Settings.from_dict(data["settings"])
    options = DownloadOptions(**data).validate()
    destination = ensure_output_dir(options.settings.download_folder)
    staging = Path(payload["staging"]).resolve()
    check_disk_space(destination, payload.get("estimated_size"))
    opts = build_options(options, staging, payload.get("ffmpeg", ""), emit)
    last_progress = 0.0

    def progress(event: dict) -> None:
        nonlocal last_progress
        if event["status"] == "finished":
            emit({"type": "state", "status": "Processing"})
        elif event["status"] == "downloading" and time.monotonic() - last_progress >= 0.2:
            last_progress = time.monotonic()
            emit(
                {
                    "type": "progress",
                    "downloaded_bytes": event.get("downloaded_bytes", 0),
                    "total_bytes": event.get("total_bytes") or event.get("total_bytes_estimate"),
                    "speed": event.get("speed"),
                    "eta": event.get("eta"),
                }
            )

    opts["progress_hooks"] = [progress]
    opts["postprocessor_hooks"] = [lambda _: emit({"type": "state", "status": "Processing"})]
    with SafeYoutubeDL(opts, staging) as ydl:
        info = ydl.extract_info(validate_url(payload["url"]), download=False)
        if not info or "entries" in info:
            raise DownloadError(
                "unavailable", "Select individual playlist entries before downloading."
            )
        if info.get("is_live"):
            raise DownloadError(
                "live", "Live streams are not supported. Try the finished recording."
            )
        if info.get("has_drm"):
            raise DownloadError("protected", "This media is protected and cannot be downloaded.")
        if payload.get("archive_directory") and ArchiveService(
            Path(payload["archive_directory"])
        ).contains_id(ydl._make_archive_id(info)):
            raise DownloadError("archive", "Previously downloaded. Choose Download again anyway.")
        info["playlist_index"] = options.playlist_index
        info["playlist"] = options.playlist_title
        estimate = info.get("filesize") or info.get("filesize_approx")
        if not estimate:
            estimate = (
                sum(
                    (f.get("filesize") or f.get("filesize_approx") or 0)
                    for f in info.get("requested_formats") or []
                )
                or None
            )
        check_disk_space(destination, estimate)
        emit({"type": "metadata", "media": compact_media(info, payload["url"])})
        collector = FinalPathCollector(ydl)
        ydl.add_post_processor(collector, when="after_move")
        emit({"type": "state", "status": "Downloading"})
        result = ydl.process_ie_result(info, download=True)
        if not result or len(collector.paths) != 1:
            raise DownloadError("output", "The engine did not produce a verified final media file.")
        media = contained_file(staging, collector.paths[0])
        if not media.is_file() or media.stat().st_size <= 0 or media.suffix in {".part", ".ytdl"}:
            raise DownloadError(
                "output", "The expected output file is missing, incomplete, or empty."
            )
        expected = options.settings.audio_format if options.mode == "audio" else options.container
        if options.mode != "custom" and media.suffix.lower() != "." + expected:
            raise DownloadError("output", "The engine produced a different format than requested.")
        final = media
        return {
            "output_file": str(final),
            "file_size": final.stat().st_size,
            "archive_id": ydl._make_archive_id(info),
            "title": info.get("title") or "Untitled",
        }


def serialize_options(options: DownloadOptions) -> dict:
    return asdict(options)
