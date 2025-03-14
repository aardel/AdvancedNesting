import adsk.core
import adsk.fusion
import os
import sys
import traceback
import json
import math

from ...lib import fusionAddInUtils as futil
from ... import config
import importlib.util

app = adsk.core.Application.get()
ui = app.userInterface

# Load the nesting algorithm module from the parent directory
spec = importlib.util.spec_from_file_location("nestingAlgorithm", 
                                             os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
                                             os.path.dirname(__file__)))), "lib", "nestingAlgorithm.py"))
nestingAlgorithm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nestingAlgorithm)

# Command ID and other constants
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_NestingCommand'
CMD_NAME = 'Advanced Nesting'
CMD_Description = 'Create optimized sheet layouts for manufacturing'
IS_PROMOTED = True  # Ensure this is True to show in toolbar

# Define command location
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'ManufacturingPanel'
COMMAND_BESIDE_ID = 'MachiningMiscExtrusionsPanel'

# Icon resource folder
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

# Local list of event handlers
local_handlers = []

# Sheet material presets
SHEET_MATERIALS = {
    'Steel Sheet (3000x2000)': (3.0, 2.0),
    'Aluminum Sheet (2500x1250)': (2.5, 1.25),
    'Plywood (2440x1220)': (2.44, 1.22),
    'Acrylic (1000x600)': (1.0, 0.6),
    'Custom': None
}

# Executed when add-in is run
def start():
    # Create a command Definition
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)
    
    # Define event handler for command creation
    futil.add_handler(cmd_def.commandCreated, command_created)
    
    # Add button to the UI
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    
    # Create the button in the UI
    if not panel:
        panel = workspace.toolbarPanels.itemById("SolidCreatePanel")  # Fallback panel
    
    control = panel.controls.addCommand(cmd_def)
    control.isPromoted = IS_PROMOTED
    control.isVisible = True  # Make sure it's visible


# Executed when add-in is stopped
def stop():
    # Clean up the UI
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)
    
    # Delete the button
    if command_control:
        command_control.deleteMe()
    
    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()


# Function called when button is clicked
def command_created(args: adsk.core.CommandCreatedEventArgs):
    # Log debug information
    futil.log(f'{CMD_NAME} Command Created Event')
    
    # Get the command inputs
    inputs = args.command.commandInputs
    
    # Create a group for the nesting parameters
    group_input = inputs.addGroupCommandInput('nestingGroup', 'ADVANCED NESTING v1.0')
    group_child_inputs = group_input.children
    
    # Create dropdown for nesting type
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
    
    # Sheet Material dropdown
    sheet_material_input = group_child_inputs.addDropDownCommandInput(
        'sheetMaterial', 
        'Sheet Material', 
        adsk.core.DropDownStyles.TextListDropDownStyle
    )
    sheet_material_list = sheet_material_input.listItems
    for material_name in SHEET_MATERIALS:
        sheet_material_list.add(material_name, material_name == 'Steel Sheet (3000x2000)')
    
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
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    
    # Connect to the input changed event
    futil.add_handler(args.command.inputChanged, input_changed, local_handlers=local_handlers)
    
    # Connect to other events
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)


def input_changed(args: adsk.core.InputChangedEventArgs):
    try:
        changed_input = args.input
        inputs = args.inputs
        
        # Check if sheet material selection changed
        if changed_input.id == 'sheetMaterial':
            sheet_material_input = inputs.itemById('sheetMaterial')
            sheet_width_input = inputs.itemById('sheetWidth')
            sheet_height_input = inputs.itemById('sheetHeight')
            
            material_name = sheet_material_input.selectedItem.name
            if material_name != 'Custom' and material_name in SHEET_MATERIALS:
                width, height = SHEET_MATERIALS[material_name]
                sheet_width_input.value = width
                sheet_height_input.value = height
                
    except:
        if ui:
            ui.messageBox('Input changed event failed:\n{}'.format(traceback.format_exc()))


