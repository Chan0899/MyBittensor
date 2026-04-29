from __future__ import annotations

from collections.abc import Mapping

from bittensor_collector.utils.http_client import HttpClient


class TaoStatsClient:
    def __init__(self, base_url: str, http_client: HttpClient, api_token: str = "") -> None:
        self.base_url = base_url.rstrip("/")
        self.http = http_client
        self.api_token = api_token.strip()
        self._identity_by_netuid: dict[int, dict] | None = None

    def _headers(self) -> Mapping[str, str] | None:
        if not self.api_token:
            return None
        return {
            "accept": "application/json",
            "Authorization": self.api_token,
        }

    def _to_tao(self, value: str | int | float | None) -> float | None:
        if value in (None, ""):
            return None
        return float(value) / 1e9

    def _load_identity_index(self) -> dict[int, dict]:
        if self._identity_by_netuid is not None:
            return self._identity_by_netuid

        url = f"{self.base_url}/api/subnet/identity/v1?limit=200"
        payload = self.http.get_json(
            url,
            cache_key="tao_stats_subnet_identity_index",
            headers=self._headers(),
        )
        self._identity_by_netuid = {
            int(item["netuid"]): item for item in payload.get("data", []) if "netuid" in item
        }
        return self._identity_by_netuid

    def _get_json_or_default(
        self,
        url: str,
        cache_key: str,
        default: dict,
    ) -> dict:
        try:
            return self.http.get_json(
                url,
                cache_key=cache_key,
                headers=self._headers(),
            )
        except Exception:
            return default

    def fetch_subnet_detail(self, netuid: int) -> dict:
        headers = self._headers()
        subnet_payload = self.http.get_json(
            f"{self.base_url}/api/subnet/latest/v1?netuid={netuid}",
            cache_key=f"tao_stats_subnet_latest_{netuid}",
            headers=headers,
        )
        metagraph_payload = self.http.get_json(
            f"{self.base_url}/api/metagraph/latest/v1?netuid={netuid}",
            cache_key=f"tao_stats_metagraph_latest_{netuid}",
            headers=headers,
        )
        pool_payload = self._get_json_or_default(
            f"{self.base_url}/api/dtao/pool/latest/v1?netuid={netuid}",
            cache_key=f"tao_stats_pool_latest_{netuid}",
            default={"data": []},
        )

        subnet = (subnet_payload.get("data") or [{}])[0]
        pool = (pool_payload.get("data") or [{}])[0]
        identity = self._load_identity_index().get(netuid, {})
        metagraph_rows = metagraph_payload.get("data") or []

        incentives = [
            float(item["incentive"])
            for item in metagraph_rows
            if item.get("incentive") not in (None, "")
        ]

        tags = identity.get("tags") or []
        domain = ", ".join(str(tag) for tag in tags[:3])

        return {
            "subnet_name": identity.get("subnet_name") or pool.get("name"),
            "domain": domain,
            "hardware_requirement": identity.get("additional") or "",
            "business_model_summary": identity.get("summary") or identity.get("description") or "",
            "registration_fee_tao": self._to_tao(subnet.get("registration_cost")),
            "immunity_period_blocks": subnet.get("immunity_period"),
            "total_stake_tao": self._to_tao(pool.get("total_tao")),
            "miner_count": subnet.get("active_miners") or subnet.get("active_keys"),
            "validator_count": subnet.get("validators") or subnet.get("active_validators"),
            "miner_income_distribution": incentives,
            "subnet_url": identity.get("subnet_url") or "",
            "github_repo": identity.get("github_repo") or "",
            "description": identity.get("description") or "",
        }
