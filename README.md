# cognihub_pygotemplate

A simple, high-performance Python wrapper for Go's native `text/template` engine.

*[中文文档](README_CN.md)*

This library allows you to use Go templates (like those from Ollama) directly in your Python projects with 100% compatibility, by calling a compiled Go shared library via CGo and Python's `ctypes`.

## Prerequisites

- Python 3.10+
- Go compiler (1.21+ recommended) installed and available in your system's PATH

## Installation

### From PyPI (Recommended)

```bash
pip install cognihub_pygotemplate
```

### From Source

```bash
# Clone the repository
git clone https://github.com/hsz1273327/cognihub_pygotemplate.git
cd cognihub_pygotemplate

# Install the package
pip install .
```

The library will automatically compile the Go source code during installation.

## Usage

```python
from cognihub_pygotemplate import GoTemplateEngine

# Your Go template string
template_str = """
Hello, {{.Name}}!
{{if .Items}}You have {{len .Items}} items:
{{range .Items}}- {{.}}
{{end}}{{else}}You have no items.{{end}}
"""

# Data to render
data = {
    "Name": "World",
    "Items": ["apple", "banana", "cherry"]
}

try:
    # Create an engine instance
    engine = GoTemplateEngine(template_str)

    # Render the template
    output = engine.render(data)

    print(output)

except (RuntimeError, ValueError) as e:
    print(f"An error occurred: {e}")

```

## Development Build

```bash
python setup.py build_py
```

## Build Wheels

```bash
# For current platform
python setup.py bdist_wheel
```

## Features

- **100% Go Template Compatibility**: Uses Go's native `text/template` engine
- **High Performance**: Direct CGo bindings with minimal overhead
- **Cross-Platform**: Supports Windows, macOS (Intel & ARM64), and Linux
- **Memory Safe**: Proper memory management to prevent leaks
- **Easy Integration**: Simple Python API that feels native

## Error Handling

The library provides clear error messages for common issues:

- `JSON_ERROR`: Invalid data format
- `TEMPLATE_PARSE_ERROR`: Template syntax errors
- `TEMPLATE_EXECUTE_ERROR`: Runtime template execution errors

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.


