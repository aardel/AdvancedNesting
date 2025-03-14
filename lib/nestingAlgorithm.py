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
    """Calculate the bounding box of a sketch"""
    try:
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        has_curves = False
        
        # Iterate through sketch curves to find min/max points
        for curve in sketch.sketchCurves:
            has_curves = True
            
            try:
                if curve.objectType == adsk.fusion.SketchCircle.classType():
                    circle = adsk.fusion.SketchCircle.cast(curve)
                    center = circle.centerPoint
                    radius = circle.radius
                    
                    min_x = min(min_x, center.x - radius)
                    min_y = min(min_y, center.y - radius)
                    max_x = max(max_x, center.x + radius)
                    max_y = max(max_y, center.y + radius)
                    
                elif curve.objectType == adsk.fusion.SketchLine.classType():
                    line = adsk.fusion.SketchLine.cast(curve)
                    
                    try:
                        # Method 1
                        start_x = line.startPoint.x
                        start_y = line.startPoint.y
                        end_x = line.endPoint.x
                        end_y = line.endPoint.y
                    except:
                        # Method 2
                        try:
                            start_x = line.startSketchPoint.geometry.x
                            start_y = line.startSketchPoint.geometry.y
                            end_x = line.endSketchPoint.geometry.x
                            end_y = line.endSketchPoint.geometry.y
                        except:
                            continue
                    
                    min_x = min(min_x, start_x, end_x)
                    min_y = min(min_y, start_y, end_y)
                    max_x = max(max_x, start_x, end_x)
                    max_y = max(max_y, start_y, end_y)
                    
                elif curve.objectType == adsk.fusion.SketchArc.classType():
                    arc = adsk.fusion.SketchArc.cast(curve)
                    
                    try:
                        center = arc.centerPoint
                        start_point = arc.startPoint
                        
                        # Get the radius
                        radius = center.distanceTo(start_point)
                        
                        min_x = min(min_x, center.x - radius)
                        min_y = min(min_y, center.y - radius)
                        max_x = max(max_x, center.x + radius)
                        max_y = max(max_y, center.y + radius)
                    except:
                        try:
                            center_x = arc.centerSketchPoint.geometry.x
                            center_y = arc.centerSketchPoint.geometry.y
                            start_x = arc.startSketchPoint.geometry.x
                            start_y = arc.startSketchPoint.geometry.y
                            
                            # Calculate radius
                            radius = math.sqrt((start_x - center_x)**2 + (start_y - center_y)**2)
                            
                            min_x = min(min_x, center_x - radius)
                            min_y = min(min_y, center_y - radius)
                            max_x = max(max_x, center_x + radius)
                            max_y = max(max_y, center_y + radius)
                        except:
                            continue
            except:
                continue
        
        if not has_curves or min_x == float('inf'):
            return None
        
        # Ensure a minimum size to prevent zero-width/height boxes
        if max_x - min_x < 0.01:
            max_x = min_x + 0.01
        if max_y - min_y < 0.01:
            max_y = min_y + 0.01
            
        return [min_x, max_x, min_y, max_y]
        
    except:
        return None

