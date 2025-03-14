import json
import adsk.core
import os
from ...lib import fusionAddInUtils as futil
from ... import config
import time
import importlib.util

app = adsk.core.Application.get()
ui = app.userInterface

# Command ID and other constants
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_NestingPalette'
CMD_NAME = 'Advanced Nesting UI'
CMD_Description = 'Open the advanced nesting interface'
IS_PROMOTED = True

# Define palette ID
PALETTE_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_nesting_palette_id'

# Specify the full path to the local html
PALETTE_URL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'html', 'index.html')
PALETTE_URL = PALETTE_URL.replace('\\', '/')

# Set default docking behavior
PALETTE_DOCKING = adsk.core.PaletteDockingStates.PaletteDockStateRight

# Define command location
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'ManufacturingPanel'
COMMAND_BESIDE_ID = 'MachiningMiscExtrusionsPanel'

# Resource location for command icons
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

# Local event handlers list
local_handlers = []

# Load the nesting algorithm module from the parent directory
try:
    spec = importlib.util.spec_from_file_location("nestingAlgorithm", 
                                                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
                                                os.path.dirname(__file__)))), "lib", "nestingAlgorithm.py"))
    if spec:
        nestingAlgorithm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(nestingAlgorithm)
    else:
        raise ImportError("Could not load nestingAlgorithm module")
except:
    futil.log("Failed to load nestingAlgorithm module", adsk.core.LogLevels.ErrorLogLevel)


def start():
    # Create command definition
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)
    
    # Define event handler for command creation
    futil.add_handler(cmd_def.commandCreated, command_created)
    
    # Add button to the UI
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    
    if not panel:
        panel = workspace.toolbarPanels.itemById("SolidCreatePanel")  # Fallback panel
    
    control = panel.controls.addCommand(cmd_def)
    control.isPromoted = IS_PROMOTED


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


def command_created(args: adsk.core.CommandCreatedEventArgs):
    futil.log(f'{CMD_NAME}: Command created event.')
    
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)


def command_execute(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME}: Command execute event.')
    
    palettes = ui.palettes
    palette = palettes.itemById(PALETTE_ID)
    
    if palette is None:
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
        futil.log(f'{CMD_NAME}: Created a new palette: ID = {palette.id}, Name = {palette.name}')
    
    if palette.dockingState == adsk.core.PaletteDockingStates.PaletteDockStateFloating:
        palette.dockingState = PALETTE_DOCKING
    
    palette.isVisible = True


def palette_closed(args: adsk.core.UserInterfaceGeneralEventArgs):
    futil.log(f'{CMD_NAME}: Palette was closed.')


def palette_incoming(html_args: adsk.core.HTMLEventArgs):
    futil.log(f'{CMD_NAME}: Palette incoming event.')
    
    message_data = json.loads(html_args.data) if html_args.data else {}
    message_action = html_args.action
    
    log_msg = f"Event received from {html_args.firingEvent.sender.name}\n"
    log_msg += f"Action: {message_action}\n"
    log_msg += f"Data: {message_data}"
    futil.log(log_msg, adsk.core.LogLevels.InfoLogLevel)
    
    # Handle incoming actions from the HTML palette
    if message_action == 'runNesting':
        # Extract settings from message_data
        try:
            # Get the active product
            product = app.activeProduct
            design = adsk.fusion.Design.cast(product)
            
            if not design:
                html_args.returnData = json.dumps({
                    "error": "No active design found."
                })
                return
            
            # Get selected objects for nesting
            selection = ui.activeSelections
            
            if selection.count == 0:
                html_args.returnData = json.dumps({
                    "error": "No objects selected for nesting."
                })
                return
            
            # Process the nesting based on settings
            sheet_width = message_data.get('sheetWidth', 120)
            sheet_height = message_data.get('sheetHeight', 240)
            edge_clearance = message_data.get('edgeClearance', 1)
            gutter_size = message_data.get('gutterSize', 0.5)
            auto_rotate = message_data.get('autoRotate', True)
            
            # Start timing for performance measurement
            start_time = time.time()
            
            # Create a sample result (in a real implementation, you would call the nesting algorithm)
            # This is a placeholder for demonstration
            if message_data.get('nestingMethod') == 'binpack':
                # Example of bin packing result
                parts_list = [{
                    'id': 'part1',
                    'width': 20,
                    'height': 10,
                    'quantity': 5
                }]
                
                result = nestingAlgorithm.bin_packing_nesting(
                    sheet_width, sheet_height,
                    parts_list, edge_clearance, gutter_size
                )
            else:
                # Example of grid pattern result
                part_width = 20  # This would come from actual selection
                part_height = 10  # This would come from actual selection
                quantity = 10
                
                bbox = (0, 20, 0, 10)  # Placeholder bounding box
                parts_placed, rotated, rows, cols = nestingAlgorithm.get_optimal_rotation(
                    part_width, part_height, sheet_width, sheet_height, edge_clearance, gutter_size
                )
                
                # Create a simulated result
                result = {
                    'sheetWidth': sheet_width,
                    'sheetHeight': sheet_height,
                    'utilization': (part_width * part_height * quantity) / (sheet_width * sheet_height) * 100,
                    'placements': []
                }
                
                # Create simulated placements
                for row in range(rows):
                    for col in range(cols):
                        if len(result['placements']) < quantity:
                            x = edge_clearance + col * (part_width + gutter_size)
                            y = edge_clearance + row * (part_height + gutter_size)
                            result['placements'].append({
                                'part_id': 'Part 1',
                                'x': x,
                                'y': y,
                                'width': part_width,
                                'height': part_height,
                                'rotated': rotated
                            })
            
            # Calculate processing time
            processing_time = time.time() - start_time
            result['processingTime'] = round(processing_time, 2)
            
            # Return the result to the palette
            html_args.returnData = json.dumps(result)
            
        except Exception as e:
            import traceback
            error_msg = f"Error in nesting: {str(e)}\n{traceback.format_exc()}"
            futil.log(error_msg, adsk.core.LogLevels.ErrorLogLevel)
            html_args.returnData = json.dumps({
                "error": str(e)
            })
    
    elif message_action == 'applyNesting':
        # This would implement the actual nesting in the Fusion model
        try:
            # Add code here to apply the nesting result to the Fusion design
            html_args.returnData = "OK"
        except Exception as e:
            html_args.returnData = json.dumps({
                "error": str(e)
            })
    
    elif message_action == 'exportNesting':
        # This would export the nesting layout to a file
        try:
            # Add code here to export the nesting result
            html_args.returnData = "OK"
        except Exception as e:
            html_args.returnData = json.dumps({
                "error": str(e)
            })
    
    elif message_action == 'saveReport':
        # This would save a report of the nesting results
        try:
            # Add code here to generate and save a report
            html_args.returnData = "OK"
        except Exception as e:
            html_args.returnData = json.dumps({
                "error": str(e)
            })
    
    else:
        html_args.returnData = "Unknown action"


def command_destroy(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME}: Command destroy event.')
    
    global local_handlers
    local_handlers = []
