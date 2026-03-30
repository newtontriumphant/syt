#!/usr/bin/env python3

import sys
import os
import re
import json
import shutil
import signal
import subprocess
import argparse
import platform
from pathlib import Path

__version__ = "1.0.1"

# ascii art generator my goat :3

LOGO = r"""
  ███████╗██╗   ██╗████████╗
  ██╔════╝╚██╗ ██╔╝╚══██╔══╝
  ███████╗ ╚████╔╝    ██║   
  ╚════██║  ╚██╔╝     ██║   
  ███████║   ██║      ██║   
  ╚══════╝   ╚═╝      ╚═╝   
     simple youtube downloader
"""

SUPPORTS_COLOR = (
    hasattr(sys.stdout, "isatty")
    and sys.stdout.isatty()
    and os.environ.get("NO_COLOR") is None
)

def _c(code, text):
    if SUPPORTS_COLOR:
        return f"\033[{code}m{text}\033[0m"
    return text

def bold(t): return _c("1", t)
def dim(t): return _c("2", t)
def green(t): return _c("32", t)
def cyan(t): return _c("36", t)
def yellow(t): return _c("33", t)
def red(t): return _c("31", t)
def magenta(t): return _c("35", t)

def out(*args, **kwargs):
    print(*args, **kwargs, flush=True)


def check_deps():
    missing = []
    if not shutil.which("yt-dlp"):
        missing.append("yt-dlp")
    if not shutil.which("ffmpeg"):
        missing.append("ffmpeg")
    if missing:
        out(red(f"\nerror :c - missing required tools: {', '.join(missing)}"))
        out(red("please install them first:"))
        if "yt-dlp" in missing:
            out(dim("    pip install yt-dlp"))
        if "ffmpeg" in missing:
            sys_name = platform.system()
            if sys_name == "Darwin":
                out(dim("    brew install ffmpeg"))
            elif sys_name == "Linux":
                out(dim("    sudo apt install ffmpeg"))
            else:
                out(dim("    download from https://ffmpeg.org/download.html/ !"))
        sys.exit(1)


def _looks_like_url(text):
    t = text.strip()
    return (
        t.startswith("http://")
        or t.startswith("https://")
        or t.startswith("www.")
        or t.startswith("youtube.com")
        or t.startswith("youtu.be")
        or t.startswith("music.youtube.com")
    )

YOUTUBE_PATTERNS = [ # i don't normally use AI but it sure as hell is good for regexes!
    r'(?:https?://)?(?:www\.)?youtube\.com/watch\?[\w&=%-]+',
    r'(?:https?://)?(?:www\.)?youtube\.com/shorts/[\w-]+',
    r'(?:https?://)?(?:www\.)?youtube\.com/live/[\w-]+',
    r'(?:https?://)?(?:www\.)?youtube\.com/embed/[\w-]+',
    r'(?:https?://)?youtu\.be/[\w-]+',
    r'(?:https?://)?(?:www\.)?youtube\.com/playlist\?[\w&=%-]+',
    r'(?:https?://)?(?:www\.)?youtube\.com/(?:c/|channel/|user/|@)[\w.-]+',
    r'(?:https?://)?music\.youtube\.com/watch\?[\w&=%-]+',
    r'(?:https?://)?music\.youtube\.com/playlist\?[\w&=%-]+',
    r'(?:https?://)?music\.youtube\.com/browse/[\w-]+',
    r'(?:https?://)?(?:www\.)?youtube\.com/clip/[\w-]+',
]

class LinkType:
    VIDEO = "video"
    SHORT = "short"
    LIVE = "live"
    PLAYLIST = "playlist"
    MUSIC_TRACK = "music_track"
    MUSIC_PLAYLIST = "music_playlist"
    MUSIC_ALBUM = "music_album"
    CHANNEL = "channel"
    CLIP = "clip"
    UNKNOWN = "unknown"

