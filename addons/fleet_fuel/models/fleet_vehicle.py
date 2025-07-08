from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.osv import expression

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    maintenance_interval_km = fields.Integer(string='Intervalo de Mantenimiento (km)')
    next_maintenance_km = fields.Integer(string='Próximo Mantenimiento (km)')
    plate_number = fields.Char(string='Número de Placa', required=True)
    fuel_logs_count = fields.Integer(string='Cantidad de Logs', compute='_compute_fuel_logs_count')
    fuel_log_ids = fields.One2many('fleet.fuel.log', 'vehicle_id', string='Logs de Combustible')
    user_id = fields.Many2one('res.users', string='Usuario Asignado', default=lambda self: self.env.user)

    @api.depends('fuel_log_ids')
    def _compute_fuel_logs_count(self):
        for rec in self:
            rec.fuel_logs_count = self.env['fleet.fuel.log'].search_count([('vehicle_id', '=', rec.id)])

    @api.onchange('maintenance_interval_km', 'odometer')
    def _onchange_maintenance_interval_or_odometer(self):
        for rec in self:
            if rec.maintenance_interval_km and rec.odometer is not None:
                rec.next_maintenance_km = rec.odometer + rec.maintenance_interval_km

    @api.constrains('maintenance_interval_km')
    def _check_interval_positive(self):
        for rec in self:
            if rec.maintenance_interval_km <= 0:
                raise ValidationError("El intervalo de mantenimiento debe ser mayor que 0 km.")

    def action_view_fuel_logs(self):
        return {
            'name': 'Logs de Combustible',
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.fuel.log',
            'view_mode': 'tree,form',
            'domain': [('vehicle_id', '=', self.id)],
        }

    @api.model
    def _cron_maintenance_reminder(self):
        threshold = 500
        vehicles = self.search([
            ('odometer', '>=', 'next_maintenance_km - %s' % threshold),
            ('odometer', '<', 'next_maintenance_km')
        ])
        for v in vehicles:
            v.message_post(
                body=(
                    f"Recordatorio: el vehículo '{v.name}' "
                    f"ya tiene {v.odometer} km y debe ir a mantenimiento en {v.next_maintenance_km} km."
                )
            )
            template = self.env.ref('fleet_fuel.email_template_manintenance')
            template.send_mail(v.id, force_send=True)

   
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|',
                ('plate_number', operator, name),
                ('name',        operator, name),
            ]
        vehicles = self.search(domain + args, limit=limit)
        return vehicles.name_get()
