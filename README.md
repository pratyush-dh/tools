# DEM to Stream Network

An ArcGIS Pro tool that derives a stream network polyline feature class
from a digital elevation model (DEM), using the standard Spatial Analyst
hydrology workflow:

`Fill -> Flow Direction -> Flow Accumulation -> threshold -> Stream Order (Strahler/Shreve) -> Stream to Feature`

## Download and install

1. Download **both** files into the same folder:
   - [`DEM to Stream Network.pyt`](./DEM%20to%20Stream%20Network.pyt) — the ArcGIS Pro toolbox
   - [`streamdelineate.py`](./streamdelineate.py) — the hydrology logic the toolbox imports
2. In ArcGIS Pro's **Catalog** pane, right-click **Toolboxes** → **Add Toolbox** and browse to the `.pyt` file (or just drag-and-drop it into the Catalog pane).
3. Expand the toolbox and open the **DEM to Stream Network** tool.

Requires ArcGIS Pro 3.x with a licensed **Spatial Analyst** extension.

`streamdelineate.py` can also be run standalone/from the command line
(inside an ArcGIS Pro Python environment) if you'd rather script it than
use the tool dialog — see the docstring at the top of the file.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| Input Surface Raster (DEM) | Yes | Elevation raster, ideally in a projected CRS. |
| Flow Accumulation Threshold | Yes | Minimum contributing-cell count for a cell to be classified as a stream. Larger = sparser network. This is a **cell count**, not a real-world drainage area — convert via `min_area / cell_size**2` if that's what you're working from. |
| Output Stream Network | Yes | Output polyline feature class or shapefile. |
| Fill Z-Limit | No | Max fill depth passed to `Fill`. Leave blank to fill all sinks regardless of depth. |
| Stream Order Method | No | `STRAHLER` (default) or `SHREVE`. |

## Why this was rewritten

This started as a raw ArcMap 10.8 ModelBuilder export: `arcpy.gp.<Tool>_sa`
geoprocessor wrappers, `%Value%`-style ModelBuilder inline variable
substitution, a call into a custom "Model Functions" toolbox
(`arcpy.ImportToolbox` / `ParsePath_mb`), hardcoded `C:\Users\new\...`
paths, and a legacy binary `.tbx` (an OLE/COM compound-document toolbox
that predates ArcGIS Pro and can't be text-edited, diffed, or opened
outside ArcGIS Desktop). None of that is portable or maintainable, which
is why the tool stopped working.

It's been rewritten against the current ArcGIS Pro (3.x) `arcpy.sa`
map-algebra API (`Fill`, `FlowDirection`, `FlowAccumulation`, `Con`,
`StreamOrder`, `StreamToFeature` as Raster-returning calls), with explicit
Spatial Analyst license checkout, and the old binary `.tbx` replaced by a
plain-text **Python toolbox** (`.pyt`) — the current ArcGIS Pro standard,
downloadable and version-controllable as a single file.

## Notes / assumptions

- Flow routing is single-direction D8 throughout — `StreamOrder` and
  `StreamToFeature` require a D8 flow direction raster, so Pro's newer
  MFD/DINF options aren't applicable to this particular pipeline.
- Hydrologic distance/area calculations assume a projected (not
  geographic/lat-lon) input DEM; the tool warns if it detects otherwise.
