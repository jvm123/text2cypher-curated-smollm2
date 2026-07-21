from types import SimpleNamespace

import pytest

from text2cypher.training import resolve_use_cpu, save_loss_curve


def test_save_loss_curve_writes_png(tmp_path) -> None:
    trainer = SimpleNamespace(
        state=SimpleNamespace(
            log_history=[
                {"step": 10, "loss": 1.2},
                {"step": 20, "loss": 0.8},
                {"step": 20, "eval_loss": 0.9},
            ]
        )
    )

    curve_path = save_loss_curve(trainer, tmp_path)

    assert curve_path == tmp_path / "loss_curve.png"
    assert curve_path.is_file()
    assert curve_path.stat().st_size > 0


def test_explicit_cpu_does_not_probe_cuda() -> None:
    assert resolve_use_cpu("cpu") is True


def test_cuda_request_requires_available_cuda(monkeypatch) -> None:
    monkeypatch.setattr("text2cypher.training.torch.cuda.is_available", lambda: False)
    with pytest.raises(RuntimeError, match="CUDA was requested"):
        resolve_use_cpu("cuda")


def test_auto_selects_cuda_when_available(monkeypatch) -> None:
    monkeypatch.setattr("text2cypher.training.torch.cuda.is_available", lambda: True)
    assert resolve_use_cpu("auto") is False
