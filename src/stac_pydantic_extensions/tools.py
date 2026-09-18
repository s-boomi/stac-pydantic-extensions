from stac_pydantic.shared import BBox


def simple_latlon_to_wgs_84(bbox: BBox) -> BBox:
    """Translates a bounding box to World Geodetic System 1984 coordinates, the standard for STAC's specs

    Args:
        bbox (BBox): _description_

    Returns:
        BBox: _description_
    """
    if len(bbox) == 4:
        xmin, ymin, xmax, ymax = bbox
        return (xmin - 180, ymin - 90, xmax - 180, ymax - 90)

    xmin, ymin, min_elev, xmax, ymax, max_elev = bbox
    return (xmin - 180, ymin - 90, min_elev, xmax - 180, ymax - 90, max_elev)
