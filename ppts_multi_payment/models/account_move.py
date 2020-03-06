from odoo import fields, models, api
from odoo.exceptions import ValidationError

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    customer_cr_partial_id = fields.Many2one("customer.multi.payment.credit.line")
    customer_de_partial_id = fields.Many2one("customer.multi.payment.debit.line")
    vendor_cr_partial_id = fields.Many2one("vendor.multi.payment.credit.line")
    vendor_de_partial_id = fields.Many2one("vendor.multi.payment.debit.line")
    
    @api.multi
    def _reconcile_lines(self, debit_moves, credit_moves, field):
        """ This function loops on the 2 recordsets given as parameter as long as it
            can find a debit and a credit to reconcile together. It returns the recordset of the
            account move lines that were not reconciled during the process.
        """
        (debit_moves + credit_moves).read([field])
        to_create = []
        cash_basis = debit_moves and debit_moves[0].account_id.internal_type in ('receivable', 'payable') or False
        cash_basis_percentage_before_rec = []
        while (debit_moves and credit_moves):
            debit_move = debit_moves[0]
            credit_move = credit_moves[0]
            company_currency = debit_move.company_id.currency_id
            # We need those temporary value otherwise the computation might be wrong below
            temp_amount_residual = min(debit_move.amount_residual, -credit_move.amount_residual)
            temp_amount_residual_currency = min(debit_move.amount_residual_currency, -credit_move.amount_residual_currency)
            amount_reconcile = min(debit_move[field], -credit_move[field])

            #Remove from recordset the one(s) that will be totally reconciled
            # For optimization purpose, the creation of the partial_reconcile are done at the end,
            # therefore during the process of reconciling several move lines, there are actually no recompute performed by the orm
            # and thus the amount_residual are not recomputed, hence we have to do it manually.
            if amount_reconcile == debit_move[field]:
                debit_moves -= debit_move
            else:
                debit_moves[0].amount_residual -= temp_amount_residual
                debit_moves[0].amount_residual_currency -= temp_amount_residual_currency

            if amount_reconcile == -credit_move[field]:
                credit_moves -= credit_move
            else:
                credit_moves[0].amount_residual += temp_amount_residual
                credit_moves[0].amount_residual_currency += temp_amount_residual_currency
            #Check for the currency and amount_currency we can set
            currency = False
            amount_reconcile_currency = 0
            if field == 'amount_residual_currency':
                currency = credit_move.currency_id.id
                amount_reconcile_currency = temp_amount_residual_currency
                amount_reconcile = temp_amount_residual

            if cash_basis:
                tmp_set = debit_move | credit_move
                cash_basis_percentage_before_rec.append(tmp_set._get_matched_percentage())
            
            amount_to_reconcile = 0.00
            if debit_move.customer_cr_partial_id and credit_move.customer_de_partial_id:
                if debit_move.customer_cr_partial_id.amount_reconcile == credit_move.customer_de_partial_id.amount_reconcile: 
                    amount_to_reconcile += debit_move.customer_cr_partial_id.amount_reconcile
                    debit_move.customer_cr_partial_id.amount_reconcile -= debit_move.customer_cr_partial_id.amount_reconcile
                    credit_move.customer_de_partial_id.amount_reconcile -= credit_move.customer_de_partial_id.amount_reconcile
                    amount_reconcile = amount_to_reconcile
                if debit_move.customer_cr_partial_id.amount_reconcile > credit_move.customer_de_partial_id.amount_reconcile:
                    amount_to_reconcile += credit_move.customer_de_partial_id.amount_reconcile
                    debit_move.customer_cr_partial_id.amount_reconcile -= credit_move.customer_de_partial_id.amount_reconcile
                    credit_move.customer_de_partial_id.amount_reconcile -= credit_move.customer_de_partial_id.amount_reconcile
                    amount_reconcile = amount_to_reconcile
                if debit_move.customer_cr_partial_id.amount_reconcile < credit_move.customer_de_partial_id.amount_reconcile: 
                    amount_to_reconcile += debit_move.customer_cr_partial_id.amount_reconcile
                    credit_move.customer_de_partial_id.amount_reconcile -= debit_move.customer_cr_partial_id.amount_reconcile
                    debit_move.customer_cr_partial_id.amount_reconcile -= debit_move.customer_cr_partial_id.amount_reconcile
                    amount_reconcile = amount_to_reconcile
                    
            if debit_move.vendor_cr_partial_id and credit_move.vendor_de_partial_id:
                if debit_move.vendor_cr_partial_id.amount_reconcile == credit_move.vendor_de_partial_id.amount_reconcile: 
                    amount_to_reconcile += debit_move.vendor_cr_partial_id.amount_reconcile
                    debit_move.vendor_cr_partial_id.amount_reconcile -= debit_move.vendor_cr_partial_id.amount_reconcile
                    credit_move.vendor_de_partial_id.amount_reconcile -= credit_move.vendor_de_partial_id.amount_reconcile
                    amount_reconcile = amount_to_reconcile
                if debit_move.vendor_cr_partial_id.amount_reconcile > credit_move.vendor_de_partial_id.amount_reconcile:
                    amount_to_reconcile += credit_move.vendor_de_partial_id.amount_reconcile
                    debit_move.vendor_cr_partial_id.amount_reconcile -= credit_move.vendor_de_partial_id.amount_reconcile
                    credit_move.vendor_de_partial_id.amount_reconcile -= credit_move.vendor_de_partial_id.amount_reconcile
                    amount_reconcile = amount_to_reconcile
                if debit_move.vendor_cr_partial_id.amount_reconcile < credit_move.vendor_de_partial_id.amount_reconcile: 
                    amount_to_reconcile += debit_move.vendor_cr_partial_id.amount_reconcile
                    credit_move.vendor_de_partial_id.amount_reconcile -= debit_move.vendor_cr_partial_id.amount_reconcile
                    debit_move.vendor_cr_partial_id.amount_reconcile -= debit_move.vendor_cr_partial_id.amount_reconcile
                    amount_reconcile = amount_to_reconcile
                    
            if debit_move.customer_cr_partial_id and not credit_move.customer_de_partial_id:
                if debit_move.customer_cr_partial_id.amount_reconcile == credit_move.credit: 
                    amount_to_reconcile += debit_move.customer_cr_partial_id.amount_reconcile
                    debit_move.customer_cr_partial_id.amount_reconcile -= debit_move.customer_cr_partial_id.amount_reconcile
                    amount_reconcile = amount_to_reconcile
                if debit_move.customer_cr_partial_id.amount_reconcile > credit_move.credit:
                    amount_to_reconcile += credit_move.credit
                    debit_move.customer_cr_partial_id.amount_reconcile -= credit_move.credit
                    amount_reconcile = amount_to_reconcile
                if debit_move.customer_cr_partial_id.amount_reconcile < credit_move.credit: 
                    amount_to_reconcile += debit_move.customer_cr_partial_id.amount_reconcile
                    debit_move.customer_cr_partial_id.amount_reconcile -= debit_move.customer_cr_partial_id.amount_reconcile
                    amount_reconcile = amount_to_reconcile
                    
            if not debit_move.vendor_cr_partial_id and credit_move.vendor_de_partial_id:
                if debit_move.debit == credit_move.vendor_de_partial_id.amount_reconcile: 
                    amount_to_reconcile += credit_move.vendor_de_partial_id.amount_reconcile
                    credit_move.vendor_de_partial_id.amount_reconcile -= credit_move.vendor_de_partial_id.amount_reconcile
                    amount_reconcile = amount_to_reconcile
                if debit_move.debit > credit_move.vendor_de_partial_id.amount_reconcile:
                    amount_to_reconcile += credit_move.vendor_de_partial_id.amount_reconcile
                    credit_move.vendor_de_partial_id.amount_reconcile -= credit_move.vendor_de_partial_id.amount_reconcile
                    amount_reconcile = amount_to_reconcile
                if debit_move.debit < credit_move.vendor_de_partial_id.amount_reconcile: 
                    amount_to_reconcile += debit_move.debit
                    credit_move.vendor_de_partial_id.amount_reconcile -= debit_move.debit
                    amount_reconcile = amount_to_reconcile
                    
            debit_move.customer_cr_partial_id = False
            credit_move.customer_de_partial_id = False
            debit_move.vendor_cr_partial_id = False
            credit_move.vendor_de_partial_id = False
            
            to_create.append({
                'debit_move_id': debit_move.id,
                'credit_move_id': credit_move.id,
                'amount': amount_reconcile,
                'amount_currency': amount_reconcile_currency,
                'currency_id': currency,
            })

        part_rec = self.env['account.partial.reconcile']
        index = 0
        with self.env.norecompute():
            for partial_rec_dict in to_create:
                new_rec = self.env['account.partial.reconcile'].create(partial_rec_dict)
                part_rec += new_rec
                if cash_basis:
                    new_rec.create_tax_cash_basis_entry(cash_basis_percentage_before_rec[index])
                    index += 1
        self.recompute()

        return debit_moves+credit_moves
    
    @api.multi
    @api.constrains('amount_currency', 'debit', 'credit')
    def _check_currency_amount(self):
        for line in self:
            if not line.payment_id.ven_multi_pay_id and not line.payment_id.cus_multi_pay_id:
                if line.amount_currency:
                    if (line.amount_currency > 0.0 and line.credit > 0.0) or (line.amount_currency < 0.0 and line.debit > 0.0):
                        raise ValidationError(_('The amount expressed in the secondary currency must be positive when account is debited and negative when account is credited.'))
