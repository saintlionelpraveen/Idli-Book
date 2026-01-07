#!/usr/bin/env python3
"""
Utility script to regenerate GL Entries for existing submitted documents
Run with: bench execute idli_book.idli_book.utils.regenerate_gl_entries
"""

import frappe

def regenerate_gl_entries():
	"""Regenerate GL entries for all submitted invoices and payments"""
	
	frappe.db.begin()
	
	try:
		# 1. Process Sales Invoices
		invoices = frappe.get_all("IB Sales Invoice", 
			filters={"docstatus": 1},
			fields=["name"]
		)
		
		print(f"\n📝 Processing {len(invoices)} Sales Invoices...")
		for inv in invoices:
			try:
				doc = frappe.get_doc("IB Sales Invoice", inv.name)
				doc.make_gl_entries()
				print(f"✅ {inv.name}")
			except Exception as e:
				print(f"❌ {inv.name}: {str(e)}")
		
		# 2. Process Payments
		payments = frappe.get_all("IB Payment",
			filters={"docstatus": 1},
			fields=["name"]
		)
		
		print(f"\n💰 Processing {len(payments)} Payments...")
		for pay in payments:
			try:
				doc = frappe.get_doc("IB Payment", pay.name)
				doc.make_gl_entries()
				print(f"✅ {pay.name}")
			except Exception as e:
				print(f"❌ {pay.name}: {str(e)}")
		
		# 3. Process Purchase Bills
		bills = frappe.get_all("IB Purchase Bill",
			filters={"docstatus": 1},
			fields=["name"]
		)
		
		print(f"\n🧾 Processing {len(bills)} Purchase Bills...")
		for bill in bills:
			try:
				doc = frappe.get_doc("IB Purchase Bill", bill.name)
				doc.make_gl_entries()
				print(f"✅ {bill.name}")
			except Exception as e:
				print(f"❌ {bill.name}: {str(e)}")
		
		frappe.db.commit()
		print("\n✨ GL Regeneration Complete!")
		
	except Exception as e:
		frappe.db.rollback()
		print(f"\n🚨 Error: {str(e)}")
		raise
