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
    if spec and spec.loader:
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
    
    # Delete the button
    if command_control:
        command_control.deleteMe()
    
    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()


def command_created(args: adsk.core.CommandCreatedEventArgs):
    futil.log(f'{CMD_NAME}: Command created event.')
    
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)


def command_execute(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME}: Command execute event.')
    
    # Add code here to execute the command


def command_destroy(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME}: Command destroy event.')
    
    global local_handlers
    local_handlers = []
