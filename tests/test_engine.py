"""Unit tests for cognihub_pygotemplate package."""
import unittest
import asyncio
import json
import ctypes
from unittest.mock import patch, Mock

from cognihub_pygotemplate import GoTemplateEngine


class TestGoTemplateEngine(unittest.TestCase):
    """Test cases for GoTemplateEngine class."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        # Reset the class-level library loading state
        GoTemplateEngine._go_lib = None
        GoTemplateEngine._free_func = None

        # Common test data
        self.simple_template = "Hello, {{.Name}}!"
        self.simple_data = {"Name": "World"}
        self.expected_simple_output = "Hello, World!"

        self.complex_template = """
Hello, {{.Name}}!
{{if .Items}}You have {{len .Items}} items:
{{range .Items}}- {{.}}
{{end}}{{else}}You have no items.{{end}}
""".strip()
        self.complex_data = {
            "Name": "John",
            "Items": ["apple", "banana", "cherry"]
        }

    def tearDown(self) -> None:
        """Clean up after each test method."""
        # Reset the class-level library loading state
        GoTemplateEngine._go_lib = None
        GoTemplateEngine._free_func = None

    @patch('os.path.exists')
    @patch('ctypes.CDLL')
    def test_library_loading_success(self, mock_cdll: Mock, mock_exists: Mock) -> None:
        """Test successful library loading."""
        mock_exists.return_value = True
        mock_lib = Mock()
        mock_cdll.return_value = mock_lib

        # Create an instance to trigger library loading
        engine = GoTemplateEngine(self.simple_template)

        # Verify library was loaded
        self.assertIsNotNone(GoTemplateEngine._go_lib)
        mock_cdll.assert_called_once()

        # Verify function signatures are set
        self.assertEqual(mock_lib.RenderTemplate.argtypes, [ctypes.c_char_p, ctypes.c_char_p])
        self.assertEqual(mock_lib.RenderTemplate.restype, ctypes.c_char_p)
        self.assertEqual(mock_lib.FreeString.argtypes, [ctypes.c_char_p])
        self.assertEqual(mock_lib.FreeString.restype, None)

    @patch('os.path.exists')
    def test_library_not_found(self, mock_exists: Mock) -> None:
        """Test library loading failure when file doesn't exist."""
        mock_exists.return_value = False

        with self.assertRaises(FileNotFoundError) as context:
            GoTemplateEngine(self.simple_template)

        self.assertIn("Shared library not found", str(context.exception))
        self.assertIn("Try reinstalling", str(context.exception))

    @patch('platform.system')
    @patch('os.path.exists')
    @patch('ctypes.CDLL')
    def test_library_name_selection_windows(self, mock_cdll: Mock, mock_exists: Mock, mock_system: Mock) -> None:
        """Test correct library name selection on Windows."""
        mock_system.return_value = "Windows"
        mock_exists.return_value = True
        mock_cdll.return_value = Mock()

        GoTemplateEngine(self.simple_template)

        # Check that the correct library name was used
        call_args = mock_cdll.call_args[0][0]
        self.assertTrue(call_args.endswith("renderer.dll"))

    @patch('platform.system')
    @patch('os.path.exists')
    @patch('ctypes.CDLL')
    def test_library_name_selection_darwin(self, mock_cdll: Mock, mock_exists: Mock, mock_system: Mock) -> None:
        """Test correct library name selection on macOS."""
        mock_system.return_value = "Darwin"
        mock_exists.return_value = True
        mock_cdll.return_value = Mock()

        GoTemplateEngine(self.simple_template)

        # Check that the correct library name was used
        call_args = mock_cdll.call_args[0][0]
        self.assertTrue(call_args.endswith("librenderer.dylib"))

    @patch('platform.system')
    @patch('os.path.exists')
    @patch('ctypes.CDLL')
    def test_library_name_selection_linux(self, mock_cdll: Mock, mock_exists: Mock, mock_system: Mock) -> None:
        """Test correct library name selection on Linux."""
        mock_system.return_value = "Linux"
        mock_exists.return_value = True
        mock_cdll.return_value = Mock()

        GoTemplateEngine(self.simple_template)

        # Check that the correct library name was used
        call_args = mock_cdll.call_args[0][0]
        self.assertTrue(call_args.endswith("librenderer.so"))

    def test_singleton_library_loading(self) -> None:
        """Test that library is loaded only once (singleton pattern)."""
        with patch('os.path.exists', return_value=True), \
                patch('ctypes.CDLL') as mock_cdll:

            mock_cdll.return_value = Mock()

            # Create multiple instances
            engine1 = GoTemplateEngine(self.simple_template)
            engine2 = GoTemplateEngine("Another template")

            # Library should be loaded only once
            self.assertEqual(mock_cdll.call_count, 1)
            self.assertIs(engine1._go_lib, engine2._go_lib)

    @patch('os.path.exists')
    @patch('ctypes.CDLL')
    def test_render_success(self, mock_cdll: Mock, mock_exists: Mock) -> None:
        """Test successful template rendering."""
        mock_exists.return_value = True
        mock_lib = Mock()
        mock_cdll.return_value = mock_lib

        # Mock the render function to return a success result
        mock_result_ptr = ctypes.c_char_p(b"Hello, World!")
        mock_lib.RenderTemplate.return_value = mock_result_ptr

        with patch('ctypes.string_at', return_value=b"Hello, World!"):
            engine = GoTemplateEngine(self.simple_template)
            result = engine.render(self.simple_data)

            self.assertEqual(result, "Hello, World!")

            # Verify the correct arguments were passed
            mock_lib.RenderTemplate.assert_called_once()
            args = mock_lib.RenderTemplate.call_args[0]
            self.assertEqual(args[0], self.simple_template.encode('utf-8'))
            self.assertEqual(args[1], json.dumps(self.simple_data).encode('utf-8'))

            # Verify memory cleanup
            mock_lib.FreeString.assert_called_once_with(mock_result_ptr)

    @patch('os.path.exists')
    @patch('ctypes.CDLL')
    def test_render_json_error(self, mock_cdll: Mock, mock_exists: Mock) -> None:
        """Test handling of JSON errors from Go renderer."""
        mock_exists.return_value = True
        mock_lib = Mock()
        mock_cdll.return_value = mock_lib

        mock_result_ptr = ctypes.c_char_p(b"JSON_ERROR: Invalid JSON format")
        mock_lib.RenderTemplate.return_value = mock_result_ptr

        with patch('ctypes.string_at', return_value=b"JSON_ERROR: Invalid JSON format"):
            engine = GoTemplateEngine(self.simple_template)

            with self.assertRaises(ValueError) as context:
                engine.render(self.simple_data)

            self.assertIn("JSON_ERROR: Invalid JSON format", str(context.exception))

    @patch('os.path.exists')
    @patch('ctypes.CDLL')
    def test_render_template_parse_error(self, mock_cdll: Mock, mock_exists: Mock) -> None:
        """Test handling of template parse errors from Go renderer."""
        mock_exists.return_value = True
        mock_lib = Mock()
        mock_cdll.return_value = mock_lib

        mock_result_ptr = ctypes.c_char_p(b"TEMPLATE_PARSE_ERROR: Invalid template syntax")
        mock_lib.RenderTemplate.return_value = mock_result_ptr

        with patch('ctypes.string_at', return_value=b"TEMPLATE_PARSE_ERROR: Invalid template syntax"):
            engine = GoTemplateEngine("{{.Invalid}")

            with self.assertRaises(ValueError) as context:
                engine.render(self.simple_data)

            self.assertIn("TEMPLATE_PARSE_ERROR: Invalid template syntax", str(context.exception))

    @patch('os.path.exists')
    @patch('ctypes.CDLL')
    def test_render_template_execute_error(self, mock_cdll: Mock, mock_exists: Mock) -> None:
        """Test handling of template execution errors from Go renderer."""
        mock_exists.return_value = True
        mock_lib = Mock()
        mock_cdll.return_value = mock_lib

        mock_result_ptr = ctypes.c_char_p(b"TEMPLATE_EXECUTE_ERROR: Field not found")
        mock_lib.RenderTemplate.return_value = mock_result_ptr

        with patch('ctypes.string_at', return_value=b"TEMPLATE_EXECUTE_ERROR: Field not found"):
            engine = GoTemplateEngine("{{.NonExistentField}}")

            with self.assertRaises(ValueError) as context:
                engine.render({})

            self.assertIn("TEMPLATE_EXECUTE_ERROR: Field not found", str(context.exception))

    def test_render_without_loaded_library(self) -> None:
        """Test rendering when library is not loaded."""
        engine = GoTemplateEngine.__new__(GoTemplateEngine)
        engine.template_content = self.simple_template
        engine._go_lib = None

        with self.assertRaises(RuntimeError) as context:
            engine.render(self.simple_data)

        self.assertIn("Go renderer library is not loaded", str(context.exception))

    @patch('os.path.exists')
    @patch('ctypes.CDLL')
    def test_render_with_complex_data(self, mock_cdll: Mock, mock_exists: Mock) -> None:
        """Test rendering with complex nested data structures."""
        mock_exists.return_value = True
        mock_lib = Mock()
        mock_cdll.return_value = mock_lib

        complex_data = {
            "user": {
                "name": "John Doe",
                "age": 30,
                "preferences": {
                    "theme": "dark",
                    "language": "en"
                }
            },
            "items": [
                {"name": "item1", "count": 5},
                {"name": "item2", "count": 3}
            ],
            "flags": [True, False, True]
        }

        expected_output = "Complex template rendered successfully"
        mock_result_ptr = ctypes.c_char_p(expected_output.encode('utf-8'))
        mock_lib.RenderTemplate.return_value = mock_result_ptr

        with patch('ctypes.string_at', return_value=expected_output.encode('utf-8')):
            engine = GoTemplateEngine("{{.user.name}}")
            result = engine.render(complex_data)

            self.assertEqual(result, expected_output)

            # Verify JSON serialization of complex data
            args = mock_lib.RenderTemplate.call_args[0]
            parsed_data = json.loads(args[1].decode('utf-8'))
            self.assertEqual(parsed_data, complex_data)

    @patch('os.path.exists')
    @patch('ctypes.CDLL')
    def test_render_with_unicode_data(self, mock_cdll: Mock, mock_exists: Mock) -> None:
        """Test rendering with Unicode data."""
        mock_exists.return_value = True
        mock_lib = Mock()
        mock_cdll.return_value = mock_lib

        unicode_data = {
            "name": "测试用户",
            "message": "こんにちは世界",
            "emoji": "🚀✨"
        }

        expected_output = "Hello, 测试用户! こんにちは世界 🚀✨"
        mock_result_ptr = ctypes.c_char_p(expected_output.encode('utf-8'))
        mock_lib.RenderTemplate.return_value = mock_result_ptr

        with patch('ctypes.string_at', return_value=expected_output.encode('utf-8')):
            engine = GoTemplateEngine("Hello, {{.name}}! {{.message}} {{.emoji}}")
            result = engine.render(unicode_data)

            self.assertEqual(result, expected_output)

    @patch('os.path.exists')
    @patch('ctypes.CDLL')
    def test_template_content_storage(self, mock_cdll: Mock, mock_exists: Mock) -> None:
        """Test that template content is properly stored."""
        mock_exists.return_value = True
        mock_cdll.return_value = Mock()

        template = "Test template {{.value}}"
        engine = GoTemplateEngine(template)

        self.assertEqual(engine.template_content, template)

    @patch('os.path.exists')
    @patch('ctypes.CDLL')
    def test_render_async(self, mock_cdll: Mock, mock_exists: Mock) -> None:
        """Test asynchronous rendering."""
        mock_exists.return_value = True
        mock_lib = Mock()
        mock_cdll.return_value = mock_lib

        expected_output = "Async Hello, World!"
        mock_result_ptr = ctypes.c_char_p(expected_output.encode('utf-8'))
        mock_lib.RenderTemplate.return_value = mock_result_ptr

        async def run_async_test() -> str:
            with patch('ctypes.string_at', return_value=expected_output.encode('utf-8')):
                engine = GoTemplateEngine(self.simple_template)
                result = await engine.render_async(self.simple_data)
                return result

        # Run the async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_async_test())
            self.assertEqual(result, expected_output)
        finally:
            loop.close()

    @patch('os.path.exists')
    @patch('ctypes.CDLL')
    def test_render_empty_data(self, mock_cdll: Mock, mock_exists: Mock) -> None:
        """Test rendering with empty data."""
        mock_exists.return_value = True
        mock_lib = Mock()
        mock_cdll.return_value = mock_lib

        expected_output = "No data template"
        mock_result_ptr = ctypes.c_char_p(expected_output.encode('utf-8'))
        mock_lib.RenderTemplate.return_value = mock_result_ptr

        with patch('ctypes.string_at', return_value=expected_output.encode('utf-8')):
            engine = GoTemplateEngine("No data template")
            result = engine.render({})

            self.assertEqual(result, expected_output)

    @patch('os.path.exists')
    @patch('ctypes.CDLL')
    def test_memory_cleanup_on_exception(self, mock_cdll: Mock, mock_exists: Mock) -> None:
        """Test that memory is properly cleaned up even when exceptions occur."""
        mock_exists.return_value = True
        mock_lib = Mock()
        mock_cdll.return_value = mock_lib

        mock_result_ptr = ctypes.c_char_p(b"test result")
        mock_lib.RenderTemplate.return_value = mock_result_ptr

        # Simulate an exception during string decoding
        with patch('ctypes.string_at', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'test error')):
            engine = GoTemplateEngine(self.simple_template)

            with self.assertRaises(UnicodeDecodeError):
                engine.render(self.simple_data)

            # Verify memory cleanup was still called
            mock_lib.FreeString.assert_called_once_with(mock_result_ptr)


