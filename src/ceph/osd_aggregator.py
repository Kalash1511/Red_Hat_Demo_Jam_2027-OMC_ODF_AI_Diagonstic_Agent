from __future__ import annotations

from src.state.ceph_osd_state import (
    CephClusterData,
    OSD,
    OSDData,
)


class CephOSDAggregator:
    """
    Aggregates Ceph OSD information from multiple
    OMC command outputs.
    """

    def aggregate(
        self,
        osd_df_data: list[dict],
        osd_tree_hosts: dict[int, str],
        osd_stat_data: dict[str, int],
    ) -> OSDData:
        """
        Combine OSD DF, OSD tree and OSD stat data.

        OSD DF provides metrics.
        OSD tree provides host information.
        OSD stat provides cluster-level counts.
        """

        osds: list[OSD] = []

        for data in osd_df_data:

            osd_id = data["id"]

            osd = OSD(
                id=osd_id,

                host=osd_tree_hosts.get(
                    osd_id,
                    ""
                ),

                device_class=data.get(
                    "device_class",
                    ""
                ),

                weight=data.get(
                    "weight",
                    0.0
                ),

                reweight=data.get(
                    "reweight",
                    0.0
                ),

                size=data.get(
                    "size",
                    ""
                ),

                raw_use=data.get(
                    "raw_use",
                    ""
                ),

                data=data.get(
                    "data",
                    ""
                ),

                omap=data.get(
                    "omap",
                    ""
                ),

                meta=data.get(
                    "meta",
                    ""
                ),

                avail=data.get(
                    "avail",
                    ""
                ),

                percent_used=data.get(
                    "percent_used",
                    0.0
                ),

                variance=data.get(
                    "variance",
                    0.0
                ),

                pgs=data.get(
                    "pgs",
                    0
                ),

                status=data.get(
                    "status",
                    ""
                ),
            )

            osds.append(osd)

        up_osds = sum(
            1
            for osd in osds
            if osd.status.lower() == "up"
        )

        down_osds = sum(
            1
            for osd in osds
            if osd.status.lower() == "down"
        )

        # osd stat is the authoritative source
        # for total/up/in counts when available.
        total_osds = osd_stat_data.get(
            "total_osds",
            len(osds)
        )

        stat_up_osds = osd_stat_data.get(
            "up_osds",
            up_osds
        )

        stat_in_osds = osd_stat_data.get(
            "in_osds",
            0
        )

        return OSDData(
            osds=osds,
            total_osds=total_osds,
            up_osds=stat_up_osds,
            in_osds=stat_in_osds,
            down_osds=down_osds,
            out_osds=max(
                total_osds - stat_in_osds,
                0
            ),
        )


def aggregate_cluster_data(
    health: str,
    health_detail: str,
    osd_stat_data: dict[str, int],
    capacity_data: dict,
    statistics_data: dict,
) -> CephClusterData:
    """
    Build cluster-level Ceph information.
    """

    return CephClusterData(
        health=health,

        health_detail=health_detail,

        total_osds=osd_stat_data.get(
            "total_osds",
            0
        ),

        up_osds=osd_stat_data.get(
            "up_osds",
            0
        ),

        in_osds=osd_stat_data.get(
            "in_osds",
            0
        ),

        total_capacity=capacity_data.get(
            "total_capacity",
            ""
        ),

        total_used=capacity_data.get(
            "total_used",
            ""
        ),

        overall_percent_used=0.0,

        min_variance=statistics_data.get(
            "min_variance",
            0.0
        ),

        max_variance=statistics_data.get(
            "max_variance",
            0.0
        ),

        stddev=statistics_data.get(
            "stddev",
            0.0
        ),
    )