def classify_link(url):
    url_lower = url.lower().strip()

    if "music.youtube.com" in url_lower:
        if "playlist?list=" in url_lower or "/playlist?" in url_lower:
            return LinkType.MUSIC_PLAYLIST
        if "/browse/" in url_lower:
            return LinkType.MUSIC_ALBUM
        return LinkType.MUSIC_TRACK
    
    if "youtube.com/shorts/" in url_lower:
        return LinkType.SHORT
    if "youtube.com/live/" in url_lower:
        return LinkType.LIVE
    if "youtube.com/playlist?list=" in url_lower or "youtube.com/playlist?" in url_lower:
        return LinkType.PLAYLIST
    if "youtube.com/clip/" in url_lower:
        return LinkType.CLIP
    if re.search(r'youtube\.com/(?:c/|channel/|user/|@)', url_lower):
        return LinkType.CHANNEL
    # the video check is last because it can be confused with playlists and shorts if done first :3
    if "youtube.com/watch" in url_lower or "youtu.be/" in url_lower or "youtube.com/embed/" in url_lower:
        return LinkType.VIDEO
    
    return LinkType.UNKNOWN

def is_valid_link(url):
    for pat in YOUTUBE_PATTERNS:
        if re.search(pat, url):
            return True
    return False

def is_collection(link_type):
    return link_type in (
        LinkType.PLAYLIST,
        LinkType.MUSIC_PLAYLIST,
        LinkType.MUSIC_ALBUM,
        LinkType.CHANNEL,
    )

def is_music(link_type):
    return link_type in (
        LinkType.MUSIC_TRACK,
        LinkType.MUSIC_PLAYLIST,
        LinkType.MUSIC_ALBUM,
    )

def strip_last_param(url):
    return re.sub(r'[&?]list=[^&]*', '', url)

# factory defaults cuz im so funny, ts took like an hour to consolidate
FACTORY_DEFAULTS = {
    "video_quality": "1080",
    "audio_quality": "0",
    "video_format": "mp4",
    "audio_format": "mp3",
    "embed_thumbnail": True,
    "embed_metadata": True,
    "embed_chapters": True,
    "embed_subs": False,
    "write_subs": False,
    "sub_lang": "en",
    "auto_subs": False,
    "embed_album_art": True,
    "add_to_archive": False,
    "archive_file": "downloaded.txt",
    "rate_limit": "",
    "concurrent_fragments": 4,
    "retries": 10,
    "sponsorblock_remove": "",
    "output_template": "%(title)s.%(ext)s",
    "playlist_output_template": "%(playlist_title)s/%(playlist_index)03d - %(title)s.%(ext)s",
    "restrict_filenames": False,
    "prefer_free_formats": False,
    "write_description": False,
    "write_comments": False,
    "write_info_json": False,
    "keep_original": False,
    "no_overwrites": True,
    "geo_bypass": True,
    "sleep_interval": 0,
    "max_sleep_interval": 0,
    "cookies_from_browser": "",
    "proxy": "",
    "ffmpeg_location": "",
}

def config_path():
    if platform.system() == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "syt" / "config.json"

def load_saved_overrides():
    p = config_path()
    if p.exists():
        try:
            with open(p) as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_overrides(saved):
    p = config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        json.dump(saved, f, indent=2)

def effective_config(saved, session):
    cfg = dict(FACTORY_DEFAULTS)
    cfg.update(saved)
    cfg.update(session)
    return cfg

