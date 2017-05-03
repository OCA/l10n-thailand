# -*- coding: utf-8 -*-
# © 2017 Ecosoft (ecosoft.co.th).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, fields


class ResCountryProvince(models.Model):

    _name = 'res.country.province'
    _description = 'Provinces'

    name = fields.Char(string='Province', required=True)
    country_id = fields.Many2one(
        'res.country',
        string='Country',
        required=True,
    )


class ResCountryDistrict(models.Model):

    _name = 'res.country.district'
    _description = 'Districts'

    name = fields.Char(
        string='District',
        required=True,
    )
    province_id = fields.Many2one(
        'res.country.province',
        string='Province',
        required=True,
    )


class ResCountryTownship(models.Model):

    _name = 'res.country.township'
    _description = 'Township'

    name = fields.Char(
        string='Township',
        required=True,
    )
    district_id = fields.Many2one(
        'res.country.district',
        string='District',
        required=True,
    )
    zip = fields.Char(
        string='Zip',
    )
    province_id = fields.Many2one(
        'res.country.province',
        related='district_id.province_id',
        string='Province',
        readonly=True,
        store=True,
    )
    country_id = fields.Many2one(
        'res.country',
        related='district_id.province_id.country_id',
        string='Country',
        readonly=True,
        store=True,
    )
