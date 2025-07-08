"""go包的包装器."""
import ctypes
import json
import os
import platform
import asyncio
from typing import Dict, Any


class GoTemplateEngine:
    """
    A Python interface to Go's text/template engine.
    It relies on a pre-compiled shared library managed by the package installation process.
    """
    _go_lib = None
    _free_func = None

    def __init__(self, template_content: str):
        self._load_library()
        self.template_content = template_content

    @classmethod
    def _load_library(cls) -> None:
        """Loads the pre-compiled Go shared library."""
        if cls._go_lib:
            return

        lib_name = "librenderer.so"
        if platform.system() == "Windows":
            lib_name = "renderer.dll"
        elif platform.system() == "Darwin":
            lib_name = "librenderer.dylib"

        # 库文件应该和这个Python文件在同一个目录下
        lib_path = os.path.join(os.path.dirname(__file__), lib_name)

        if not os.path.exists(lib_path):
            raise FileNotFoundError(
                f"Shared library not found at {lib_path}. "
                "The package may not have been installed correctly. "
                "Try reinstalling with 'pip install .'"
            )

        cls._go_lib = ctypes.CDLL(lib_path)

        cls._go_lib.RenderTemplate.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        cls._go_lib.RenderTemplate.restype = ctypes.c_char_p

        cls._go_lib.FreeString.argtypes = [ctypes.c_char_p]
        cls._go_lib.FreeString.restype = None

        cls._free_func = cls._go_lib.FreeString

    def render(self, data: Dict[str, Any]) -> str:
        """Renders the template with the given data."""
        if not self._go_lib:
            raise RuntimeError("Go renderer library is not loaded.")

        template_bytes = self.template_content.encode('utf-8')
        json_data_bytes = json.dumps(data).encode('utf-8')

        result_ptr = self._go_lib.RenderTemplate(template_bytes, json_data_bytes)

        try:
            rendered_string = ctypes.string_at(result_ptr).decode('utf-8')
        finally:
            if self._free_func and result_ptr:
                self._free_func(result_ptr)

        if rendered_string.startswith(("JSON_ERROR:", "TEMPLATE_PARSE_ERROR:", "TEMPLATE_EXECUTE_ERROR:")):
            raise ValueError(f"Error from Go renderer: {rendered_string}")

        return rendered_string

    async def render_async(self, data: Dict[str, Any]) -> str:
        """Asynchronously renders the template with the given data."""
        return await asyncio.to_thread(self.render, data)
