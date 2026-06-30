#!/usr/bin/env python3
"""
pipeline_config.py

Shared configuration loader for the Python HyperDeck pipeline. This keeps the
pipeline on the standard library while treating config.yaml as the single
source of truth for Python scripts.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path


CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "config.yaml"


@dataclass(frozen=True)
class HyperDeckConfig:
    name: str
    ip: str
    volumes: tuple[str, ...]


@dataclass(frozen=True)
class ServiceWindow:
    time: str
    label: str

    @property
    def minutes(self) -> int:
        hours, minutes = self.time.split(":", 1)
        return int(hours) * 60 + int(minutes)


@dataclass(frozen=True)
class PipelineConfig:
    hyperdecks: tuple[HyperDeckConfig, ...]
    downloads_dir: Path
    log_file: Path
    hd1_services: tuple[ServiceWindow, ...]
    hd2_services: tuple[ServiceWindow, ...]
    time_tolerance_min: int
    upload_remote: str
    upload_dest_base: str
    upload_extension: str
    email_recipients: tuple[str, ...]
    mail_tail_lines: int


def default_config() -> PipelineConfig:
    return PipelineConfig(
        hyperdecks=(
            HyperDeckConfig(name="HD1", ip="10.20.193.141", volumes=("sd1", "sd2")),
            HyperDeckConfig(name="HD2", ip="10.20.193.113", volumes=("1", "2")),
        ),
        downloads_dir=Path.home() / "HyperDeckDownloads",
        log_file=Path("/usr/local/var/log/hyperdeck/sync_upload.log"),
        hd1_services=(
            ServiceWindow(time="08:25", label="08-30am"),
            ServiceWindow(time="09:40", label="09-45am"),
            ServiceWindow(time="10:55", label="11-00am"),
            ServiceWindow(time="12:10", label="12-15pm"),
        ),
        hd2_services=(
            ServiceWindow(time="08:54", label="09-00am"),
            ServiceWindow(time="10:24", label="10-30am"),
        ),
        time_tolerance_min=3,
        upload_remote="gdrive",
        upload_dest_base="Online",
        upload_extension=".mp4",
        email_recipients=(
            "bfiles@northridgerochester.com",
            "joconnor@northridgerochester.com",
        ),
        mail_tail_lines=65,
    )


def strip_comment(raw_line: str) -> str:
    quote_char = None
    result: list[str] = []
    for char in raw_line:
        if char in {"'", '"'}:
            if quote_char is None:
                quote_char = char
            elif quote_char == char:
                quote_char = None
        if char == "#" and quote_char is None:
            break
        result.append(char)
    return "".join(result).rstrip()


def parse_inline_list(raw_value: str) -> list[object]:
    inner = raw_value[1:-1].strip()
    if not inner:
        return []

    items: list[str] = []
    current: list[str] = []
    quote_char = None
    for char in inner:
        if char in {"'", '"'}:
            if quote_char is None:
                quote_char = char
            elif quote_char == char:
                quote_char = None
        if char == "," and quote_char is None:
            items.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    if current:
        items.append("".join(current).strip())
    return [parse_scalar(item) for item in items]


def parse_scalar(raw_value: str) -> object:
    value = raw_value.strip()
    if not value:
        return ""
    if value.startswith("[") and value.endswith("]"):
        return parse_inline_list(value)
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.lstrip("-").isdigit():
        return int(value)
    return value


def parse_yaml_subset(path: Path) -> object:
    tokens: list[tuple[int, str]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = strip_comment(raw_line)
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        tokens.append((indent, line.strip()))

    index = 0

    def parse_block(expected_indent: int) -> object:
        nonlocal index
        if index >= len(tokens):
            return {}

        current_indent, current_value = tokens[index]
        if current_indent != expected_indent:
            return {}

        if current_value.startswith("- "):
            result: list[object] = []
            while index < len(tokens):
                indent, value = tokens[index]
                if indent != expected_indent or not value.startswith("- "):
                    break

                item_body = value[2:].strip()
                index += 1

                if not item_body:
                    item = parse_block(expected_indent + 2)
                    result.append(item)
                    continue

                if ":" in item_body:
                    key, rest = item_body.split(":", 1)
                    item: dict[str, object] = {}
                    rest = rest.strip()
                    if rest:
                        item[key.strip()] = parse_scalar(rest)
                    else:
                        item[key.strip()] = {}

                    if index < len(tokens) and tokens[index][0] > expected_indent:
                        nested = parse_block(expected_indent + 2)
                        if isinstance(nested, dict):
                            item.update(nested)
                    result.append(item)
                    continue

                result.append(parse_scalar(item_body))

            return result

        result_dict: dict[str, object] = {}
        while index < len(tokens):
            indent, value = tokens[index]
            if indent != expected_indent or value.startswith("- "):
                break

            key, _, rest = value.partition(":")
            key = key.strip()
            rest = rest.strip()
            index += 1

            if rest:
                result_dict[key] = parse_scalar(rest)
                continue

            if index < len(tokens) and tokens[index][0] > expected_indent:
                result_dict[key] = parse_block(expected_indent + 2)
            else:
                result_dict[key] = {}

        return result_dict

    parsed = parse_block(0)
    return parsed if isinstance(parsed, dict) else {}


def _service_windows(raw_values: object) -> tuple[ServiceWindow, ...]:
    if not isinstance(raw_values, list):
        return ()
    windows: list[ServiceWindow] = []
    for item in raw_values:
        if not isinstance(item, dict):
            continue
        time_value = str(item.get("time", "")).strip()
        label_value = str(item.get("label", "")).strip()
        if time_value and label_value:
            windows.append(ServiceWindow(time=time_value, label=label_value))
    return tuple(windows)


def _hyperdecks(raw_values: object) -> tuple[HyperDeckConfig, ...]:
    if not isinstance(raw_values, list):
        return ()
    decks: list[HyperDeckConfig] = []
    for item in raw_values:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        ip = str(item.get("ip", "")).strip()
        volumes_raw = item.get("volumes", [])
        if isinstance(volumes_raw, list):
            volumes = tuple(str(value).strip() for value in volumes_raw if str(value).strip())
        else:
            volumes = ()
        if name and ip:
            decks.append(HyperDeckConfig(name=name, ip=ip, volumes=volumes))
    return tuple(decks)


def load_config(config_path: Path | None = None) -> PipelineConfig:
    path = (config_path or CONFIG_PATH).expanduser()
    if not path.exists():
        return default_config()

    raw = parse_yaml_subset(path)
    if not isinstance(raw, dict):
        return default_config()

    defaults = default_config()
    paths = raw.get("paths", {})
    rename = raw.get("rename", {})
    upload = raw.get("upload", {})
    email = raw.get("email", {})

    downloads_dir = Path(str(paths.get("downloads_dir", defaults.downloads_dir))).expanduser()
    log_file = Path(str(paths.get("log_file", defaults.log_file))).expanduser()

    recipients_raw = email.get("recipients", list(defaults.email_recipients))
    if isinstance(recipients_raw, list):
        recipients = tuple(str(value).strip() for value in recipients_raw if str(value).strip())
    else:
        recipients = defaults.email_recipients

    return PipelineConfig(
        hyperdecks=_hyperdecks(raw.get("hyperdecks")) or defaults.hyperdecks,
        downloads_dir=downloads_dir,
        log_file=log_file,
        hd1_services=_service_windows(rename.get("hd1_services")) or defaults.hd1_services,
        hd2_services=_service_windows(rename.get("hd2_services")) or defaults.hd2_services,
        time_tolerance_min=int(rename.get("time_tolerance_min", defaults.time_tolerance_min)),
        upload_remote=str(upload.get("remote", defaults.upload_remote)),
        upload_dest_base=str(upload.get("dest_base", defaults.upload_dest_base)),
        upload_extension=str(upload.get("extension", defaults.upload_extension)),
        email_recipients=recipients or defaults.email_recipients,
        mail_tail_lines=int(email.get("tail_lines", defaults.mail_tail_lines)),
    )
