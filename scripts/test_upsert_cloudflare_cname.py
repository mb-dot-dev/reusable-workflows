from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from upsert_cloudflare_cname import upsert_cname


def make_client():
    return MagicMock()


def test_creates_record_when_none_exists():
    client = make_client()
    client.dns.records.list.return_value = []

    upsert_cname(client, "zone-1", "app.example.com", "target.example.com")

    client.dns.records.list.assert_called_once_with(
        zone_id="zone-1",
        type="CNAME",
        name={"exact": "app.example.com"},
    )
    client.dns.records.create.assert_called_once_with(
        zone_id="zone-1",
        type="CNAME",
        name="app.example.com",
        content="target.example.com",
        ttl=1,
    )
    client.dns.records.update.assert_not_called()


def test_updates_record_when_one_exists():
    client = make_client()
    existing = SimpleNamespace(id="rec-1", ttl=300, proxied=False)
    client.dns.records.list.return_value = [existing]

    upsert_cname(client, "zone-1", "app.example.com", "target.example.com")

    client.dns.records.update.assert_called_once_with(
        "rec-1",
        zone_id="zone-1",
        type="CNAME",
        name="app.example.com",
        content="target.example.com",
        ttl=300,
        proxied=False,
    )
    client.dns.records.create.assert_not_called()


def test_raises_when_multiple_records_match():
    client = make_client()
    client.dns.records.list.return_value = [
        SimpleNamespace(id="rec-1", ttl=300, proxied=False),
        SimpleNamespace(id="rec-2", ttl=300, proxied=False),
    ]

    with pytest.raises(RuntimeError):
        upsert_cname(client, "zone-1", "app.example.com", "target.example.com")

    client.dns.records.create.assert_not_called()
    client.dns.records.update.assert_not_called()
