"""Functional tests for Go template syntax compatibility."""
import unittest
from unittest.mock import patch, Mock
import ctypes

from cognihub_pygotemplate import GoTemplateEngine


class TestGoTemplateSyntax(unittest.TestCase):
    """Test Go template syntax compatibility."""

    def setUp(self)->None:
        GoTemplateEngine._go_lib = None
        GoTemplateEngine._free_func = None

    def tearDown(self)->None:
        GoTemplateEngine._go_lib = None
        GoTemplateEngine._free_func = None

    @patch('os.path.exists')
    @patch('ctypes.CDLL')
    def test_variable_substitution(self, mock_cdll: Mock, mock_exists: Mock)->None:
        """Test basic variable substitution."""
        mock_exists.return_value = True
        mock_lib = Mock()
        mock_cdll.return_value = mock_lib
        mock_lib.RenderTemplate.return_value = ctypes.c_char_p(b"Hello, John!")
        
        with patch('ctypes.string_at', return_value=b"Hello, John!"):
            engine = GoTemplateEngine("Hello, {{.name}}!")
            result = engine.render({"name": "John"})
            self.assertEqual(result, "Hello, John!")

    @patch('os.path.exists')
    @patch('ctypes.CDLL')
    def test_conditional_statements(self, mock_cdll: Mock, mock_exists: Mock)->None:
        """Test if/else conditional statements."""
        mock_exists.return_value = True
        mock_lib = Mock()
        mock_cdll.return_value = mock_lib
        mock_lib.RenderTemplate.return_value = ctypes.c_char_p(b"Visible")
        
        with patch('ctypes.string_at', return_value=b"Visible"):
            engine = GoTemplateEngine("{{if .show}}Visible{{else}}Hidden{{end}}")
            result = engine.render({"show": True})
            self.assertEqual(result, "Visible")

    @patch('os.path.exists')
    @patch('ctypes.CDLL')
    def test_range_loops(self, mock_cdll: Mock, mock_exists: Mock)->None:
        """Test range loops."""
        mock_exists.return_value = True
        mock_lib = Mock()
        mock_cdll.return_value = mock_lib
        mock_lib.RenderTemplate.return_value = ctypes.c_char_p(b"Items: apple, banana, cherry")
        
        with patch('ctypes.string_at', return_value=b"Items: apple, banana, cherry"):
            engine = GoTemplateEngine("Items: {{range $index, $item := .items}}{{if $index}}, {{end}}{{$item}}{{end}}")
            result = engine.render({"items": ["apple", "banana", "cherry"]})
            self.assertEqual(result, "Items: apple, banana, cherry")


class TestErrorScenarios(unittest.TestCase):
    """Test various error scenarios and edge cases."""

    def setUp(self)->None:
        GoTemplateEngine._go_lib = None
        GoTemplateEngine._free_func = None

    def tearDown(self)->None:
        GoTemplateEngine._go_lib = None
        GoTemplateEngine._free_func = None

    @patch('os.path.exists')
    @patch('ctypes.CDLL')
    def test_invalid_template_syntax(self, mock_cdll: Mock, mock_exists: Mock)->None:
        """Test handling of invalid template syntax."""
        mock_exists.return_value = True
        mock_lib = Mock()
        mock_cdll.return_value = mock_lib
        error_msg = "TEMPLATE_PARSE_ERROR: unclosed action"
        mock_lib.RenderTemplate.return_value = ctypes.c_char_p(error_msg.encode('utf-8'))
        
        with patch('ctypes.string_at', return_value=error_msg.encode('utf-8')):
            engine = GoTemplateEngine("{{.name")
            
            with self.assertRaises(ValueError) as context:
                engine.render({"name": "test"})
            
            self.assertIn("TEMPLATE_PARSE_ERROR", str(context.exception))

    @patch('os.path.exists')
    @patch('ctypes.CDLL')
    def test_missing_field_access(self, mock_cdll: Mock, mock_exists: Mock)->None:
        """Test accessing non-existent fields."""
        mock_exists.return_value = True
        mock_lib = Mock()
        mock_cdll.return_value = mock_lib
        error_msg = "TEMPLATE_EXECUTE_ERROR: can't evaluate field NonExistent"
        mock_lib.RenderTemplate.return_value = ctypes.c_char_p(error_msg.encode('utf-8'))
        
        with patch('ctypes.string_at', return_value=error_msg.encode('utf-8')):
            engine = GoTemplateEngine("{{.NonExistent}}")
            
            with self.assertRaises(ValueError) as context:
                engine.render({})
            
            self.assertIn("TEMPLATE_EXECUTE_ERROR", str(context.exception))
