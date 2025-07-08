from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = 'account.move'
    _description = 'Account Move Fleet Fuel'
    
    fuel_log_ids = fields.One2many('fleet.fuel.log', 'invoice_id', string='Fuel Logs', domain=[('invoice_id', '=', False)])


    @api.onchange('fuel_log_ids')
    def _onchange_fuel_log_ids(self):
        self.invoice_line_ids = [(5, 0, 0)]
        for log in self.fuel_log_ids:
            self.invoice_line_ids = [(0, 0, {
                'name': f'{log.fuel_id.name} - {log.vehicle_id.name}',
                'quantity': log.gallons,
                'price_unit': log.price_per_gallon,
                'tax_ids': [(6, 0, log.tax_ids.ids)],
            })]