import sys
import os

sys.path.append(os.path.abspath("./communication/out/ice"))

import Ice
import Bank

to_enum = {key: item for key, item in Bank.Currency.__dict__.items() if type(item) is Bank.Currency}

def print_warn(err, end='\n'):
    sys.stderr.write('\x1b[1;33m' + str(err) + '\x1b[0m' + end)

with Ice.initialize(sys.argv) as communicator:
    base = communicator.stringToProxy("AccountManager:default -p 10000")
    manager = Bank.AccountManagerPrx.checkedCast(base)
    if not manager:
        raise RuntimeError("Invalid proxy")
    text = input(">")
    while "quit" not in text:
        words = str.split(text)
        if words[0] in "create":
            out = manager.create(words[1] + words[2], words[3], float(words[4]))
            print("Succesfully created {0} account\nYour password is: {1}".format(out.accountType, out.password))
        elif words[0] in "access":
            access_text = input("access>")
            while "exit" not in access_text:
                try:
                    ctx = {words[1]: words[2]}
                    base = manager.access(words[1], context=ctx)
                    hndl = Bank.PremiumAccountPrx.checkedCast(base)
                    if hndl is None:
                        hndl = Bank.AccountPrx.checkedCast(base)
                    access_words = str.split(access_text)
                    if access_words[0] in "balance":
                        balance = hndl.checkBalance(context=ctx)
                        print("Balance: {0}".format(balance))
                    elif access_words[0] in "loans":
                        loans = hndl.checkLoans(context=ctx)
                        print("Loans: {0}".format(loans))
                    elif access_words[0] in "pay":
                        currency = to_enum[access_words[1]]
                        amount = float(access_words[2])
                        hndl.payInto(currency, amount, context=ctx)
                    elif access_words[0] in "take":
                        currency = to_enum[access_words[1]]
                        amount = float(access_words[2])
                        hndl.takeLoan(currency, amount, context=ctx)
                    elif access_words[0] in "repay":
                        currency = to_enum[access_words[1]]
                        amount = float(access_words[2])
                        hndl.repayLoan(currency, amount, context=ctx)
                    elif access_words[0] in "rates":
                        print(hndl.checkRates(context=ctx))
                except Bank.ForbiddenOperationException as e:
                    print_warn(e)
                except Bank.AuthorisationException as e:
                    print_warn(e)
                except KeyError as e:
                    print_warn("Currency {0} is not supported in this bank".format(e))
                finally:
                    access_text = input("access>")
        text = input(">")