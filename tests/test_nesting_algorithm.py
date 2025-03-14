import sys
import os
import unittest
from unittest import mock

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the module to test
from lib import nestingAlgorithm

class TestNestingAlgorithm(unittest.TestCase):
    """Tests for the nesting algorithm functions"""
    
    def test_get_optimal_rotation(self):
        """Test the get_optimal_rotation function"""
        # Test case where normal orientation is better
        result = nestingAlgorithm.get_optimal_rotation(
            part_width=10, 
            part_height=5, 
            sheet_width_cm=100, 
            sheet_height_cm=50, 
            edge_clearance=1, 
            gutter_size=0.5
        )
        self.assertEqual(result, (False, 9, 9))  # Not rotated, 9 per row, 9 per column
        
        # Test case where rotated orientation is better
        result = nestingAlgorithm.get_optimal_rotation(
            part_width=20, 
            part_height=5, 
            sheet_width_cm=100, 
            sheet_height_cm=50, 
            edge_clearance=1, 
            gutter_size=0.5
        )
        self.assertEqual(result, (True, 19, 2))  # Rotated, 19 per row, 2 per column
        
        # Test with edge case (tiny part)
        result = nestingAlgorithm.get_optimal_rotation(
            part_width=1, 
            part_height=1, 
            sheet_width_cm=100, 
            sheet_height_cm=50, 
            edge_clearance=1, 
            gutter_size=0.5
        )
        # Both orientations are identical for a square part
        self.assertEqual(result[1] * result[2], 98 * 48)  # 98 * 48 = 4704 parts
        
        # Test with edge case (part bigger than sheet)
        result = nestingAlgorithm.get_optimal_rotation(
            part_width=150, 
            part_height=100, 
            sheet_width_cm=100, 
            sheet_height_cm=50, 
            edge_clearance=1, 
            gutter_size=0.5
        )
        # Should return all zeros since part won't fit
        self.assertEqual(result, (False, 0, 0))  
    
    def test_bin_packing_nesting(self):
        """Test the bin packing algorithm"""
        # Simple test case with one part
        parts_list = [{
            'id': 'part1',
            'width': 10,
            'height': 5,
            'quantity': 10
        }]
        
        result = nestingAlgorithm.bin_packing_nesting(
            sheet_width=100,
            sheet_height=50,
            parts_list=parts_list,
            edge_clearance=1,
            gutter_size=0.5
        )
        
        # Check if we have the expected output keys
        self.assertIn('utilization', result)
        self.assertIn('placements', result)
        self.assertIn('unused_area', result)
        
        # Check if all requested parts were placed
        self.assertEqual(len(result['placements']), 10)
        
        # Test with multiple different parts
        parts_list = [
            {'id': 'part1', 'width': 10, 'height': 5, 'quantity': 5},
            {'id': 'part2', 'width': 20, 'height': 15, 'quantity': 3}
        ]
        
        result = nestingAlgorithm.bin_packing_nesting(
            sheet_width=100,
            sheet_height=50,
            parts_list=parts_list,
            edge_clearance=1,
            gutter_size=0.5
        )
        
        # Make sure we have the right number of parts
        self.assertEqual(len([p for p in result['placements'] if p['part_id'] == 'part1']), 5)
        self.assertEqual(len([p for p in result['placements'] if p['part_id'] == 'part2']), 3)


if __name__ == '__main__':
    unittest.main()
