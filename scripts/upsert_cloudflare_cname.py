"""Insert or update a Cloudflare CNAME record on a given zone."""

import argparse
import sys
from typing import cast

from cloudflare import Cloudflare, APIError
from cloudflare.types.dns.record_response import CNAMERecord


def upsert_cname(client: Cloudflare, zone: str, record_name: str, record_content: str) -> None:
    existing = client.dns.records.list(
        zone_id=zone,
        type="CNAME",
        name={"exact": record_name},
    )
    matches = list(existing)

    if len(matches) > 1:
        raise RuntimeError(
            f"Expected at most one CNAME record named {record_name!r} in zone {zone!r}, "
            f"found {len(matches)}"
        )

    if matches:
        record = cast(CNAMERecord, matches[0])
        assert record.id is not None
        client.dns.records.update(
            record.id,
            zone_id=zone,
            type="CNAME",
            name=record_name,
            content=record_content,
            ttl=record.ttl,
            proxied=record.proxied,
        )
        print(f"Updated CNAME record {record_name} -> {record_content} (id={record.id})")
    else:
        created = client.dns.records.create(
            zone_id=zone,
            type="CNAME",
            name=record_name,
            content=record_content,
            ttl=1,
        )
        assert created is not None
        print(f"Created CNAME record {record_name} -> {record_content} (id={created.id})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zone", required=True, help="Cloudflare zone ID")
    parser.add_argument("--record-name", required=True, help="Cloudflare record name")
    parser.add_argument("--record-content", required=True, help="Cloudflare record content")
    parser.add_argument("--token", required=True, help="Cloudflare API token")
    args = parser.parse_args()

    client = Cloudflare(api_token=args.token)

    try:
        upsert_cname(client, args.zone, args.record_name, args.record_content)
    except APIError as error:
        print(f"Cloudflare API error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
