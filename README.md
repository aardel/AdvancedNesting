# Advanced Nesting Add-in for Fusion 360

A powerful nesting solution for optimizing part layouts on sheet materials.

## Features

- **Grid Pattern Nesting**: Efficiently arrange parts in rows and columns
- **Bin Packing Algorithm**: Advanced algorithm for optimal material utilization 
- **Automatic Rotation**: Automatically rotates parts for better yield
- **Interactive UI**: Easy-to-use interface for configuring nesting parameters
- **Preview Generation**: Preview the layout before creating sketches

## Installation

1. Download the latest release from GitHub
2. Unzip the folder to a location on your computer
3. In Fusion 360, go to the "Scripts and Add-Ins" dialog (Shift+S)
4. Select the "Add-Ins" tab and click the "+" icon
5. Browse to the unzipped folder and select it
6. The add-in should now appear in your list of add-ins

## Usage

### Basic Nesting

1. Create or open a design containing the parts you want to nest
2. Select the "Advanced Nesting" command from the Manufacturing panel
3. Set your sheet dimensions and spacing parameters
4. Select the sketch, profile, or component to nest
5. Choose your nesting method and quantity
6. Click OK to generate the nesting layout

### Nesting Parameters

- **Sheet Width/Height**: Dimensions of your stock material
- **Edge Clearance**: Minimum distance from parts to the edge of the sheet
- **Space Between Parts**: Minimum distance between adjacent parts
- **Nesting Method**: Choose between grid pattern or bin packing algorithms
- **Quantity**: Number of parts to nest

## Advanced Features

### Bin Packing Algorithm

The bin packing algorithm provides more efficient material utilization than simple grid patterns:

- Handles multiple different parts in a single nest
- Automatically rotates parts when beneficial
- Optimizes placement to minimize waste
- Reports material utilization percentage

### Multiple Sheet Support

For large quantities that don't fit on a single sheet:

1. Enter the total quantity needed
2. The add-in will calculate how many sheets are required
3. Each sheet will be created as a separate sketch

## Development

This add-in is built using the Fusion 360 API. To contribute:

1. Clone the repository
2. Make your changes
3. Test in Fusion 360 using the Scripts and Add-ins dialog
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions and support, please open an issue on the GitHub repository.
