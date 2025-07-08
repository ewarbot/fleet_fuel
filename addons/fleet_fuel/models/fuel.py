from odoo import models, fields, api

FUEL_TYPES = [
    ('diesel', 'Diesel'),
    ('gasoline', 'Gasolina'),
    ('full_hybrid', 'Híbrido Completo'),
    ('plug_in_hybrid_diesel', 'Híbrido Enchufable Diesel'),
    ('plug_in_hybrid_gasoline', 'Híbrido Enchufable Gasolina'),
    ('cng', 'GNC'),
    ('lpg', 'GLP'),
    ('hydrogen', 'Hidrógeno'),
    ('electric', 'Eléctrico'),
]

class FuelData(models.Model):
    _name = 'fuel.data'
    _description = 'Combustible'
    _rec_name = 'fuel_type'
    _order = 'sequence'

    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.fuel_type}"   

    name = fields.Char(string='Nombre', compute='_compute_name', required=True)
    sequence = fields.Integer('Secuencia', default=10)
    fuel_type = fields.Selection(FUEL_TYPES, 'Tipo de Combustible')
    price = fields.Float(string='Precio por Galón', required=True)
    start_date = fields.Date(string='Fecha de Inicio', required=True)
    end_date = fields.Date(string='Fecha de Fin', required=True)
    active = fields.Boolean(string="Activo", default=True)
    tax_ids = fields.Many2many(
        'account.tax',
        string='Impuestos',
        domain=[('type_tax_use', '=', 'purchase')]
    )
