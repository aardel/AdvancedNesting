import adsk.core
import adsk.fusion
import os
import traceback

from .commands.commandDialog import CommandCreatedEventHandler

# Global variables
app = None
ui = None
commandId = 'advancedNestingCmdId'
commandName = 'Advanced Nesting'
commandDescription = 'Create optimized nesting layout based on selected sketches'
panelId = 'SolidCreatePanel'  # This will place it in the Create panel under Solid tab
handlers = []

# This is the main entry point function for the add-in
def run(context):
    global app, ui, handlers
    
    try:
        # Initialize Fusion API objects
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        # Add a command button to the target panel
        workspaces = ui.workspaces
        modelingWorkspace = workspaces.itemById('FusionSolidEnvironment')
        toolbarPanels = modelingWorkspace.toolbarPanels
        
        # Get the panel to add the command to
        targetPanel = toolbarPanels.itemById(panelId)
        
        # Create the button command definition
        commandDefinition = ui.commandDefinitions.itemById(commandId)
        if not commandDefinition:
            commandDefinition = ui.commandDefinitions.addButtonDefinition(
                commandId, 
                commandName, 
                commandDescription,
                './resources/nesting'  # Optional path to icon resource folder
            )
        
        # Add command created event handler
        onCommandCreated = CommandCreatedEventHandler()
        commandDefinition.commandCreated.add(onCommandCreated)
        handlers.append(onCommandCreated)
        
        # Add button to the target panel
        buttonControl = targetPanel.controls.itemById(commandId)
        if not buttonControl:
            targetPanel.controls.addCommand(commandDefinition)
        
        # Add to the File menu (drop-down menu)
        dropDownMenu = ui.allToolbarPanels.itemById('ToolsPanel').controls
        dropDownControl = dropDownMenu.itemById('ScriptsManagerCommand')
        if dropDownControl:
            # If we want to add to the Scripts and Add-Ins dropdown
            dropDownControl.controls.addCommand(commandDefinition)
        
        # Make your command visible in the UI
        if buttonControl:
            buttonControl.isVisible = True
        
        # Log success
        print('Advanced Nesting add-in loaded successfully')
        
    except:
        if ui:
            ui.messageBox('Failed to initialize Advanced Nesting add-in:\n{}'.format(traceback.format_exc()))


# This function will be called when the add-in is stopped
def stop(context):
    global ui, handlers
    
    try:
        # Clean up the UI
        commandControl = ui.allToolbarPanels.itemById(panelId).controls.itemById(commandId)
        if commandControl:
            commandControl.deleteMe()
        
        commandDefinition = ui.commandDefinitions.itemById(commandId)
        if commandDefinition:
            commandDefinition.deleteMe()
        
        # Also check for the command in the drop-down
        dropDownMenu = ui.allToolbarPanels.itemById('ToolsPanel').controls
        dropDownControl = dropDownMenu.itemById('ScriptsManagerCommand')
        if dropDownControl:
            cmd = dropDownControl.controls.itemById(commandId)
            if cmd:
                cmd.deleteMe()
        
        # Clear all event handlers
        handlers.clear()
        
        print('Advanced Nesting add-in stopped')
        
    except:
        if ui:
            ui.messageBox('Failed to clean up Advanced Nesting add-in:\n{}'.format(traceback.format_exc()))
