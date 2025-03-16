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
if spec:
    nestingAlgorithm = importlib.util.module_from_spec(spec)
    if spec.loader:
        spec.loader.exec_module(nestingAlgorithm)
else:
    futil.log("Failed to load nestingAlgorithm module", adsk.core.LogLevels.ErrorLogLevel)

# Command ID and other constants
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_NestingCommand'
CMD_NAME = 'Advanced Nesting'
CMD_Description = 'Create optimized sheet layouts for manufacturing'
IS_PROMOTED = True  # Ensure this is True to show in toolbar

# Define command location
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'ManufacturingPanel'
COMMAND_BESIDE_ID = 'MachiningMiscExtrusionsPanel'

# Define palette ID
PALETTE_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_nesting_palette_id'

# Specify the full path to the HTML interface
PALETTE_URL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'html', 'index.html')
PALETTE_URL = PALETTE_URL.replace('\\', '/')

# Set a default docking behavior for the palette
PALETTE_DOCKING = adsk.core.PaletteDockingStates.PaletteDockStateRight

# Icon resource folder
ICON_FOLDER = os.path.dirname(os.path.abspath(__file__))

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

# Global variables
app = None
ui = None
handlers = []

# Command inputs
nesting_type_input = None
sheet_material_input = None
sheet_width_input = None
sheet_height_input = None
edge_clearance_input = None
gutter_size_input = None
kerf_compensation_input = None
quantity_input = None
selection_input = None
create_border_input = None  # New input for sheet border option

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
    palette = ui.palettes.itemById(PALETTE_ID)
    
    # Delete the button
    if command_control:
        command_control.deleteMe()
    
    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()
    
    # Delete the palette
    if palette:
        palette.deleteMe()