def place_sketch_with_offset(layout_sketch, sketch, x_offset, y_offset, bbox, rotate=False):
    """
    Place a sketch in the layout with offset and rotation
    
    Args:
        layout_sketch: The sketch where parts will be placed
        sketch: The sketch to copy
        x_offset, y_offset: Position to place the part
        bbox: Bounding box [min_x, max_x, min_y, max_y]
        rotate: Whether to rotate 90 degrees
    """
    min_x, max_x, min_y, max_y = bbox
    
    # Copy each curve with offset and possible rotation
    for curve in sketch.sketchCurves:
        try:
            if rotate:
                # Rotate the part by 90 degrees
                if curve.objectType == adsk.fusion.SketchCircle.classType():
                    circle = adsk.fusion.SketchCircle.cast(curve)
                    
                    # Calculate center point after rotation (90 degrees around origin)
                    orig_x = circle.centerPoint.x - min_x
                    orig_y = circle.centerPoint.y - min_y
                    
                    # Rotate 90 degrees (swap x,y and negate one)
                    rot_x = orig_y
                    rot_y = -orig_x
                    
                    # Apply offset
                    center_x = rot_x + x_offset + min_x
                    center_y = rot_y + y_offset + min_y
                    
                    # Create the circle at the new position
                    layout_sketch.sketchCurves.sketchCircles.addByCenterRadius(
                        adsk.core.Point3D.create(center_x, center_y, 0),
                        circle.radius
                    )
                    
                elif curve.objectType == adsk.fusion.SketchLine.classType():
                    line = adsk.fusion.SketchLine.cast(curve)
                    
                    try:
                        orig_start_x = line.startPoint.x - min_x
                        orig_start_y = line.startPoint.y - min_y
                        orig_end_x = line.endPoint.x - min_x
                        orig_end_y = line.endPoint.y - min_y
                        
                        # Rotate 90 degrees
                        rot_start_x = orig_start_y
                        rot_start_y = -orig_start_x
                        rot_end_x = orig_end_y
                        rot_end_y = -orig_end_x
                        
                        # Apply offset
                        start_x = rot_start_x + x_offset + min_x
                        start_y = rot_start_y + y_offset + min_y
                        end_x = rot_end_x + x_offset + min_x
                        end_y = rot_end_y + y_offset + min_y
                        
                        # Create new line
                        layout_sketch.sketchCurves.sketchLines.addByTwoPoints(
                            adsk.core.Point3D.create(start_x, start_y, 0),
                            adsk.core.Point3D.create(end_x, end_y, 0)
                        )
                    except:
                        # Try alternative method
                        try:
                            # Method using startSketchPoint
                            orig_start_x = line.startSketchPoint.geometry.x - min_x
                            orig_start_y = line.startSketchPoint.geometry.y - min_y
                            orig_end_x = line.endSketchPoint.geometry.x - min_x
                            orig_end_y = line.endSketchPoint.geometry.y - min_y
                            
                            # Rotate 90 degrees
                            rot_start_x = orig_start_y
                            rot_start_y = -orig_start_x
                            rot_end_x = orig_end_y
                            rot_end_y = -orig_end_x
                            
                            # Apply offset
                            start_x = rot_start_x + x_offset + min_x
                            start_y = rot_start_y + y_offset + min_y
                            end_x = rot_end_x + x_offset + min_x
                            end_y = rot_end_y + y_offset + min_y
                            
                            # Create new line
                            layout_sketch.sketchCurves.sketchLines.addByTwoPoints(
                                adsk.core.Point3D.create(start_x, start_y, 0),
                                adsk.core.Point3D.create(end_x, end_y, 0)
                            )
                        except:
                            pass
                            
                elif curve.objectType == adsk.fusion.SketchArc.classType():
                    arc = adsk.fusion.SketchArc.cast(curve)
                    
                    try:
                        # Get points from the arc
                        orig_center_x = arc.centerPoint.x - min_x
                        orig_center_y = arc.centerPoint.y - min_y
                        orig_start_x = arc.startPoint.x - min_x
                        orig_start_y = arc.startPoint.y - min_y
                        orig_end_x = arc.endPoint.x - min_x
                        orig_end_y = arc.endPoint.y - min_y
                        
                        # Rotate 90 degrees
                        rot_center_x = orig_center_y
                        rot_center_y = -orig_center_x
                        rot_start_x = orig_start_y
                        rot_start_y = -orig_start_x
                        rot_end_x = orig_end_y
                        rot_end_y = -orig_end_x
                        
                        # Apply offset
                        center_x = rot_center_x + x_offset + min_x
                        center_y = rot_center_y + y_offset + min_y
                        start_x = rot_start_x + x_offset + min_x
                        start_y = rot_start_y + y_offset + min_y
                        end_x = rot_end_x + x_offset + min_x
                        end_y = rot_end_y + y_offset + min_y
                        
                        # Create new arc
                        layout_sketch.sketchCurves.sketchArcs.addByThreePoints(
                            adsk.core.Point3D.create(start_x, start_y, 0),
                            adsk.core.Point3D.create(end_x, end_y, 0),
                            adsk.core.Point3D.create(center_x, center_y, 0)
                        )
                    except:
                        pass
            else:
                # Normal orientation (no rotation)
                if curve.objectType == adsk.fusion.SketchCircle.classType():
                    circle = adsk.fusion.SketchCircle.cast(curve)
                    center_x = circle.centerPoint.x + x_offset
                    center_y = circle.centerPoint.y + y_offset
                    
                    # Create the circle at the new position
                    layout_sketch.sketchCurves.sketchCircles.addByCenterRadius(
                        adsk.core.Point3D.create(center_x, center_y, 0),
                        circle.radius
                    )
                    
                elif curve.objectType == adsk.fusion.SketchLine.classType():
                    line = adsk.fusion.SketchLine.cast(curve)
                    
                    try:
                        # Method 1
                        start_x = line.startPoint.x + x_offset
                        start_y = line.startPoint.y + y_offset
                        end_x = line.endPoint.x + x_offset
                        end_y = line.endPoint.y + x_offset
                        
                        # Create new line
                        layout_sketch.sketchCurves.sketchLines.addByTwoPoints(
                            adsk.core.Point3D.create(start_x, start_y, 0),
                            adsk.core.Point3D.create(end_x, end_y, 0)
                        )
                    except:
                        try:
                            # Method 2 using startSketchPoint
                            start_x = line.startSketchPoint.geometry.x + x_offset
                            start_y = line.startSketchPoint.geometry.y + y_offset
                            end_x = line.endSketchPoint.geometry.x + x_offset
                            end_y = line.endSketchPoint.geometry.y + y_offset
                            
                            # Create new line
                            layout_sketch.sketchCurves.sketchLines.addByTwoPoints(
                                adsk.core.Point3D.create(start_x, start_y, 0),
                                adsk.core.Point3D.create(end_x, end_y, 0)
                            )
                        except:
                            pass
                            
                elif curve.objectType == adsk.fusion.SketchArc.classType():
                    arc = adsk.fusion.SketchArc.cast(curve)
                    
                    try:
                        center_x = arc.centerPoint.x + x_offset
                        center_y = arc.centerPoint.y + y_offset
                        start_x = arc.startPoint.x + x_offset
                        start_y = arc.startPoint.y + y_offset
                        end_x = arc.endPoint.x + x_offset
                        end_y = arc.endPoint.y + y_offset
                        
                        # Create new arc
                        layout_sketch.sketchCurves.sketchArcs.addByThreePoints(
                            adsk.core.Point3D.create(start_x, start_y, 0),
                            adsk.core.Point3D.create(end_x, end_y, 0),
                            adsk.core.Point3D.create(center_x, center_y, 0)
                        )
                    except:
                        try:
                            # Try alternative method for arcs
                            center_x = arc.centerSketchPoint.geometry.x + x_offset
                            center_y = arc.centerSketchPoint.geometry.y + y_offset
                            start_x = arc.startSketchPoint.geometry.x + x_offset
                            start_y = arc.startSketchPoint.geometry.y + y_offset
                            end_x = arc.endSketchPoint.geometry.x + x_offset
                            end_y = arc.endSketchPoint.geometry.y + y_offset
                            
                            # Create new arc
                            layout_sketch.sketchCurves.sketchArcs.addByThreePoints(
                                adsk.core.Point3D.create(start_x, start_y, 0),
                                adsk.core.Point3D.create(end_x, end_y, 0),
                                adsk.core.Point3D.create(center_x, center_y, 0)
                            )
                        except:
                            pass
        except:
            pass
