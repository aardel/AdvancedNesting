import adsk.core
import adsk.fusion
import traceback
import math
import os
from ..lib import nestingAlgorithm

# Global command inputs
nesting_type_input = None
sheet_material_input = None
sheet_width_input = None
sheet_height_input = None
edge_clearance_input = None
gutter_size_input = None
kerf_compensation_input = None
quantity_input = None
selection_input = None
create_border_input = None

# Get app objects
def getAppObjects():
    app = adsk.core.Application.get()
    ui = app.userInterface
    return app, ui


class CommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        try:
            # Get the command
            cmd = args.command
            app, ui = getAppObjects()
            
            # Get the CommandInputs collection
            inputs = cmd.commandInputs
            
            # Create a group for the nesting parameters
            group_input = inputs.addGroupCommandInput('nestingGroup', 'ADVANCED NESTING v1.0')
            group_child_inputs = group_input.children
            
            # Create dropdown for nesting type
            global nesting_type_input
            nesting_type_input = group_child_inputs.addDropDownCommandInput(
                'nestingType', 
                'Nesting Type', 
                adsk.core.DropDownStyles.TextListDropDownStyle
            )
            nesting_type_list = nesting_type_input.listItems
            nesting_type_list.add('Simple Nesting', True)
            nesting_type_list.add('Advanced Nesting', False)
            
            # Create description for nesting types
            group_child_inputs.addTextBoxCommandInput(
                'nestingTypeDesc', 
                '', 
                'Simple: Grid layout | Advanced: Optimized layout with rotation',
                2, 
                True
            )
            
            # Create dropdowns, value inputs, and selection input
            global sheet_material_input, sheet_width_input, sheet_height_input
            global edge_clearance_input, gutter_size_input, kerf_compensation_input
            global quantity_input, selection_input, create_border_input
            
            # Sheet Material dropdown
            sheet_material_input = group_child_inputs.addDropDownCommandInput(
                'sheetMaterial', 
                'Sheet Material', 
                adsk.core.DropDownStyles.TextListDropDownStyle
            )
            sheet_material_list = sheet_material_input.listItems
            sheet_material_list.add('Steel Sheet (3000x2000)', True)
            sheet_material_list.add('Aluminum Sheet (2500x1250)', False)
            sheet_material_list.add('Plywood (2440x1220)', False)
            sheet_material_list.add('Acrylic (1000x600)', False)
            sheet_material_list.add('Custom', False)
            
            # Sheet dimensions
            sheet_width_input = group_child_inputs.addValueInput(
                'sheetWidth', 
                'Sheet Width', 
                'm', 
                adsk.core.ValueInput.createByReal(3.0)
            )
            
            sheet_height_input = group_child_inputs.addValueInput(
                'sheetHeight', 
                'Sheet Height', 
                'm', 
                adsk.core.ValueInput.createByReal(2.0)
            )
            
            # Edge clearance
            edge_clearance_input = group_child_inputs.addValueInput(
                'edgeClearance', 
                'Edge Clearance', 
                'cm', 
                adsk.core.ValueInput.createByReal(1.0)
            )
            
            # Gutter size
            gutter_size_input = group_child_inputs.addValueInput(
                'gutterSize', 
                'Gutter Size', 
                'cm', 
                adsk.core.ValueInput.createByReal(0.8)
            )
            
            # Kerf compensation
            kerf_compensation_input = group_child_inputs.addValueInput(
                'kerfCompensation', 
                'Kerf Compensation', 
                'mm', 
                adsk.core.ValueInput.createByReal(0.0)
            )
            
            # Quantity
            quantity_input = group_child_inputs.addIntegerSpinnerCommandInput(
                'quantity', 
                'Quantity', 
                1, 
                100, 
                1, 
                10
            )
            
            # Create border option
            create_border_input = group_child_inputs.addBoolValueInput(
                'createBorder', 
                'Create Sheet Border', 
                True, 
                '', 
                True
            )
            
            # Selection input
            selection_input = group_child_inputs.addSelectionInput(
                'selection', 
                'Select Sketch', 
                'Select a sketch to nest'
            )
            selection_input.addSelectionFilter('Sketches')
            selection_input.setSelectionLimits(1, 1)  # Require exactly one sketch
            
            # Connect to the execute event
            on_execute = CommandExecuteHandler()
            cmd.execute.add(on_execute)
            global handlers
            handlers = []
            handlers.append(on_execute)
            
            # Connect to the input changed event
            on_input_changed = InputChangedHandler()
            cmd.inputChanged.add(on_input_changed)
            handlers.append(on_input_changed)
            
        except:
            app, ui = getAppObjects()
            if ui:
                ui.messageBox('Command created failed:\n{}'.format(traceback.format_exc()))


class InputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        try:
            changed_input = args.input
            app, ui = getAppObjects()
            
            # Check if sheet material selection changed
            if changed_input.id == 'sheetMaterial':
                sheet_material = sheet_material_input.selectedItem.name
                
                # Update sheet dimensions based on material selection
                if sheet_material == 'Steel Sheet (3000x2000)':
                    sheet_width_input.value = 3.0
                    sheet_height_input.value = 2.0
                elif sheet_material == 'Aluminum Sheet (2500x1250)':
                    sheet_width_input.value = 2.5
                    sheet_height_input.value = 1.25
                elif sheet_material == 'Plywood (2440x1220)':
                    sheet_width_input.value = 2.44
                    sheet_height_input.value = 1.22
                elif sheet_material == 'Acrylic (1000x600)':
                    sheet_width_input.value = 1.0
                    sheet_height_input.value = 0.6
                
        except:
            app, ui = getAppObjects()
            if ui:
                ui.messageBox('Input changed event failed:\n{}'.format(traceback.format_exc()))


class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        try:
            app, ui = getAppObjects()
            
            # Get the active design
            design = app.activeProduct
            rootComp = design.rootComponent
            
            # Get the units manager
            unitsMgr = design.unitsManager
            
            # Get input values
            nesting_type = nesting_type_input.selectedItem.name
            sheet_width = sheet_width_input.value
            sheet_height = sheet_height_input.value
            edge_clearance = edge_clearance_input.value
            gutter_size = gutter_size_input.value
            kerf_compensation = kerf_compensation_input.value
            quantity = quantity_input.value
            create_border = create_border_input.value
            
            # Convert units to ensure consistency
            sheet_width_cm = unitsMgr.convert(sheet_width, 'm', 'cm')
            sheet_height_cm = unitsMgr.convert(sheet_height, 'm', 'cm')
            
            # Get selected sketch
            if selection_input.selectionCount == 0:
                ui.messageBox("No sketch selected. Please select a sketch to nest.")
                return
                
            selected_sketch = adsk.fusion.Sketch.cast(selection_input.selection(0).entity)
            
            # Create a single sketch for the layout
            layout_sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)
            layout_sketch.name = f"Nesting Layout - {nesting_type}"
            
            # Create rectangle for sheet boundary if option is selected
            if create_border:
                boundary = layout_sketch.sketchCurves.sketchLines.addTwoPointRectangle(
                    adsk.core.Point3D.create(0, 0, 0),
                    adsk.core.Point3D.create(sheet_width, sheet_height, 0)
                )
            
            # Calculate bounding box of the selected sketch
            bbox = self.calculate_sketch_bounding_box(selected_sketch)
            if not bbox:
                ui.messageBox("Could not calculate bounding box for the selected sketch.")
                return
                
            bbox_min_x, bbox_max_x, bbox_min_y, bbox_max_y = bbox
            
            # Calculate part dimensions
            part_width = bbox_max_x - bbox_min_x
            part_height = bbox_max_y - bbox_min_y
            
            # Apply kerf compensation
            part_width += kerf_compensation / 10  # Convert mm to cm
            part_height += kerf_compensation / 10  # Convert mm to cm
            
            # For advanced nesting, check if rotating gives better yield
            rotate_parts = False
            if nesting_type == 'Advanced Nesting' and abs(part_width - part_height) > 0.01:
                # Calculate parts per row for both orientations
                parts_per_row_normal = math.floor((sheet_width_cm - 2 * edge_clearance + gutter_size) / (part_width + gutter_size))
                parts_per_column_normal = math.floor((sheet_height_cm - 2 * edge_clearance + gutter_size) / (part_height + gutter_size))
                normal_total = parts_per_row_normal * parts_per_column_normal
                
                parts_per_row_rotated = math.floor((sheet_width_cm - 2 * edge_clearance + gutter_size) / (part_height + gutter_size))
                parts_per_column_rotated = math.floor((sheet_height_cm - 2 * edge_clearance + gutter_size) / (part_width + gutter_size))
                rotated_total = parts_per_row_rotated * parts_per_column_rotated
                
                # Use the orientation that gives better yield
                if rotated_total > normal_total:
                    rotate_parts = True
                    # Swap dimensions for layout calculation
                    temp = part_width
                    part_width = part_height
                    part_height = temp
                    
                    parts_per_row = parts_per_row_rotated
                    parts_per_column = parts_per_column_rotated
                else:
                    parts_per_row = parts_per_row_normal
                    parts_per_column = parts_per_column_normal
            else:
                # Simple nesting or square parts
                parts_per_row = math.floor((sheet_width_cm - 2 * edge_clearance + gutter_size) / (part_width + gutter_size))
                parts_per_column = math.floor((sheet_height_cm - 2 * edge_clearance + gutter_size) / (part_height + gutter_size))
            
            # Make sure at least one part fits
            parts_per_row = max(1, parts_per_row)
            parts_per_column = max(1, parts_per_column)
            
            # Calculate total parts that can fit
            max_parts = parts_per_row * parts_per_column
            
            # Limit to requested quantity
            parts_to_place = min(quantity, max_parts)
            
            if parts_to_place == 0:
                ui.messageBox(f"The selected sketch is too large to fit on the sheet with the current settings.")
                return
            
            # Place parts in appropriate pattern
            parts_placed = 0
            for row in range(parts_per_column):
                if parts_placed >= parts_to_place:
                    break
                    
                # For advanced nesting, stagger every other row
                row_offset = 0
                if nesting_type == 'Advanced Nesting':
                    row_offset = (gutter_size / 2) if row % 2 == 1 else 0
                    
                for col in range(parts_per_row):
                    if parts_placed >= parts_to_place:
                        break
                        
                    # Calculate position for this part
                    x_offset = edge_clearance + row_offset + col * (part_width + gutter_size) - bbox_min_x
                    y_offset = edge_clearance + row * (part_height + gutter_size) - bbox_min_y
                    
                    # Skip if part would extend beyond sheet width
                    if x_offset + part_width + bbox_min_x > sheet_width_cm - edge_clearance:
                        continue
                    
                    # Copy each curve with offset and possible rotation
                    for curve in selected_sketch.sketchCurves:
                        try:
                            if rotate_parts:
                                if curve.objectType == adsk.fusion.SketchCircle.classType():
                                    circle = adsk.fusion.SketchCircle.cast(curve)
                                    
                                    # Calculate center point after rotation (90 degrees around origin)
                                    orig_x = circle.centerPoint.x - bbox_min_x
                                    orig_y = circle.centerPoint.y - bbox_min_y
                                    
                                    # Rotate 90 degrees (swap x,y and negate one)
                                    rot_x = orig_y
                                    rot_y = -orig_x
                                    
                                    # Apply offset
                                    center_x = rot_x + x_offset + bbox_min_x
                                    center_y = rot_y + y_offset + bbox_min_y
                                    
                                    # Create the circle at the new position
                                    layout_sketch.sketchCurves.sketchCircles.addByCenterRadius(
                                        adsk.core.Point3D.create(center_x, center_y, 0),
                                        circle.radius
                                    )
                                    
                                elif curve.objectType == adsk.fusion.SketchLine.classType():
                                    line = adsk.fusion.SketchLine.cast(curve)
                                    
                                    try:
                                        orig_start_x = line.startPoint.x - bbox_min_x
                                        orig_start_y = line.startPoint.y - bbox_min_y
                                        orig_end_x = line.endPoint.x - bbox_min_x
                                        orig_end_y = line.endPoint.y - bbox_min_y
                                        
                                        # Rotate 90 degrees
                                        rot_start_x = orig_start_y
                                        rot_start_y = -orig_start_x
                                        rot_end_x = orig_end_y
                                        rot_end_y = -orig_end_x
                                        
                                        # Apply offset
                                        start_x = rot_start_x + x_offset + bbox_min_x
                                        start_y = rot_start_y + y_offset + bbox_min_y
                                        end_x = rot_end_x + x_offset + bbox_min_x
                                        end_y = rot_end_y + y_offset + bbox_min_y
                                        
                                        # Create new line
                                        layout_sketch.sketchCurves.sketchLines.addByTwoPoints(
                                            adsk.core.Point3D.create(start_x, start_y, 0),
                                            adsk.core.Point3D.create(end_x, end_y, 0)
                                        )
                                    except:
                                        # Try alternative method
                                        try:
                                            # Method using startSketchPoint
                                            orig_start_x = line.startSketchPoint.geometry.x - bbox_min_x
                                            orig_start_y = line.startSketchPoint.geometry.y - bbox_min_y
                                            orig_end_x = line.endSketchPoint.geometry.x - bbox_min_x
                                            orig_end_y = line.endSketchPoint.geometry.y - bbox_min_y
                                            
                                            # Rotate 90 degrees
                                            rot_start_x = orig_start_y
                                            rot_start_y = -orig_start_x
                                            rot_end_x = orig_end_y
                                            rot_end_y = -orig_end_x
                                            
                                            # Apply offset
                                            start_x = rot_start_x + x_offset + bbox_min_x
                                            start_y = rot_start_y + y_offset + bbox_min_y
                                            end_x = rot_end_x + x_offset + bbox_min_x
                                            end_y = rot_end_y + y_offset + bbox_min_y
                                            
                                            # Create new line
                                            layout_sketch.sketchCurves.sketchLines.addByTwoPoints(
                                                adsk.core.Point3D.create(start_x, start_y, 0),
                                                adsk.core.Point3D.create(end_x, end_y, 0)
                                            )
                                        except:
                                            pass
                            else:
                                # For normal orientation parts
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
                                        end_y = line.endPoint.y + y_offset
                                        
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
                    
                    parts_placed += 1
            
            result_message = f"{nesting_type} complete. {parts_placed} parts placed in a single sketch."
            if rotate_parts:
                result_message += " Parts were rotated for optimal yield."
                
            ui.messageBox(result_message)
            
        except:
            app, ui = getAppObjects()
            if ui:
                ui.messageBox('Execute failed:\n{}'.format(traceback.format_exc()))
    
    def calculate_sketch_bounding_box(self, sketch):
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
            app, ui = getAppObjects()
            if ui:
                ui.messageBox('Calculate sketch bounding box failed:\n{}'.format(traceback.format_exc()))
            return None