"""
Database of HSN and SAC codes with tax rates and descriptions.
Acts as a local 'Free API' data source.
"""

HSN_DATA = {
    # Electronics
    '8471': {'description': 'Automatic data processing machines (Computers, Laptops)', 'tax_rate': 18},
    '847130': {'description': 'Portable automatic data processing machines (Laptops)', 'tax_rate': 18},
    '8517': {'description': 'Telephone sets, including smartphones', 'tax_rate': 18},
    '8528': {'description': 'Monitors and Projectors', 'tax_rate': 18},
    '8443': {'description': 'Printers and copying machines', 'tax_rate': 18},
    
    # Food (Essentials vs Luxuries)
    '0201': {'description': 'Meat of bovine animals, fresh or chilled', 'tax_rate': 0},
    '0401': {'description': 'Milk and cream, not concentrated', 'tax_rate': 0},
    '1006': {'description': 'Rice', 'tax_rate': 5},
    '2106': {'description': 'Food preparations not elsewhere specified', 'tax_rate': 18},
    
    # Vehicles
    '8703': {'description': 'Motor cars and other motor vehicles', 'tax_rate': 28},
    '8711': {'description': 'Motorcycles (including mopeds)', 'tax_rate': 28},
    
    # Materials
    '2523': {'description': 'Portland cement, aluminous cement', 'tax_rate': 28},
    '7214': {'description': 'Other bars and rods of iron or non-alloy steel', 'tax_rate': 18},
}

SAC_DATA = {
    # IT Services
    '998311': {'description': 'Management consulting and management services', 'tax_rate': 18},
    '998313': {'description': 'Information technology (IT) consulting and support', 'tax_rate': 18},
    '998314': {'description': 'IT design and development services', 'tax_rate': 18},
    
    # Professional Services
    '998211': {'description': 'Legal services', 'tax_rate': 18},
    '998222': {'description': 'Accounting, auditing and bookkeeping', 'tax_rate': 18},
    
    # Construction
    '995411': {'description': 'Construction services of residential buildings', 'tax_rate': 18},
    
    # Transport
    '996411': {'description': 'Local land transport services of passengers', 'tax_rate': 5},
    '996421': {'description': 'Long-distance transport services of passengers', 'tax_rate': 5},
}

def get_hsn_details(code):
    # Try exact match
    if code in HSN_DATA:
        return HSN_DATA[code]
    # Try 4-digit prefix
    if len(code) > 4 and code[:4] in HSN_DATA:
        return HSN_DATA[code[:4]]
    return None

def get_sac_details(code):
    # Try exact match
    if code in SAC_DATA:
        return SAC_DATA[code]
    # Try 4-digit prefix
    if len(code) > 4 and code[:4] in SAC_DATA:
        return SAC_DATA[code[:4]]
    return None
