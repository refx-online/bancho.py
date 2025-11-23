from __future__ import annotations

from dataclasses import dataclass

from httpx import AsyncClient


@dataclass
class PerformanceResult:
    stars: float
    pp: float


@dataclass
class PerformanceRequest:
    beatmap_id: int
    mode: int
    mods: int
    max_combo: int
    accuracy: float
    miss_count: int
    legacy_score: int
    passed_objects: int | None = None


class Omajinai:
    def __init__(self, base_url: str, http_client: AsyncClient) -> None:
        self._base_url = base_url
        self._http_client = http_client

    async def __make_performance_request(
        self,
        req: PerformanceRequest,
    ) -> dict[str, float]:
        params = {k: v for k, v in vars(req).items() if v is not None}
        params["mode"] %= 4

        # XXX: wrapped in try except since sometime my pc
        #      is too slow to waking omajinai
        #      aand safety first!
        try:
            resp = await self._http_client.get(
                f"{self._base_url}/calculate",
                params=params,
            )

            # i dont like how there has 2 fallbacks here but whatever
            if resp.status_code != 200:
                return {"stars": 0.0, "pp": 0.0}
        except:
            return {"stars": 0.0, "pp": 0.0}

        data = resp.json()

        return {
            "stars": data["data"]["stars"],
            "pp": data["data"]["pp"],
        }

    async def calculate_performance_single(
        self,
        beatmap_id: int,
        mode: int,
        mods: int,
        max_combo: int,
        accuracy: float,
        miss_count: int,
        legacy_score: int,
        passed_objects: int | None = None,
    ) -> PerformanceResult:
        request = PerformanceRequest(
            beatmap_id=beatmap_id,
            mode=mode,
            mods=mods,
            max_combo=max_combo,
            accuracy=accuracy,
            miss_count=miss_count,
            legacy_score=legacy_score,
            passed_objects=passed_objects,
        )
        data = await self.__make_performance_request(request)

        return PerformanceResult(
            stars=data["stars"],
            pp=data["pp"],
        )
