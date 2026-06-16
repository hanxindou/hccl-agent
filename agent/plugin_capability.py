"""Parse plugin algorithm strings into structured Python data.

Reads the comma-separated algorithm list from the HCCL plugin bridge and
produces a Python list.  This is a lightweight optional helper — it does
not modify the Agent main flow.
"""


def parse_algorithm_list(raw):
    """Split a comma-separated algorithm string into a list.

    Parameters
    ----------
    raw : str
        e.g. "RingAllReduce,Butterfly,Mesh,NHR,FatTree"

    Returns
    -------
    list[str]
        e.g. ["RingAllReduce", "Butterfly", "Mesh", "NHR", "FatTree"]
    """
    if not raw or not raw.strip():
        return []
    return [name.strip() for name in raw.split(",") if name.strip()]


def map_algorithm_name(name):
    """Map a compact algorithm name to the display name used by the Agent.

    The C plugin uses compact names (no spaces); the Python Agent uses
    human-readable names with spaces.

    Parameters
    ----------
    name : str
        Compact name, e.g. "RingAllReduce".

    Returns
    -------
    str
        Display name, e.g. "Ring AllReduce".
    """
    MAPPING = {
        "RingAllReduce": "Ring AllReduce",
        "Butterfly":     "Butterfly",
        "Mesh":          "Mesh",
        "NHR":           "NHR",
        "FatTree":       "Fat-Tree",
        "PairWise":      "PairWise",
    }
    return MAPPING.get(name, name)
