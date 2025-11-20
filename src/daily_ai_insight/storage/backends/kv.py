"""Cloudflare KV storage backend."""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    logger.warning("aiohttp not installed. KV storage requires: uv add aiohttp")


class KVStorage:
    """Cloudflare KV storage backend.

    Requires environment variables:
        - CF_ACCOUNT_ID: Cloudflare account ID
        - CF_KV_NAMESPACE_ID: KV namespace ID
        - CF_API_TOKEN: API token with KV write permissions
    """

    def __init__(
        self,
        account_id: Optional[str] = None,
        namespace_id: Optional[str] = None,
        api_token: Optional[str] = None,
        default_ttl: int = 86400 * 7  # 7 days
    ):
        """Initialize KV storage.

        Args:
            account_id: Cloudflare account ID (or from CF_ACCOUNT_ID env)
            namespace_id: KV namespace ID (or from CF_KV_NAMESPACE_ID env)
            api_token: API token (or from CF_API_TOKEN env)
            default_ttl: Default TTL in seconds for raw data

        Raises:
            ValueError: If credentials are missing
            ImportError: If aiohttp is not installed
        """
        if not HAS_AIOHTTP:
            raise ImportError(
                "Cloudflare KV storage requires aiohttp. "
                "Install with: uv add aiohttp"
            )

        self.account_id = account_id or os.getenv("CF_ACCOUNT_ID")
        self.namespace_id = namespace_id or os.getenv("CF_KV_NAMESPACE_ID")
        self.api_token = api_token or os.getenv("CF_API_TOKEN")
        self.default_ttl = default_ttl

        if not all([self.account_id, self.namespace_id, self.api_token]):
            raise ValueError(
                "Missing Cloudflare credentials. Set:\n"
                "  CF_ACCOUNT_ID\n"
                "  CF_KV_NAMESPACE_ID\n"
                "  CF_API_TOKEN\n"
                "in your .env file"
            )

        self.base_url = (
            f"https://api.cloudflare.com/client/v4"
            f"/accounts/{self.account_id}"
            f"/storage/kv/namespaces/{self.namespace_id}"
        )
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    async def save_raw(
        self,
        items: List[Dict[str, Any]],
        source: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Save raw data to KV with TTL.

        Args:
            items: List of data items
            source: Data source name
            metadata: Optional metadata

        Returns:
            KV key
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        key = f"{date_str}-{source}-raw"

        data = {
            "source": source,
            "collected_at": datetime.now().isoformat(),
            "count": len(items),
            "items": items,
            **(metadata or {})
        }

        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/values/{key}"
            params = {"expiration_ttl": self.default_ttl}

            async with session.put(
                url,
                headers=self.headers,
                json=data,
                params=params
            ) as resp:
                resp.raise_for_status()

        logger.info(f"☁️  Saved {len(items)} items to KV: {key} (TTL: {self.default_ttl}s)")
        return key

    async def save_processed(
        self,
        data: Dict[str, Any],
        report_type: str = "daily"
    ) -> str:
        """Save processed data to KV.

        Args:
            data: Processed data
            report_type: Type of report

        Returns:
            KV key
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        key = f"{date_str}-{report_type}-processed"

        payload = {
            "type": report_type,
            "processed_at": datetime.now().isoformat(),
            "data": data
        }

        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/values/{key}"
            params = {"expiration_ttl": self.default_ttl * 2}  # Keep longer

            async with session.put(
                url,
                headers=self.headers,
                json=payload,
                params=params
            ) as resp:
                resp.raise_for_status()

        logger.info(f"☁️  Saved processed data to KV: {key}")
        return key

    async def save_report(
        self,
        content: str,
        format: str = "markdown"
    ) -> str:
        """Save final report to KV.

        Args:
            content: Report content
            format: Report format

        Returns:
            KV key
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        key = f"report-{date_str}"

        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/values/{key}"
            params = {"expiration_ttl": 86400 * 30}  # 30 days for reports

            # Store as plain text for markdown
            headers = {**self.headers, "Content-Type": "text/plain; charset=utf-8"}

            async with session.put(
                url,
                headers=headers,
                data=content.encode('utf-8'),
                params=params
            ) as resp:
                resp.raise_for_status()

        logger.info(f"☁️  Saved report to KV: {key} (30 days TTL)")
        return key

    async def load_recent(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Load recent data from KV.

        Note: KV is key-based, so we query recent dates.

        Args:
            hours: Time window in hours

        Returns:
            List of all items from recent data
        """
        # Generate possible keys for recent days
        all_items = []
        days_to_check = max(1, hours // 24 + 1)

        dates = [
            (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(days_to_check)
        ]

        async with aiohttp.ClientSession() as session:
            for date_str in dates:
                # List keys with prefix
                list_url = f"{self.base_url}/keys"
                params = {"prefix": date_str}

                async with session.get(
                    list_url,
                    headers=self.headers,
                    params=params
                ) as resp:
                    if resp.status != 200:
                        continue

                    result = await resp.json()
                    keys = [k["name"] for k in result.get("result", [])]

                    # Fetch each key's data
                    for key in keys:
                        if not key.endswith("-raw"):
                            continue

                        value_url = f"{self.base_url}/values/{key}"
                        async with session.get(value_url, headers=self.headers) as vresp:
                            if vresp.status == 200:
                                data = await vresp.json()
                                all_items.extend(data.get("items", []))

        logger.info(f"☁️  Loaded {len(all_items)} items from KV")
        return all_items

    async def query(
        self,
        pattern: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Query KV by key prefix.

        Args:
            pattern: Key prefix pattern
            start_date: Optional start date (limited support)
            end_date: Optional end date (limited support)

        Returns:
            List of matching data
        """
        results = []

        async with aiohttp.ClientSession() as session:
            list_url = f"{self.base_url}/keys"
            params = {"prefix": pattern}

            async with session.get(
                list_url,
                headers=self.headers,
                params=params
            ) as resp:
                resp.raise_for_status()
                result = await resp.json()
                keys = [k["name"] for k in result.get("result", [])]

                # Fetch each key
                for key in keys:
                    value_url = f"{self.base_url}/values/{key}"
                    async with session.get(value_url, headers=self.headers) as vresp:
                        if vresp.status == 200:
                            data = await vresp.json()
                            results.append(data)

        logger.info(f"☁️  Query '{pattern}' found {len(results)} entries")
        return results

    async def cleanup(self, days: int = 7):
        """KV uses TTL, so cleanup is automatic.

        Args:
            days: Ignored (TTL handles expiration)
        """
        logger.info("☁️  KV auto-expires via TTL, cleanup skipped")

    def get_statistics(self) -> Dict[str, Any]:
        """Get KV storage statistics.

        Note: Requires synchronous API call, returns limited info.

        Returns:
            Dictionary with basic stats
        """
        return {
            "backend": "cloudflare_kv",
            "namespace_id": self.namespace_id,
            "default_ttl_days": self.default_ttl // 86400,
            "note": "KV statistics require async API calls"
        }
