from odoo import api, fields, models, _

class KSCMixin(models.AbstractModel):
    _name = "ksc.mixin"
    _description = "KSC Mixin"

    def ksc_prepare_invoice_data(self, partner, product_data, inv_data):
        fiscal_position = partner.property_account_position_id
        data = {
            "partner_id": partner.id,
            "move_type": inv_data.get("move_type", "out_invoice"),
            "ref": self.name,
            "invoice_origin": self.name,
            "currency_id": self.env.user.company_id.currency_id.id,
            "invoice_line_ids": self.ksc_get_invoice_lines(
                product_data, partner, inv_data, fiscal_position
            ),
            "fiscal_position_id": fiscal_position.id if fiscal_position else False,
        }
        return data

    @api.model
    def ksc_create_invoice(self, partner, product_data=[], inv_data={}):
        inv_data = self.ksc_prepare_invoice_data(partner, product_data, inv_data)
        invoice = self.env["account.move"].create(inv_data)
        
        # Ensure the invoice is validated and posted if necessary
        if inv_data.get('move_type') == 'out_invoice':
            invoice.action_post()
        
        return invoice

    @api.model
    def ksc_get_invoice_lines(self, product_data, partner, inv_data, fiscal_position_id):
        lines = []
        for data in product_data:
            product = data.get("product_id")
            if product:
                ksc_pricelist_id = self.env.context.get("ksc_pricelist_id")
                if not data.get("price_unit") and (
                    partner.property_product_pricelist or ksc_pricelist_id
                ):
                    pricelist_id = (
                        ksc_pricelist_id or partner.property_product_pricelist.id
                    )
                    price = product.with_context(pricelist=pricelist_id).price
                else:
                    price = data.get("price_unit", product.list_price)
                
                tax_ids = product.taxes_id
                if inv_data.get("move_type", "out_invoice") == "in_invoice":
                    tax_ids = product.supplier_taxes_id
                
                if tax_ids and fiscal_position_id:
                    tax_ids = fiscal_position_id.map_tax(
                        tax_ids._origin, partner=partner
                    )
                tax_ids = [(6, 0, tax_ids.ids)] if tax_ids else []

                lines.append(
                    (
                        0,
                        0,
                        {
                            "name": data.get("name", product.name),
                            "product_id": product.id,
                            "price_unit": price,
                            "quantity": data.get("quantity", 1.0),
                            "discount": data.get("discount", 0.0),
                            "product_uom_id": data.get("product_uom_id", product.uom_id.id),
                            "tax_ids": tax_ids,
                            "account_id": product.property_account_income_id.id or product.categ_id.property_account_income_categ_id.id,
                        },
                    )
                )
            else:
                lines.append(
                    (
                        0,
                        0,
                        {
                            "name": data.get("name"),
                            "display_type": "line_section",
                        },
                    )
                )

        return lines

    def ksc_action_view_invoice(self, invoices):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_move_out_invoice_type"
        )
        if len(invoices) > 1:
            action["domain"] = [("id", "in", invoices.ids)]
        elif len(invoices) == 1:
            action["views"] = [(self.env.ref("account.view_move_form").id, "form")]
            action["res_id"] = invoices.id
        elif self.env.context.get("ksc_open_blank_list"):
            # Allow to open invoices
            action["domain"] = [("id", "in", invoices.ids)]
        else:
            action = {"type": "ir.actions.act_window_close"}
        context = {
            "default_move_type": "out_invoice",
        }
        action["context"] = context
        return action

    @api.model
    def assign_given_lots(self, move, lot_id, lot_qty):
        MoveLine = self.env["stock.move.line"]
        move_line_id = MoveLine.search(
            [("move_id", "=", move.id), ("lot_id", "=", False)], limit=1
        )
        if move_line_id:
            move_line_id.lot_id = lot_id
            move_line_id.quantity_done = lot_qty

    def consume_material(self, source_location_id, dest_location_id, product_data):
        product = product_data["product"]
        move = self.env["stock.move"].create(
            {
                "name": product.name,
                "product_id": product.id,
                "product_uom": product.uom_id.id,
                "product_uom_qty": product_data.get("qty", 1.0),
                "date": product_data.get("date", fields.Datetime.now()),
                "location_id": source_location_id,
                "location_dest_id": dest_location_id,
                "state": "draft",
                "origin": self.name,
                "quantity_done": product_data.get("qty", 1.0),
            }
        )
        move._action_confirm()
        move._action_assign()
        if product_data.get("lot_id", False):
            lot_id = product_data.get("lot_id")
            lot_qty = product_data.get("qty", 1.0)
            self.assign_given_lots(move, lot_id, lot_qty)
        if move.state == "assigned":
            move._action_done()
        return move
