from odoo import models, fields, api
from odoo.exceptions import ValidationError

class FleetFuelLog(models.Model):
    _name = 'fleet.fuel.log'
    _description = 'Registro de Combustible'
    _order = 'date desc'

    name = fields.Char(
        string='Referencia',
        readonly=True,
        copy=False,
        default=lambda self: self.env['ir.sequence'].next_by_code('fleet.fuel.log')
    )
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True)
    driver_id = fields.Many2one('res.partner', string='Driver', readonly=True)
    fuel_id = fields.Many2one('fuel.data', string='Fuel Data', required=True)
    plate_number = fields.Char(string='Plate Number', readonly=True)

    odometer = fields.Float(string='Previous Odometer', readonly=True)
    odometer_current = fields.Float(string='Current Odometer', required=True)
    kilometers = fields.Float(
        string='Kilometers Driven',
        compute='_compute_kilometers',
        store=True
    )

    date = fields.Date(
        string='Date',
        default=fields.Date.context_today,
        required=True
    )

    gallons = fields.Float(string='Gallons', required=True)
    price_per_gallon = fields.Float(
        string='Price per Gallon',
        related='fuel_id.price',
        readonly=True,
        store=True
    )
    fuel_cost = fields.Monetary(
        string='Fuel Cost',
        compute='_compute_fuel_cost',
        store=True,
        currency_field='company_currency_id'
    )
    cost_per_km = fields.Monetary(
        string='Cost per Km',
        compute='_compute_cost_per_km',
        store=True,
        currency_field='company_currency_id'
    )

    invoice_id = fields.Many2one('account.move', string='Fuel Invoice')
    company_currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        readonly=True
    )
    tax_ids = fields.Many2many(
        'account.tax',
        related='fuel_id.tax_ids'
    )
    notes = fields.Text(string='Notes')

    @api.onchange('vehicle_id')
    def _onchange_vehicle_id(self):
        self.odometer = self.vehicle_id.odometer if self.vehicle_id else 0.0
        self.driver_id = self.vehicle_id.driver_id.id if self.vehicle_id else None
        self.plate_number = self.vehicle_id.plate_number if self.vehicle_id else None
        if self.vehicle_id:
            fuel_data = self.env['fuel.data'].search([('fuel_type', '=', self.vehicle_id.fuel_type)], limit=1)
            self.fuel_id = fuel_data.id if fuel_data else None
        else:
            self.fuel_id = False

    @api.depends('odometer', 'odometer_current')
    def _compute_kilometers(self):
        for rec in self:
            rec.kilometers = max(rec.odometer_current - rec.odometer, 0.0)

    @api.depends('gallons', 'price_per_gallon')
    def _compute_fuel_cost(self):
        for rec in self:
            rec.fuel_cost = rec.gallons * rec.price_per_gallon

    @api.depends('fuel_cost', 'kilometers')
    def _compute_cost_per_km(self):
        for rec in self:
            rec.cost_per_km = rec.fuel_cost / rec.kilometers if rec.kilometers > 0 else 0.0

    @api.constrains('odometer_current', 'odometer')
    def _check_odometer(self):
        for rec in self:
            if rec.odometer_current < rec.odometer:
                raise ValidationError("The current odometer must be greater than or equal to the previous one.")

    @api.model
    def create(self, vals):
        rec = super().create(vals)
        if rec.vehicle_id and rec.odometer_current:
            rec.vehicle_id.odometer = rec.odometer_current
        return rec

    def write(self, vals):
        res = super().write(vals)
        if 'odometer_current' in vals:
            for rec in self:
                if rec.vehicle_id:
                    rec.vehicle_id.odometer = rec.odometer_current
        return res

    def action_view_vehicle(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vehicle',
            'res_model': 'fleet.vehicle',
            'view_mode': 'tree,form,kanban',
            'domain': [('id', '=', self.vehicle_id.id)] if self.vehicle_id else [],
        }
