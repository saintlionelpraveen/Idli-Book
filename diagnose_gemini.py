#!/usr/bin/env python3
"""
Gemini API Diagnostic Script
Run this to check if your API key and region support Gemini models
"""

import frappe

def diagnose_gemini():
    print("\n=== GEMINI API DIAGNOSTIC ===\n")
    
    # 1. Check Settings
    try:
        settings = frappe.get_single("IB Chatbot Settings")
        print(f"✅ Chatbot enabled: {settings.enable_chatbot}")
        print(f"   Provider: {settings.llm_provider}")
        print(f"   Configured model: '{settings.model}'" if settings.model else "   Configured model: (blank - auto-discovery)")
        
        if not settings.api_key:
            print("❌ ERROR: No API key configured!")
            return
        
        print(f"   API key: {'*' * 20}{settings.get_password('api_key')[-4:]}")
    except Exception as e:
        print(f"❌ Failed to load settings: {e}")
        return
    
    # 2. Test API Connection
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.get_password("api_key"))
        print("\n✅ API configured successfully")
    except Exception as e:
        print(f"\n❌ Failed to configure API: {e}")
        return
    
    # 3. List Available Models
    try:
        print("\n📋 Listing available models...")
        available = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available.append(m.name)
                print(f"   ✅ {m.name}")
        
        if not available:
            print("   ❌ No compatible models found!")
            print("   This usually means:")
            print("      - Invalid API key")
            print("      - Region restrictions")
            print("      - Billing not enabled")
        else:
            print(f"\n✅ Found {len(available)} compatible models")
            print(f"   Recommended: {available[0]}")
            
    except Exception as e:
        print(f"\n❌ Failed to list models: {e}")
        print("   Possible causes:")
        print("   - Network connectivity issue")
        print("   - API key invalid or expired")
        print("   - Google AI Studio not accessible from your region")

if __name__ == "__main__":
    frappe.connect()
    diagnose_gemini()
