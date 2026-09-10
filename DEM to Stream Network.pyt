# -*- coding: utf-8 -*-
"""
DEM to Stream Network.pyt

ArcGIS Pro Python toolbox wrapping streamdelineate.delineate_streams().
Keep this file in the same folder as streamdelineate.py -- it imports
that module rather than duplicating the hydrology logic, so the toolbox
tool and the standalone/command-line script stay in sync.

To install: download this file and streamdelineate.py into the same
folder, then in ArcGIS Pro's Catalog pane right-click Toolboxes ->
Add Toolbox -> browse to this .pyt (or just drag-and-drop it in).
Requires a licensed Spatial Analyst extension.
"""

import importlib
import os
import sys

import arcpy

_TOOLBOX_DIR = os.path.dirname(__file__)
if _TOOLBOX_DIR not in sys.path:
    sys.path.insert(0, _TOOLBOX_DIR)

import streamdelineate  # noqa: E402 (must follow the sys.path setup above)

# Pick up edits to streamdelineate.py without restarting ArcGIS Pro.
importlib.reload(streamdelineate)


class Toolbox(object):
    def __init__(self):
        self.label = "DEM to Stream Network"
        self.alias = "demstreamnetwork"
        self.tools = [DemToStreamNetwork]


class DemToStreamNetwork(object):
    def __init__(self):
        self.label = "DEM to Stream Network"
        self.description = (
            "Derives a stream network polyline feature class from a DEM: "
            "Fill -> Flow Direction -> Flow Accumulation -> threshold -> "
            "Stream Order -> Stream to Feature."
        )
        self.category = "Hydrology"
        self.canRunInBackground = False

    def getParameterInfo(self):
        input_dem = arcpy.Parameter(
            displayName="Input Surface Raster (DEM)",
            name="input_surface_raster",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input",
        )

        threshold = arcpy.Parameter(
            displayName="Flow Accumulation Threshold (contributing cells)",
            name="threshold",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input",
        )
        threshold.value = 1000

        output_streams = arcpy.Parameter(
            displayName="Output Stream Network",
            name="output_stream_network",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output",
        )

        z_limit = arcpy.Parameter(
            displayName="Fill Z-Limit (optional)",
            name="z_limit",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input",
        )

        order_method = arcpy.Parameter(
            displayName="Stream Order Method",
            name="order_method",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
        )
        order_method.filter.type = "ValueList"
        order_method.filter.list = ["STRAHLER", "SHREVE"]
        order_method.value = "STRAHLER"

        return [input_dem, threshold, output_streams, z_limit, order_method]

    def isLicensed(self):
        return arcpy.CheckExtension("Spatial") == "Available"

    def updateMessages(self, parameters):
        input_dem, threshold = parameters[0], parameters[1]
        if input_dem.altered and not input_dem.hasBeenValidated:
            sr = arcpy.Describe(input_dem.value).spatialReference
            if sr is None or sr.type == "Geographic":
                input_dem.setWarningMessage(
                    "Input raster is not in a projected CRS; flow "
                    "accumulation and stream geometry will be distorted."
                )
        if threshold.value is not None and threshold.value <= 0:
            threshold.setErrorMessage("Threshold must be a positive number of cells.")
        return

    def execute(self, parameters, messages):
        input_surface_raster = parameters[0].valueAsText
        threshold = parameters[1].value
        output_stream_network = parameters[2].valueAsText
        z_limit = parameters[3].value  # None if left blank
        order_method = parameters[4].valueAsText or "STRAHLER"

        streamdelineate.delineate_streams(
            input_surface_raster,
            threshold,
            output_stream_network,
            z_limit=z_limit,
            order_method=order_method,
        )
