from __future__ import annotations

import re


def parse_health_detail(output: str) -> tuple[str, str]:
    """
    Parse:

        omc ceph health detail

    Returns:

        (health_status, health_detail)
    """

    output = output.strip()

    if not output:
        return "", ""

    first_line = output.splitlines()[0].strip()

    match = re.match(
        r"^(HEALTH_\w+)",
        first_line
    )

    health = match.group(1) if match else ""

    return health, output


def parse_osd_stat(output: str) -> dict[str, int]:
    """
    Parse:

        omc ceph osd stat

    Example:

        20 osds: 20 up (since 9M), 20 in (since 11M); epoch: e41076

    Returns:

        {
            "total_osds": 20,
            "up_osds": 20,
            "in_osds": 20,
        }
    """

    output = output.strip()

    result = {
        "total_osds": 0,
        "up_osds": 0,
        "in_osds": 0,
    }

    if not output:
        return result

    match = re.search(
        r"(\d+)\s+osds:\s+"
        r"(\d+)\s+up.*?,\s+"
        r"(\d+)\s+in",
        output,
        re.IGNORECASE,
    )

    if not match:
        return result

    result["total_osds"] = int(match.group(1))
    result["up_osds"] = int(match.group(2))
    result["in_osds"] = int(match.group(3))

    return result


def parse_osd_tree(output: str) -> dict[int, str]:
    """
    Parse:

        omc ceph osd tree

    Returns:

        {
            2: "compute1-...",
            5: "compute1-...",
            ...
        }

    Mapping is:

        OSD ID -> Host
    """

    osd_hosts: dict[int, str] = {}

    current_host = ""

    for line in output.splitlines():

        stripped = line.strip()

        if not stripped:
            continue

        # Host line
        host_match = re.search(
            r"\bhost\s+(\S+)",
            stripped
        )

        if host_match:
            current_host = host_match.group(1)
            continue

        # OSD line
        osd_match = re.match(
            r"^\s*(\d+)\s+"
            r"(\S+)\s+"
            r"[\d.]+\s+"
            r"osd\.\d+",
            line
        )

        if osd_match:
            osd_id = int(osd_match.group(1))
            osd_hosts[osd_id] = current_host

    return osd_hosts


def _parse_float(value: str) -> float:
    """
    Safely convert a string to float.
    """

    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _parse_int(value: str) -> int:
    """
    Safely convert a string to int.
    """

    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def parse_osd_df(output: str) -> list[dict]:
    """
    Parse:

        omc ceph osd df

    Returns structured information for every OSD.
    """

    lines = [
        line
        for line in output.splitlines()
        if line.strip()
    ]

    if not lines:
        return []

    header_index = None

    for index, line in enumerate(lines):
        if (
            "ID" in line
            and "CLASS" in line
            and "STATUS" in line
        ):
            header_index = index
            break

    if header_index is None:
        return []

    osds: list[dict] = []

    for line in lines[header_index + 1:]:

        stripped = line.strip()

        if not stripped:
            continue

        if stripped.startswith("TOTAL"):
            continue

        parts = stripped.split()

        try:
            osd_id = int(parts[0])
        except (ValueError, IndexError):
            continue

        # Based on:
        #
        # ID CLASS WEIGHT REWEIGHT SIZE RAW USE DATA
        # OMAP META AVAIL %USE VAR PGS STATUS

        if len(parts) < 20:
            continue

        osd = {
            "id": osd_id,
            "device_class": parts[1],

            "weight": _parse_float(parts[2]),

            "reweight": _parse_float(parts[3]),

            "size": f"{parts[4]} {parts[5]}",

            "raw_use": f"{parts[6]} {parts[7]}",

            "data": f"{parts[8]} {parts[9]}",

            "omap": f"{parts[10]} {parts[11]}",

            "meta": f"{parts[12]} {parts[13]}",

            "avail": f"{parts[14]} {parts[15]}",

            "percent_used": _parse_float(parts[16]),

            "variance": _parse_float(parts[17]),

            "pgs": _parse_int(parts[18]),

            "status": parts[19],
        }

        osds.append(osd)

    return osds


def parse_osd_df_total(output: str) -> dict:
    """
    Parse the TOTAL line from:

        omc ceph osd df

    Example:

        TOTAL 58 TiB 1.6 TiB 1.5 TiB
        13 GiB 43 GiB 57 TiB 2.67

    Returns cluster-level capacity information.
    """

    for line in output.splitlines():

        stripped = line.strip()

        if not stripped.startswith("TOTAL"):
            continue

        parts = stripped.split()

        # TOTAL
        # 58
        # TiB
        # 1.6
        # TiB
        # 1.5
        # TiB
        # 13
        # GiB
        # 43
        # GiB
        # 57
        # TiB
        # 2.67

        if len(parts) < 11:
            return {}

        return {
            "total_capacity": f"{parts[1]} {parts[2]}",
            "total_used": f"{parts[3]} {parts[4]}",
            "total_data": f"{parts[5]} {parts[6]}",
            "total_omap": f"{parts[7]} {parts[8]}",
            "total_meta": f"{parts[9]} {parts[10]}",
        }

    return {}


def parse_osd_df_statistics(output: str) -> dict:
    """
    Parse:

        MIN/MAX VAR: 0.89/1.13  STDDEV: 0.20

    from omc ceph osd df.
    """

    result = {
        "min_variance": 0.0,
        "max_variance": 0.0,
        "stddev": 0.0,
    }

    match = re.search(
        r"MIN/MAX\s+VAR:\s*"
        r"([\d.]+)\s*/\s*([\d.]+)"
        r"\s+STDDEV:\s*([\d.]+)",
        output,
        re.IGNORECASE,
    )

    if not match:
        return result

    result["min_variance"] = float(match.group(1))
    result["max_variance"] = float(match.group(2))
    result["stddev"] = float(match.group(3))

    return result