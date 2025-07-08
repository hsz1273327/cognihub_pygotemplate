# cognihub_pygotemplate

一个简单、高性能的Python包装器，用于Go原生的`text/template`模板引擎。

该库允许你在Python项目中直接使用Go模板（如Ollama中使用的模板），通过CGo和Python的`ctypes`调用编译后的Go共享库，实现100%兼容性。

## 系统要求

- Python 3.10+
- Go编译器（推荐1.21+版本）已安装并在系统PATH中可用

## 安装

### 从PyPI安装（推荐）

```bash
pip install cognihub_pygotemplate
```

### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/hsz1273327/cognihub_pygotemplate.git
cd cognihub_pygotemplate

# 安装包
pip install .
```

库会在安装过程中自动编译Go源代码。

## 使用方法

```python
from cognihub_pygotemplate import GoTemplateEngine

# 你的Go模板字符串
template_str = """
Hello, {{.Name}}!
{{if .Items}}You have {{len .Items}} items:
{{range .Items}}- {{.}}
{{end}}{{else}}You have no items.{{end}}
"""

# 要渲染的数据
data = {
    "Name": "World",
    "Items": ["apple", "banana", "cherry"]
}

try:
    # 创建引擎实例
    engine = GoTemplateEngine(template_str)

    # 渲染模板
    output = engine.render(data)

    print(output)

except (RuntimeError, ValueError) as e:
    print(f"发生错误: {e}")
```

## 开发构建

```bash
python setup.py build_py
```

## 构建轮子包

```bash
# 为当前平台构建
python setup.py bdist_wheel
```

## 特性

- **100% Go模板兼容性**: 使用Go原生的`text/template`引擎
- **高性能**: 直接CGo绑定，开销最小
- **跨平台**: 支持Windows、macOS（Intel和ARM64）以及Linux
- **内存安全**: 适当的内存管理防止内存泄漏
- **易于集成**: 简单的Python API，使用体验原生化

## 错误处理

库为常见问题提供清晰的错误消息：

- `JSON_ERROR`: 无效的数据格式
- `TEMPLATE_PARSE_ERROR`: 模板语法错误
- `TEMPLATE_EXECUTE_ERROR`: 模板执行时运行错误

## 许可证

本项目采用MIT许可证 - 查看[LICENSE](LICENSE)文件了解详情。

## 贡献

欢迎贡献代码！请随时提交Pull Request。

## 支持的平台

- **Windows**: x64
- **macOS**: Intel (x86_64) 和 Apple Silicon (ARM64)
- **Linux**: x86_64

## 技术细节

- 使用Go的`text/template`包进行模板解析和执行
- 通过CGo构建为共享库（.dll/.dylib/.so）
- Python通过ctypes调用Go函数
- 自动内存管理避免内存泄漏
- 支持复杂的模板语法，包括条件语句、循环、函数调用等

## 常见问题

### Q: 为什么使用Go模板而不是Jinja2？

A: Go模板与Ollama等工具100%兼容，如果你需要在Python中使用相同的模板，这个库是完美的选择。

### Q: 性能如何？

A: 由于直接调用Go的原生实现，性能非常接近纯Go程序，比Python模板引擎更快。

### Q: 支持哪些Go模板功能？

A: 支持Go `text/template`包的所有功能，包括：

- 变量替换
- 条件语句（if/else）
- 循环（range）
- 管道操作
- 函数调用
- 嵌套模板

### Q: 如何处理复杂的数据结构？

A: 库会自动将Python的字典、列表等转换为Go能理解的JSON格式，支持任意嵌套的数据结构。
