from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

import noaa_spec.deterministic_io as deterministic_io


def test_write_deterministic_csv_is_atomic_when_writer_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output_path = tmp_path / "artifact.csv"
    output_path.write_text("stable\n", encoding="utf-8")

    class _FailingFrame:
        def to_csv(self, path: Path, **_kwargs: object) -> None:
            Path(path).write_text("partial\n", encoding="utf-8")
            raise RuntimeError("simulated write interruption")

    def _fake_prepare(_frame: pd.DataFrame, *, sort_by: tuple[str, ...]) -> _FailingFrame:
        return _FailingFrame()

    monkeypatch.setattr(deterministic_io, "_prepare_frame", _fake_prepare)

    with pytest.raises(RuntimeError, match="simulated write interruption"):
        deterministic_io.write_deterministic_csv(
            pd.DataFrame({"value": [1]}),
            output_path,
        )

    assert output_path.read_text(encoding="utf-8") == "stable\n"
    assert not list(output_path.parent.glob(f".{output_path.name}.tmp-*"))


def test_write_deterministic_csv_formats_usable_metric_fraction(tmp_path: Path) -> None:
    output_path = tmp_path / "artifact.csv"

    deterministic_io.write_deterministic_csv(
        pd.DataFrame(
            {
                "DATE": ["2000-01-01", "2000-01-02", "2000-01-03"],
                "usable_metric_fraction": [
                    0.06666666666666667,
                    0.3333333333333333,
                    1.0,
                ],
            }
        ),
        output_path,
        sort_by=("DATE",),
    )

    assert output_path.read_text(encoding="utf-8") == (
        "DATE,usable_metric_fraction\n"
        "2000-01-01,0.066667\n"
        "2000-01-02,0.333333\n"
        "2000-01-03,1.0\n"
    )
