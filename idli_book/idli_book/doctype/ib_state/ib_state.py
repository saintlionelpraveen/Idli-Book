import frappe
from frappe.model.document import Document

class IBState(Document):
	def validate(self):
		"""Auto-fill state code and UT flag based on state name"""
		self.set_state_code()
	
	def set_state_code(self):
		"""Set GST state code based on state name"""
		state_codes = {
			# States
			"Andhra Pradesh": {"code": "37", "is_ut": 0},
			"Arunachal Pradesh": {"code": "12", "is_ut": 0},
			"Assam": {"code": "18", "is_ut": 0},
			"Bihar": {"code": "10", "is_ut": 0},
			"Chhattisgarh": {"code": "22", "is_ut": 0},
			"Goa": {"code": "30", "is_ut": 0},
			"Gujarat": {"code": "24", "is_ut": 0},
			"Haryana": {"code": "06", "is_ut": 0},
			"Himachal Pradesh": {"code": "02", "is_ut": 0},
			"Jharkhand": {"code": "20", "is_ut": 0},
			"Karnataka": {"code": "29", "is_ut": 0},
			"Kerala": {"code": "32", "is_ut": 0},
			"Madhya Pradesh": {"code": "23", "is_ut": 0},
			"Maharashtra": {"code": "27", "is_ut": 0},
			"Manipur": {"code": "14", "is_ut": 0},
			"Meghalaya": {"code": "17", "is_ut": 0},
			"Mizoram": {"code": "15", "is_ut": 0},
			"Nagaland": {"code": "13", "is_ut": 0},
			"Odisha": {"code": "21", "is_ut": 0},
			"Punjab": {"code": "03", "is_ut": 0},
			"Rajasthan": {"code": "08", "is_ut": 0},
			"Sikkim": {"code": "11", "is_ut": 0},
			"Tamil Nadu": {"code": "33", "is_ut": 0},
			"Telangana": {"code": "36", "is_ut": 0},
			"Tripura": {"code": "16", "is_ut": 0},
			"Uttar Pradesh": {"code": "09", "is_ut": 0},
			"Uttarakhand": {"code": "05", "is_ut": 0},
			"West Bengal": {"code": "19", "is_ut": 0},
			
			# Union Territories
			"Andaman and Nicobar Islands": {"code": "35", "is_ut": 1},
			"Chandigarh": {"code": "04", "is_ut": 1},
			"Dadra and Nagar Haveli and Daman and Diu": {"code": "26", "is_ut": 1},
			"Delhi": {"code": "07", "is_ut": 1},
			"Jammu and Kashmir": {"code": "01", "is_ut": 1},
			"Ladakh": {"code": "38", "is_ut": 1},
			"Lakshadweep": {"code": "31", "is_ut": 1},
			"Puducherry": {"code": "34", "is_ut": 1}
		}
		
		if self.state_name in state_codes:
			self.state_code = state_codes[self.state_name]["code"]
			self.is_union_territory = state_codes[self.state_name]["is_ut"]
