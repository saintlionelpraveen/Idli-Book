
import unittest
from unittest.mock import MagicMock
import sys
import os

# Mock google.generativeai
mock_genai = MagicMock()
sys.modules["google.generativeai"] = mock_genai
sys.modules["google.generativeai.types"] = MagicMock()

mock_frappe = MagicMock()
sys.modules["frappe"] = mock_frappe
sys.modules["frappe.utils"] = MagicMock()

sys.path.append(os.getcwd())

if os.path.exists("idli_book"):
    from idli_book.ai.llm_provider import LLMProvider
else:
    raise ImportError("Could not find idli_book package")

class TestGeminiInit(unittest.TestCase):
    def setUp(self):
        self.settings_mock = MagicMock()
        self.settings_mock.enable_chatbot = 1
        self.settings_mock.api_key = "test"
        self.settings_mock.llm_provider = "Google Gemini"
        mock_frappe.get_single.return_value = self.settings_mock
        
        self.provider = LLMProvider()

    def test_tool_format(self):
        """Test that _convert_to_gemini_tools returns a list"""
        functions = [{"name": "test_func", "description": "test"}]
        tools = self.provider._convert_to_gemini_tools(functions)
        
        print(f"\nTools format: {tools}")
        
        self.assertIsInstance(tools, list, "Tools must be a list")
        self.assertEqual(len(tools), 1)
        self.assertIn("function_declarations", tools[0])
        
    def test_init_call(self):
        """Test that GenerativeModel is called with tools"""
        # Mock _build_gemini_contents_and_system
        self.provider._build_gemini_contents_and_system = MagicMock(return_value=([], "sys inst"))
        
        # Mock genai.GenerativeModel
        mock_model_cls = mock_genai.GenerativeModel
        mock_model_instance = MagicMock()
        mock_model_cls.return_value = mock_model_instance
        
        # Call chat
        self.provider._gemini_chat([{"role": "user", "content": "hi"}], functions=[{"name": "f"}])
        
        # Verify call args
        call_args = mock_model_cls.call_args
        print(f"\nInit Args: {call_args}")
        
        _, kwargs = call_args
        self.assertIn("tools", kwargs)
        self.assertIsInstance(kwargs["tools"], list)

if __name__ == '__main__':
    unittest.main()
