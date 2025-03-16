# Advanced Nesting User Guide

This guide will help you use the Advanced Nesting add-in for Fusion 360 effectively.

## Getting Started

After installing the add-in, you'll find the "Advanced Nesting" command in the Manufacture tab of Fusion 360.

## Workflow

1. **Create or Select a Sketch**: Start by creating or selecting an existing sketch that you want to nest
2. **Launch the Command**: Click the "Advanced Nesting" button in the toolbar
3. **Configure Settings**: In the command dialog, configure your nesting settings:
   - **Nesting Type**: Choose between Basic or Advanced nesting algorithms
   - **Sheet Material**: Select from preset material sizes or use custom dimensions
   - **Sheet Dimensions**: Set the width and height of your sheet
   - **Edge Clearance**: Set the minimum distance from part to sheet edge
   - **Spacing Between Parts**: Set the minimum distance between parts
   - **Kerf Compensation**: Account for material loss due to cutting tool width
   - **Quantity**: Specify how many copies of the part to nest
   - **Create Sheet Border**: Option to include a border around the sheet
4. **Run the Nesting**: Click OK to generate the nesting layout
5. **Review the Result**: A new sketch will be created with your nested parts

## Tips for Best Results

- **Use Clean Sketches**: Make sure your source sketch is well-defined with no duplicate lines
- **Consider Part Orientation**: The add-in will automatically determine if rotating parts improves yield
- **Adjust Spacing**: For intricate parts, increase the spacing to ensure adequate clearance
- **Test Different Settings**: Try both Basic and Advanced nesting to see which gives better results

## Advanced Nesting Algorithm

The Advanced Nesting algorithm uses optimization techniques to:

1. Determine optimal part orientation
2. Calculate maximum parts per sheet
3. Arrange parts efficiently on the material

## Troubleshooting

- **Command Not Showing**: Restart Fusion 360 after installing the add-in
- **Nesting Failed**: Ensure your sketch is valid and not too complex
- **Poor Material Utilization**: Try adjusting the spacing and edge clearance parameters