def build_cmd(url, mode, cfg, output_dir):
    link_type = classify_link(url)
    cmd = ["yt-dlp", "--no-warnings", "--progress"]

    if not is_collection(link_type):
        cmd.append("--no-playlist")
        url = strip_last_param(url) # prevents yt-dlp from treating some videos as playlists because of the presence of a list param in the url, even if it's not actually a playlist (:

    cmd += ["--retries", str(cfg["retries"])]
    if cfg["geo_bypass"]:
        cmd.append("--geo-bypass")
    if cfg["rate_limit"]:
        cmd += ["--rate-limit", cfg["rate_limit"]]
    if cfg["concurrent_fragments"] > 1:
        cmd += ["--concurrent-fragments", str(cfg["concurrent_fragments"])]
    if cfg["proxy"]:
        cmd += ["--proxy", cfg["proxy"]]
    if cfg["cookies_from_browser"]:
        cmd += ["--cookies-from-browser", cfg["cookies_from_browser"]]
    if cfg["ffmpeg_location"]:
        cmd += ["--ffmpeg-location", cfg["ffmpeg_location"]]
    if cfg["sleep_interval"]:
        cmd += ["--sleep-interval", str(cfg["sleep_interval"])]
    if cfg["max_sleep_interval"]:
        cmd += ["--max-sleep-interval", str(cfg["max_sleep_interval"])]

    if cfg["add_to_archive"]:
        cmd += ["--download-archive", str(Path(output_dir) / cfg["archive_file"])]

    if cfg["no_overwrites"]:
        cmd.append("--no-overwrites")

    if cfg["restrict_filenames"]:
        cmd.append("--restrict-filenames")

    if is_collection(link_type):
        tmpl = cfg["playlist_output_template"]
    else:
        tmpl = cfg["output_template"]
    cmd += ["-o", str(Path(output_dir) / tmpl)]

    if cfg["sponsorblock_remove"]:
        cmd += ["--sponsorblock-remove", cfg["sponsorblock_remove"]]

    if mode == "audio" or (mode == "video" and is_music(link_type)):
        _build_audio_args(cmd, cfg)
    else:
        _build_video_args(cmd, cfg)

    if cfg["write_description"]:
        cmd.append("--write-description")
    if cfg["write_comments"]:
        cmd.append("--write-comments")
    if cfg["write_info_json"]:
        cmd.append("--write-info-json")
    if cfg["keep_original"]:
        cmd.append("--keep-video")

    cmd.append(url)
    return cmd

def _build_audio_args(cmd, cfg):
    cmd += ["-x", "--audio-format", cfg["audio_format"]]
    cmd += ["--audio-quality", str(cfg["audio_quality"])]
    if cfg["embed_thumbnail"] or cfg["embed_album_art"]:
        cmd.append("--embed-thumbnail")
    if cfg["embed_metadata"]:
        cmd.append("--embed-metadata")
    if cfg["embed_chapters"]:
        cmd.append("--embed-chapters")
    if cfg["prefer_free_formats"]:
        cmd.append("--prefer-free-formats")


# disclaimer: AI used to debug codecs and heightmap on lines 304-315 and 325-330

def _build_video_args(cmd, cfg):
    quality = cfg["video_quality"]
    vfmt = cfg["video_format"]

    height_map = {
        "4320": 4320, "8k": 4320,
        "2160": 2160, "4k": 2160,
        "1440": 1440, "2k": 1440,
        "1080": 1080,
        "720": 720,
        "480": 480,
        "360": 360,
        "240": 240,
        "144": 144,
        "best": None,
    }
    max_h = height_map.get(str(quality).lower())

    sort_parts = []

    if max_h:
        sort_parts.append(f"res:{max_h}")
    else:
        sort_parts.append("res")

    if vfmt == "mp4":
        sort_parts.extend(["vcodec:h264", "acodec:aac", "ext:mp4"])
    elif vfmt == "webm":
        sort_parts.extend(["vcodec:vp9", "acodec:opus", "ext:webm"])
    elif vfmt == "mkv":
        sort_parts.extend(["vcodec:h264", "acodec:aac"])

    cmd += ["-S", ",".join(sort_parts)]
    cmd += ["--merge-output-format", vfmt]

    if cfg["embed_thumbnail"]:
        cmd.append("--embed-thumbnail")
    if cfg["embed_metadata"]:
        cmd.append("--embed-metadata")
    if cfg["embed_chapters"]:
        cmd.append("--embed-chapters")
    if cfg["embed_subs"] or cfg["write_subs"]:
        if cfg["write_subs"]:
            cmd.append("--write-subs")
        if cfg["embed_subs"]:
            cmd.append("--embed-subs")
        cmd += ["--sub-lang", cfg["sub_lang"]]
        if cfg["auto_subs"]:
            cmd.append("--write-auto-subs")
    if cfg["prefer_free_formats"]:
        cmd.append("--prefer-free-formats")


