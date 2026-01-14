# Copyright (c) 2026, Praveen and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class IBCountry(Document):
	def validate(self):
		"""Validate country data"""
		# Ensure country code is uppercase
		if self.country_code:
			self.country_code = self.country_code.upper()
		
		# Validate country code format (2 letters)
		if self.country_code and len(self.country_code) != 2:
			frappe.throw("Country Code must be exactly 2 characters (ISO 3166-1 alpha-2)")
