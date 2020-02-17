from odoo import fields, models

class AccountMove(models.Model):
    _inherit = "account.payment"
    
    cus_multi_pay_id = fields.Many2one("customer.multi.payment", "Payment ID")
    ven_multi_pay_id = fields.Many2one("vendor.multi.payment", "Payment ID")
    
    # multi customer invoice fully paid
    def _get_shared_move_line_vals_cus_inherit(self, debit, credit, amount_currency, move_id):
        return {
            'account_id': self.cus_multi_pay_id.writeoff_account_id.id,
            'partner_id': self.cus_multi_pay_id.partner_id.id,
            'name': self.cus_multi_pay_id.writeoff_label,
            'debit': debit,
            'credit': credit,
            'currency_id': self.currency_id.id,
            'amount_currency': amount_currency or False,
            'payment_id': self.id,
            'move_id': move_id
        }
        
    # multi vendor bills fully paid
    def _get_shared_move_line_vals_inherit(self, credit, debit, amount_currency, move_id):
        return {
            'account_id': self.ven_multi_pay_id.writeoff_account_id.id,
            'partner_id': self.ven_multi_pay_id.partner_id.id,
            'name': self.ven_multi_pay_id.writeoff_label,
            'debit': debit,
            'credit': credit,
            'amount_currency': amount_currency or False,
            'currency_id': self.currency_id.id,
            'payment_id': self.id,
            'move_id': move_id
        }
        
    def _create_payment_entry(self, amount):
        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        move = self.env['account.move'].create(self._get_move_vals())
        invoice_currency = False
        if self.invoice_ids and all([x.currency_id == self.invoice_ids[0].currency_id for x in self.invoice_ids]):
            invoice_currency = self.invoice_ids[0].currency_id
        if not self._context.get('split_payment'):
            aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
            debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amount, self.currency_id, self.company_id.currency_id)
            counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
            counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
            counterpart_aml_dict.update({'currency_id': currency_id})
            counterpart_aml = aml_obj.create(counterpart_aml_dict)
    
            if self.payment_difference_handling == 'reconcile' and self.payment_difference:
                writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
                debit_wo, credit_wo, amount_currency_wo, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(self.payment_difference, self.currency_id, self.company_id.currency_id)
                writeoff_line['name'] = self.writeoff_label
                writeoff_line['account_id'] = self.writeoff_account_id.id
                writeoff_line['debit'] = debit_wo
                writeoff_line['credit'] = credit_wo
                writeoff_line['amount_currency'] = amount_currency_wo
                writeoff_line['currency_id'] = currency_id
                writeoff_line = aml_obj.create(writeoff_line)
                if counterpart_aml['debit'] or (writeoff_line['credit'] and not counterpart_aml['credit']):
                    counterpart_aml['debit'] += credit_wo - debit_wo
                if counterpart_aml['credit'] or (writeoff_line['debit'] and not counterpart_aml['debit']):
                    counterpart_aml['credit'] += debit_wo - credit_wo
                counterpart_aml['amount_currency'] -= amount_currency_wo
    
            if not self.currency_id.is_zero(self.amount):
                if not self.currency_id != self.company_id.currency_id:
                    amount_currency = 0
                liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
                liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
                aml_obj.create(liquidity_aml_dict)
    
            if not self.journal_id.post_at_bank_rec:
                move.post()
            if self.invoice_ids:
                self.invoice_ids.register_payment(counterpart_aml)
            return move

        elif self._context.get('split_payment'):

            for loop in self._context['split_payment']:
                invoice_ids = list(loop.keys())[0]
                loop_amount = list(loop.values())[0]
                debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(loop_amount,self.currency_id,self.company_id.currency_id)
                counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
                counterpart_aml_dict.update(self._get_counterpart_move_line_vals(invoice_ids))
                counterpart_aml_dict.update({'currency_id': self.currency_id != self.company_id.currency_id and self.currency_id.id or False})

