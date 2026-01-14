import frappe
import sys

from idli_book.ai.llm_provider import LLMProvider
from idli_book.ai.action_executor import ActionExecutor

def test_manual_query():
    print("\n=== IDLI BOOK CHATBOT DIAGNOSTIC ===")
    
    # 0. Check Available Models (Diagnostic)
    try:
        import google.generativeai as genai
        # We need to get api_key from settings or just skip if not easy
        # Assuming provider will load it
        pass 
    except:
        pass

    # 1. Initialize Provider
    try:
        provider = LLMProvider()
        print("✅ LLM Provider initialized")
        print(f"   Model: {provider.model}")
        print(f"   Provider: {provider.provider}")
    except Exception as e:
        print(f"❌ Initialization Failed: {e}")
        return

    # 2. Get Tools
    functions = ActionExecutor.get_available_functions()
    print(f"✅ Tools Loaded: {len(functions)} tools available")
    print(f"   Tools: {[f['name'] for f in functions]}")

    # 3. Simulate Query
    query = "Show me all unpaid invoices"
    messages = [{"role": "user", "content": query}]
    
    print(f"\n🚀 Sending Query: '{query}'")
    
    try:
        # Check system instruction construction
        _, sys_instruct, _ = provider._build_gemini_contents_and_system(messages, functions)
        if "CRITICAL INSTRUCTION" in sys_instruct:
             print("✅ System Instruction contains Authorization Override")
        else:
             print("⚠️  Warning: System Instruction might be missing authorization")

        # Perform Chat
        response = provider.chat(messages, functions)
        
        print("\n=== RESPONSE ===")
        print(response)
        
        if response.get('function_call'):
            fc = response['function_call']
            print(f"\n✅ SUCCESS! Function Call Triggered:")
            print(f"   Function: {fc.get('name')}")
            print(f"   Arguments: {fc.get('arguments')}")
        else:
            print("\n⚠️  NO FUNCTION CALL TRIGGERED.")
            print("   The model responded with text only. Check if the response is a refusal.")

    except Exception as e:
        print(f"\n❌ Execution Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    frappe.connect()
    test_manual_query()
