from cognihub_cognihub_pygotemplate import GoTemplateEngine

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