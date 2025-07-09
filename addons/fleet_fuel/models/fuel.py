from odoo import models, fields, api

FUEL_TYPES = [
    ('diesel', 'Diesel'),
    ('gasoline', 'Gasoline'),
    ('full_hybrid', 'Full Hybrid'),
    ('plug_in_hybrid_diesel', 'Plug-in Hybrid Diesel'),
    ('plug_in_hybrid_gasoline', 'Plug-in Hybrid Gasoline'),
    ('cng', 'CNG'),
    ('lpg', 'LPG'),
    ('hydrogen', 'Hydrogen'),
    ('electric', 'Electric'),
]

class FuelData(models.Model):
    _name = 'fuel.data'
    _description = 'Fuel Data'
    _rec_name = 'fuel_type'
    _order = 'sequence'

    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.fuel_type}"   

    name = fields.Char(string='Name', compute='_compute_name', required=True)
    sequence = fields.Integer('Sequence', default=10)
    fuel_type = fields.Selection(FUEL_TYPES, 'Fuel Type')
    price = fields.Float(string='Price per Gallon', required=True)
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    active = fields.Boolean(string="Active", default=True)
    tax_ids = fields.Many2many(
        'account.tax',
        string='Taxes',
        domain=[('type_tax_use', '=', 'purchase')]
    )
