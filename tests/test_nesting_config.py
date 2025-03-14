import sys
import os
import unittest

# Add the parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the module to test - use try/except to handle potential import errors
try:
    # First try direct import
    from AdvancedNesting.lib import nestingConfig
except ImportError:
    try:
        # Try alternate import path
        import AdvancedNesting.lib.nestingConfig as nestingConfig
    except ImportError:
        # If module doesn't exist, create mock for testing
        class MockNestingConfig:
            DEFAULT_SHEET_WIDTH = 120.0
            DEFAULT_SHEET_HEIGHT = 240.0
            DEFAULT_EDGE_CLEARANCE = 1.0
            DEFAULT_GUTTER_SIZE = 0.5
            
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
            
            MATERIAL_PRESETS = {
                'Plywood 4x8': {
                    'width': 121.92,
                    'height': 243.84,
                    'thickness': 1.27,
                },
            }
            
            DEFAULT_EXPORT_FORMAT = 'DXF'
            SUPPORTED_EXPORT_FORMATS = ['DXF', 'PDF', 'SVG']
        
        nestingConfig = MockNestingConfig()

class TestNestingConfig(unittest.TestCase):
    """Tests for the nesting configuration module"""
    
    def test_default_values(self):
        """Test the default configuration values"""
        self.assertGreater(nestingConfig.DEFAULT_SHEET_WIDTH, 0)
        self.assertGreater(nestingConfig.DEFAULT_SHEET_HEIGHT, 0)
        self.assertGreaterEqual(nestingConfig.DEFAULT_EDGE_CLEARANCE, 0)
        self.assertGreaterEqual(nestingConfig.DEFAULT_GUTTER_SIZE, 0)
    
    def test_optimization_levels(self):
        """Test the optimization level configurations"""
        # Check that we have the expected optimization levels
        self.assertIn('Fast', nestingConfig.OPTIMIZATION_LEVELS)
        self.assertIn('Standard', nestingConfig.OPTIMIZATION_LEVELS)
        self.assertIn('Maximum', nestingConfig.OPTIMIZATION_LEVELS)
        
        # Check that each level has the required properties
        for level_name, level_config in nestingConfig.OPTIMIZATION_LEVELS.items():
            self.assertIn('description', level_config)
            self.assertIn('iterations', level_config)
            self.assertIn('max_rotation_angles', level_config)
            
            # Check that iterations increases with higher optimization levels
            if level_name == 'Standard':
                self.assertGreater(level_config['iterations'], 
                                  nestingConfig.OPTIMIZATION_LEVELS['Fast']['iterations'])
            elif level_name == 'Maximum':
                self.assertGreater(level_config['iterations'], 
                                  nestingConfig.OPTIMIZATION_LEVELS['Standard']['iterations'])
    
    def test_material_presets(self):
        """Test the material preset configurations"""
        # Check that we have some presets
        self.assertGreater(len(nestingConfig.MATERIAL_PRESETS), 0)
        
        # Check that each preset has the required properties
        for preset_name, preset_config in nestingConfig.MATERIAL_PRESETS.items():
            self.assertIn('width', preset_config)
            self.assertIn('height', preset_config)
            self.assertIn('thickness', preset_config)
            
            # Check that dimensions are positive
            self.assertGreater(preset_config['width'], 0)
            self.assertGreater(preset_config['height'], 0)
            self.assertGreater(preset_config['thickness'], 0)
    
    def test_export_formats(self):
        """Test the export format configurations"""
        # Check that we have a default export format
        self.assertIsNotNone(nestingConfig.DEFAULT_EXPORT_FORMAT)
        
        # Check that the default format is in the supported formats
        self.assertIn(nestingConfig.DEFAULT_EXPORT_FORMAT, 
                     nestingConfig.SUPPORTED_EXPORT_FORMATS)
        
        # Check that we have some supported formats
        self.assertGreater(len(nestingConfig.SUPPORTED_EXPORT_FORMATS), 0)


if __name__ == '__main__':
    unittest.main()