def run_download(url, mode, cfg, output_dir):
    link_type = classify_link(url)
    type_label = link_type.replace("_", " ").title()
    mode_label = "Audio + Video" if mode == "video" else "Audio Only"

    out()
    out(cyan(f"  -- Detected: {bold(type_label)}"))
    out(cyan(f"  │  Mode:     {bold(mode_label)}"))
    out(cyan(f"  │  Save to:  {dim(output_dir)}"))
    out(cyan(f"  -- Starting Goon Sesh..."))
    out()

    cmd = build_cmd(url, mode, cfg, output_dir)

    try:
        proc = subprocess.run(cmd, cwd=output_dir)
        if proc.returncode == 0:
            out(green(f"\n  ✓ download complete!"))
        else:
            out(red(f"\n  ✗ yt-dlp exited with code {proc.returncode}"))
            out(dim(f"    Command was: {' '.join(cmd)}"))
    except KeyboardInterrupt:
        out(yellow("\n  ✗ download cancelled manually :c"))
    except FileNotFoundError:
        out(red("\n  ✗ yt-dlp not found. Install it!! pip install yt-dlp"))

    
def clear_screen():
    os.system("cls" if platform.system() == "Windows" else "clear")

def ask_link():
    while True:
        try:
            url = input(magenta("  paste link :3 --> ")).strip()
        except (EOFError, KeyboardInterrupt):
            out()
            sys.exit(0)
        if not url:
            continue
        if is_valid_link(url):
            return url
        out(red("  ✗ that doesn't look like a youtube link. try again!"))

def auto_mode_for_link(url):
    link_type = classify_link(url)
    if is_music(link_type):
        return "audio"
    return "video"

def main_menu(saved, session, output_dir):
    while True:
        cfg = effective_config(saved, session)
        clear_screen()
        out(magenta(LOGO))
        out(f"  {bold('1.')} Audio + Video")
        out(f"  {bold('2.')} Audio Only")
        out(f"  {bold('3.')} Advanced Options")
        out(f"  {bold('q.')} Quit")
        out()
        out(dim("  or just paste a link directly :3"))
        out()

        try:
            choice = input(cyan("  --> ")).strip()
        except (EOFError, KeyboardInterrupt):
            out()
            break

        choice_lower = choice.lower()

        if _looks_like_url(choice) and is_valid_link(choice):
            mode = auto_mode_for_link(choice)
            mode_name = "audio" if mode == "audio" else "video (1080p)"
            out(dim(f"\n  Auto-detected link! Downloading as {mode_name}..."))
            run_download(choice, mode, cfg, output_dir)
            _pause()
            continue

        if choice_lower == "1":
            url = ask_link()
            run_download(url, "video", cfg, output_dir)
            _pause()
        elif choice_lower == "2":
            url = ask_link()
            run_download(url, "audio", cfg, output_dir)
            _pause()
        elif choice_lower == "3":
            advanced_menu(saved, session)
        elif choice_lower in ("q", "quit", "exit"):
            break
        else:
            out(red("  ✗ Invalid choice."))
            _pause()

def _pause():
    try:
        input(dim("\n  Press Enter to continue..."))
    except (EOFError, KeyboardInterrupt):
        pass

