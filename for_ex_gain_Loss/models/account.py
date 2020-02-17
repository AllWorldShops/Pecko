# -*- coding: utf-8 -*-

from odoo.tools import float_is_zero
from odoo.exceptions import UserError
from odoo import fields, models, api, _
from odoo.tools import float_is_zero, float_compare
from odoo.addons import decimal_precision as dp
from datetime import date

class ResCompany(models.Model):
    _inherit = 'res.company'

    exchange_account_type = fields.Selection([('journal','Based on Journal'),('account','Based on Direct Account')], string='Account Type',default='journal')
    debit_account_id = fields.Many2one('account.account', string='Gain Exchange Rate Account')
    credit_account_id = fields.Many2one('account.account', string='Loss Exchange Rate Account')
    partial_payment = fields.Boolean(string='Create Journal Entry for Partial Payment')

class for_ex_gain_loss(models.TransientModel):
    _inherit = 'res.config.settings'
    
    # round_off = fields.Boolean(string='Allow rounding of invoice amount', help="Allow rounding of invoice amount")
    # round_off_account = fields.Many2one('account.account', string='Round Off Account')
    exchange_account_type = fields.Selection(related="company_id.exchange_account_type", string='Account Type',readonly=False)
    debit_account_id = fields.Many2one('account.account',related="company_id.debit_account_id", string='Gain Exchange Rate Account',readonly=False)
    credit_account_id = fields.Many2one('account.account',related="company_id.credit_account_id", string='Loss Exchange Rate Account',readonly=False)
    partial_payment = fields.Boolean(related="company_id.partial_payment", string='Create Journal Entry for Partial Payment',readonly=False)

    @api.onchange('exchange_account_type')
    def onchange_account_id(self):
        if self.exchange_account_type and self.exchange_account_type == 'journal':
            self.debit_account_id = ''
            self.credit_account_id = ''

    # def set_values(self):
    #     super(for_ex_gain_loss, self).set_values()
    #     ICPSudo = self.env['ir.config_parameter'].sudo()
    #     ICPSudo.set_param('account.exchange_account_type', self.exchange_account_type)
    #     ICPSudo.set_param('account.debit_account_id', self.debit_account_id.id)
    #     ICPSudo.set_param('account.credit_account_id', self.credit_account_id.id)

    #To get values from respected model #
    # @api.model
    # def get_values(self):
    #     res = super(for_ex_gain_loss, self).get_values()
    #     ICPSudo = self.env['ir.config_parameter'].sudo()
    #     res.update(
    #         # exchange_account_type=ICPSudo.get_param('account.exchange_account_type'),debit_account_id=ICPSudo.get_param('account.debit_account_id'),credit_account_id=ICPSudo.get_param('account.credit_account_id')
    #         exchange_account_type=ICPSudo.get_param('account.exchange_account_type')
    #     )
    #     # res.update(
    #     #     debit_account_id=ICPSudo.get_param('account.debit_account_id')
    #     # )
    #     # res.update(
    #     #     credit_account_id=ICPSudo.get_param('account.credit_account_id')
    #     # )
    #     return res

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    
    @api.multi
    def check_full_reconcile(self):
        """
        This method check if a move is totally reconciled and if we need to create exchange rate entries for the move.
        In case exchange rate entries needs to be created, one will be created per currency present.
        In case of full reconciliation, all moves belonging to the reconciliation will belong to the same account_full_reconcile object.
        """
        # Get first all aml involved
        part_recs = self.env['account.partial.reconcile'].search(['|', ('debit_move_id', 'in', self.ids), ('credit_move_id', 'in', self.ids)])
        amls = self
        sample_move_id = False
        todo = set(part_recs)
        seen = set()
        while todo:
            partial_rec = todo.pop()
            seen.add(partial_rec)
            for aml in [partial_rec.debit_move_id, partial_rec.credit_move_id]:
                sample_move_id = partial_rec.credit_move_id.move_id
                if aml not in amls:
                    amls += aml
                    for x in aml.matched_debit_ids | aml.matched_credit_ids:
                        if x not in seen:
                            todo.add(x)
        partial_rec_ids = [x.id for x in seen]
        if not amls:
            return
        # If we have multiple currency, we can only base ourselve on debit-credit to see if it is fully reconciled
        currency = set([a.currency_id for a in amls if a.currency_id.id != False])
        multiple_currency = False
        if len(currency) != 1:
            currency = False
            multiple_currency = True
        else:
            currency = list(currency)[0]
        # Get the sum(debit, credit, amount_currency) of all amls involved
        total_debit = 0
        total_credit = 0
        total_amount_currency = 0
        maxdate = date.min
        to_balance = {}
        for aml in amls:
            total_debit += aml.debit
            total_credit += aml.credit
            maxdate = max(aml.date, maxdate)
            total_amount_currency += aml.amount_currency
            # Convert in currency if we only have one currency and no amount_currency
            if not aml.amount_currency and currency:
                multiple_currency = True
                total_amount_currency += aml.company_id.currency_id._convert(aml.balance, currency, aml.company_id, aml.date)
            # If we still have residual value, it means that this move might need to be balanced using an exchange rate entry
            if aml.amount_residual != 0 or aml.amount_residual_currency != 0:
                if not to_balance.get(aml.currency_id):
                    to_balance[aml.currency_id] = [self.env['account.move.line'], 0]
                to_balance[aml.currency_id][0] += aml
                to_balance[aml.currency_id][1] += aml.amount_residual != 0 and aml.amount_residual or aml.amount_residual_currency
        # Check if reconciliation is total
        # To check if reconciliation is total we have 3 differents use case:
        # 1) There are multiple currency different than company currency, in that case we check using debit-credit
        # 2) We only have one currency which is different than company currency, in that case we check using amount_currency
        # 3) We have only one currency and some entries that don't have a secundary currency, in that case we check debit-credit
        #   or amount_currency.
        digits_rounding_precision = amls[0].company_id.currency_id.rounding
        if (currency and float_is_zero(total_amount_currency, precision_rounding=currency.rounding)) or \
            (multiple_currency and float_compare(total_debit, total_credit, precision_rounding=digits_rounding_precision) == 0):
            exchange_move_id = False
            exchange_account_type = aml.company_id.exchange_account_type
            # Eventually create a journal entry to book the difference due to foreign currency's exchange rate that fluctuates
            if to_balance and any([residual for aml, residual in to_balance.values()]):
                if exchange_account_type == 'account':
                    part_reconcile = self.env['account.partial.reconcile']
                    for aml_to_balance, total in to_balance.values():
                        if total:
                            rate_diff_amls, rate_diff_partial_rec = part_reconcile.create_exchange_rate_entry(aml_to_balance,sample_move_id)
                            amls += rate_diff_amls
                            partial_rec_ids += rate_diff_partial_rec.ids
                        else:
                            aml_to_balance.reconcile()
                    sample_move_id.post()
                    exchange_move_id = sample_move_id.id
                    
                else:
                    exchange_move = self.env['account.move'].create(
                        self.env['account.full.reconcile']._prepare_exchange_diff_move(move_date=maxdate, company=amls[0].company_id))
                    part_reconcile = self.env['account.partial.reconcile']
                    for aml_to_balance, total in to_balance.values():
                        if total:
                            rate_diff_amls, rate_diff_partial_rec = part_reconcile.create_exchange_rate_entry(aml_to_balance, exchange_move)
                            amls += rate_diff_amls
                            partial_rec_ids += rate_diff_partial_rec.ids
                        else:
                            aml_to_balance.reconcile()
                    exchange_move.post()
                    exchange_move_id = exchange_move.id
            #mark the reference of the full reconciliation on the exchange rate entries and on the entries
            self.env['account.full.reconcile'].create({
                'partial_reconcile_ids': [(6, 0, partial_rec_ids)],
                'reconciled_line_ids': [(6, 0, amls.ids)],
                'exchange_move_id': exchange_move_id,
            })
    
