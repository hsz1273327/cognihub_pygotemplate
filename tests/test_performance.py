"""Performance tests for cognihub_pygotemplate package."""
import unittest
import time
from unittest.mock import patch, Mock
import ctypes

from cognihub_pygotemplate import GoTemplateEngine


class TestPerformance(unittest.TestCase):
    """Performance tests for GoTemplateEngine."""

    def setUp(self)->None:
        GoTemplateEngine._go_lib = None
        GoTemplateEngine._free_func = None

    def tearDown(self)->None:
        GoTemplateEngine._go_lib = None
        GoTemplateEngine._free_func = None

    @patch('os.path.exists')
    @patch('ctypes.CDLL')
    def test_multiple_render_performance(self, mock_cdll: Mock, mock_exists: Mock)->None:
        """Test performance of multiple renders."""
        mock_exists.return_value = True
        mock_lib = Mock()
        mock_cdll.return_value = mock_lib
        mock_lib.RenderTemplate.return_value = ctypes.c_char_p(b"Fast result")
        
        with patch('ctypes.string_at', return_value=b"Fast result"):
            engine = GoTemplateEngine("{{.name}}")
            
            start_time = time.time()
            for i in range(100):
                result = engine.render({"name": f"test{i}"})
                self.assertEqual(result, "Fast result")
            end_time = time.time()
            
            self.assertLess(end_time - start_time, 1.0)
            self.assertEqual(mock_lib.RenderTemplate.call_count, 100)

    @patch('os.path.exists')
    @patch('ctypes.CDLL')
    def test_large_data_performance(self, mock_cdll: Mock, mock_exists: Mock)->None:
        """Test performance with large data structures."""
        mock_exists.return_value = True
        mock_lib = Mock()
        mock_cdll.return_value = mock_lib
        mock_lib.RenderTemplate.return_value = ctypes.c_char_p(b"Large data rendered")
        
        large_data = {
            "users": [{"name": f"user{i}", "age": i % 100} for i in range(1000)],
            "metadata": {"total": 1000}
        }
        
        with patch('ctypes.string_at', return_value=b"Large data rendered"):
            engine = GoTemplateEngine("{{.metadata.total}} users")
            
            start_time = time.time()
            result = engine.render(large_data)
            end_time = time.time()
            
            self.assertEqual(result, "Large data rendered")
            self.assertLess(end_time - start_time, 0.5)
