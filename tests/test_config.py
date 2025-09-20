from src.config import ConfigManager

def test_default_values(tmp_path):
    # создаём временный файл config.ini в папке pytest-а
    test_file = tmp_path / "test.ini"
    test_cfg = ConfigManager(test_file)

    # проверяем дефолтные значения
    assert test_cfg.get_info("DEFAULT", "dd_hotkey", fallback="") == ""
    assert test_cfg.get_info("DEFAULT", "default_device", fallback="") == ""
    assert test_cfg.get_info("DEFAULT", "nonexistoption", fallback="") == ""

def test_set_and_get(tmp_path):
    test_file = tmp_path / "test.ini"
    test_cfg = ConfigManager(test_file)

    test_cfg.set("DEFAULT", "dd_hotkey", "ctrl+alt+x")
    test_cfg.set("DEFAULT", "default_device", "Smart LightBulb")
    assert test_cfg.get_info("DEFAULT", "dd_hotkey") == "ctrl+alt+x"
    assert test_cfg.get_info("DEFAULT", "default_device") == "Smart LightBulb"