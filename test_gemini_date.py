
import unittest
from unittest.mock import MagicMock
import sys
import os
from datetime import date

mock_frappe = MagicMock()
sys.modules["frappe"] = mock_frappe
mock_utils = MagicMock()
sys.modules["frappe.utils"] = mock_utils
mock_frappe.utils = mock_utils

# Mock utils.nowdate
mock_utils.nowdate.return_value = "2024-05-20"

sys.path.append(os.getcwd())

if os.path.exists("idli_book"):
    from idli_book.ai.llm_provider import LLMProvider
else:
    raise ImportError("Could not find idli_book package")

class TestGeminiDate(unittest.TestCase):
    def setUp(self):
        self.settings_mock = MagicMock()
        self.settings_mock.enable_chatbot = 1
        self.settings_mock.api_key = "test"
        self.settings_mock.llm_provider = "Google Gemini"
        mock_frappe.get_single.return_value = self.settings_mock
        
        self.provider = LLMProvider()

    def test_date_injection(self):
        """Test that current date is injected into system instruction"""
        messages = [{"role": "user", "content": "Hello"}]
        functions = [{"name": "get_payments", "description": "Get payments"}]
        
        try:
            contents, system_instruction = self.provider._build_gemini_contents_and_system(messages, functions)
            
            print("\n=== SYSTEM INSTRUCTION ===")
            print(system_instruction)
            
            self.assertIn("Current Date: 2024-05-20", system_instruction)
            self.assertIn("appropriate `from_date`", system_instruction)
        except Exception:
            import traceback
            traceback.print_exc()
            raise

if __name__ == '__main__':
    unittest.main()
