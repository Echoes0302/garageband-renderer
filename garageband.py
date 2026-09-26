#!/usr/bin/env python3
"""Render ABC or MIDI files through GarageBand, then apply a local mix preset."""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Iterable


HERE = Path(__file__).resolve().parent
DEFAULT_GARAGEBAND_DIR = Path.home() / "Music" / "GarageBand"
DEFAULT_OUTPUT_DIR = DEFAULT_GARAGEBAND_DIR / "exports"
MIX_PRESETS = ("none", "dry", "room", "hall", "oldrecord", "musicbox")


class GarageBandError(RuntimeError):
    pass


def run(command: list[str], *, timeout: float | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise GarageBandError(f"命令超时：{' '.join(command)}") from exc


def garageband_running() -> bool:
    return run(["pgrep", "-x", "GarageBand"], timeout=5).returncode == 0


def validate_output_name(name: str) -> str:
    if not name or name in {".", ".."}:
        raise GarageBandError("输出名称不能为空")
    if Path(name).name != name or "/" in name or "\0" in name:
        raise GarageBandError("输出名称只能是文件名，不能包含路径")
    return name


def require_command(name: str, install_hint: str) -> None:
    if shutil.which(name) is None:
        raise GarageBandError(f"缺少 {name}。{install_hint}")


def check_runtime(*, needs_abc: bool) -> None:
    if platform.system() != "Darwin":
        raise GarageBandError("这个工具只支持 macOS")
    if not Path("/Applications/GarageBand.app").exists():
        raise GarageBandError("没有找到 /Applications/GarageBand.app")
    require_command("osascript", "它应当随 macOS 自带。")
    if needs_abc:
        require_command("abc2midi", "请先运行 brew install abcmidi。")


def accessibility_enabled() -> bool:
    result = run(
        [
            "osascript",
            "-e",
            'tell application "System Events" to get UI elements enabled',
        ],
        timeout=10,
    )
    return result.returncode == 0 and result.stdout.strip().lower() == "true"


def doctor() -> int:
    checks = [
        ("macOS", platform.system() == "Darwin", platform.platform()),
        (
            "GarageBand",
            Path("/Applications/GarageBand.app").exists(),
            "/Applications/GarageBand.app",
        ),
        ("abc2midi", shutil.which("abc2midi") is not None, shutil.which("abc2midi") or "未安装"),
        ("辅助功能权限", accessibility_enabled(), "System Events UI automation"),
    ]
    failed = False
    for label, ok, detail in checks:
        failed = failed or not ok
        print(f"[{'OK' if ok else 'FAIL'}] {label}: {detail}")
    try:
        probe = run(
            [sys.executable, "-c", "import numpy, pedalboard; print(pedalboard.__version__)"],
            timeout=10,
        )
        ok = probe.returncode == 0
        detail = probe.stdout.strip() if ok else "请运行 ./install.sh"
    except GarageBandError:
        ok, detail = False, "请运行 ./install.sh"
    failed = failed or not ok
    print(f"[{'OK' if ok else 'FAIL'}] Python 混音依赖: {detail}")
    return 1 if failed else 0


def quit_garageband(timeout: float = 12) -> None:
    # 先收掉可能悬着的对话框，再请求不保存退出；不使用 pkill，避免误伤未保存工程。
    run(
        [
            "osascript",
            "-e",
            'tell application "GarageBand" to activate',
            "-e",
            'tell application "System Events" to key code 53',
            "-e",
            "delay 0.3",
            "-e",
            'tell application "System Events" to key code 53',
        ],
        timeout=10,
    )
    result = run(
        ["osascript", "-e", 'tell application "GarageBand" to quit saving no'],
        timeout=10,
    )
    if result.returncode != 0:
        raise GarageBandError(f"GarageBand 退出失败：{result.stderr.strip()}")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not garageband_running():
            return
        time.sleep(0.25)
    raise GarageBandError("GarageBand 没有退出；为保护未保存工程，工具没有强制杀进程")


def convert_abc_to_midi(source: Path, destination: Path) -> None:
    result = run(["abc2midi", str(source), "-o", str(destination)], timeout=60)
    if result.returncode != 0 or not destination.exists() or destination.stat().st_size == 0:
        detail = (result.stdout + result.stderr).strip()
        raise GarageBandError(f"abc2midi 转换失败：\n{detail}")
    warnings = [
        line
        for line in (result.stdout + result.stderr).splitlines()
        if "Warning" in line or "Error" in line
    ]
    if warnings:
        print("abc2midi 提示：\n  " + "\n  ".join(warnings[:10]), file=sys.stderr)


def prepare_midi(source: Path, destination: Path) -> None:
    suffix = source.suffix.lower()
    if suffix == ".abc":
        convert_abc_to_midi(source, destination)
    elif suffix in {".mid", ".midi"}:
        if source != destination:
            shutil.copy2(source, destination)
    else:
        raise GarageBandError("输入文件只支持 .abc、.mid 或 .midi")


def wait_for_garageband_window(timeout: float = 45) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = run(
            [
                "osascript",
                "-e",
                'tell application "System Events" to tell process "GarageBand" to get count of windows',
            ],
            timeout=5,
        )
        try:
            if result.returncode == 0 and int(result.stdout.strip()) > 0:
                return
        except ValueError:
            pass
        time.sleep(0.5)
    raise GarageBandError("GarageBand 窗口没有出现")


def candidate_directories(output_dir: Path) -> list[Path]:
    directories = [
        output_dir,
        DEFAULT_GARAGEBAND_DIR,
        Path.home() / "Music",
        Path.home() / "Desktop",
        Path.home() / "Documents",
        Path.home() / "Downloads",
    ]
    return list(dict.fromkeys(directories))


def is_fresh_file(path: Path, *, started_at: float) -> bool:
    try:
        stat = path.stat()
    except FileNotFoundError:
        return False
    return path.is_file() and stat.st_size > 0 and stat.st_mtime >= started_at - 2


def find_export(
    filename: str,
    *,
    started_at: float,
    directories: Iterable[Path],
    timeout: float = 120,
) -> Path:
    deadline = time.monotonic() + timeout
    last_sizes: dict[Path, int] = {}
    while time.monotonic() < deadline:
        for directory in directories:
            path = directory / filename
            if not is_fresh_file(path, started_at=started_at):
                continue
            size = path.stat().st_size
            if last_sizes.get(path) == size:
                return path
            last_sizes[path] = size
        time.sleep(0.5)

    # Spotlight is only a final fallback. The unique staging name and timestamp
    # guard prevent a stale file elsewhere from being mistaken for this export.
    result = run(["mdfind", "-name", filename], timeout=15)
    for line in result.stdout.splitlines():
        path = Path(line)
        if path.name == filename and is_fresh_file(path, started_at=started_at):
            return path
    raise GarageBandError(f"没有找到 GarageBand 导出的文件：{filename}")


def render(
    midi: Path,
    output_dir: Path,
    output_name: str,
    *,
    force_close: bool,
    keep_open: bool,
) -> Path:
    if garageband_running():
        if not force_close:
            raise GarageBandError(
                "GarageBand 已经开着；工具拒绝碰现有工程。确认可以不保存关闭时再加 --force-close。"
            )
        quit_garageband()

    staging_stem = f"garageband-render-{uuid.uuid4().hex}"
    staging_filename = f"{staging_stem}.mp3"
    raw_destination = output_dir / f"{output_name}-raw.mp3"
    started_at = time.time()

    opened = False
    try:
        result = run(["open", "-a", "GarageBand", str(midi)], timeout=15)
        if result.returncode != 0:
            raise GarageBandError(f"无法打开 GarageBand：{result.stderr.strip()}")
        opened = True
        wait_for_garageband_window()
        time.sleep(1.5)
        result = run(
            [
                "osascript",
                str(HERE / "export.applescript"),
                str(output_dir),
                staging_stem,
                "MP3",
            ],
            timeout=60,
        )
        if result.returncode != 0:
            raise GarageBandError(f"导出脚本失败：{result.stderr.strip()}")
        exported = find_export(
            staging_filename,
            started_at=started_at,
            directories=candidate_directories(output_dir),
        )
        raw_destination.unlink(missing_ok=True)
        shutil.move(str(exported), raw_destination)
        return raw_destination
    finally:
        if opened and not keep_open and garageband_running():
            quit_garageband()


def apply_mix(source: Path, destination: Path, preset: str) -> None:
    if preset == "none":
        shutil.copy2(source, destination)
        return
    result = run(
        [
            sys.executable,
            str(HERE / "mix.py"),
            str(source),
            str(destination),
            "--preset",
            preset,
        ],
        timeout=300,
    )
    if result.returncode != 0:
        raise GarageBandError(
            "混音失败。先运行 ./install.sh，然后重试。\n" + result.stderr.strip()
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="把 ABC/MIDI 交给 GarageBand 出声，再生成混音 MP3。"
    )
    parser.add_argument("source", nargs="?", help=".abc、.mid 或 .midi 文件")
    parser.add_argument("--mix", choices=MIX_PRESETS, default="room")
    parser.add_argument("--out", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--name", help="输出文件名（不含扩展名）")
    parser.add_argument(
        "--force-close",
        "--force",
        action="store_true",
        dest="force_close",
        help="先不保存关闭当前 GarageBand 工程；有未保存内容时请勿使用",
    )
    parser.add_argument("--keep-open", action="store_true", help="导出后保留 GarageBand 窗口")
    parser.add_argument("--doctor", action="store_true", help="只检查运行环境")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.doctor:
        return doctor()
    if not args.source:
        raise GarageBandError("请提供 .abc、.mid 或 .midi 文件，或运行 --doctor")

    source = Path(args.source).expanduser().resolve()
    if not source.is_file():
        raise GarageBandError(f"输入文件不存在：{source}")
    name = validate_output_name(args.name or source.stem)
    output_dir = Path(args.out).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    check_runtime(needs_abc=source.suffix.lower() == ".abc")

    midi = output_dir / f"{name}.mid"
    prepare_midi(source, midi)
    raw = render(
        midi,
        output_dir,
        name,
        force_close=args.force_close,
        keep_open=args.keep_open,
    )
    final = output_dir / f"{name}.mp3"
    apply_mix(raw, final, args.mix)
    print(final)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GarageBandError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        raise SystemExit(2)
