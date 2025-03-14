# Development Notes for Advanced Nesting Add-in

## Import Error Resolution for `adsk` modules

When developing Fusion 360 add-ins, you may see import errors for `adsk.core` and `adsk.fusion` in your IDE. This is normal because these modules are only available when running inside Fusion 360.

This project includes:

1. **pyrightconfig.json** - Tells Pylance to ignore `adsk` import errors
2. **Type stubs in /stubs directory** - Provides basic type hints for IDE auto-completion

These files are only used for development and don't affect the actual execution of the add-in.

## Testing

When running unit tests that depend on Fusion 360 API, use mock objects to simulate the behavior of Fusion 360 API objects.

## Debugging

1. Set breakpoints in your code
2. Start Fusion 360
3. Use the "Python: Attach" configuration in VS Code (.vscode/launch.json is already configured)
4. Run your add-in in Fusion 360
5. The debugger will attach when your code runs

## Development Workflow

1. Make changes to the code
2. Test in Fusion 360
3. If necessary, restart Fusion 360 to see code changes
4. For HTML/JS changes in palettes, use shift+refresh in the palette to force reload

## Project Structure

- `/AdvancedNesting` - Main add-in code
  - `/commands` - Individual command implementations
  - `/lib` - Utility functions and modules
- `/lib` - External libraries and algorithms
- `/tests` - Unit tests
- `/stubs` - Type stub files for development only
