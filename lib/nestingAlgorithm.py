# This file can contain any custom nesting algorithm functions
# that you might want to separate from the main command logic

import math
import adsk.core
import adsk.fusion
import traceback

def get_optimal_rotation(part_width, part_height, sheet_width_cm, sheet_height_cm, edge_clearance, gutter_size):
    """
    Determine if rotating parts would provide better yield
    
    Returns:
        tuple: (should_rotate, parts_per_row, parts_per_column)
    """
    # Calculate parts per row for both orientations
    parts_per_row_normal = math.floor((sheet_width_cm - 2 * edge_clearance + gutter_size) / (part_width + gutter_size))
    parts_per_column_normal = math.floor((sheet_height_cm - 2 * edge_clearance + gutter_size) / (part_height + gutter_size))
    normal_total = parts_per_row_normal * parts_per_column_normal
    
    parts_per_row_rotated = math.floor((sheet_width_cm - 2 * edge_clearance + gutter_size) / (part_height + gutter_size))
    parts_per_column_rotated = math.floor((sheet_height_cm - 2 * edge_clearance + gutter_size) / (part_width + gutter_size))
    rotated_total = parts_per_row_rotated * parts_per_column_rotated
    
    # Use the orientation that gives better yield
    if rotated_total > normal_total:
        return (True, parts_per_row_rotated, parts_per_column_rotated)
    else:
        return (False, parts_per_row_normal, parts_per_column_normal)

def advanced_nesting(layout_sketch, selected_sketch, bbox, sheet_width_cm, sheet_height_cm, 
                     edge_clearance, gutter_size, part_width, part_height, quantity):
    """
    Perform advanced nesting with optimized placement and potential rotation
    
    Returns:
        tuple: (parts_placed, rotated_parts, parts_per_row, parts_per_column)
    """
    bbox_min_x, bbox_max_x, bbox_min_y, bbox_max_y = bbox
    
    # Check if rotating gives better yield
    rotate_parts, parts_per_row, parts_per_column = get_optimal_rotation(
        part_width, part_height, sheet_width_cm, sheet_height_cm, edge_clearance, gutter_size
    )
    
    if rotate_parts:
        # Swap dimensions for layout calculation
        temp = part_width
        part_width = part_height
        part_height = temp
    
    # Make sure at least one part fits
    parts_per_row = max(1, parts_per_row)
    parts_per_column = max(1, parts_per_column)
    
    # Calculate total parts that can fit
    max_parts = parts_per_row * parts_per_column
    
    # Limit to requested quantity
    parts_to_place = min(quantity, max_parts)
    
    # Place the parts in the layout sketch
    placed_parts = 0
    
    try:
        for row in range(parts_per_column):
            for col in range(parts_per_row):
                if placed_parts >= parts_to_place:
                    break
                
                # Calculate position for this part
                pos_x = edge_clearance + col * (part_width + gutter_size)
                pos_y = edge_clearance + row * (part_height + gutter_size)
                
                # Copy the sketch to the new position
                copy_result = copy_sketch_to_position(
                    layout_sketch, 
                    selected_sketch,
                    pos_x, 
                    pos_y, 
                    rotate_parts
                )
                
                if copy_result:
                    placed_parts += 1
    except Exception as e:
        adsk.core.Application.get().userInterface.messageBox(
            f'Error placing parts: {str(e)}\n{traceback.format_exc()}'
        )
    
    return (placed_parts, rotate_parts, parts_per_row, parts_per_column)

def copy_sketch_to_position(layout_sketch, source_sketch, target_x, target_y, rotate=False):
    """
    Copy a sketch to a target position in the layout sketch
    
    Args:
        layout_sketch: The target sketch where parts will be placed
        source_sketch: The sketch to copy
        target_x: X position to place the part
        target_y: Y position to place the part
        rotate: Whether to rotate the part 90 degrees
        
    Returns:
        bool: Success or failure
    """
    try:
        # Get the sketch entities
        entities = adsk.core.ObjectCollection.create()
        
        for curve in source_sketch.sketchCurves:
            entities.add(curve)
        for point in source_sketch.sketchPoints:
            entities.add(point)
        
        # Create a transform to move the entities
        transform = adsk.core.Matrix3D.create()
        transform.translation = adsk.core.Vector3D.create(target_x, target_y, 0)
        
        # Add rotation if needed
        if rotate:
            rot_transform = adsk.core.Matrix3D.create()
            rot_transform.setToRotation(math.pi/2, adsk.core.Vector3D.create(0, 0, 1), 
                                       adsk.core.Point3D.create(target_x, target_y, 0))
            transform.transformBy(rot_transform)
        
        # Copy the entities to the target sketch
        layout_sketch.copy(entities, transform)
        return True
    except:
        return False

