from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.osv import expression

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    maintenance_interval_km = fields.Integer(string='maintenance interval (km)')
    next_maintenance_km = fields.Integer(string='Next Maintenance (km)')
    plate_number = fields.Char(string='Plate Number', required=True)
    fuel_logs_count = fields.Integer(string='Number of Logs', compute='_compute_fuel_logs_count')
    fuel_log_ids = fields.One2many('fleet.fuel.log', 'vehicle_id', string='Fuel Logs')
    user_id = fields.Many2one('res.users', string='Assigned User', default=lambda self: self.env.user)

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
                raise ValidationError("The maintenance interval must be greater than 0 km.")

    def action_view_fuel_logs(self):
        return {
            'name': 'Fuel Logs',
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
                    f"Reminder: the vehicle '{v.name}' "
                    f"already has {v.odometer} km and needs maintenance at {v.next_maintenance_km} km."
                )
            )
            template = self.env.ref('fleet_fuel.email_template_manintenance')
            template.send_mail(v.id, force_send=True)

   
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if domain and ('plate_number', '=', True) in domain and operator in ('like', 'ilike') and limit is not None:
            sols = self.search_fetch(
                domain,  ['|',
                ('plate_number', operator, name),
                ('name',        operator, name),
            ], limit=limit, order='order_id.id DESC, sequence, id',
            )
            return [(sol.id, sol.plate_number) for sol in sols]
        return super().name_search(name, domain, operator, limit)

