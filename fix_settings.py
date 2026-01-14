-- Run this in your bench console to update the chatbot model setting

import frappe

# Update the chatbot settings to use a model that works in your region
settings = frappe.get_single("IB Chatbot Settings")
settings.model = "gemini-2.0-flash-exp"  # or leave blank to use discovery
settings.save()

print("✅ Updated chatbot model setting")
print(f"Current model: {settings.model}")
