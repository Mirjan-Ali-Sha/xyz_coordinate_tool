# -*- coding: utf-8 -*-

import math
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QCursor
from qgis.gui import QgsMapToolEmitPoint
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject


# XYZ Tile Functions

def deg2tile(lat_deg, lon_deg, zoom):
    """Convert latitude/longitude to XYZ tile coordinates."""
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    x = int((lon_deg + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (x, y, zoom)


def tile2deg(x, y, zoom):
    """Convert XYZ tile coordinates to latitude/longitude (top-left corner)."""
    n = 2.0 ** zoom
    lon_deg = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)


# UTM Projection Functions

def latlon_to_utm(lat, lon):
    """Convert latitude/longitude to UTM coordinates."""
    # Determine UTM zone
    zone = int((lon + 180) / 6) + 1
    
    # Handle special cases for Norway and Svalbard
    if 56.0 <= lat < 64.0 and 3.0 <= lon < 12.0:
        zone = 32
    elif 72.0 <= lat <= 84.0 and lon >= 0.0:
        if lon < 9.0:
            zone = 31
        elif lon < 21.0:
            zone = 33
        elif lon < 33.0:
            zone = 35
        elif lon < 42.0:
            zone = 37
    
    # UTM parameters
    a = 6378137.0  # WGS84 semi-major axis
    e_sq = 0.00669437999014  # WGS84 eccentricity squared
    k0 = 0.9996  # UTM scale factor
    
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    lon_origin = math.radians((zone - 1) * 6 - 180 + 3)
    
    # UTM calculations
    N = a / math.sqrt(1 - e_sq * math.sin(lat_rad) ** 2)
    T = math.tan(lat_rad) ** 2
    C = e_sq * math.cos(lat_rad) ** 2 / (1 - e_sq)
    A = math.cos(lat_rad) * (lon_rad - lon_origin)
    
    M = a * ((1 - e_sq/4 - 3*e_sq**2/64 - 5*e_sq**3/256) * lat_rad -
             (3*e_sq/8 + 3*e_sq**2/32 + 45*e_sq**3/1024) * math.sin(2*lat_rad) +
             (15*e_sq**2/256 + 45*e_sq**3/1024) * math.sin(4*lat_rad) -
             (35*e_sq**3/3072) * math.sin(6*lat_rad))
    
    x = k0 * N * (A + (1-T+C)*A**3/6 + (5-18*T+T**2+72*C-58*0.0067394967)*A**5/120)
    y = k0 * (M + N*math.tan(lat_rad)*(A**2/2 + (5-T+9*C+4*C**2)*A**4/24 + 
                                       (61-58*T+T**2+600*C-330*0.0067394967)*A**6/720))
    
    # Add false easting/northing
    x += 500000
    if lat < 0:
        y += 10000000
    
    hemisphere = 'N' if lat >= 0 else 'S'
    
    return zone, hemisphere, x, y


def utm_to_latlon(zone, hemisphere, x, y):
    """Convert UTM coordinates to latitude/longitude."""
    # UTM parameters
    a = 6378137.0  # WGS84 semi-major axis
    e_sq = 0.00669437999014  # WGS84 eccentricity squared
    k0 = 0.9996  # UTM scale factor
    
    # Remove false easting/northing
    x -= 500000
    if hemisphere == 'S':
        y -= 10000000
    
    lon_origin = math.radians((zone - 1) * 6 - 180 + 3)
    
    # Calculate meridional arc
    M = y / k0
    mu = M / (a * (1 - e_sq/4 - 3*e_sq**2/64 - 5*e_sq**3/256))
    
    e1 = (1 - math.sqrt(1 - e_sq)) / (1 + math.sqrt(1 - e_sq))
    J1 = (3*e1/2 - 27*e1**3/32)
    J2 = (21*e1**2/16 - 55*e1**4/32)
    J3 = (151*e1**3/96)
    J4 = (1097*e1**4/512)
    
    fp = mu + J1*math.sin(2*mu) + J2*math.sin(4*mu) + J3*math.sin(6*mu) + J4*math.sin(8*mu)
    
    e1_sq = e_sq / (1 - e_sq)
    C1 = e1_sq * math.cos(fp)**2
    T1 = math.tan(fp)**2
    N1 = a / math.sqrt(1 - e_sq * math.sin(fp)**2)
    R1 = a * (1 - e_sq) / (1 - e_sq * math.sin(fp)**2)**1.5
    D = x / (N1 * k0)
    
    lat = (fp - (N1*math.tan(fp)/R1) * (D**2/2 - (5+3*T1+10*C1-4*C1**2-9*e1_sq)*D**4/24 +
                                        (61+90*T1+298*C1+45*T1**2-252*e1_sq-3*C1**2)*D**6/720))
    lon = lon_origin + (D - (1+2*T1+C1)*D**3/6 + (5-2*C1+28*T1-3*C1**2+8*e1_sq+24*T1**2)*D**5/120)/math.cos(fp)
    
    return math.degrees(lat), math.degrees(lon)


# CORRECTED MGRS Functions

def get_mgrs_grid_designator(lat):
    """Get MGRS grid zone designator letter from latitude - FIXED."""
    if lat >= 84:
        return None
    elif lat >= 72:
        return 'X'
    elif lat >= 64:
        return 'W'
    elif lat >= 56:
        return 'V'
    elif lat >= 48:
        return 'U'
    elif lat >= 40:
        return 'T'
    elif lat >= 32:
        return 'S'
    elif lat >= 24:
        return 'R'
    elif lat >= 16:
        return 'Q'
    elif lat >= 8:
        return 'P'
    elif lat >= 0:
        return 'N'
    elif lat >= -8:
        return 'M'
    elif lat >= -16:
        return 'L'
    elif lat >= -24:
        return 'K'
    elif lat >= -32:
        return 'J'
    elif lat >= -40:
        return 'H'
    elif lat >= -48:
        return 'G'
    elif lat >= -56:
        return 'F'
    elif lat >= -64:
        return 'E'
    elif lat >= -72:
        return 'D'
    elif lat >= -80:
        return 'C'
    else:
        return None


def get_mgrs_100km_square_id(utm_zone, utm_x, utm_y):
    """Get MGRS 100km square identifier - CORRECTED."""
    
    # Column letters - pattern repeats every 3 zones
    col_letters_sets = [
        'ABCDEFGH',    # Zones 1, 4, 7, 10, etc.
        'JKLMNPQR',    # Zones 2, 5, 8, 11, etc.
        'STUVWXYZ'     # Zones 3, 6, 9, 12, etc.
    ]
    
    # Determine which column letter set to use based on zone
    col_set_index = (utm_zone - 1) % 3
    col_letters = col_letters_sets[col_set_index]
    
    # Calculate column index based on easting
    col_index = int((utm_x - 500000 + 400000) / 100000)  # Adjusted for proper offset
    col_index = max(0, min(7, col_index))  # Clamp to valid range
    
    col_letter = col_letters[col_index]
    
    # Row letters - alternating pattern based on zone number
    if utm_zone % 2 == 1:  # Odd zones
        row_letters = 'ABCDEFGHJKLMNPQRSTUV'
    else:  # Even zones  
        row_letters = 'FGHJKLMNPQRSTUVABCDE'
    
    # Calculate row index based on northing
    row_index = int(utm_y / 100000) % 20
    row_letter = row_letters[row_index]
    
    return col_letter + row_letter


def latlon_to_mgrs(lat, lon, precision=0):
    """
    Convert latitude/longitude to MGRS coordinate string - FIXED.
    """
    try:
        # Get UTM coordinates
        zone, hemisphere, x, y = latlon_to_utm(lat, lon)
        
        # Get grid zone designator
        grid_designator = get_mgrs_grid_designator(lat)
        if grid_designator is None:
            print(f"No grid designator for lat {lat}")
            return None
        
        # Get 100km square identifier
        square_id = get_mgrs_100km_square_id(zone, x, y)
        
        # Create base MGRS reference (GZD + 100km square)
        base_mgrs = f"{zone:02d}{grid_designator}{square_id}"
        
        print(f"MGRS generation: lat={lat:.6f}, lon={lon:.6f} -> Zone={zone}, Grid={grid_designator}, Square={square_id}, Result={base_mgrs}")
        
        # Return just the 100km square reference if precision is 0
        if precision == 0:
            return base_mgrs
        
        # Calculate grid coordinates within 100km square for higher precision
        grid_x = int(x % 100000)
        grid_y = int(y % 100000)
        
        # Format coordinates based on precision
        coord_format = f"{{:0{precision}d}}"
        scale = 10 ** (5 - precision)
        grid_x_scaled = grid_x // scale
        grid_y_scaled = grid_y // scale
        coord_str = coord_format.format(grid_x_scaled) + coord_format.format(grid_y_scaled)
        
        return base_mgrs + coord_str
    
    except Exception as e:
        print(f"Error converting to MGRS: {e}")
        import traceback
        traceback.print_exc()
        return None


# def mgrs_to_latlon(mgrs_string):
#     """Convert MGRS coordinate string to latitude/longitude - COMPLETELY FIXED."""
#     try:
#         mgrs = mgrs_string.strip().upper()
#         print(f"Converting MGRS: {mgrs}")
        
#         # Parse MGRS string
#         if len(mgrs) < 5:
#             print(f"MGRS string too short: {mgrs}")
#             return None
            
#         # Extract zone number (first 2 digits)
#         zone = int(mgrs[:2])
        
#         # Extract grid zone designator (3rd character)
#         grid_designator = mgrs[2]
        
#         # Extract 100km square identifier (4th and 5th characters)
#         square_id = mgrs[3:5]
        
#         print(f"Zone: {zone}, Grid: {grid_designator}, Square: {square_id}")
        
#         # Extract coordinates (everything after position 5)
#         coord_part = mgrs[5:]
        
#         # For 100km square only (no numerical coordinates)
#         if len(coord_part) == 0:
#             # Return center of 100km square
#             grid_x = 50000  # Center of square
#             grid_y = 50000
#         else:
#             if len(coord_part) % 2 != 0:
#                 return None
            
#             precision = len(coord_part) // 2
#             x_str = coord_part[:precision]
#             y_str = coord_part[precision:]
            
#             # Scale coordinates
#             scale = 10 ** (5 - precision)
#             grid_x = int(x_str) * scale
#             grid_y = int(y_str) * scale
        
#         # Get hemisphere from grid designator
#         hemisphere = 'N' if grid_designator >= 'N' else 'S'
        
#         # Calculate base UTM coordinates for the 100km square
#         col_letters_sets = [
#             'ABCDEFGH',    # Zones 1, 4, 7, 10, etc.
#             'JKLMNPQR',    # Zones 2, 5, 8, 11, etc.
#             'STUVWXYZ'     # Zones 3, 6, 9, 12, etc.
#         ]
        
#         col_set_index = (zone - 1) % 3
#         col_letters = col_letters_sets[col_set_index]
        
#         try:
#             col_index = col_letters.index(square_id[0])
#         except ValueError:
#             print(f"Invalid column letter: {square_id[0]}")
#             return None
        
#         # Calculate base X coordinate
#         base_x = 500000 + (col_index - 4) * 100000  # 500000 is false easting, adjust for central column
        
#         # Row calculation
#         if zone % 2 == 1:
#             row_letters = 'ABCDEFGHJKLMNPQRSTUV'
#         else:
#             row_letters = 'FGHJKLMNPQRSTUVABCDE'
        
#         try:
#             row_index = row_letters.index(square_id[1])
#         except ValueError:
#             print(f"Invalid row letter: {square_id[1]}")
#             return None
        
#         # Calculate base Y coordinate
#         base_y = row_index * 100000
        
#         # Final UTM coordinates
#         utm_x = base_x + grid_x
#         utm_y = base_y + grid_y
        
#         print(f"UTM: Zone {zone}{hemisphere}, X: {utm_x}, Y: {utm_y}")
        
#         # Convert UTM to lat/lon
#         lat, lon = utm_to_latlon(zone, hemisphere, utm_x, utm_y)
        
#         print(f"Result: Lat {lat:.6f}, Lon {lon:.6f}")
#         return lat, lon
        
#     except Exception as e:
#         print(f"Error converting from MGRS: {e}")
#         import traceback
#         traceback.print_exc()
#         return None
def mgrs_to_latlon(mgrs_string):
    """Convert MGRS coordinate string to latitude/longitude - COMPLETELY FIXED."""
    try:
        mgrs = mgrs_string.strip().upper()
        print(f"Converting MGRS: {mgrs}")
        
        # Parse MGRS string
        if len(mgrs) < 5:
            print(f"MGRS string too short: {mgrs}")
            return None
            
        # Extract zone number (first 2 digits)
        zone = int(mgrs[:2])
        
        # Extract grid zone designator (3rd character)
        grid_designator = mgrs[2]
        
        # Extract 100km square identifier (4th and 5th characters)
        square_id = mgrs[3:5]
        
        print(f"Zone: {zone}, Grid: {grid_designator}, Square: {square_id}")
        
        # Extract coordinates (everything after position 5)
        coord_part = mgrs[5:]
        
        # For 100km square only (no numerical coordinates)
        if len(coord_part) == 0:
            # Return center of 100km square
            grid_x = 50000  # Center of square
            grid_y = 50000
        else:
            if len(coord_part) % 2 != 0:
                return None
            
            precision = len(coord_part) // 2
            x_str = coord_part[:precision]
            y_str = coord_part[precision:]
            
            # Scale coordinates
            scale = 10 ** (5 - precision)
            grid_x = int(x_str) * scale
            grid_y = int(y_str) * scale
        
        # Get hemisphere from grid designator
        hemisphere = 'N' if grid_designator >= 'N' else 'S'
        
        # Calculate base UTM coordinates for the 100km square
        col_letters_sets = [
            'ABCDEFGH',    # Zones 1, 4, 7, 10, etc.
            'JKLMNPQR',    # Zones 2, 5, 8, 11, etc.
            'STUVWXYZ'     # Zones 3, 6, 9, 12, etc.
        ]
        
        col_set_index = (zone - 1) % 3
        col_letters = col_letters_sets[col_set_index]
        
        try:
            col_index = col_letters.index(square_id[0])
        except ValueError:
            print(f"Invalid column letter: {square_id[0]}")
            return None
        
        # Calculate base X coordinate
        base_x = 500000 + (col_index - 4) * 100000  # 500000 is false easting
        
        # Row calculation with 2,000,000m cycle handling
        if zone % 2 == 1:  # Odd zones
            row_letters = 'ABCDEFGHJKLMNPQRSTUV'
        else:  # Even zones
            row_letters = 'FGHJKLMNPQRSTUVABCDE'
        
        try:
            row_index = row_letters.index(square_id[1])
        except ValueError:
            print(f"Invalid row letter: {square_id[1]}")
            return None
        
        # Calculate base Y within 0-2,000,000m cycle
        base_y_in_cycle = row_index * 100000
        
        # Get expected latitude range for this band
        lat_band_ranges = {
            'C': (-80, -72), 'D': (-72, -64), 'E': (-64, -56), 'F': (-56, -48),
            'G': (-48, -40), 'H': (-40, -32), 'J': (-32, -24), 'K': (-24, -16),
            'L': (-16, -8), 'M': (-8, 0),
            'N': (0, 8), 'P': (8, 16), 'Q': (16, 24), 'R': (24, 32),
            'S': (32, 40), 'T': (40, 48), 'U': (48, 56), 'V': (56, 64),
            'W': (64, 72), 'X': (72, 84)
        }
        
        expected_lat_range = lat_band_ranges.get(grid_designator)
        if expected_lat_range is None:
            print(f"Invalid grid designator: {grid_designator}")
            return None
        
        # Try different 2,000,000m cycles to find the correct one
        # that produces a latitude within the expected band
        best_result = None
        best_lat_error = float('inf')
        
        for cycle in range(0, 10):  # Try up to 10 cycles (0-20,000,000m)
            test_base_y = base_y_in_cycle + (cycle * 2000000)
            
            # For southern hemisphere, adjust
            if hemisphere == 'S':
                test_base_y = 10000000 - test_base_y
            
            # Final UTM coordinates
            utm_x = base_x + grid_x
            utm_y = test_base_y + grid_y
            
            # Convert to lat/lon
            try:
                lat, lon = utm_to_latlon(zone, hemisphere, utm_x, utm_y)
                
                # Check if latitude is in expected range
                lat_min, lat_max = expected_lat_range
                if lat_min <= lat <= lat_max:
                    print(f"Found match: Cycle {cycle}, UTM Y: {utm_y}, Lat: {lat:.6f}, Lon: {lon:.6f}")
                    return lat, lon
                
                # Track closest match in case exact match not found
                lat_center = (lat_min + lat_max) / 2
                lat_error = abs(lat - lat_center)
                if lat_error < best_lat_error:
                    best_lat_error = lat_error
                    best_result = (lat, lon, utm_y, cycle)
                    
            except Exception as e:
                continue
        
        # If no exact match, use the closest one
        if best_result:
            lat, lon, utm_y, cycle = best_result
            print(f"Using closest match: Cycle {cycle}, UTM Y: {utm_y}, Lat: {lat:.6f}, Lon: {lon:.6f}")
            return lat, lon
        
        print(f"Failed to find valid conversion for {mgrs_string}")
        return None
        
    except Exception as e:
        print(f"Error converting from MGRS: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_mgrs_grid_bounds_enhanced(mgrs_string):
    """Enhanced MGRS bounds calculation."""
    try:
        # Get center point
        result = mgrs_to_latlon(mgrs_string)
        if result is None:
            return None
            
        center_lat, center_lon = result
        
        # Determine grid size based on precision
        coord_part = mgrs_string[5:] if len(mgrs_string) > 5 else ""
        
        if len(coord_part) == 0:
            # 100km square
            grid_size = 100000
        else:
            precision = len(coord_part) // 2
            grid_size = 10 ** (5 - precision)
        
        # Convert to approximate degrees
        lat_deg_per_meter = 1 / 111320.0
        lon_deg_per_meter = 1 / (111320.0 * math.cos(math.radians(center_lat)))
        
        lat_offset = grid_size * lat_deg_per_meter / 2
        lon_offset = grid_size * lon_deg_per_meter / 2
        
        min_lat = center_lat - lat_offset
        max_lat = center_lat + lat_offset
        min_lon = center_lon - lon_offset  
        max_lon = center_lon + lon_offset
        
        return min_lat, min_lon, max_lat, max_lon
        
    except Exception as e:
        print(f"Error getting enhanced MGRS bounds: {e}")
        return None


# Keep the get_mgrs_grid_bounds function for backward compatibility
get_mgrs_grid_bounds = get_mgrs_grid_bounds_enhanced


# Map Tool Class

class XYZMapTool(QgsMapToolEmitPoint):
    """Custom map tool for capturing XYZ/MGRS coordinates from canvas clicks."""
    
    coordinates_clicked = pyqtSignal(str, object, object, object)  # system, param1, param2, param3

    def __init__(self, canvas, dock_widget=None):
        super(XYZMapTool, self).__init__(canvas)
        self.canvas = canvas
        self.dock_widget = dock_widget
        self.cursor = QCursor()

    def set_dock_widget(self, dock_widget):
        """Set the dock widget reference after initialization."""
        self.dock_widget = dock_widget

    def activate(self):
        """Called when the map tool is activated."""
        self.canvas.setCursor(QCursor(Qt.CrossCursor))
        
    def deactivate(self):
        """Called when the map tool is deactivated."""
        self.canvas.unsetCursor()

    def canvasReleaseEvent(self, event):
        """Handle mouse release events on the canvas."""
        # Get clicked point in map coordinates
        point = self.toMapCoordinates(event.pos())
        
        # Transform to WGS84 if needed
        map_crs = self.canvas.mapSettings().destinationCrs()
        wgs84_crs = QgsCoordinateReferenceSystem("EPSG:4326")
        
        if map_crs != wgs84_crs:
            transform = QgsCoordinateTransform(map_crs, wgs84_crs, QgsProject.instance())
            try:
                wgs84_point = transform.transform(point)
                lat, lon = wgs84_point.y(), wgs84_point.x()
            except Exception as e:
                print(f"Error transforming coordinates: {e}")
                return
        else:
            lat, lon = point.y(), point.x()
        
        if not self.dock_widget:
            return
            
        current_system = self.dock_widget.get_current_system()
        
        if current_system == "XYZ Tiles":
            # Get current Z value from dock widget
            current_z = self.dock_widget.z_input.value() if hasattr(self.dock_widget, 'z_input') else 14
            x, y, z = deg2tile(lat, lon, current_z)
            self.coordinates_clicked.emit("XYZ", x, y, z)
            
        elif current_system == "MGRS":
            # Convert to MGRS with precision=0 (100km square only)
            mgrs_ref = latlon_to_mgrs(lat, lon, precision=0)
            if mgrs_ref:
                self.coordinates_clicked.emit("MGRS", mgrs_ref, None, None)
                print(f"Generated MGRS: {mgrs_ref} from lat/lon: {lat:.6f}, {lon:.6f}")
            else:
                print(f"Failed to convert lat/lon {lat}, {lon} to MGRS")
