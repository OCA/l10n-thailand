# -*- coding: utf-8 -*-
# © 2017 Ecosoft (ecosoft.co.th).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, fields, api


ADDRESS_FIELDS = ('street', 'street2', 'zip', 'city', 'state_id', 'country_id',
                  'province_id', 'district_id', 'township_id',)


class ResPartner(models.Model):

    _inherit = 'res.partner'

    province_id = fields.Many2one(
        'res.country.province',
        domain="[('country_id','=',country_id)]",
        ondelete='restrict'
    )
    district_id = fields.Many2one(
        'res.country.district',
        domain="[('province_id','=',province_id)]",
        ondelete='restrict'
    )
    township_id = fields.Many2one(
        'res.country.township',
        domain="[('district_id','=',district_id)]",
        ondelete='restrict'
    )

    @api.onchange('township_id')
    def _onchange_township_id(self):
        township = self.township_id
        if township:
            self.zip = township.zip
            self.province_id = township.province_id and township.province_id.id
            self.district_id = township.district_id and township.district_id.id
            self.country_id = township.country_id and township.country_id.id

    @api.model
    def _address_fields(self):
        """ Returns the list of address fields that are synced from the parent
        when the `use_parent_address` flag is set. """
        return list(ADDRESS_FIELDS)

    @api.model
    def _display_address(self, address, without_company=False):
        """ Overwrite for Thai """
        # get the information that will be injected into the display format
        # get the address format
        default_format = "%(street)s\n%(street2)s\n%(district_name)s \
               %(township_name)s\n%(province_name)s %(zip)s"
        address_format = address.country_id.address_format or default_format

        args = {
            'state_code': address.state_id.code or '',
            'state_name': address.state_id.name or '',
            'country_code': address.country_id.code or '',
            'country_name': address.country_id.name or '',
            'company_name': address.parent_name or '',
            'district_name': address.district_id.name or '',
            'township_name': address.township_id.name or '',
            'province_name': address.province_id.name or '',
        }
        for field in self._address_fields():
            args[field] = getattr(address, field) or ''
        if without_company:
            args['company_name'] = ''
        elif address.parent_id:
            address_format = '%(company_name)s\n' + address_format
        return address_format % args
