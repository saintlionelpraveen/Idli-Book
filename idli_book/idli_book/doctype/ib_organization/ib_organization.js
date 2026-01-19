// Copyright (c) 2025, Idli Book and contributors
// For license information, please see license.txt

frappe.ui.form.on('IB Organization', {
    refresh: function (frm) {
        if (!frm.doc.__islocal) {
            // Button to reset all account links and recreate them
            frm.add_custom_button('🔄 Recreate Accounts', function () {
                frappe.confirm(
                    'This will clear all account links and recreate them based on Organization name. Continue?',
                    () => {
                        frappe.call({
                            method: 'idli_book.idli_book.doctype.ib_organization.ib_organization.reset_account_defaults',
                            callback: function (r) {
                                if (r.message) {
                                    frappe.msgprint(r.message);
                                }
                                frm.reload_doc();
                            }
                        });
                    }
                );
            }, 'Actions');

            // Button to force create all org accounts now
            frm.add_custom_button('📋 Setup Default Accounts', function () {
                // Just save the doc - before_save will create accounts if missing
                frm.save().then(() => {
                    frappe.msgprint('Default accounts have been set up.');
                });
            }, 'Actions');
        }
    }
});