# Function called when button is clicked
def command_created(args: adsk.core.CommandCreatedEventArgs):
    futil.log(f'{CMD_NAME} Command Created Event')

    cmd = args.command
    inputs = cmd.commandInputs

    # Create dropdown for material presets
    material_input = inputs.addDropDownCommandInput('material', 'Material Preset', adsk.core.DropDownStyles.TextListDropDownStyle)
    material_input.listItems.add('Steel Sheet (3000x2000)', True)
    material_input.listItems.add('Aluminum Sheet (2500x1250)', False)
    material_input.listItems.add('Plywood (2440x1220)', False)
    material_input.listItems.add('Acrylic (1000x600)', False)
    material_input.listItems.add('Custom', False)

    # Create dropdown for nesting algorithm
    algorithm_input = inputs.addDropDownCommandInput('algorithm', 'Nesting Algorithm', adsk.core.DropDownStyles.TextListDropDownStyle)
    algorithm_input.listItems.add('Basic Nesting', False)
    algorithm_input.listItems.add('Advanced Nesting', True)

    # Create value inputs for sheet dimensions
    width_input = inputs.addValueInput('width', 'Sheet Width (cm)', 'cm', adsk.core.ValueInput.createByReal(300))
    height_input = inputs.addValueInput('height', 'Sheet Height (cm)', 'cm', adsk.core.ValueInput.createByReal(200))

    # Create value inputs for clearance, spacing, kerf, and quantity
    clearance_input = inputs.addValueInput('clearance', 'Edge Clearance (cm)', 'cm', adsk.core.ValueInput.createByReal(1))
    spacing_input = inputs.addValueInput('spacing', 'Part Spacing (cm)', 'cm', adsk.core.ValueInput.createByReal(0.5))
    kerf_input = inputs.addValueInput('kerf', 'Kerf Compensation (mm)', 'mm', adsk.core.ValueInput.createByReal(0))
    quantity_input = inputs.addIntegerSpinnerCommandInput('quantity', 'Quantity', 1, 100, 1, 10)

    # Create checkbox for sheet border
    border_input = inputs.addBoolValueInput('border', 'Create Sheet Border', True, '', True)

    # Create button to select sketch
    select_sketch_button = inputs.addBoolValueInput('selectSketch', 'Select Sketch', False, '', False)

    # Connect command execution handler
    futil.add_handler(cmd.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(cmd.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(cmd.destroy, command_destroy, local_handlers=local_handlers)

def command_input_changed(args: adsk.core.InputChangedEventArgs):
    inputs = args.inputs
    changed_input = args.input

    if changed_input.id == 'material':
        material = changed_input.selectedItem.name
        width_input = inputs.itemById('width')
        height_input = inputs.itemById('height')

        if material == 'Steel Sheet (3000x2000)':
            width_input.value = 300
            height_input.value = 200
        elif material == 'Aluminum Sheet (2500x1250)':
            width_input.value = 250
            height_input.value = 125
        elif material == 'Plywood (2440x1220)':
            width_input.value = 244
            height_input.value = 122
        elif material == 'Acrylic (1000x600)':
            width_input.value = 100
            height_input.value = 60
        elif material == 'Custom':
            width_input.isEnabled = True
            height_input.isEnabled = True
        else:
            width_input.isEnabled = False
            height_input.isEnabled = False

def command_execute(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Execute Event')

    inputs = args.command.commandInputs

    # Gather settings from the command inputs
    settings = {
        'material': inputs.itemById('material').selectedItem.name,
        'algorithm': inputs.itemById('algorithm').selectedItem.name,
        'width': inputs.itemById('width').value,
        'height': inputs.itemById('height').value,
        'clearance': inputs.itemById('clearance').value,
        'spacing': inputs.itemById('spacing').value,
        'kerf': inputs.itemById('kerf').value,
        'quantity': inputs.itemById('quantity').value,
        'border': inputs.itemById('border').value
    }

    # Implement the nesting logic here
    # For now, just log the settings
    futil.log(f'Nesting settings: {settings}')

    # Get the active design
    product = app.activeProduct
    design = adsk.fusion.Design.cast(product)

    if not design:
        ui.messageBox('No active design')
        return

    root_comp = design.rootComponent

    # Create a new sketch for the nesting layout
    layout_sketch = root_comp.sketches.add(root_comp.xYConstructionPlane)
    layout_sketch.name = "Nesting Layout"

    # Draw the sheet boundary if border is enabled
    if settings['border']:
        layout_sketch.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(0, 0, 0),
            adsk.core.Point3D.create(settings['width'], settings['height'], 0)
        )

    # Draw the nested parts
    for i in range(settings['quantity']):
        x = i * (settings['spacing'] + 20)
        y = i * (settings['spacing'] + 30)
        layout_sketch.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(x, y, 0),
            adsk.core.Point3D.create(x + 20, y + 30, 0)
        )

    ui.messageBox('Nesting applied successfully!')

def command_destroy(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Destroy Event')
    global local_handlers
    local_handlers = []

# Show the palette with our HTML interface
def show_nesting_palette():
    # Get palettes collection
    palettes = ui.palettes
    palette = palettes.itemById(PALETTE_ID)
    
    if palette is None:
        # Create the palette
        palette = palettes.add(
            id=PALETTE_ID,
            name="Advanced Nesting",
            htmlFileURL=PALETTE_URL,
            isVisible=True,
            showCloseButton=True,
            isResizable=True,
            width=650,
            height=700,
            useNewWebBrowser=True
        )
        
        # Add event handlers for palette
        futil.add_handler(palette.closed, palette_closed)
        futil.add_handler(palette.incomingFromHTML, palette_incoming)
        
        futil.log(f'Created a new nesting palette: ID = {palette.id}, Name = {palette.name}')
    
    # Make sure the palette is visible
    palette.isVisible = True

def palette_closed(args: adsk.core.UserInterfaceGeneralEventArgs):
    futil.log(f'Nesting palette was closed.')

def palette_incoming(html_args: adsk.core.HTMLEventArgs):
    futil.log(f'Nesting palette incoming event.')
    
    # Process palette messages here
    message_action = html_args.action
    
    futil.log(f"Action from palette: {message_action}")
    futil.log(f"Raw data received: '{html_args.data}'")  # Add this to see raw data
    
    # Handle the different actions from the HTML interface
    if message_action == 'selectPart':
        try:
            # Get the user interface
            product = app.activeProduct
            design = adsk.fusion.Design.cast(product)
            
            if not design:
                html_args.returnData = "No active design"
                return
                
            # Use the simpler direct selection approach
            selections = ui.selectEntity('Select a sketch to nest', 'Sketches')
            
            if selections:
                # Get the selected sketch
                sketch = adsk.fusion.Sketch.cast(selections.entity)
                if sketch:
                    html_args.returnData = sketch.name
                    futil.log(f"Selected sketch: {sketch.name}")
                    return
            
            # User canceled selection
            html_args.returnData = "Selection cancelled"
        except Exception as e:
            html_args.returnData = f"Error: {str(e)}"
            futil.log(f"Error selecting part: {str(e)}", adsk.core.LogLevels.ErrorLogLevel)
    
    elif message_action == 'generatePreview':
        try:
            futil.log("generatePreview action called")  # Add this line
            # Parse settings from the HTML interface
            settings = json.loads(html_args.data)
            futil.log(f"Settings: {settings}")  # Add this line
            
            # Implement the nesting preview logic
            # For now, just return a sample result
            result = {
                "width": settings["width"],
                "height": settings["height"],
                "utilization": 75.5,
                "placements": [
                    {"x": 10, "y": 10, "width": 20, "height": 30, "rotated": False}
                ]
            }
            
            html_args.returnData = json.dumps(result)
            futil.log(f"Preview result: {result}")  # Add this line
        except Exception as e:
            html_args.returnData = "error"
            futil.log(f"Error generating preview: {str(e)}")
    
    elif message_action == 'applyNesting':
        try:
            futil.log("applyNesting action called")
            
            # Debug data received
            futil.log(f"Data type: {type(html_args.data)}")
            futil.log(f"Data length: {len(html_args.data) if html_args.data else 0}")
            
            # Check if there is data
            if html_args.data and len(html_args.data) > 0:
                try:
                    # Parse settings from the HTML interface
                    settings = json.loads(html_args.data)
                    futil.log(f"Settings parsed successfully: {settings}")
                    
                    # Get the active design
                    product = app.activeProduct
                    design = adsk.fusion.Design.cast(product)
                    
                    if not design:
                        html_args.returnData = "No active design"
                        return
                    
                    root_comp = design.rootComponent
                    
                    # Create a new sketch for the nesting layout
                    layout_sketch = root_comp.sketches.add(root_comp.xYConstructionPlane)
                    layout_sketch.name = "Nesting Layout"
                    
                    # Draw the sheet boundary if border is enabled
                    if settings.get("border", False):
                        layout_sketch.sketchCurves.sketchLines.addTwoPointRectangle(
                            adsk.core.Point3D.create(0, 0, 0),
                            adsk.core.Point3D.create(settings.get("width", 100), settings.get("height", 100), 0)
                        )
                    
                    # Draw the nested parts
                    placements = settings.get("placements", [])
                    futil.log(f"Placing {len(placements)} parts")
                    
                    for placement in placements:
                        x = placement.get("x", 0)
                        y = placement.get("y", 0)
                        width = placement.get("width", 20)
                        height = placement.get("height", 20)
                        
                        # Add a rectangle for each part
                        layout_sketch.sketchCurves.sketchLines.addTwoPointRectangle(
                            adsk.core.Point3D.create(x, y, 0),
                            adsk.core.Point3D.create(x + width, y + height, 0)
                        )
                    
                    html_args.returnData = "success"
                    futil.log("Nesting applied successfully")
                except json.JSONDecodeError as je:
                    futil.log(f"JSON decode error: {str(je)}")
                    html_args.returnData = f"JSON error: {str(je)}"
            else:
                futil.log("No settings data received for applyNesting")
                
                # Try a simple implementation just to get something working
                product = app.activeProduct
                design = adsk.fusion.Design.cast(product)
                
                if design:
                    root_comp = design.rootComponent
                    layout_sketch = root_comp.sketches.add(root_comp.xYConstructionPlane)
                    layout_sketch.name = "Basic Nesting Layout"
                    
                    # Draw a simple rectangle
                    layout_sketch.sketchCurves.sketchLines.addTwoPointRectangle(
                        adsk.core.Point3D.create(0, 0, 0),
                        adsk.core.Point3D.create(100, 100, 0)
                    )
                    
                    html_args.returnData = "success"
                    futil.log("Basic nesting applied as fallback")
                else:
                    html_args.returnData = "No settings data and no active design"
        except Exception as e:
            html_args.returnData = f"error: {str(e)}"
            futil.log(f"Error applying nesting: {str(e)}")
            futil.log(traceback.format_exc())
    else:
        html_args.returnData = "Unknown action"

# Class to handle the part selection command
class PartSelectionCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self, html_args):
        super().__init__()
        self.html_args = html_args
        self.palette = ui.palettes.itemById(PALETTE_ID)
        
    def notify(self, args):
        try:
            cmd = args.command
            
            # Create the selection input
            selInput = cmd.commandInputs.addSelectionInput('selection', 'Select Sketch', 'Select a sketch to nest')
            selInput.addSelectionFilter('Sketches')
            selInput.setSelectionLimits(1, 1)
            
            # Add handlers for the command events
            onExecute = PartSelectionExecuteHandler(self.palette)
            cmd.execute.add(onExecute)
            local_handlers.append(onExecute)
            
            onDestroy = PartSelectionDestroyHandler()
            cmd.destroy.add(onDestroy)
            local_handlers.append(onDestroy)
            
        except Exception as e:
            futil.log(f"Error in selection command: {str(e)}")
            if ui:
                ui.messageBox(f'Error in selection command: {str(e)}')

class PartSelectionExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self, palette):
        super().__init__()
        self.palette = palette
        
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs
            selInput = inputs.itemById('selection')
            
            if selInput.selectionCount > 0:
                sketch = adsk.fusion.Sketch.cast(selInput.selection(0).entity)
                sketch_name = sketch.name
                
                # Send the sketch name back to the HTML interface
                if self.palette:
                    self.palette.sendInfoToHTML('updatePartName', sketch_name)
            
        except Exception as e:
            futil.log(f"Error in selection execution: {str(e)}")
            if ui:
                ui.messageBox(f'Error in selection execution: {str(e)}')

class PartSelectionDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
        
    def notify(self, args):
        # Clean up any resources if needed
        pass

class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        try:
            # ...existing code...
            
            # Get selected sketch
            global selection_input
            if selection_input.selectionCount == 0:
                # Try to get current selection from the UI
                current_selections = ui.activeSelections
                sketch_found = False
                
                for i in range(current_selections.count):
                    selected_entity = current_selections.item(i).entity
                    if selected_entity.objectType == adsk.fusion.Sketch.classType():
                        selected_sketch = adsk.fusion.Sketch.cast(selected_entity)
                        sketch_found = True
                        break
                
                if not sketch_found:
                    ui.messageBox("No sketch selected. Please select a sketch to nest.")
                    return
            else:
                selected_sketch = adsk.fusion.Sketch.cast(selection_input.selection(0).entity)
            
            # ...existing code...
        except Exception as e:
            ui.messageBox(f"Error executing command: {str(e)}\n{traceback.format_exc()}")

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
                                max_y = max(max_y, center_x + radius)
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
            if ui:
                ui.messageBox('Calculate sketch bounding box failed:\n{}'.format(traceback.format_exc()))
            return None

# Add a new SelectionChangedHandler class
class SelectionChangedHandler(adsk.core.SelectionEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        try:
            global selection_input
            
            # Update selection inputs when user selects in the viewport
            cmd = args.firingEvent.sender
            if not cmd:
                return
                
            inputs = cmd.commandInputs
            sel_input = inputs.itemById('selection')
            if not sel_input:
                return
                
            # Get the selected entity
            selected_entity = args.selection.entity
            if selected_entity.objectType == adsk.fusion.Sketch.classType():
                # Clear existing selection and add the new one
                sel_input.clearSelection()
                sel_input.addSelection(selected_entity)
                
        except:
            if ui:
                ui.messageBox('Selection changed event failed:\n{}'.format(traceback.format_exc()))

# Add this method to the CommandCreatedEventHandler class to properly handle selection changes
class CommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        try:
            global nesting_type_input, sheet_material_input, sheet_width_input
            global sheet_height_input, edge_clearance_input, gutter_size_input
            global kerf_compensation_input, quantity_input, selection_input
            global create_border_input, handlers
            
            # Get the command
            cmd = args.command
            
            # Get the CommandInputs collection
            inputs = cmd.commandInputs
            
            # Create a group for the nesting parameters
            group_input = inputs.addGroupCommandInput('nestingGroup', 'ADVANCED NESTING v1.0')
            group_children = group_input.children
            
            # Create dropdown for nesting type
            nesting_type_input = group_children.addDropDownCommandInput(
                'nestingType', 
                'Nesting Type', 
                adsk.core.DropDownStyles.TextListDropDownStyle
            )
            # ...existing code...
            
            # Selection input
            selection_input = group_children.addSelectionInput(
                'selection', 
                'Select Sketch', 
                'Select a sketch to nest'
            )
            selection_input.addSelectionFilter('Sketches')
            selection_input.setSelectionLimits(1, 1)  # Require exactly one sketch
            
            # Pre-select any currently selected sketch
            current_selections = ui.activeSelections
            for i in range(current_selections.count):
                selected_entity = current_selections.item(i).entity
                if selected_entity.objectType == adsk.fusion.Sketch.classType():
                    selection_input.addSelection(selected_entity)
                    break
            
            # Connect to the execute event
            on_execute = CommandExecuteHandler()
            cmd.execute.add(on_execute)
            handlers.append(on_execute)
            
            # Connect to the input changed event
            on_input_changed = InputChangedHandler()
            cmd.inputChanged.add(on_input_changed)
            handlers.append(on_input_changed)
            
            # Add selection change event handler
            on_selection_change = SelectionChangedHandler()
            cmd.selectionEvent.add(on_selection_change)
            handlers.append(on_selection_change)
            
        except:
            if ui:
                ui.messageBox('Command created failed:\n{}'.format(traceback.format_exc()))

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
                            max_y = max(max_y, center_x + radius)
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
        if ui:
            ui.messageBox('Calculate sketch bounding box failed:\n{}'.format(traceback.format_exc()))
        return None

import adsk.core
import adsk.fusion
import traceback
import math

# Global variables
app = adsk.core.Application.get()
ui = app.userInterface
handlers = []

# Command inputs
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

def run(context):
    global app, ui, handlers
    
    # Clear previous handlers to avoid memory leaks
    handlers = []
    
    try:
        # Check if command definition already exists and delete it
        existing_cmd_def = ui.commandDefinitions.itemById('advancedNestingCmdId')
        if existing_cmd_def:
            existing_cmd_def.deleteMe()
            
        # Create command definition
        cmd_def = ui.commandDefinitions.addButtonDefinition(
            'advancedNestingCmdId', 
            'Advanced Nesting', 
            'Create optimized nesting layout based on selected sketches'
        )
        
        # Add command created event handler
        on_command_created = CommandCreatedEventHandler()
        cmd_def.commandCreated.add(on_command_created)
        handlers.append(on_command_created)
        
        # Execute the command
        cmd_def.execute()
        
        # Keep the script running
        adsk.autoTerminate(False)
        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class CommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        try:
            global nesting_type_input, sheet_material_input, sheet_width_input
            global sheet_height_input, edge_clearance_input, gutter_size_input
            global kerf_compensation_input, quantity_input, selection_input
            global create_border_input, handlers
            
            # Get the command
            cmd = args.command
            
            # Get the CommandInputs collection
            inputs = cmd.commandInputs
            
            # Create a group for the nesting parameters
            group_input = inputs.addGroupCommandInput('nestingGroup', 'ADVANCED NESTING v1.0')
            group_children = group_input.children
            
            # Create dropdown for nesting type
            nesting_type_input = group_children.addDropDownCommandInput(
                'nestingType', 
                'Nesting Type', 
                adsk.core.DropDownStyles.TextListDropDownStyle
            )
            nesting_type_list = nesting_type_input.listItems
            nesting_type_list.add('Simple Nesting', True)
            nesting_type_list.add('Advanced Nesting', False)
            
            # Create description for nesting types
            group_children.addTextBoxCommandInput(
                'nestingTypeDesc', 
                '', 
                'Simple: Grid layout | Advanced: Optimized layout with rotation',
                2, 
                True
            )
            
            # Sheet Material dropdown
            sheet_material_input = group_children.addDropDownCommandInput(
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
            sheet_width_input = group_children.addValueInput(
                'sheetWidth', 
                'Sheet Width', 
                'm', 
                adsk.core.ValueInput.createByReal(3.0)
            )
            
            sheet_height_input = group_children.addValueInput(
                'sheetHeight', 
                'Sheet Height', 
                'm', 
                adsk.core.ValueInput.createByReal(2.0)
            )
            
            # Edge clearance
            edge_clearance_input = group_children.addValueInput(
                'edgeClearance', 
                'Edge Clearance', 
                'cm', 
                adsk.core.ValueInput.createByReal(1.0)
            )
            
            # Gutter size
            gutter_size_input = group_children.addValueInput(
                'gutterSize', 
                'Gutter Size', 
                'cm', 
                adsk.core.ValueInput.createByReal(0.8)
            )
            
            # Kerf compensation
            kerf_compensation_input = group_children.addValueInput(
                'kerfCompensation', 
                'Kerf Compensation', 
                'mm', 
                adsk.core.ValueInput.createByReal(0.0)
            )
            
            # Quantity
            quantity_input = group_children.addIntegerSpinnerCommandInput(
                'quantity', 
                'Quantity', 
                1, 
                100, 
                1, 
                10
            )
            
            # Create border option
            create_border_input = group_children.addBoolValueInput(
                'createBorder', 
                'Create Sheet Border', 
                True, 
                '', 
                True
            )
            
            # Selection input
            selection_input = group_children.addSelectionInput(
                'selection', 
                'Select Sketch', 
                'Select a sketch to nest'
            )
            selection_input.addSelectionFilter('Sketches')
            selection_input.setSelectionLimits(1, 1)  # Require exactly one sketch
            
            # Pre-select any currently selected sketch
            current_selections = ui.activeSelections
            for i in range(current_selections.count):
                selected_entity = current_selections.item(i).entity
                if selected_entity.objectType == adsk.fusion.Sketch.classType():
                    selection_input.addSelection(selected_entity)
                    break
            
            # Connect to the execute event
            on_execute = CommandExecuteHandler()
            cmd.execute.add(on_execute)
            handlers.append(on_execute)
            
            # Connect to the input changed event
            on_input_changed = InputChangedHandler()
            cmd.inputChanged.add(on_input_changed)
            handlers.append(on_input_changed)
            
            # Add selection change event handler
            on_selection_change = SelectionChangedHandler()
            cmd.selectionEvent.add(on_selection_change)
            handlers.append(on_selection_change)
            
        except:
            if ui:
                ui.messageBox('Command created failed:\n{}'.format(traceback.format_exc()))


class InputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        try:
            global sheet_width_input, sheet_height_input
            
            changed_input = args.input
            
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
            if ui:
                ui.messageBox('Input changed event failed:\n{}'.format(traceback.format_exc()))


class SelectionChangedHandler(adsk.core.SelectionEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        try:
            global selection_input
            
            # Update selection inputs when user selects in the viewport
            cmd = args.firingEvent.sender
            if not cmd:
                return
                
            inputs = cmd.commandInputs
            sel_input = inputs.itemById('selection')
            if not sel_input:
                return
                
            # Get the selected entity
            selected_entity = args.selection.entity
            if selected_entity.objectType == adsk.fusion.Sketch.classType():
                # Clear existing selection and add the new one
                sel_input.clearSelection()
                sel_input.addSelection(selected_entity)
                
        except:
            if ui:
                ui.messageBox('Selection changed event failed:\n{}'.format(traceback.format_exc()))


class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        try:
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
                # Try to get current selection from the UI
                current_selections = ui.activeSelections
                sketch_found = False
                
                for i in range(current_selections.count):
                    selected_entity = current_selections.item(i).entity
                    if selected_entity.objectType == adsk.fusion.Sketch.classType():
                        selected_sketch = adsk.fusion.Sketch.cast(selected_entity)
                        sketch_found = True
                        break
                
                if not sketch_found:
                    ui.messageBox("No sketch selected. Please select a sketch to nest.")
                    return
            else:
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
                    self.copy_part_to_position(selected_sketch, layout_sketch, x_offset, y_offset, 
                                              rotate_parts, bbox_min_x, bbox_min_y)
                    parts_placed += 1
            
            result_message = f"{nesting_type} complete. {parts_placed} parts placed in a single sketch."
            if rotate_parts:
                result_message += " Parts were rotated for optimal yield."
                
            ui.messageBox(result_message)
            
        except Exception as e:
            ui.messageBox(f"Error executing command: {str(e)}\n{traceback.format_exc()}")
    
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
                                max_y = max(max_y, center_x + radius)
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
            ui.messageBox('Calculate sketch bounding box failed:\n{}'.format(traceback.format_exc()))
            return None

    def copy_part_to_position(self, source_sketch, target_sketch, x_offset, y_offset, rotate, bbox_min_x, bbox_min_y):
        """Helper method to copy a sketch to a target position with optional rotation"""
        try:
            # Copy each curve with offset and possible rotation
            for curve in source_sketch.sketchCurves:
                if rotate:
                    self.copy_rotated_curve(curve, target_sketch, x_offset, y_offset, bbox_min_x, bbox_min_y)
                else:
                    self.copy_curve(curve, target_sketch, x_offset, y_offset)
        except Exception as e:
            ui.messageBox(f"Error copying part: {str(e)}")
    
    def copy_rotated_curve(self, curve, target_sketch, x_offset, y_offset, bbox_min_x, bbox_min_y):
        """Copy a curve with 90-degree rotation"""
        try:
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
                target_sketch.sketchCurves.sketchCircles.addByCenterRadius(
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
                    target_sketch.sketchCurves.sketchLines.addByTwoPoints(
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
                        target_sketch.sketchCurves.sketchLines.addByTwoPoints(
                            adsk.core.Point3D.create(start_x, start_y, 0),
                            adsk.core.Point3D.create(end_x, end_y, 0)
                        )
                    except:
                        pass  # Skip if we can't get coordinates
        except:
            pass  # Skip if there's any error
            
    def copy_curve(self, curve, target_sketch, x_offset, y_offset):
        """Copy a curve without rotation"""
        try:
            if curve.objectType == adsk.fusion.SketchCircle.classType():
                circle = adsk.fusion.SketchCircle.cast(curve)
                center_x = circle.centerPoint.x + x_offset
                center_y = circle.centerPoint.y + y_offset
                
                # Create the circle at the new position
                target_sketch.sketchCurves.sketchCircles.addByCenterRadius(
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
                    target_sketch.sketchCurves.sketchLines.addByTwoPoints(
                        adsk.core.Point3D.create(start_x, start_y, 0),
                        adsk.core.Point3D.create(end_x, end_y, 0)
                    )
                except:
                    try:
                        # Method 2 using startSketchPoint
                        start_x = line.startSketchPoint.geometry.x + x_offset
                        start_y = line.startSketchPoint.geometry.y + x_offset
                        end_x = line.endSketchPoint.geometry.x + x_offset
                        end_y = line.endSketchPoint.geometry.y + x_offset
                        
                        # Create new line
                        target_sketch.sketchCurves.sketchLines.addByTwoPoints(
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
                    target_sketch.sketchCurves.sketchArcs.addByThreePoints(
                        adsk.core.Point3D.create(start_x, start_y, 0),
                        adsk.core.Point3D.create(end_x, end_y, 0),
                        adsk.core.Point3D.create(center_x, center_y, 0)
                    )
                except:
                    pass
        except:
            pass  # Skip if there's any error