class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"

    @api.model
    def create_exchange_rate_entry(self, aml_to_fix, move):
        """
        Automatically create a journal items to book the exchange rate
        differences that can occur in multi-currencies environment. That
        new journal item will be made into the given `move` in the company
        `currency_exchange_journal_id`, and one of its journal items is
        matched with the other lines to balance the full reconciliation.

        :param aml_to_fix: recordset of account.move.line (possible several
            but sharing the same currency)
        :param move: account.move
        :return: tuple.
            [0]: account.move.line created to balance the `aml_to_fix`
            [1]: recordset of account.partial.reconcile created between the
                tuple first element and the `aml_to_fix`
        """
        partial_rec = self.env['account.partial.reconcile']
        aml_model = self.env['account.move.line']

        created_lines = self.env['account.move.line']
        for aml in aml_to_fix:
            exchange_account_type = move.company_id.exchange_account_type
            exchange_journal = move.company_id.currency_exchange_journal_id
            if exchange_account_type == 'account':
                account_id = aml.amount_residual > 0 and move.company_id.debit_account_id.id or move.company_id.credit_account_id.id
            else:
                account_id = aml.amount_residual > 0 and exchange_journal.default_debit_account_id.id or exchange_journal.default_credit_account_id.id
            #create the line that will compensate all the aml_to_fix
            line_to_rec = aml_model.with_context(check_move_validity=False).create({
                'name': _('Currency exchange rate difference'),
                'debit': aml.amount_residual < 0 and -aml.amount_residual or 0.0,
                'credit': aml.amount_residual > 0 and aml.amount_residual or 0.0,
                'account_id': aml.account_id.id,
                'move_id': move.id,
                'currency_id': aml.currency_id.id,
                'amount_currency': aml.amount_residual_currency and -aml.amount_residual_currency or 0.0,
                'partner_id': aml.partner_id.id,
            })
            #create the counterpart on exchange gain/loss account
            aml_model.with_context(check_move_validity=False).create({
                'name': _('Currency exchange rate difference'),
                'debit': aml.amount_residual > 0 and aml.amount_residual or 0.0,
                'credit': aml.amount_residual < 0 and -aml.amount_residual or 0.0,
                'account_id': account_id,
                'move_id': move.id,
                'currency_id': aml.currency_id.id,
                'amount_currency': aml.amount_residual_currency and aml.amount_residual_currency or 0.0,
                'partner_id': aml.partner_id.id,
            })

            #reconcile all aml_to_fix
            partial_rec |= self.create(
                self._prepare_exchange_diff_partial_reconcile(
                        aml=aml,
                        line_to_reconcile=line_to_rec,
                        currency=aml.currency_id or False)
            )
            created_lines |= line_to_rec
        return created_lines, partial_rec
    
# #         # stop