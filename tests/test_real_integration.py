"""Integration tests that require the actual compiled Go library."""
import unittest
import os
from cognihub_pygotemplate import GoTemplateEngine


class TestRealIntegration(unittest.TestCase):
    """Integration tests using the real compiled Go library."""

    lib_exists = False
    lib_path = None

    @classmethod
    def setUpClass(cls)->None:
        """Check if the compiled library exists before running tests."""
        # 检查是否存在编译的库文件
        cls.lib_exists = False
        
        lib_names = ["librenderer.dylib", "librenderer.so", "renderer.dll"]
        package_dir = os.path.dirname(os.path.dirname(__file__))
        cognihub_dir = os.path.join(package_dir, "cognihub_pygotemplate")
        
        for lib_name in lib_names:
            lib_path = os.path.join(cognihub_dir, lib_name)
            if os.path.exists(lib_path):
                cls.lib_exists = True
                cls.lib_path = lib_path
                break
        
        if not cls.lib_exists:
            print(f"\n⚠️  WARNING: No compiled Go library found in {cognihub_dir}")
            print("   These integration tests will be skipped.")
            print("   Run 'python setup.py build_py' to compile the Go library first.")

    def setUp(self)->None:
        """Skip tests if library doesn't exist."""
        if not self.lib_exists:
            self.skipTest("Compiled Go library not found - run 'python setup.py build_py' first")
        
        # Reset library state for each test
        GoTemplateEngine._go_lib = None
        GoTemplateEngine._free_func = None

    def tearDown(self)->None:
        """Clean up after each test."""
        # Reset library state
        GoTemplateEngine._go_lib = None
        GoTemplateEngine._free_func = None

    def test_real_library_loading(self)->None:
        """Test that the real library can be loaded."""
        engine = GoTemplateEngine("Hello, {{.Name}}!")
        self.assertIsNotNone(GoTemplateEngine._go_lib)
        self.assertIsNotNone(GoTemplateEngine._free_func)

    def test_real_simple_template_rendering(self)->None:
        """Test real template rendering with simple data."""
        template = "Hello, {{.Name}}!"
        data = {"Name": "World"}
        expected = "Hello, World!"
        
        engine = GoTemplateEngine(template)
        result = engine.render(data)
        self.assertEqual(result, expected)

    def test_real_complex_template_rendering(self)->None:
        """Test real template rendering with complex data."""
        template = """Hello, {{.Name}}!
{{if .Items}}You have {{len .Items}} items:
{{range .Items}}- {{.}}
{{end}}{{else}}You have no items.{{end}}"""
        
        data = {
            "Name": "John",
            "Items": ["apple", "banana", "cherry"]
        }
        
        engine = GoTemplateEngine(template)
        result = engine.render(data)
        
        self.assertIn("Hello, John!", result)
        self.assertIn("You have 3 items:", result)
        self.assertIn("- apple", result)
        self.assertIn("- banana", result)
        self.assertIn("- cherry", result)

    def test_real_empty_data_rendering(self)->None:
        """Test real template rendering with empty data."""
        template = "{{if .Items}}Has items{{else}}No items{{end}}"
        data: dict = {"Items": []}
        expected = "No items"
        
        engine = GoTemplateEngine(template)
        result = engine.render(data)
        self.assertEqual(result, expected)

    def test_real_unicode_data_rendering(self)->None:
        """Test real template rendering with Unicode data."""
        template = "Hello, {{.Name}}! 你好，{{.ChineseName}}！"
        data = {"Name": "World", "ChineseName": "世界"}
        expected = "Hello, World! 你好，世界！"
        
        engine = GoTemplateEngine(template)
        result = engine.render(data)
        self.assertEqual(result, expected)

    def test_real_template_error_handling(self)->None:
        """Test real error handling with invalid template."""
        template = "{{.Name"  # 故意缺少闭合括号
        data = {"Name": "World"}
        
        engine = GoTemplateEngine(template)
        with self.assertRaises(ValueError) as cm:
            engine.render(data)
        
        self.assertIn("TEMPLATE_PARSE_ERROR", str(cm.exception))


if __name__ == '__main__':
    unittest.main()
