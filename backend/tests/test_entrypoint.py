"""Tests for backend entrypoint helpers."""

from backend import main as main_module


def test_main_runs_uvicorn_with_settings(monkeypatch):
    calls = []

    def fake_run(app, host: str, port: int, reload: bool) -> None:
        calls.append(
            {
                "app": app,
                "host": host,
                "port": port,
                "reload": reload,
            }
        )

    monkeypatch.setattr(main_module.settings, "app_host", "127.0.0.1")
    monkeypatch.setattr(main_module.settings, "app_port", 8050)
    monkeypatch.setattr(main_module.uvicorn, "run", fake_run)

    main_module.main()

    assert calls == [
        {
            "app": main_module.app,
            "host": "127.0.0.1",
            "port": 8050,
            "reload": False,
        }
    ]