# holy fudge (ai-assisted)
ADVANCED_OPTIONS = [
    ("video_quality", "Video quality", "choice", ["144","240","360","480","720","1080","1440","2160","4320","best"]),
    ("audio_quality", "Audio quality (0=best, 9=worst)", "choice", ["0","1","2","3","4","5","6","7","8","9"]),
    ("video_format", "Video container format", "choice", ["mp4","mkv","webm","avi","mov","flv"]),
    ("audio_format", "Audio format", "choice", ["mp3","m4a","opus","flac","wav","aac","ogg","vorbis"]),
    ("embed_thumbnail", "Embed thumbnail in file", "bool", None),
    ("embed_album_art", "Embed album art (music)", "bool", None),
    ("embed_metadata", "Embed metadata tags", "bool", None),
    ("embed_chapters", "Embed chapter markers", "bool", None),
    ("embed_subs", "Embed subtitles in video", "bool", None),
    ("write_subs", "Download subtitle files", "bool", None),
    ("sub_lang", "Subtitle language(s)", "str", "e.g. en, en,es,fr"),
    ("auto_subs", "Include auto-generated subs", "bool", None),
    ("sponsorblock_remove", "SponsorBlock segments to remove", "str", "e.g. sponsor,intro,outro,selfpromo"),
    ("restrict_filenames", "Restrict filenames (ASCII only)", "bool", None),
    ("no_overwrites", "Skip already-downloaded files", "bool", None),
    ("concurrent_fragments", "Concurrent download fragments", "int", "1-16"),
    ("retries", "Retry attempts on failure", "int", "1-100"),
    ("rate_limit", "Download speed limit", "str", "e.g. 5M, 500K, or empty for unlimited"),
    ("output_template", "Output filename template", "str", "yt-dlp template syntax"),
    ("playlist_output_template", "Playlist filename template", "str", "yt-dlp template syntax"),
    ("add_to_archive", "Track downloaded files (skip re-downloads)", "bool", None),
    ("archive_file", "Archive filename", "str", "default: downloaded.txt"),
    ("write_description", "Save video description to .txt", "bool", None),
    ("write_comments", "Save video comments", "bool", None),
    ("write_info_json", "Save metadata as .info.json", "bool", None),
    ("keep_original", "Keep original file after conversion", "bool", None),
    ("prefer_free_formats", "Prefer free/open formats (webm/opus)", "bool", None),
    ("geo_bypass", "Bypass geo-restrictions", "bool", None),
    ("sleep_interval", "Sleep between downloads (seconds)", "int", "0-60"),
    ("max_sleep_interval", "Max random sleep (seconds)", "int", "0-300"),
    ("cookies_from_browser", "Use cookies from browser", "str", "chrome, firefox, edge, safari, or empty"),
    ("proxy", "Proxy URL", "str", "e.g. socks5://127.0.0.1:1080 or empty"),
    ("ffmpeg_location", "Custom ffmpeg path", "str", "leave empty for system default"),
]

def advanced_menu(saved, session):
    while True:
        cfg = effective_config(saved, session)
        clear_screen()
        out(magenta(LOGO))
        out(bold("  -- Advanced Options --\n"))

        for i, (key, label, vtype, _) in enumerate(ADVANCED_OPTIONS, 1):
            val = cfg.get(key, FACTORY_DEFAULTS.get(key))
            val_str = _format_val(val)
            factory_val = FACTORY_DEFAULTS.get(key)
            tag = ""
            if key in session:
                tag = dim(" [session]")
            elif key in saved and saved[key] != factory_val:
                tag = dim(" [saved]")
            num = f"{i:>2}"
            out(f"  {dim(num)}.  {label}: {cyan(val_str)}{tag}")

        out(f"\n  {dim(' r')}.  Reset all to factory defaults")
        out(f"  {dim(' b')}.  Back")
        out()

        try:
            choice = input(cyan("  option --> ")).strip().lower()
        except (EOFError, KeyboardInterrupt):
            out()
            break

        if choice in ("b", "back", "q"):
            break
        if choice in ("r", "reset"):
            saved.clear()
            session.clear()
            p = config_path()
            if p.exists():
                p.unlink()
            out(green("  ✓ Reset to factory defaults."))
            _pause()
            continue

        try:
            idx = int(choice) - 1
        except ValueError:
            out(red("  ✗ Invalid choice."))
            _pause()
            continue

        if idx < 0 or idx >= len(ADVANCED_OPTIONS):
            out(red("  ✗ Invalid choice."))
            _pause()
            continue

        key, label, vtype, hint = ADVANCED_OPTIONS[idx]
        _edit_option(saved, session, key, label, vtype, hint)

