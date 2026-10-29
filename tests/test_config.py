"""配置读写测试。"""

import pathway.config as config_module


def use_temp_config_csy(tmp_path, monkeypatch):
    """把配置文件重定向到临时目录，避免污染真实配置。"""
    path = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "config_file_csy", lambda: path)
    return path


def test_load_missing_returns_default_csy(tmp_path, monkeypatch):
    """配置文件不存在时返回默认值。"""
    use_temp_config_csy(tmp_path, monkeypatch)
    config = config_module.load_config_csy()
    assert config["last_page"] == "overview"
    assert config["last_year"] == ""


def test_save_and_load_roundtrip_csy(tmp_path, monkeypatch):
    """保存后能原样读回。"""
    use_temp_config_csy(tmp_path, monkeypatch)
    config_module.save_config_csy(
        {"last_page": "kaoyan", "last_year": "2024", "last_discipline": "工学"})
    config = config_module.load_config_csy()
    assert config["last_page"] == "kaoyan"
    assert config["last_year"] == "2024"


def test_corrupt_file_falls_back_csy(tmp_path, monkeypatch):
    """配置内容损坏时不抛异常，回退到默认值。"""
    path = use_temp_config_csy(tmp_path, monkeypatch)
    path.write_text("{ 这不是合法 JSON", encoding="utf-8")
    assert config_module.load_config_csy()["last_page"] == "overview"


def test_update_merges_changes_csy(tmp_path, monkeypatch):
    """update 只改指定字段。"""
    use_temp_config_csy(tmp_path, monkeypatch)
    config_module.update_config_csy(last_discipline="法学")
    config = config_module.load_config_csy()
    assert config["last_discipline"] == "法学"
    assert config["last_page"] == "overview"


def test_unknown_keys_ignored_csy(tmp_path, monkeypatch):
    """配置里多出的未知字段不应被带进来。"""
    path = use_temp_config_csy(tmp_path, monkeypatch)
    path.write_text('{"last_page": "path", "unexpected": 1}', encoding="utf-8")
    config = config_module.load_config_csy()
    assert config["last_page"] == "path"
    assert "unexpected" not in config
