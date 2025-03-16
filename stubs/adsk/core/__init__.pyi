"""Type stubs for adsk.core module"""

class Application:
    @staticmethod
    def get() -> 'Application': ...
    
    @property
    def userInterface(self) -> UserInterface: ...
    
    @property
    def activeProduct(self) -> object: ...
    
    def log(self, message: str, level: LogLevels, log_type: LogTypes) -> None: ...

class UserInterface:
    def createProgressDialog(self) -> ProgressDialog: ...
    def messageBox(self, message: str) -> None: ...
    
    @property
    def commandDefinitions(self) -> CommandDefinitions: ...
    
    @property
    def workspaces(self) -> Workspaces: ...
    
    @property
    def palettes(self) -> Palettes: ...
    
    @property
    def activeSelections(self) -> Selections: ...

class CommandDefinitions:
    def addButtonDefinition(self, id: str, name: str, tooltip: str, resourceFolder: str) -> CommandDefinition: ...
    def itemById(self, id: str) -> CommandDefinition: ...

class CommandDefinition:
    @property
    def commandCreated(self) -> CommandCreatedEvent: ...
    def deleteMe(self) -> bool: ...

class CommandCreatedEvent:
    def add(self, handler: CommandCreatedEventHandler) -> bool: ...

class CommandCreatedEventHandler:
    def notify(self, args: CommandCreatedEventArgs) -> None: ...

class CommandCreatedEventArgs:
    @property
    def command(self) -> Command: ...

class Command:
    @property
    def commandInputs(self) -> CommandInputs: ...
    @property
    def execute(self) -> CommandEvent: ...
    @property
    def executePreview(self) -> CommandEvent: ...
    @property
    def destroy(self) -> CommandEvent: ...
    @property
    def inputChanged(self) -> InputChangedEvent: ...
    @property
    def validateInputs(self) -> ValidateInputsEvent: ...

class CommandInputs:
    def addDropDownCommandInput(self, id: str, name: str, dropDownStyle: int) -> DropDownCommandInput: ...
    def addValueInput(self, id: str, name: str, units: str, initialValue: ValueInput) -> ValueCommandInput: ...
    def addSelectionInput(self, id: str, name: str, tooltip: str) -> SelectionCommandInput: ...
    def addIntegerSpinnerCommandInput(self, id: str, name: str, min: int, max: int, step: int, initialValue: int) -> IntegerSpinnerCommandInput: ...
    def addBoolValueInput(self, id: str, name: str, initialValue: bool) -> BoolValueCommandInput: ...
    def addTextBoxCommandInput(self, id: str, name: str, text: str, numRows: int, isReadOnly: bool) -> TextBoxCommandInput: ...
    def itemById(self, id: str) -> CommandInput: ...

class LogLevels:
    InfoLogLevel: int
    ErrorLogLevel: int

class LogTypes:
    FileLogType: int
    ConsoleLogType: int

class PaletteDockingStates:
    PaletteDockStateRight: int
    PaletteDockStateFloating: int

class ProgressDialog:
    pass

class Workspaces:
    pass

class Palettes:
    pass

class Selections:
    pass

class CommandEvent:
    pass

class InputChangedEvent:
    pass

class ValidateInputsEvent:
    pass

class DropDownCommandInput:
    pass

class ValueInput:
    pass

class ValueCommandInput:
    pass

class SelectionCommandInput:
    pass

class IntegerSpinnerCommandInput:
    pass

class BoolValueCommandInput:
    pass

class TextBoxCommandInput:
    pass

class CommandInput:
    pass

# Add more classes as needed...
