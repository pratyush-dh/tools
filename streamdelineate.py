# -*- coding: utf-8 -*-
"""
streamdelineate.py

Derive a stream network from a digital elevation model (DEM) using ArcGIS
Pro's Spatial Analyst hydrology tools: Fill -> Flow Direction ->
Flow Accumulation -> threshold -> Stream Order (Strahler/Shreve) ->
Stream to Feature.

Rewritten for current ArcGIS Pro (3.x) arcpy.sa map-algebra API. The
original ModelBuilder export this replaces relied on legacy
arcpy.gp.<Tool>_sa geoprocessor wrappers, %Value%-style ModelBuilder
inline variable substitution, a "Model Functions" custom toolbox
(arcpy.ImportToolbox / ParsePath_mb) that isn't portable, and hardcoded
per-user paths under C:\\Users\\new\\... None of that resolves outside
the machine the model was authored on, which is why it stopped running.

This module is imported directly by `DEM to Stream Network.pyt` (keep
both files in the same folder) so the ArcGIS Pro toolbox tool and the
command-line entry point share one implementation. It can also be run
standalone as a script tool or from the command line:

    streamdelineate.py <input_surface_raster> <threshold> <output_stream_network>
                        [z_limit] [order_method]

Assumptions:
    - `threshold` is a flow-accumulation cell count, not a drainage-area
      threshold in real-world units. Convert if needed
      (min_area / cell_size**2) since cell size varies by input DEM.
    - Flow routing is single-direction D8 throughout, since the downstream
      Stream Order / Stream to Feature tools require a D8 flow direction
      raster. Pro 2.5+ added MFD/DINF flow direction/accumulation, but
      those aren't usable in this particular workflow.
    - The input DEM should be in a projected CRS with linear (not angular)
      units; hydrologic distance/area calculations on a geographic
      (lat/lon) DEM will be distorted.
"""

import os
from typing import Optional

import arcpy
from arcpy.sa import Con, Fill, FlowAccumulation, FlowDirection, StreamOrder, StreamToFeature


def delineate_streams(
    input_surface_raster: str,
    threshold: float,
    output_stream_network: str,
    z_limit: Optional[float] = None,
    order_method: str = "STRAHLER",
) -> str:
    """Derive a stream network polyline feature class from a DEM.

    Args:
        input_surface_raster: Path to the input elevation raster.
        threshold: Minimum flow-accumulation (contributing cell count) for a
            cell to be classified as a stream. Larger values produce a
            sparser network.
        output_stream_network: Output polyline feature class or shapefile
            path (a file geodatabase feature class is recommended over a
            shapefile for field-name/precision reasons, but either works).
        z_limit: Optional maximum z-value difference for sink filling
            (Fill's z_limit parameter). None fills all sinks regardless of
            depth, matching the original script's behavior.
        order_method: "STRAHLER" (default) or "SHREVE" stream ordering.

    Returns:
        The path to the output stream network feature class.

    Raises:
        FileNotFoundError: If the input raster doesn't exist.
        RuntimeError: If the Spatial Analyst extension isn't licensed.
        arcpy.ExecuteError: If a Spatial Analyst tool fails (e.g. a CRS
            mismatch or a fully-NoData input raster).
    """
    if not arcpy.Exists(input_surface_raster):
        raise FileNotFoundError(f"Input surface raster not found: {input_surface_raster}")

    sr = arcpy.Describe(input_surface_raster).spatialReference
    if sr is None or sr.type == "Geographic":
        arcpy.AddWarning(
            "Input raster has no projected CRS (angular/geographic units). "
            "Flow accumulation and stream geometry will be distorted; "
            "reproject the DEM to a projected CRS first."
        )

    if arcpy.CheckExtension("Spatial") != "Available":
        raise RuntimeError("Spatial Analyst extension is not available/licensed.")
    arcpy.CheckOutExtension("Spatial")

    try:
        filled_dem = Fill(input_surface_raster, z_limit)
        flow_dir = FlowDirection(filled_dem, "NORMAL", None, "D8")
        flow_acc = FlowAccumulation(flow_dir, None, "FLOAT", "D8")

        # Con with no false-case raster returns NoData where the condition
        # is false, which is what StreamOrder expects for non-stream cells
        # (this replaces the old Raster Calculator boolean expression).
        stream_raster = Con(flow_acc >= threshold, 1)

        stream_order = StreamOrder(stream_raster, flow_dir, order_method)
        StreamToFeature(stream_order, flow_dir, output_stream_network, "SIMPLIFY")
    finally:
        arcpy.CheckInExtension("Spatial")

    return output_stream_network


def main() -> None:
    input_surface_raster = arcpy.GetParameterAsText(0)
    threshold_text = arcpy.GetParameterAsText(1)
    output_stream_network = arcpy.GetParameterAsText(2)
    z_limit_text = arcpy.GetParameterAsText(3)
    order_method = arcpy.GetParameterAsText(4) or "STRAHLER"

    if not output_stream_network:
        # Default to the current scratch geodatabase instead of a
        # hardcoded per-user path.
        output_stream_network = os.path.join(arcpy.env.scratchGDB, "StreamNetwork")

    try:
        threshold = float(threshold_text)
    except (TypeError, ValueError):
        raise ValueError(f"Threshold must be numeric, got {threshold_text!r}")
    z_limit = float(z_limit_text) if z_limit_text else None

    arcpy.env.overwriteOutput = True
    arcpy.env.scratchWorkspace = arcpy.env.scratchGDB
    arcpy.env.workspace = arcpy.env.scratchGDB
    # Keep hydrology outputs aligned to the source DEM's cell size/extent
    # instead of whatever the current default environment happens to be.
    arcpy.env.snapRaster = input_surface_raster
    arcpy.env.cellSize = input_surface_raster
    arcpy.env.extent = input_surface_raster

    try:
        out_path = delineate_streams(
            input_surface_raster,
            threshold,
            output_stream_network,
            z_limit=z_limit,
            order_method=order_method,
        )
    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
        raise

    arcpy.SetParameterAsText(2, out_path)


if __name__ == "__main__":
    main()
