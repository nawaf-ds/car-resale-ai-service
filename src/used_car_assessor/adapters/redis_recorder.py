from collections.abc import Mapping

from redis import Redis
from redis.exceptions import RedisError


class RedisAssessmentRecorder:
    _TOTAL_KEY = "used-car-assessor:assessments:total"
    _BANDS_KEY = "used-car-assessor:assessments:bands"

    def __init__(self, url: str, socket_timeout_seconds: float) -> None:
        self._client: Redis[str] = Redis.from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=socket_timeout_seconds,
            socket_timeout=socket_timeout_seconds,
        )

    def record(self, band: str) -> None:
        with self._client.pipeline(transaction=True) as pipeline:
            pipeline.incr(self._TOTAL_KEY)
            pipeline.hincrby(self._BANDS_KEY, band, 1)
            pipeline.execute()

    def ping(self) -> bool:
        try:
            return bool(self._client.ping())
        except RedisError:
            return False

    def snapshot(self) -> Mapping[str, int]:
        total = int(self._client.get(self._TOTAL_KEY) or 0)
        bands = self._client.hgetall(self._BANDS_KEY)
        return {
            "total": total,
            "below_range": int(bands.get("BELOW_RANGE", 0)),
            "within_range": int(bands.get("WITHIN_RANGE", 0)),
            "above_range": int(bands.get("ABOVE_RANGE", 0)),
        }

    def close(self) -> None:
        self._client.close()
