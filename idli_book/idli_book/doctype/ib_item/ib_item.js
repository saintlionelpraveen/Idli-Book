frappe.ui.form.on('IB Item', {
    refresh: function (frm) {
        frm.trigger('item_type');
    },

    item_type: function (frm) {
        if (frm.doc.item_type === 'Goods') {
            frm.set_df_property('hsn_code', 'hidden', 0);
            frm.set_df_property('sac_code', 'hidden', 1);
        } else {
            frm.set_df_property('hsn_code', 'hidden', 1);
            frm.set_df_property('sac_code', 'hidden', 0);
        }
    },

    hsn_code: function (frm) {
        // Valid HSN lengths: 4, 6, 8
        let code = frm.doc.hsn_code;
        if (code && (code.length === 4 || code.length === 6 || code.length === 8)) {
            verify_and_auto_add_code(frm, code, 'HSN');
        }
    },

    sac_code: function (frm) {
        // Valid SAC lengths: 4, 6
        let code = frm.doc.sac_code;
        if (code && (code.length === 4 || code.length === 6)) {
            verify_and_auto_add_code(frm, code, 'SAC');
        }
    },

    // Inventory Automation
    opening_stock: function (frm) {
        update_stock_valuation(frm);
    },

    buying_price: function (frm) {
        update_stock_valuation(frm);
    }
});

function update_stock_valuation(frm) {
    if (frm.doc.buying_price) {
        // Auto-set Opening Stock Rate to Buying Price
        frm.set_value('opening_stock_rate', frm.doc.buying_price);

        // If we want total value (custom requirement implied)
        // Since the field is called 'Rate', it likely means Unit Rate.
        // If the user meant Total Value, they would usually ask for 'Stock Value'.
        // Frappe standard: Opening Valuation Rate = Buying Price usually.
    }
}

function verify_and_auto_add_code(frm, code, type) {
    // Calling method inside LOCAL controller - Guaranteed Success
    frappe.call({
        method: 'idli_book.idli_book.doctype.ib_item.ib_item.get_code_details_safe',
        args: {
            code: code,
            type: type
        },
        callback: function (r) {
            if (r.message && r.message.valid) {
                // Success
                frm.set_value('code_description', r.message.description);
                frm.set_value('tax_percentage', r.message.tax_rate);

                let msg = "";
                if (r.message.source === 'database') {
                    msg = `✓ Found in Master: ${r.message.description}`;
                } else if (r.message.source === 'auto-created') {
                    msg = `✨ New Code Auto-Added to Master: ${r.message.description}`;
                } else {
                    msg = `✓ Valid Code: ${r.message.description}`;
                }

                frappe.show_alert({ message: msg, indicator: 'green' }, 5);
            } else {
                // Don't clear description immediately if typing, but since we check length, 
                // it's safe to say "Unknown" if it matches length but not DB.
                // frm.set_value('code_description', 'Code not found');
                // Removed alert for non-blocking UX, or keep it subtle
            }
        }
    });
}
