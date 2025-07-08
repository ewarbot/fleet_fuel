# Módulo: Gestión de Flota y Combustible

Este documento ofrece la **documentación completa** del complemento Odoo `fleet_fuel`, creado para optimizar la gestión de flotas mediante:
- Registro detallado de cada carga de combustible  
- Cálculo automático de costes y kilometraje  
- Integración con facturación  
- Planificación y recordatorios de mantenimiento  
- Informes de consumo  

---

## Tabla de Contenidos

1. Introducción  
2. Requisitos  
3. Instalación  
4. Grupos y Permisos  
5. Modelos y Campos  
   - fleet.fuel.log  
   - Extensión de fleet.vehicle  
   - fuel.data  
   - Extensión de account.move  
6. Vistas y Menús  
7. Acciones Programadas  
8. Informes  
9. Ejemplos de Uso  
10. Modulos adicionales
11. Licencia

---

## Introducción

El módulo `fleet_fuel` extiende la app de flota para:
- Registrar cada carga de combustible junto con conductor y vehículo.  
- Calcular kilómetros recorridos y coste por kilómetro.  
- Vincular esos logs a facturas de combustible y crear líneas automáticas.  
- Generar recordatorios de mantenimiento basados en kilometraje.  
- Ofrecer informes QWeb con tendencias de consumo.  

---

## Requisitos

- **Odoo** ≥ 17 (Community o Enterprise)  
- **Python** ≥ 3.10  
- Sin dependencias externas adicionales  

---

## Instalación

1. Copia la carpeta `fleet_fuel` a tu ruta de addons (p.ej. `/mnt/extra-addons/`).  
2. En Odoo, ve a **Apps** → **Actualizar lista de aplicaciones**.  
3. Busca **Fleet Fuel** y haz clic en **Instalar**.  
4. Ajusta permisos según los grupos (ver siguiente sección).  

---

## Grupos y Permisos

Se crean dos grupos bajo la categoría **Flota y Combustible**:
- **Usuario** (`fleet_fuel.group_fleet_fuel_user`):  
  - Sólo puede crear y ver logs de combustible.  
- **Administrador** (`fleet_fuel.group_fleet_fuel_administrator`):  
  - Hereda todos los permisos de “Usuario”  
  - Incluye al grupo base de administración de sistema (`base.group_system`)  

---

## Modelos y Campos

### fleet.fuel.log

Registro individual de una carga de combustible:

| Campo               | Tipo       | Descripción                                                                                  |
| ------------------- | ---------- | -------------------------------------------------------------------------------------------- |
| name                | Char       | Secuencia automática (ir.sequence con código fleet.fuel.log).                                |
| vehicle_id          | Many2one   | Vehículo (fleet.vehicle), obligatorio.                                                       |
| driver_id           | Many2one   | Conductor (res.partner), se autoasigna al cambiar vehículo.                                  |
| plate_number        | Char       | Placa del vehículo, rellenado al seleccionar vehículo.                                       |
| date                | Date       | Fecha de la carga, por defecto hoy.                                                         |
| odometer            | Float      | Kilometraje previo, readonly y fijado al cambiar vehículo.                                   |
| odometer_current    | Float      | Kilometraje actual, obligatorio.                                                             |
| kilometers          | Float      | Computado: max(odometer_current - odometer, 0).                                              |
| gallons             | Float      | Cantidad de galones cargados, obligatorio.                                                   |
| fuel_id             | Many2one   | Datos de combustible (fuel.data), se filtra según tipo de vehículo.                          |
| price_per_gallon    | Float      | Precio unitario (relacionado con fuel_id.price).                                             |
| fuel_cost           | Monetary   | Cálculo: gallons * price_per_gallon.                                                         |
| cost_per_km         | Monetary   | Cálculo: fuel_cost / kilometers (si > 0).                                                    |
| tax_ids             | Many2many  | Impuestos de compra (heredado de fuel.data.tax_ids).                                         |
| invoice_id          | Many2one   | Factura (account.move).                                                                      |
| company_currency_id | Many2one   | Moneda de la compañía.                                                                       |
| notes               | Text       | Notas opcionales.                                                                            |

**Restricciones y sobrecargas**  
- Valida que odometer_current ≥ odometer.  
- Al crear o escribir, actualiza el campo vehicle_id.odometer.  
- Botón action_view_vehicle para navegar al formulario del vehículo.  

### Extensión de fleet.vehicle

| Campo                    | Tipo       | Descripción                                               |
| ------------------------ | ---------- | --------------------------------------------------------- |
| maintenance_interval_km  | Integer    | Intervalo entre servicios (km).                           |
| next_maintenance_km      | Integer    | Calculado: odometer + maintenance_interval_km.            |
| plate_number             | Char       | Requerido en el vehículo.                                 |
| fuel_log_ids             | One2many   | Logs asociados (fleet.fuel.log).                          |
| fuel_logs_count          | Integer    | Contador de logs (compute).                               |
| user_id                  | Many2one   | Usuario asignado (default: usuario actual).               |

**Métodos**  
- _onchange_maintenance_interval_or_odometer: recalcula next_maintenance_km.  
- _cron_maintenance_reminder: cron semanal que envía notificaciones y correo.  
- action_view_fuel_logs: abre vista de logs filtrados por vehículo.  
- name_search: búsqueda por placa o nombre.  

### fuel.data

Catálogo de combustibles y precios vigentes:

| Campo       | Tipo         | Descripción                                |
| ----------- | ------------ | ------------------------------------------ |
| fuel_type   | Selection    | Tipo (diesel, gasoline, etc.).            |
| name        | Char         | Computado a partir de fuel_type.          |
| sequence    | Integer      | Orden de aparición.                       |
| price       | Float        | Precio por galón, obligatorio.            |
| start_date  | Date         | Fecha de inicio de vigencia.              |
| end_date    | Date         | Fecha de fin de vigencia.                 |
| active      | Boolean      | Estado activo/inactivo.                   |
| tax_ids     | Many2many    | Impuestos de compra aplicables.           |

### Extensión de account.move

Vincula logs de combustible a facturas:

| Campo          | Tipo     | Descripción                                                            |
| -------------- | -------- | ---------------------------------------------------------------------- |
| fuel_log_ids   | One2many | Logs sin factura asignada (domain=[('invoice_id','=',False)]).         |

**Onchange**  
Regenera invoice_line_ids según logs añadidos, con descripción, cantidad, precio_unit y tax_ids.  

---

## Vistas y Menús

- **Flota → Logs de Combustible**: árbol y formulario.  
- **Flota → Vehículos**: pestaña “Mantenimiento” con nuevos campos y botón “Ver Logs”.  
- **Contabilidad → Facturas**: pestaña “Fuel Logs”.  
- **Catálogo**: menú para fuel.data.  

---

## Acciones Programadas

- Nombre: Flota: Recordatorio de Mantenimiento  
- Modelo: fleet.vehicle  
- Método: _cron_maintenance_reminder  
- Frecuencia: Semanal — Lunes 08:00  
- Lógica: umbral de 500 km, mensaje en chatter y correo con plantilla.  

---

## Informes

- **Reporte QWeb** (`report_fleet_fuel_log`): logs, gráficos y totales.  

---

## Ejemplos de Uso

1. Crear log de combustible.  
2. Generar factura usando “Fuel Logs”.  
3. Ver notificaciones de mantenimiento.  
4. Consultar tendencias de consumo.  
---

## Modulos adicionales

ica_web_responsive (para visualizar el tema como el entreprise)
No es Obligatorio

---

## Licencia

Apache License Version 2.0