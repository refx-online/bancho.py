from __future__ import annotations

import asyncio
from collections.abc import Iterable
from dataclasses import dataclass
from dataclasses import replace
from typing import Any

import app
from app.adapters.omajinai import PerformanceResult


@dataclass
class ScoreParams:
    mode: int
    mods: int | None = None
    combo: int | None = None
    acc: float | None = None
    nmiss: int | None = None
    legacy_score: int | None = None


async def calculate_performances(
    beatmap_id: int,
    scores: Iterable[ScoreParams],
) -> list[dict[str, Any]]:
    """\
    Calculate performance for multiple scores on a single beatmap.

    Typically most useful for mass-recalculation situations.
    """

    async def _(score: ScoreParams) -> dict[str, Any]:
        # HACK: handling !with command
        if not score.acc:
            score.acc = 100.0

        result: PerformanceResult = (
            await app.state.services.omajinai.calculate_performance_single(
                beatmap_id=beatmap_id,
                mode=score.mode,
                mods=score.mods,
                max_combo=score.combo,
                accuracy=score.acc,
                miss_count=score.nmiss,
                legacy_score=score.legacy_score,
            )
        )

        return {
            "performance": {"pp": result.pp, "hypothetical_pp": result.hypothetical_pp},
            "difficulty": {"stars": result.stars},
        }

    # parallelize calculations
    # each calculation is independent of the others
    # and the performance gain is *GODLY*
    return await asyncio.gather(*[_(score) for score in scores])
