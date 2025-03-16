# Contributing to Advanced Nesting

Thank you for your interest in contributing to the Advanced Nesting project! This guide will help you get set up for development.

## Development Setup

1. Fork this repository on GitHub
2. Clone your fork to your local machine
3. Set up a development environment:

```bash
# Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate

# Install development dependencies
pip install flake8 pytest
```

## Testing

Run the tests with:

```bash
python -m pytest tests/
```

## Coding Standards

- Follow PEP 8 guidelines for Python code
- Use descriptive variable names
- Add docstrings to all functions and classes
- Keep functions focused on a single task

## Debugging in Fusion 360

1. Launch Fusion 360
2. Go to Tools tab → Add-Ins → Scripts and Add-Ins
3. Click the "+" icon under "My Add-Ins" tab
4. Browse to your development folder
5. Run the add-in with the "Run" button
6. Use VS Code's "Python: Attach" debug configuration to attach to Fusion 360

## Pull Request Process

1. Update documentation to reflect any changes
2. Make sure your code passes all tests
3. Create a pull request with a clear description of the changes
4. Your PR will be reviewed by maintainers
