COMMON_TASKS = [
    {
        "id": "zoom",
        "label": "View — Show the complete layer on the map",
        "description": "Zooms the map to the full extent of the active layer.",
    },
    {
        "id": "attributes",
        "label": "View — Open the layer's data table",
        "description": "Opens the attribute table so you can inspect rows and fields.",
    },
    {
        "id": "summary",
        "label": "Understand — Explain this layer",
        "description": "Shows a plain-language summary of source, CRS, fields and features.",
    },
    {
        "id": "select_all",
        "label": "Select — Select every feature",
        "description": "Selects all features in the active vector layer.",
    },
    {
        "id": "clear_selection",
        "label": "Select — Clear the current selection",
        "description": "Removes the current feature selection without changing data.",
    },
]

POINT_TASKS = [
    {
        "id": "buffer",
        "label": "Analyse — Create an area around each point",
        "description": "Creates temporary buffer polygons at a distance you enter.",
    },
    {
        "id": "geometry_columns",
        "label": "Measure — Add coordinate information",
        "description": "Creates a temporary copy with X/Y geometry information.",
    },
]

LINE_TASKS = [
    {
        "id": "buffer",
        "label": "Analyse — Create an area along each line",
        "description": "Creates temporary buffer polygons along the lines.",
    },
    {
        "id": "extract_vertices",
        "label": "Convert — Convert line vertices to points",
        "description": "Creates a temporary point layer from every line vertex.",
    },
    {
        "id": "geometry_columns",
        "label": "Measure — Add length information",
        "description": "Creates a temporary copy with calculated geometry information.",
    },
]

POLYGON_TASKS = [
    {
        "id": "centroids",
        "label": "Convert — Create a centre point for each area",
        "description": "Creates a temporary point layer at each polygon centroid.",
    },
    {
        "id": "buffer",
        "label": "Analyse — Expand or shrink the areas",
        "description": "Uses a positive distance to expand or a negative distance to shrink.",
    },
    {
        "id": "fix_geometries",
        "label": "Clean — Repair geometry problems",
        "description": "Creates a temporary repaired copy; the original layer is unchanged.",
    },
    {
        "id": "geometry_columns",
        "label": "Measure — Add area and perimeter information",
        "description": "Creates a temporary copy with calculated geometry information.",
    },
]

RASTER_TASKS = [
    {
        "id": "zoom",
        "label": "View — Show the complete raster on the map",
        "description": "Zooms the map to the full raster extent.",
    },
    {
        "id": "summary",
        "label": "Understand — Explain this raster",
        "description": "Shows size, bands, CRS, source and resolution information.",
    },
    {
        "id": "stretch",
        "label": "View — Improve raster display contrast",
        "description": "Applies a min-max contrast stretch to improve visibility.",
    },
]
