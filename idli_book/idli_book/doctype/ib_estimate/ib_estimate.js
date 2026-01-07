frappe.ui.form.on('IB Estimate', {
    setup: function (frm) {
        // Map fields: Item Field -> Target Field
        frm.add_fetch('item_code', 'item_name', 'item_name');
        frm.add_fetch('item_code', 'sales_description', 'description');
        frm.add_fetch('item_code', 'unit', 'uom');
        frm.add_fetch('item_code', 'selling_price', 'rate');
        frm.add_fetch('item_code', 'tax_percentage', 'tax_rate');
    },

    refresh: function (frm) {
        // Create Sales Order Button
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Create Sales Order'), function () {
                frappe.call({
                    method: 'idli_book.idli_book.doctype.ib_estimate.ib_estimate.make_sales_order',
                    args: { source_name: frm.doc.name },
                    callback: function (r) {
                        if (r.message) {
                            frappe.model.sync(r.message);
                            frappe.set_route('Form', 'IB Sales Order', r.message.name);
                        }
                    }
                });
            }, __('Create'));
        }
    },

    // Header Triggers
    discount_type: function (frm) { calculate_totals(frm); },
    discount_percentage: function (frm) { calculate_totals(frm); },
    discount_amount: function (frm) { calculate_totals(frm); }
});

frappe.ui.form.on('IB Invoice Item', {
    item_code: function (frm, cdt, cdn) {
        // Set default quantity 1 to enable row calc
        let row = locals[cdt][cdn];
        if (!row.quantity) frappe.model.set_value(cdt, cdn, 'quantity', 1);
    },

    // Recalculate on ANY change
    quantity: function (frm, cdt, cdn) { calculate_row(frm, cdt, cdn); },
    rate: function (frm, cdt, cdn) { calculate_row(frm, cdt, cdn); },
    tax_rate: function (frm, cdt, cdn) { calculate_row(frm, cdt, cdn); },

    discount_type: function (frm, cdt, cdn) { calculate_row(frm, cdt, cdn); },
    discount_percentage: function (frm, cdt, cdn) { calculate_row(frm, cdt, cdn); },
    discount_amount: function (frm, cdt, cdn) {
        // Reverse calc percentage
        let row = locals[cdt][cdn];
        let base = (row.quantity || 0) * (row.rate || 0);
        if (base > 0) {
            frappe.model.set_value(cdt, cdn, 'discount_percentage', (row.discount_amount / base) * 100);
        }
        calculate_row(frm, cdt, cdn, true);
    }
});

var calculate_row = function (frm, cdt, cdn, skip_disc_amt) {
    let row = locals[cdt][cdn];
    let qty = row.quantity || 0;
    let rate = row.rate || 0;
    let base_amount = qty * rate;

    // 1. Calculate Discount
    let discount_amt = 0;
    if (row.discount_type === 'Percentage') {
        discount_amt = (base_amount * (row.discount_percentage || 0)) / 100;
        if (!skip_disc_amt) {
            frappe.model.set_value(cdt, cdn, 'discount_amount', discount_amt);
        }
    } else {
        discount_amt = row.discount_amount || 0;
        if (base_amount > 0 && !skip_disc_amt) {
            frappe.model.set_value(cdt, cdn, 'discount_percentage', (discount_amt / base_amount) * 100);
        }
    }

    // 2. Net Amount
    let net_amount = base_amount - discount_amt;
    frappe.model.set_value(cdt, cdn, 'amount', net_amount);

    // 3. Tax
    let tax_rate = row.tax_rate || 0;
    let tax_amt = (net_amount * tax_rate) / 100;
    frappe.model.set_value(cdt, cdn, 'tax_amount', tax_amt);

    // 4. Update Header Totals
    calculate_totals(frm);
};

var calculate_totals = function (frm) {
    let subtotal = 0;
    let total_tax = 0;

    // Sum rows
    (frm.doc.items || []).forEach(item => {
        subtotal += item.amount || 0;
        total_tax += item.tax_amount || 0;
    });

    frm.set_value('subtotal', subtotal);
    frm.set_value('tax_amount', total_tax);

    // Global Discount
    let global_disc = 0;
    if (frm.doc.discount_type === 'Percentage') {
        global_disc = (subtotal * (frm.doc.discount_percentage || 0)) / 100;
        frm.set_value('discount_amount', global_disc);
    } else {
        global_disc = frm.doc.discount_amount || 0;
        if (subtotal > 0) {
            frm.set_value('discount_percentage', (global_disc / subtotal) * 100);
        }
    }

    let grand_total = subtotal - global_disc + total_tax;
    frm.set_value('grand_total', grand_total);

    // Force Visual Refresh
    frm.refresh_field('subtotal');
    frm.refresh_field('tax_amount');
    frm.refresh_field('discount_amount');
    frm.refresh_field('grand_total');
    frm.refresh_field('items');
};
