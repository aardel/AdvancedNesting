#!/bin/bash

# This script creates sample icons for the commands
# You'll need ImageMagick installed (brew install imagemagick)

# Create directories if they don't exist
mkdir -p "AdvancedNesting/commands/nestingCommand/resources"
mkdir -p "AdvancedNesting/commands/commandDialog/resources"
mkdir -p "AdvancedNesting/commands/paletteShow/resources"
mkdir -p "AdvancedNesting/commands/paletteSend/resources"

# Generate a sample 16x16 icon for nestingCommand
convert -size 16x16 xc:white \
  -fill blue -draw "rectangle 2,2 14,14" \
  -fill red -draw "rectangle 4,4 12,12" \
  "AdvancedNesting/commands/nestingCommand/resources/16x16.png"

# Generate a sample 32x32 icon for nestingCommand
convert -size 32x32 xc:white \
  -fill blue -draw "rectangle 4,4 28,28" \
  -fill red -draw "rectangle 8,8 24,24" \
  "AdvancedNesting/commands/nestingCommand/resources/32x32.png"

# Copy the icons to the other command folders
cp "AdvancedNesting/commands/nestingCommand/resources/16x16.png" "AdvancedNesting/commands/commandDialog/resources/"
cp "AdvancedNesting/commands/nestingCommand/resources/32x32.png" "AdvancedNesting/commands/commandDialog/resources/"

cp "AdvancedNesting/commands/nestingCommand/resources/16x16.png" "AdvancedNesting/commands/paletteShow/resources/"
cp "AdvancedNesting/commands/nestingCommand/resources/32x32.png" "AdvancedNesting/commands/paletteShow/resources/"

cp "AdvancedNesting/commands/nestingCommand/resources/16x16.png" "AdvancedNesting/commands/paletteSend/resources/"
cp "AdvancedNesting/commands/nestingCommand/resources/32x32.png" "AdvancedNesting/commands/paletteSend/resources/"

echo "Sample icons created successfully!"
