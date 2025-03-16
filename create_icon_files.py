import os
import shutil
import sys

def create_empty_png(filepath, size=(16, 16)):
    """Create an empty PNG file of the specified size."""
    try:
        from PIL import Image
        
        # Create a blank white image
        img = Image.new('RGB', size, color='white')
        img.save(filepath)
        print(f"Created icon: {filepath}")
    except ImportError:
        print("PIL (Pillow) not installed. Cannot create PNG files.")
        print("Please install Pillow: pip install Pillow")
        sys.exit(1)

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    command_dirs = [
        "AdvancedNesting/commands/nestingCommand",
        "AdvancedNesting/commands/paletteShow",
        "AdvancedNesting/commands/commandDialog",
        "AdvancedNesting/commands/paletteSend"
    ]
    
    for cmd_dir in command_dirs:
        full_path = os.path.join(base_dir, cmd_dir)
        
        # Create 16x16.png and 32x32.png in each command directory
        create_empty_png(os.path.join(full_path, "16x16.png"), (16, 16))
        create_empty_png(os.path.join(full_path, "32x32.png"), (32, 32))

if __name__ == "__main__":
    main()
    print("Icon files created. Please restart Fusion 360 to see the changes.")
