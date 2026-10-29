from __future__ import annotations

from src.ceph.osd_commands import CephOSDCommands
from src.ceph.osd_parser import (
    parse_health_detail,
    parse_osd_stat,
    parse_osd_tree,
    parse_osd_df,
)
from src.omc_client import OMCClient


def main() -> None:
    client = OMCClient()
    commands = CephOSDCommands(client)

    print("=" * 80)
    print("Ceph Parser Test")
    print("=" * 80)

    # ------------------------------------------------------------------
    # 1. Health
    # ------------------------------------------------------------------
    print("\n[1] Parsing ceph health detail")
    print("-" * 80)

    health_raw = commands.health_detail()
    health = parse_health_detail(health_raw)

    print("Raw:")
    print(health_raw)

    print("\nParsed:")
    print(health)

    # ------------------------------------------------------------------
    # 2. OSD Stat
    # ------------------------------------------------------------------
    print("\n[2] Parsing ceph osd stat")
    print("-" * 80)

    osd_stat_raw = commands.osd_stat()
    osd_stat = parse_osd_stat(osd_stat_raw)

    print("Raw:")
    print(osd_stat_raw)

    print("\nParsed:")
    print(osd_stat)

    # ------------------------------------------------------------------
    # 3. OSD Tree
    # ------------------------------------------------------------------
    print("\n[3] Parsing ceph osd tree")
    print("-" * 80)

    osd_tree_raw = commands.osd_tree()
    osd_tree = parse_osd_tree(osd_tree_raw)

    print("Raw:")
    print(osd_tree_raw)

    print("\nParsed OSDs:")
    for osd in osd_tree:
        print(osd)

    print(f"\nTotal parsed OSDs: {len(osd_tree)}")

    # ------------------------------------------------------------------
    # 4. OSD DF
    # ------------------------------------------------------------------
    print("\n[4] Parsing ceph osd df")
    print("-" * 80)

    osd_df_raw = commands.osd_df()
    osd_df = parse_osd_df(osd_df_raw)

    print("Raw:")
    print(osd_df_raw)

    print("\nParsed OSD DF:")
    for osd in osd_df:
        print(osd)

    print(f"\nTotal parsed OSD DF entries: {len(osd_df)}")

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("Parser Validation")
    print("=" * 80)

    assert health is not None, "Health parser returned None"
    assert osd_stat is not None, "OSD stat parser returned None"

    assert len(osd_tree) == 20, (
        f"Expected 20 OSDs from osd tree, got {len(osd_tree)}"
    )

    assert len(osd_df) == 20, (
        f"Expected 20 OSDs from osd df, got {len(osd_df)}"
    )

    print("✓ Health parser passed")
    print("✓ OSD stat parser passed")
    print("✓ OSD tree parser passed")
    print("✓ OSD DF parser passed")
    print("✓ Expected 20 OSDs found in OSD tree")
    print("✓ Expected 20 OSDs found in OSD DF")

    print("\n" + "=" * 80)
    print("All Ceph parser tests passed successfully.")
    print("=" * 80)


if __name__ == "__main__":
    main()