def _format_val(val):
    if isinstance(val, bool):
        return "Yes" if val else "No"
    if val == "" or val is None:
        return "(not set)"
    return str(val)

def _edit_option(saved, session, key, label, vtype, hint):
    cfg = effective_config(saved, session)
    current = cfg.get(key, FACTORY_DEFAULTS.get(key))
    out()
    out(f"  {bold(label)}")
    out(f"  Current: {cyan(_format_val(current))}")

    new_val = None

    if vtype == "bool":
        out(f"  {dim('Enter y/n:')}")
        try:
            v = input(cyan("  --> ")).strip().lower()
        except (EOFError, KeyboardInterrupt):
            return
        if v in ("y", "yes", "true", "1", "on"):
            new_val = True
        elif v in ("n", "no", "false", "0", "off"):
            new_val = False
        else:
            out(red("  ✗ Invalid. Kept previous value."))
            _pause()
            return
    elif vtype == "choice":
        out(f"  {dim('Choices:')} {', '.join(hint)}")
        try:
            v = input(cyan("  --> ")).strip()
        except (EOFError, KeyboardInterrupt):
            return
        if v in hint:
            new_val = v
        else:
            out(red(f"  ✗ Must be one of: {', '.join(hint)}"))
            _pause()
            return
    elif vtype == "int":
        if hint:
            out(f"  {dim(hint)}")
        try:
            v = input(cyan("  --> ")).strip()
        except (EOFError, KeyboardInterrupt):
            return
        try:
            new_val = int(v)
        except ValueError:
            out(red("  ✗ Must be a number."))
            _pause()
            return
    else:
        if hint:
            out(f"  {dim(hint)}")
        out(f"  {dim('Leave blank to clear.')}")
        try:
            v = input(cyan("  --> ")).strip()
        except (EOFError, KeyboardInterrupt):
            return
        new_val = v

    out(green(f"  ✓ {label} set to {_format_val(new_val)}"))
    out()
    out(f"  {bold('d.')} Save as default")
    out(f"  {bold('s.')} This session only")

    try:
        persist = input(cyan("  --> ")).strip().lower()
    except (EOFError, KeyboardInterrupt):
        return

    if persist in ("d", "default"):
        saved[key] = new_val
        session.pop(key, None)
        save_overrides(saved)
        out(green("  ✓ Saved as default."))
    else:
        session[key] = new_val
        out(green("  ✓ Applied for this session only."))

    _pause()


def main():
    signal.signal(signal.SIGINT, lambda *_: (print(), sys.exit(0)))

    check_deps()
    saved = load_saved_overrides()
    session = {}
    output_dir = os.getcwd()

    parser = argparse.ArgumentParser(
        prog="syt",
        description="SYT — Simple YouTube Downloader",
        add_help=True,
    )
    parser.add_argument("url", nargs="?", help="YouTube URL to download")
    parser.add_argument("-a", "--audio", action="store_true", help="Download audio only")
    parser.add_argument("-v", "--version", action="version", version=f"syt {__version__}")
    args = parser.parse_args()

    if args.url:
        url = args.url
        if not is_valid_link(url):
            out(red(f"  ✗ Not a recognized YouTube link: {url}"))
            out(dim('  Tip: quote the URL so your shell doesn\'t mangle it:'))
            out(dim('       syt "https://www.youtube.com/watch?v=..."'))
            sys.exit(1)
        cfg = effective_config(saved, session)
        mode = "audio" if args.audio else "video"
        run_download(url, mode, cfg, output_dir)
    else:
        main_menu(saved, session, output_dir)


if __name__ == "__main__":
    main()