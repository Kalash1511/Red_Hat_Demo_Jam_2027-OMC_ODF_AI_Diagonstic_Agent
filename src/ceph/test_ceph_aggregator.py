from __future__ import annotations

from src.ceph.osd_commands import CephOSDCommands
from src.ceph.osd_parser import (
    parse_health_detail,
    parse_osd_stat,
    parse_osd_tree,
    parse_osd_df,
)
from src.ceph.osd_aggregator import CephOSDAggregator
from src.omc_client import OMCClient


def main() -> None:
    client = OMCClient()
    commands = CephOSDCommands(client)

    print("=" * 80)
    print("Ceph Aggregator Test")
    print("=" * 80)

    # ------------------------------------------------------------------
    # Collect
    # ------------------------------------------------------------------
    print("\n[1] Collecting Ceph data")
    print("-" * 80)

    health_raw = commands.health_detail()
    osd_stat_raw = commands.osd_stat()
    osd_tree_raw = commands.osd_tree()
    osd_df_raw = commands.osd_df()

    print("✓ Health collected")
    print("✓ OSD stat collected")
    print("✓ OSD tree collected")
    print("✓ OSD DF collected")

    # ------------------------------------------------------------------
    # Parse
    # ------------------------------------------------------------------
    print("\n[2] Parsing Ceph data")
    print("-" * 80)

    health = parse_health_detail(health_raw)
    osd_stat = parse_osd_stat(osd_stat_raw)
    osd_tree = parse_osd_tree(osd_tree_raw)
    osd_df = parse_osd_df(osd_df_raw)

    print(f"Health   : {health}")
    print(f"OSD stat : {osd_stat}")
    print(f"OSD tree : {len(osd_tree)} entries")
    print(f"OSD DF   : {len(osd_df)} entries")

    # ------------------------------------------------------------------
    # Aggregate
    # ------------------------------------------------------------------
    print("\n[3] Aggregating OSD data")
    print("-" * 80)

    aggregator = CephOSDAggregator()

    aggregated_data = aggregator.aggregate(
        osd_df_data=osd_df,
        osd_tree_hosts=osd_tree,
        osd_stat_data=osd_stat,
    )

    print("✓ Aggregator executed successfully")

    # ------------------------------------------------------------------
    # Display result
    # ------------------------------------------------------------------
    print("\n[4] Aggregated result")
    print("-" * 80)

    print(f"Type: {type(aggregated_data).__name__}")
    print(f"Data: {aggregated_data}")

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("Aggregator Validation")
    print("=" * 80)

    assert aggregated_data is not None, (
        "Aggregator returned None"
    )

    print("✓ Aggregator returned data")
    print(f"✓ Return type: {type(aggregated_data).__name__}")

    print("\n" + "=" * 80)
    print("Ceph aggregator test completed successfully.")
    print("=" * 80)





if __name__ == "__main__":
    main()