// Copyright (c) 2025, Idli Book and contributors
// For license information, please see license.txt

frappe.ui.form.on('IB Item', {
    refresh: function (frm) {
        // Auto-fetch Tax info from HSN (Optional, skipping for now to rely on manual entry or simple logic)
    },
    hsn_sac_code: function (frm) {
        if (frm.doc.hsn_sac_code) {
            frappe.db.get_value('IB HSN SAC', frm.doc.hsn_sac_code, 'tax_rate', (r) => {
                if (r && r.tax_rate) {
                    frm.set_value('tax_percentage', r.tax_rate);
                }
            });
        }
    }
});
