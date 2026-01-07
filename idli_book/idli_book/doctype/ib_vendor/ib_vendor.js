frappe.ui.form.on('IB Vendor', {
    refresh: function (frm) {
        if (frm.is_new() && !frm.doc.shipping_address) {
            // Auto-fetch Organization Address as Shipping Address (where we receive goods)
            frappe.db.get_single_value('IB Organization', 'organization_name').then(name => {
                frappe.call({
                    method: 'frappe.client.get',
                    args: { doctype: 'IB Organization' },
                    callback: function (r) {
                        if (r.message) {
                            let org = r.message;
                            let address_parts = [
                                org.organization_name,
                                org.street_address_1,
                                org.street_address_2,
                                org.city,
                                org.state_province,
                                org.zip_postal_code,
                                org.country
                            ].filter(Boolean);
                            frm.set_value('shipping_address', address_parts.join('\n'));
                        }
                    }
                });
            });
        }
    },

    gstin: function (frm) {
        if (frm.doc.gstin) {
            let gstin = frm.doc.gstin.toUpperCase();
            let regex = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/;
            if (!regex.test(gstin)) {
                frappe.msgprint('Invalid GSTIN Format');
                return;
            }

            // Auto-set State based on first 2 digits
            let state_code = gstin.substring(0, 2);
            // Search IB State for this code
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'IB State',
                    filters: { 'state_code': state_code },
                    fields: ['name']
                },
                callback: function (r) {
                    if (r.message && r.message.length > 0) {
                        frm.set_value('state', r.message[0].name);
                    }
                }
            });
        }
    },

    validate: function (frm) {
        // Validate Phone
        if (frm.doc.phone) {
            let phone = frm.doc.phone;
            if (phone.length < 10) {
                frappe.msgprint('Phone number should be at least 10 digits');
                frappe.validated = false;
            }
        }

        // Validate Email
        if (frm.doc.email && !validate_email(frm.doc.email)) {
            frappe.msgprint('Invalid Email Address');
            frappe.validated = false;
        }
    }
});