def bin_packing_nesting(sheet_width, sheet_height, parts_list, edge_clearance, gutter_size):
    """
    Implements a more advanced bin packing algorithm for nesting irregular parts
    
    Args:
        sheet_width: Width of the sheet
        sheet_height: Height of the sheet
        parts_list: List of parts with their dimensions and quantities
        edge_clearance: Clearance from sheet edge
        gutter_size: Space between parts
        
    Returns:
        dict: Nesting solution with part placements
    """
    # Placeholder for a more sophisticated bin packing algorithm
    # This could implement algorithms like:
    # - Guillotine cutting
    # - Maximal rectangles approach
    # - Genetic algorithm optimization
    
    solution = {
        'utilization': 0,
        'placements': [],
        'unused_area': sheet_width * sheet_height
    }
    
    # Sort parts by area (largest first)
    sorted_parts = sorted(parts_list, key=lambda p: p['width'] * p['height'], reverse=True)
    
    # Simple implementation of next-fit decreasing height algorithm
    x, y = edge_clearance, edge_clearance
    max_height_in_row = 0
    
    for part in sorted_parts:
        for _ in range(part['quantity']):
            part_w = part['width']
            part_h = part['height']
            
            # Try normal orientation first
            if x + part_w <= sheet_width - edge_clearance:
                # Part fits in current row
                solution['placements'].append({
                    'part_id': part['id'],
                    'x': x,
                    'y': y,
                    'rotated': False
                })
                x += part_w + gutter_size
                max_height_in_row = max(max_height_in_row, part_h)
            
            # Try rotated orientation
            elif x + part_h <= sheet_width - edge_clearance and y + part_w <= sheet_height - edge_clearance:
                # Rotated part fits in current row
                solution['placements'].append({
                    'part_id': part['id'],
                    'x': x,
                    'y': y,
                    'rotated': True
                })
                x += part_h + gutter_size
                max_height_in_row = max(max_height_in_row, part_w)
                
            else:
                # Start a new row
                x = edge_clearance
                y += max_height_in_row + gutter_size
                max_height_in_row = 0
                
                # Check if we still have room vertically
                if y + part_h > sheet_height - edge_clearance:
                    # Cannot place any more parts
                    break
                    
                # Place part in the new row
                solution['placements'].append({
                    'part_id': part['id'],
                    'x': x,
                    'y': y,
                    'rotated': False
                })
                x += part_w + gutter_size
                max_height_in_row = part_h
    
    # Calculate utilization
    used_area = 0
    for part in sorted_parts:
        part_area = part['width'] * part['height']
        parts_placed = sum(1 for p in solution['placements'] if p['part_id'] == part['id'])
        used_area += part_area * parts_placed
        
    sheet_area = sheet_width * sheet_height
    solution['utilization'] = (used_area / sheet_area) * 100
    solution['unused_area'] = sheet_area - used_area
    
    return solution

def calculate_sketch_bounding_box(sketch):
    """
    Calculate the bounding box of a sketch
    
    Args:
        sketch: The Fusion 360 sketch to analyze
        
    Returns:
        tuple: (min_x, max_x, min_y, max_y) or None if sketch is empty
    """
    try:
        if not sketch:
            return None
            
        min_x = float('inf')
        max_x = float('-inf')
        min_y = float('inf')
        max_y = float('-inf')
        
        # Process sketch curves (lines, arcs, circles, etc.)
        for curve in sketch.sketchCurves:
            # Get the bounding box of each curve
            bbox = curve.boundingBox
            if not bbox:
                continue
                
            # Update global bounds
            min_x = min(min_x, bbox.minPoint.x)
            max_x = max(max_x, bbox.maxPoint.x)
            min_y = min(min_y, bbox.minPoint.y)
            max_y = max(max_y, bbox.maxPoint.y)
            
        # Process sketch points
        for point in sketch.sketchPoints:
            geo = point.geometry
            min_x = min(min_x, geo.x)
            max_x = max(max_x, geo.x)
            min_y = min(min_y, geo.y)
            max_y = max(max_y, geo.y)
            
        # Check if we found any geometry
        if min_x == float('inf'):
            return None
            
        return (min_x, max_x, min_y, max_y)
        
    except:
        print(f"Error calculating bounding box: {traceback.format_exc()}")
        return None

def place_sketch_with_offset(target_sketch, source_sketch, x_offset, y_offset, bbox, rotate=False):
    """
    Copy a sketch to a target sketch with offset
    
    Args:
        target_sketch: The target sketch to copy into
        source_sketch: The source sketch to copy from
        x_offset: The X offset to apply
        y_offset: The Y offset to apply
        bbox: The bounding box of the source sketch (min_x, max_x, min_y, max_y)
        rotate: Whether to rotate the sketch 90 degrees
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        app = adsk.core.Application.get()
        design = app.activeProduct
        
        # Create a transform to apply to the copied entities
        transform = adsk.core.Matrix3D.create()
        
        # Apply rotation if requested (around center of bounding box)
        if rotate:
            min_x, max_x, min_y, max_y = bbox
            center_x = (min_x + max_x) / 2
            center_y = (min_y + max_y) / 2
            
            # Translate to origin, rotate, translate back
            transform.translation = adsk.core.Vector3D.create(-center_x, -center_y, 0)
            rot_transform = adsk.core.Matrix3D.create()
            rot_transform.setToRotation(math.pi/2, adsk.core.Vector3D.create(0, 0, 1), adsk.core.Point3D.create(0, 0, 0))
            transform.transformBy(rot_transform)
            transform.translation = adsk.core.Vector3D.create(center_y, -center_x, 0)  # Swapped due to rotation
        
        # Apply the offset
        if rotate:
            transform.translation = adsk.core.Vector3D.create(x_offset, y_offset, 0)
        else:
            transform.translation = adsk.core.Vector3D.create(x_offset, y_offset, 0)
        
        # Copy the sketch
        target_sketch.copy(source_sketch, transform)
        return True
        
    except:
        print(f"Error placing sketch: {traceback.format_exc()}")
        return False
