"""应用配置的读写。

系统本身不需要联网，配置只用来记住用户的使用偏好：
    last_page       上次停留的页面
    last_year       上次查看的就业届别
    last_discipline 上次查看的考研学科门类

配置文件放在可写目录（开发时是项目根目录，打包后是 exe 旁边），
文件不存在或内容损坏时一律回退到默认值，不影响启动。
"""

import json
from typing import Any

from .paths import config_file_csy

DEFAULT_CONFIG_CSY = {
    "last_page": "overview",
    "last_year": "",
    "last_discipline": "",
}


def load_config_csy() -> dict:
    """读取配置；文件不存在或内容损坏时回退到默认配置。"""
    config = dict(DEFAULT_CONFIG_CSY)
    path = config_file_csy()
    if not path.exists():
        return config
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return config
    if isinstance(loaded, dict):
        for key, value in loaded.items():
            if key in config:
                config[key] = value
    return config


def save_config_csy(config: dict) -> bool:
    """把配置写回 JSON 文件，写入失败返回 False。"""
    try:
        config_file_csy().write_text(
            json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
        return True
    except OSError:
        return False


def update_config_csy(**changes: Any) -> dict:
    """局部更新配置并落盘，返回更新后的完整配置。"""
    config = load_config_csy()
    config.update(changes)
    save_config_csy(config)
    return config
