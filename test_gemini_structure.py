
import unittest
from unittest.mock import MagicMock
import sys
import os

# Mock frappe module
mock_frappe = MagicMock()
sys.modules["frappe"] = mock_frappe

sys.path.append(os.getcwd())

if os.path.exists("idli_book"):
    from idli_book.ai.llm_provider import LLMProvider
else:
    raise ImportError("Could not find idli_book package")

class TestGeminiStructure(unittest.TestCase):
    def setUp(self):
        self.settings_mock = MagicMock()
        self.settings_mock.enable_chatbot = 1
        self.settings_mock.api_key = "test"
        self.settings_mock.llm_provider = "Google Gemini"
        mock_frappe.get_single.return_value = self.settings_mock
        
        self.provider = LLMProvider()

    def test_prompt_structure(self):
        """Test conversion of messages to Gemini contents and system instruction"""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"}
        ]
        functions = [{"name": "get_weather", "description": "Get weather info"}]
        
        contents, system_instruction = self.provider._build_gemini_contents_and_system(messages, functions)
        
        print("\n=== SYSTEM INSTRUCTION ===")
        print(system_instruction)
        print("\n=== CONTENTS ===")
        print(contents)
        
        # Verify
        self.assertIn("You are a helpful assistant", system_instruction)
        self.assertIn("get_weather", system_instruction)
        self.assertEqual(len(contents), 3)

if __name__ == '__main__':
    unittest.main()
