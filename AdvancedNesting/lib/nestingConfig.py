"""
Configuration settings for the Advanced Nesting add-in.
This module provides a central place to manage configuration settings.
"""

# Default sheet dimensions (in cm)
DEFAULT_SHEET_WIDTH = 120.0  # cm
DEFAULT_SHEET_HEIGHT = 240.0  # cm

# Default spacing parameters (in cm)
DEFAULT_EDGE_CLEARANCE = 1.0  # cm
DEFAULT_GUTTER_SIZE = 0.5  # cm

# Algorithm parameters
OPTIMIZATION_LEVELS = {
    'Fast': {
        'description': 'Quick nesting with good material utilization',
        'iterations': 10,
        'max_rotation_angles': [0, 90],
    },
    'Standard': {
        'description': 'Balanced speed and material utilization',
        'iterations': 50,
        'max_rotation_angles': [0, 90, 180, 270],
    },
    'Maximum': {
        'description': 'Best material utilization (slower)',
        'iterations': 200,
        'max_rotation_angles': [0, 45, 90, 135, 180, 225, 270, 315],
    }
}

# UI settings
PALETTE_WIDTH = 650
PALETTE_HEIGHT = 600

# Material database - common sheet sizes
MATERIAL_PRESETS = {
    'Plywood 4x8': {
        'width': 121.92,  # 48 inches in cm
        'height': 243.84,  # 96 inches in cm
        'thickness': 1.27,  # 0.5 inches in cm
    },
    'MDF 5x5': {
        'width': 152.4,  # 60 inches in cm
        'height': 152.4,  # 60 inches in cm
        'thickness': 1.90,  # 0.75 inches in cm
    },
    'Acrylic 4x6': {
        'width': 121.92,  # 48 inches in cm
        'height': 182.88,  # 72 inches in cm
        'thickness': 0.635,  # 0.25 inches in cm
    },
    'Aluminum 4x8': {
        'width': 121.92,  # 48 inches in cm
        'height': 243.84,  # 96 inches in cm
        'thickness': 0.3175,  # 0.125 inches in cm
    }
}

# File export settings
DEFAULT_EXPORT_FORMAT = 'DXF'
SUPPORTED_EXPORT_FORMATS = ['DXF', 'PDF', 'SVG']