#                 if self.currency_rate:
#                     current_amt = self.currency_rate * counterpart_aml_dict['amount_currency']
#                     if current_amt < 0:
#                         current_amt = current_amt * -1
#                     counterpart_aml_dict.update({'credit': current_amt})

                journal_vals = self.env['account.journal'].search_read([('id','=',self.journal_id.id)],limit=1)[0]
                if journal_vals.get('round_up', False):
                    counterpart_aml_dict.update({'debit':round(counterpart_aml_dict.get('debit',0)),'credit':round(counterpart_aml_dict.get('credit',0))})
                
                counterpart_aml = aml_obj.create(counterpart_aml_dict)
                if not self.ven_multi_pay_id and  not self.cus_multi_pay_id:
                    if self.payment_difference_handling == 'reconcile':
                        invoice_ids.register_payment(counterpart_aml, self.writeoff_account_id, self.journal_id)
                    else:
                        invoice_ids.register_payment(counterpart_aml)
            # Write counterpart lines
            debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amount,self.currency_id,self.company_id.currency_id)
            
            # multi vendor bills fully paid
            if debit and self.ven_multi_pay_id:
                diff = self.ven_multi_pay_id.debit_amount - self.ven_multi_pay_id.paid_amount
                if diff > 0.0:
                    diff_amt, cre, amount_cur, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(diff,self.currency_id,self.company_id.currency_id)
                    counterpart_aml_dict_inh = self._get_shared_move_line_vals_inherit(diff_amt, cre, amount_cur, move.id)
                    if amount_cur:
                        amount_currency = amount_currency + amount_cur
#                         if self.currency_rate:
#                             current_amt = self.currency_rate * amount_cur
#                         else:
                        rate_id = self.env['res.currency'].search([('id','=',self.ven_multi_pay_id.currency_id.id)])
                        current_amt = (1/rate_id.rate) * amount_cur
                        counterpart_aml_dict_inh.update({'credit': current_amt})
                    aml_obj.create(counterpart_aml_dict_inh)
            # multi customer invoice fully paid
            if credit and self.cus_multi_pay_id:
                diff = self.cus_multi_pay_id.credit_amount - self.cus_multi_pay_id.paid_amount
                if diff > 0.0:
                    diff_amt, cre, amount_cur, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(diff,self.currency_id,self.company_id.currency_id)
                    counterpart_aml_dict_inh = self._get_shared_move_line_vals_cus_inherit(diff_amt, cre, amount_cur, move.id)
                    if amount_cur:
                        amount_currency = amount_currency + amount_cur
#                         if self.currency_rate:
#                             current_amt = self.currency_rate * amount_cur
#                         else:
                        rate_id = self.env['res.currency'].search([('id','=',self.cus_multi_pay_id.currency_id.id)])
                        current_amt = (1/rate_id.rate) * amount_cur
                        counterpart_aml_dict_inh.update({'debit': current_amt})
                    aml_obj.create(counterpart_aml_dict_inh)
                    
            liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
            liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
#             if self.currency_rate:
#                 current_amt = self.currency_rate * liquidity_aml_dict['amount_currency']
#                 if current_amt < 0:
#                     current_amt = current_amt * -1
#                 liquidity_aml_dict.update({'debit': current_amt})
                
            if journal_vals.get('round_up', False):
                liquidity_aml_dict.update({'debit':round(liquidity_aml_dict.get('debit',0)),'credit':round(liquidity_aml_dict.get('credit',0))})
            aml_obj.create(liquidity_aml_dict)
            
#             if self.ven_multi_pay_id:
#                 for loop in self._context['split_payment']:
#                     invoice_id = list(loop.keys())[0]
#                     move_line_invoice_id = self.env['account.move.line'].search([('invoice_id', '=', invoice_id.id), ('reconciled', '=', False), ('credit', '>', 0)])
#                     move_line_payment_id = self.env['account.move.line'].search([('payment_id', '=', self.id), ('reconciled', '=', False), ('debit', '>', 0)])
#                     self.trans_rec_reconcile_payment(move_line_payment_id,move_line_invoice_id)
#             if self.cus_multi_pay_id:
#                 for loop in self._context['split_payment']:
#                     invoice_id = list(loop.keys())[0]
#                     move_line_invoice_id = self.env['account.move.line'].search([('invoice_id', '=', invoice_id.id), ('reconciled', '=', False), ('debit', '>', 0)])
#                     move_line_payment_id = self.env['account.move.line'].search([('payment_id', '=', self.id), ('reconciled', '=', False), ('credit', '>', 0)])
#                     self.trans_rec_reconcile_payment(move_line_payment_id,move_line_invoice_id)
        move.post()
        return move
    
#     @api.multi
#     def trans_rec_reconcile_payment(self,line_to_reconcile,payment_line,writeoff_acc_id=False,writeoff_journal_id=False):
#         return (line_to_reconcile + payment_line).reconcile(writeoff_acc_id, writeoff_journal_id)