def command_execute(args: adsk.core.CommandEventArgs):
    # Create a variable to hold the progress dialog
    progressDialog = None
    
    try:
        # Get command inputs
        inputs = args.command.commandInputs
        
        # Get the active design
        design = app.activeProduct
        rootComp = design.rootComponent
        
        # Get the units manager
        unitsMgr = design.unitsManager
        
        # Get input values
        nesting_type_input = inputs.itemById('nestingType')
        sheet_width_input = inputs.itemById('sheetWidth')
        sheet_height_input = inputs.itemById('sheetHeight')
        edge_clearance_input = inputs.itemById('edgeClearance')
        gutter_size_input = inputs.itemById('gutterSize')
        kerf_compensation_input = inputs.itemById('kerfCompensation')
        quantity_input = inputs.itemById('quantity')
        create_border_input = inputs.itemById('createBorder')
        selection_input = inputs.itemById('selection')
        
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
        
        # Create a progress dialog
        progressDialog = ui.createProgressDialog()
        progressDialog.cancelButtonText = 'Cancel'
        progressDialog.isBackgroundTranslucent = False
        progressDialog.show('Advanced Nesting', 'Calculating bounding box...', 0, 10)
        
        # Create a single sketch for the layout
        layout_sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)
        layout_sketch.name = f"Nesting Layout - {nesting_type}"
        
        # Create rectangle for sheet boundary if option is selected
        if create_border:
            boundary = layout_sketch.sketchCurves.sketchLines.addTwoPointRectangle(
                adsk.core.Point3D.create(0, 0, 0),
                adsk.core.Point3D.create(sheet_width_cm, sheet_height_cm, 0)
            )
        
        # Calculate bounding box of the selected sketch
        progressDialog.message = 'Calculating bounding box...'
        progressDialog.progressValue = 2
        
        bbox = nestingAlgorithm.calculate_sketch_bounding_box(selected_sketch)
        if not bbox:
            progressDialog.hide()
            ui.messageBox("Could not calculate bounding box for the selected sketch.")
            return
            
        min_x, max_x, min_y, max_y = bbox
        
        # Calculate part dimensions
        progressDialog.message = 'Calculating part dimensions...'
        progressDialog.progressValue = 3
        
        part_width = max_x - min_x
        part_height = max_y - min_y
        
        # Apply kerf compensation
        part_width += kerf_compensation / 10  # Convert mm to cm
        part_height += kerf_compensation / 10  # Convert mm to cm
        
        # For advanced nesting, check if rotating gives better yield
        progressDialog.message = 'Optimizing layout...'
        progressDialog.progressValue = 5
        
        rotate_parts = False
        if nesting_type == 'Advanced Nesting' and abs(part_width - part_height) > 0.01:
            rotate_parts, parts_per_row, parts_per_column = nestingAlgorithm.get_optimal_rotation(
                part_width, part_height, sheet_width_cm, sheet_height_cm, edge_clearance, gutter_size
            )
            
            # If rotating, swap dimensions for layout calculation
            if rotate_parts:
                temp = part_width
                part_width = part_height
                part_height = temp
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
            progressDialog.hide()
            ui.messageBox(f"The selected sketch is too large to fit on the sheet with the current settings.")
            return
        
        # Place parts in appropriate pattern
        progressDialog.message = 'Placing parts...'
        progressDialog.progressValue = 7
        
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
                x_offset = edge_clearance + row_offset + col * (part_width + gutter_size) - min_x
                y_offset = edge_clearance + row * (part_height + gutter_size) - min_y
                
                # Skip if part would extend beyond sheet width
                if x_offset + part_width + min_x > sheet_width_cm - edge_clearance:
                    continue
                
                # Place the part
                nestingAlgorithm.place_sketch_with_offset(
                    layout_sketch, selected_sketch, x_offset, y_offset, bbox, rotate_parts
                )
                
                parts_placed += 1
                
                # Update progress periodically with fixed values
                if parts_placed == int(parts_to_place / 2):
                    progressDialog.progressValue = 8
        
        # Final progress update
        progressDialog.progressValue = 9
        progressDialog.hide()
        
        # Display results
        result_message = f"{nesting_type} complete. {parts_placed} parts placed in a single sketch."
        if rotate_parts:
            result_message += " Parts were rotated for optimal yield."
            
        ui.messageBox(result_message)
        
    except Exception:
        if progressDialog:
            progressDialog.hide()
        ui.messageBox('Execute failed:\n{}'.format(traceback.format_exc()))


def command_destroy(args: adsk.core.CommandEventArgs):
    global local_handlers
    local_handlers = []


def get_bounding_box(entity):
    """Get the bounding box of a sketch, profile, or body"""
    try:
        if isinstance(entity, adsk.fusion.Sketch):
            # For sketches, get bounding box from curves and points
            min_x, min_y, max_x, max_y = float('inf'), float('inf'), float('-inf'), float('-inf')
            # Process all sketch curves
            for curve in entity.sketchCurves:
                for i in range(2):  # Start and end points
                    point = curve.startSketchPoint if i == 0 else curve.endSketchPoint
                    min_x = min(min_x, point.geometry.x)
                    min_y = min(min_y, point.geometry.y)
                    max_x = max(max_x, point.geometry.x)
                    max_y = max(max_y, point.geometry.y)
            # Process all sketch points
            for point in entity.sketchPoints:
                min_x = min(min_x, point.geometry.x)
                min_y = min(min_y, point.geometry.y)
                max_x = max(max_x, point.geometry.x)
                max_y = max(max_y, point.geometry.y)
                
            return (min_x, max_x, min_y, max_y)
        
        elif isinstance(entity, adsk.fusion.BRepBody):
            # For bodies, get the bounding box from Fusion API
            bbox = entity.boundingBox
            min_pt = bbox.minPoint
            max_pt = bbox.maxPoint
            return (min_pt.x, max_pt.x, min_pt.y, max_pt.y)
        
        elif isinstance(entity, adsk.fusion.Profile):
            # For profiles, get loops and process points
            min_x, min_y, max_x, max_y = float('inf'), float('inf'), float('-inf'), float('-inf')
            for loop in entity.loops:
                for curve in loop.profileCurves:
                    geometry = curve.geometry
                    if hasattr(geometry, 'evaluator'):
                        # For curves with evaluators (arcs, splines, etc.)
                        evaluator = geometry.evaluator
                        start_param, end_param = evaluator.parametricRange
                        num_points = 10  # Sample points along curve
                        for i in range(num_points + 1):
                            param = start_param + (end_param - start_param) * i / num_points
                            point = evaluator.getPointAtParameter(param)[1]
                            min_x = min(min_x, point.x)
                            min_y = min(min_y, point.y)
                            max_x = max(max_x, point.x)
                            max_y = max(max_y, point.y)
                    else:
                        # For simple curves like lines
                        start_point = geometry.startPoint
                        end_point = geometry.endPoint
                        min_x = min(min_x, start_point.x, end_point.x)
                        min_y = min(min_y, start_point.y, end_point.y)
                        max_x = max(max_x, start_point.x, end_point.x)
                        max_y = max(max_y, start_point.y, end_point.y)
            
            return (min_x, max_x, min_y, max_y)
        
        return None
    except:
        return None

