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
            "performance": {"pp": result.pp},
            "difficulty": {"stars": result.stars},
        }

    # parallelize calculations
    # each calculation is independent of the others
    # and the performance gain is *GODLY*
    return await asyncio.gather(*[_(score) for score in scores])


async def calculate_performance_single(
    beatmap_id: int,
    score: ScoreParams,
    hypothetical: bool = False,
) -> tuple[float, float, float | None]:
    """
    Calculate performance for a single score on a beatmap.

    If `hypothetical` is True, also calculate the hypothetical performance
    assuming a full combo with no misses.
    """

    scores = [score]

    if hypothetical:
        hypothetical_score = replace(score, combo=None, nmiss=0)
        scores.append(hypothetical_score)

    results = await calculate_performances(
        beatmap_id=beatmap_id,
        scores=scores,
    )
    real = results[0]
    hypo = results[1] if hypothetical else None

    return (
        real["performance"]["pp"],
        real["difficulty"]["stars"],
        hypo["performance"]["pp"] if hypo is not None else None,
    )
