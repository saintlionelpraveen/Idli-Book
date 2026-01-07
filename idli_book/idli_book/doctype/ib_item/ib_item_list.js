frappe.listview_settings['IB Item'] = {
    add_fields: ["stock_quantity", "reorder_level", "track_inventory"],

    get_indicator: function (doc) {
        if (!doc.track_inventory) {
            return [__("Not Tracked"), "grey", "track_inventory,=,0"];
        }

        let stock = doc.stock_quantity || 0;
        let reorder = doc.reorder_level || 0;

        // Low Stock (Red)
        if (reorder > 0 && stock < reorder) {
            return [__("Low Stock"), "red", "stock_quantity,<,reorder_level"];
        }

        // Out of Stock (Orange)
        if (stock <= 0) {
            return [__("Out of Stock"), "orange", "stock_quantity,<=,0"];
        }

        // Stock Good (Green)
        return [__("Stock Good"), "green", "stock_quantity,>,0"];
    }
};
