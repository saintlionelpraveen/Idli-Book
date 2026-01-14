# Copyright (c) 2026, Praveen and contributors
# For license information, please see license.txt

import frappe

def execute():
	"""Create default currencies, UOMs, and countries for Idli Book"""
	
	# Create default currencies
	create_default_currencies()
	
	# Create default UOMs
	create_default_uoms()
	
	# Create default countries
	create_default_countries()
	
	frappe.db.commit()

def create_default_currencies():
	"""Insert comprehensive global currency data"""
	currencies = [
		# Major Currencies
		{"currency_code": "INR", "currency_name": "Indian Rupee", "symbol": "Rs", "fraction": "Paisa", "number_format": "#,##,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "USD", "currency_name": "US Dollar", "symbol": "$", "fraction": "Cent", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "EUR", "currency_name": "Euro", "symbol": "EUR", "fraction": "Cent", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "GBP", "currency_name": "British Pound", "symbol": "GBP", "fraction": "Penny", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "JPY", "currency_name": "Japanese Yen", "symbol": "JPY", "fraction": "Sen", "number_format": "#,###", "smallest_currency_fraction_value": 1.0},
		{"currency_code": "CHF", "currency_name": "Swiss Franc", "symbol": "CHF", "fraction": "Rappen", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		
		# Asia Pacific
		{"currency_code": "CNY", "currency_name": "Chinese Yuan", "symbol": "CNY", "fraction": "Fen", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "AUD", "currency_name": "Australian Dollar", "symbol": "AUD", "fraction": "Cent", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "NZD", "currency_name": "New Zealand Dollar", "symbol": "NZD", "fraction": "Cent", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "SGD", "currency_name": "Singapore Dollar", "symbol": "SGD", "fraction": "Cent", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "HKD", "currency_name": "Hong Kong Dollar", "symbol": "HKD", "fraction": "Cent", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "KRW", "currency_name": "South Korean Won", "symbol": "KRW", "fraction": "Jeon", "number_format": "#,###", "smallest_currency_fraction_value": 1.0},
		{"currency_code": "THB", "currency_name": "Thai Baht", "symbol": "THB", "fraction": "Satang", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "MYR", "currency_name": "Malaysian Ringgit", "symbol": "MYR", "fraction": "Sen", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "IDR", "currency_name": "Indonesian Rupiah", "symbol": "IDR", "fraction": "Sen", "number_format": "#,###", "smallest_currency_fraction_value": 1.0},
		{"currency_code": "PHP", "currency_name": "Philippine Peso", "symbol": "PHP", "fraction": "Centavo", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "VND", "currency_name": "Vietnamese Dong", "symbol": "VND", "fraction": "Xu", "number_format": "#,###", "smallest_currency_fraction_value": 1.0},
		{"currency_code": "PKR", "currency_name": "Pakistani Rupee", "symbol": "PKR", "fraction": "Paisa", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "BDT", "currency_name": "Bangladeshi Taka", "symbol": "BDT", "fraction": "Paisa", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "LKR", "currency_name": "Sri Lankan Rupee", "symbol": "LKR", "fraction": "Cent", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		
		# Middle East
		{"currency_code": "AED", "currency_name": "UAE Dirham", "symbol": "AED", "fraction": "Fils", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "SAR", "currency_name": "Saudi Riyal", "symbol": "SAR", "fraction": "Halala", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "QAR", "currency_name": "Qatari Riyal", "symbol": "QAR", "fraction": "Dirham", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "KWD", "currency_name": "Kuwaiti Dinar", "symbol": "KWD", "fraction": "Fils", "number_format": "#,###.###", "smallest_currency_fraction_value": 0.001},
		{"currency_code": "OMR", "currency_name": "Omani Rial", "symbol": "OMR", "fraction": "Baisa", "number_format": "#,###.###", "smallest_currency_fraction_value": 0.001},
		{"currency_code": "BHD", "currency_name": "Bahraini Dinar", "symbol": "BHD", "fraction": "Fils", "number_format": "#,###.###", "smallest_currency_fraction_value": 0.001},
		{"currency_code": "ILS", "currency_name": "Israeli Shekel", "symbol": "ILS", "fraction": "Agora", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		
		# Americas
		{"currency_code": "CAD", "currency_name": "Canadian Dollar", "symbol": "CAD", "fraction": "Cent", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "MXN", "currency_name": "Mexican Peso", "symbol": "MXN", "fraction": "Centavo", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "BRL", "currency_name": "Brazilian Real", "symbol": "BRL", "fraction": "Centavo", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "ARS", "currency_name": "Argentine Peso", "symbol": "ARS", "fraction": "Centavo", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "CLP", "currency_name": "Chilean Peso", "symbol": "CLP", "fraction": "Centavo", "number_format": "#,###", "smallest_currency_fraction_value": 1.0},
		
		# Europe
		{"currency_code": "SEK", "currency_name": "Swedish Krona", "symbol": "SEK", "fraction": "Ore", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "NOK", "currency_name": "Norwegian Krone", "symbol": "NOK", "fraction": "Ore", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "DKK", "currency_name": "Danish Krone", "symbol": "DKK", "fraction": "Ore", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "PLN", "currency_name": "Polish Zloty", "symbol": "PLN", "fraction": "Grosz", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "CZK", "currency_name": "Czech Koruna", "symbol": "CZK", "fraction": "Haler", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "HUF", "currency_name": "Hungarian Forint", "symbol": "HUF", "fraction": "Filler", "number_format": "#,###", "smallest_currency_fraction_value": 1.0},
		{"currency_code": "RUB", "currency_name": "Russian Ruble", "symbol": "RUB", "fraction": "Kopek", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "TRY", "currency_name": "Turkish Lira", "symbol": "TRY", "fraction": "Kurus", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		
		# Africa
		{"currency_code": "ZAR", "currency_name": "South African Rand", "symbol": "ZAR", "fraction": "Cent", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "EGP", "currency_name": "Egyptian Pound", "symbol": "EGP", "fraction": "Piastre", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "NGN", "currency_name": "Nigerian Naira", "symbol": "NGN", "fraction": "Kobo", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		{"currency_code": "KES", "currency_name": "Kenyan Shilling", "symbol": "KES", "fraction": "Cent", "number_format": "#,###.##", "smallest_currency_fraction_value": 0.01},
		
		# Cryptocurrencies
		{"currency_code": "BTC", "currency_name": "Bitcoin", "symbol": "BTC", "fraction": "Satoshi", "number_format": "#,###.########", "smallest_currency_fraction_value": 0.00000001},
		{"currency_code": "ETH", "currency_name": "Ethereum", "symbol": "ETH", "fraction": "Wei", "number_format": "#,###.######", "smallest_currency_fraction_value": 0.000001},
	]
	
	for currency in currencies:
		if not frappe.db.exists("IB Currency", currency["currency_code"]):
			doc = frappe.new_doc("IB Currency")
			doc.update(currency)
			doc.insert(ignore_permissions=True)
			print(f"Created currency: {currency['currency_code']}")
		else:
			print(f"Currency already exists: {currency['currency_code']}")

def create_default_uoms():
	"""Insert standard UOM data"""
	uoms = [
		{"uom_name": "Nos", "uom_abbreviation": "Nos", "uom_type": "Quantity"},
		{"uom_name": "Numbers", "uom_abbreviation": "Nos", "uom_type": "Quantity"},
		{"uom_name": "Pieces", "uom_abbreviation": "Pcs", "uom_type": "Quantity"},
		{"uom_name": "Box", "uom_abbreviation": "Box", "uom_type": "Quantity"},
		{"uom_name": "Dozen", "uom_abbreviation": "Dzn", "uom_type": "Quantity"},
		{"uom_name": "Kilogram", "uom_abbreviation": "Kg", "uom_type": "Weight"},
		{"uom_name": "Gram", "uom_abbreviation": "g", "uom_type": "Weight"},
		{"uom_name": "Litre", "uom_abbreviation": "Ltr", "uom_type": "Volume"},
		{"uom_name": "Millilitre", "uom_abbreviation": "ml", "uom_type": "Volume"},
		{"uom_name": "Meter", "uom_abbreviation": "m", "uom_type": "Length"},
		{"uom_name": "Centimeter", "uom_abbreviation": "cm", "uom_type": "Length"},
		{"uom_name": "Square Meter", "uom_abbreviation": "sqm", "uom_type": "Area"},
		{"uom_name": "Square Feet", "uom_abbreviation": "sqft", "uom_type": "Area"},
		{"uom_name": "Hour", "uom_abbreviation": "Hr", "uom_type": "Time"},
		{"uom_name": "Day", "uom_abbreviation": "Day", "uom_type": "Time"},
		{"uom_name": "Unit", "uom_abbreviation": "Unit", "uom_type": "Other"},
		{"uom_name": "Set", "uom_abbreviation": "Set", "uom_type": "Other"}
	]
	
	for uom in uoms:
		if not frappe.db.exists("IB UOM", uom["uom_name"]):
			doc = frappe.new_doc("IB UOM")
			doc.update(uom)
			doc.insert(ignore_permissions=True)
			print(f"Created UOM: {uom['uom_name']}")

def create_default_countries():
	"""Insert comprehensive global country data"""
	countries = [
		{"country_name": "India", "country_code": "IN"},
		{"country_name": "United States", "country_code": "US"},
		{"country_name": "United Kingdom", "country_code": "GB"},
		{"country_name": "Canada", "country_code": "CA"},
		{"country_name": "Australia", "country_code": "AU"},
		{"country_name": "Germany", "country_code": "DE"},
		{"country_name": "France", "country_code": "FR"},
		{"country_name": "Italy", "country_code": "IT"},
		{"country_name": "Spain", "country_code": "ES"},
		{"country_name": "Japan", "country_code": "JP"},
		{"country_name": "China", "country_code": "CN"},
		{"country_name": "South Korea", "country_code": "KR"},
		{"country_name": "Singapore", "country_code": "SG"},
		{"country_name": "Malaysia", "country_code": "MY"},
		{"country_name": "Thailand", "country_code": "TH"},
		{"country_name": "Indonesia", "country_code": "ID"},
		{"country_name": "Philippines", "country_code": "PH"},
		{"country_name": "Vietnam", "country_code": "VN"},
		{"country_name": "Hong Kong", "country_code": "HK"},
		{"country_name": "Taiwan", "country_code": "TW"},
		{"country_name": "New Zealand", "country_code": "NZ"},
		{"country_name": "United Arab Emirates", "country_code": "AE"},
		{"country_name": "Saudi Arabia", "country_code": "SA"},
		{"country_name": "Qatar", "country_code": "QA"},
		{"country_name": "Kuwait", "country_code": "KW"},
		{"country_name": "Oman", "country_code": "OM"},
		{"country_name": "Bahrain", "country_code": "BH"},
		{"country_name": "Israel", "country_code": "IL"},
		{"country_name": "Turkey", "country_code": "TR"},
		{"country_name": "Egypt", "country_code": "EG"},
		{"country_name": "South Africa", "country_code": "ZA"},
		{"country_name": "Nigeria", "country_code": "NG"},
		{"country_name": "Kenya", "country_code": "KE"},
		{"country_name": "Brazil", "country_code": "BR"},
		{"country_name": "Mexico", "country_code": "MX"},
		{"country_name": "Argentina", "country_code": "AR"},
		{"country_name": "Chile", "country_code": "CL"},
		{"country_name": "Colombia", "country_code": "CO"},
		{"country_name": "Russia", "country_code": "RU"},
		{"country_name": "Poland", "country_code": "PL"},
		{"country_name": "Netherlands", "country_code": "NL"},
		{"country_name": "Belgium", "country_code": "BE"},
		{"country_name": "Switzerland", "country_code": "CH"},
		{"country_name": "Sweden", "country_code": "SE"},
		{"country_name": "Norway", "country_code": "NO"},
		{"country_name": "Denmark", "country_code": "DK"},
		{"country_name": "Finland", "country_code": "FI"},
		{"country_name": "Ireland", "country_code": "IE"},
		{"country_name": "Portugal", "country_code": "PT"},
		{"country_name": "Greece", "country_code": "GR"},
		{"country_name": "Austria", "country_code": "AT"},
		{"country_name": "Czech Republic", "country_code": "CZ"},
		{"country_name": "Hungary", "country_code": "HU"},
		{"country_name": "Romania", "country_code": "RO"},
		{"country_name": "Pakistan", "country_code": "PK"},
		{"country_name": "Bangladesh", "country_code": "BD"},
		{"country_name": "Sri Lanka", "country_code": "LK"},
		{"country_name": "Nepal", "country_code": "NP"},
		{"country_name": "Afghanistan", "country_code": "AF"},
		{"country_name": "Myanmar", "country_code": "MM"},
	]
	
	for country in countries:
		if not frappe.db.exists("IB Country", country["country_name"]):
			doc = frappe.new_doc("IB Country")
			doc.update(country)
			doc.insert(ignore_permissions=True)
			print(f"Created country: {country['country_name']}")
		else:
			print(f"Country already exists: {country['country_name']}")