class TestIntegration(unittest.TestCase):
    """Integration tests that test the overall functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Reset the class-level library loading state
        GoTemplateEngine._go_lib = None
        GoTemplateEngine._free_func = None

    def tearDown(self) -> None:
        """Clean up after each test."""
        GoTemplateEngine._go_lib = None
        GoTemplateEngine._free_func = None

    @patch('os.path.exists')
    @patch('ctypes.CDLL')
    def test_multiple_engines_same_library(self, mock_cdll: Mock, mock_exists: Mock) -> None:
        """Test that multiple engine instances share the same library."""
        mock_exists.return_value = True
        mock_lib = Mock()
        mock_cdll.return_value = mock_lib

        engine1 = GoTemplateEngine("Template 1: {{.value}}")
        engine2 = GoTemplateEngine("Template 2: {{.name}}")

        # Both engines should use the same library instance
        self.assertIs(engine1._go_lib, engine2._go_lib)
        self.assertEqual(mock_cdll.call_count, 1)

    @patch('os.path.exists')
    @patch('ctypes.CDLL')
    def test_sequential_renders(self, mock_cdll: Mock, mock_exists: Mock) -> None:
        """Test multiple sequential renders with the same engine."""
        mock_exists.return_value = True
        mock_lib = Mock()
        mock_cdll.return_value = mock_lib

        # Mock different outputs for different calls
        outputs = [b"Result 1", b"Result 2", b"Result 3"]
        mock_lib.RenderTemplate.side_effect = [ctypes.c_char_p(output) for output in outputs]

        with patch('ctypes.string_at', side_effect=outputs):
            engine = GoTemplateEngine("{{.message}}")

            result1 = engine.render({"message": "test1"})
            result2 = engine.render({"message": "test2"})
            result3 = engine.render({"message": "test3"})

            self.assertEqual(result1, "Result 1")
            self.assertEqual(result2, "Result 2")
            self.assertEqual(result3, "Result 3")

            # Verify all renders were called
            self.assertEqual(mock_lib.RenderTemplate.call_count, 3)
            self.assertEqual(mock_lib.FreeString.call_count, 3)


if __name__ == '__main__':
    # Configure test runner
    unittest.main(verbosity=2, buffer=True)
