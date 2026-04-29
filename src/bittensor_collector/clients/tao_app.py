from __future__ import annotations

from bittensor_collector.utils.http_client import HttpClient


class TaoAppClient:
    def __init__(self, base_url: str, http_client: HttpClient) -> None:
        self.base_url = base_url.rstrip("/")
        self.http = http_client

    def fetch_subnet_overview(self, netuid: int) -> dict:
        url = f"{self.base_url}/api/v1/subnets/{netuid}"
        return self.http.get_json(url, cache_key=f"tao_app_subnet_{netuid}")

    def fetch_metagraph(self, netuid: int) -> dict:
        url = f"{self.base_url}/api/v1/subnets/{netuid}/metagraph"
        return self.http.get_json(url, cache_key=f"tao_app_metagraph_{netuid}")

    def fetch_validators(self, netuid: int) -> dict:
        url = f"{self.base_url}/api/v1/subnets/{netuid}/validators"
        return self.http.get_json(url, cache_key=f"tao_app_validators_{netuid}")
