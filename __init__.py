# -*- coding: utf-8 -*-
"""
XYZ Coordinate Tool
A QGIS plugin for working with XYZ tile coordinates
"""

def classFactory(iface):
    from .xyz_coordinate_tool import XYZCoordinateTool
    return XYZCoordinateTool(iface)
