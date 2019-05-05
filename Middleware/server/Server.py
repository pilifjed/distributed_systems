from collections import defaultdict
from random import choices
from functools import wraps
import signal
import string
import sys
import os
import threading

sys.path.append(os.path.abspath("./communication/out/ice"))

import Ice
import Bank

sys.path.append(os.path.abspath("./communication/out/proto"))

import grpc
import Service_pb2_grpc
import Service_pb2

def authorise_premium(fun):
    @wraps(fun)
    def authorisation(self, *args, **kwargs):
        if self.accountType == Bank.AccountType.PREMIUM:
            return fun(self, *args, **kwargs)
        else:
            raise Bank.ForbiddenOperationException
    return authorisation


def authorise_user(fun):
    @wraps(fun)
    def authorisation(self, *args, **kwargs):
        context = args[-1].ctx
        if self.pesel in context:
            if context[self.pesel] in self.password:
                return fun(self, *args, **kwargs)
        raise Bank.AuthorisationException
    return authorisation


currency_rates = {}


class RateSynchroniser(threading.Thread):
    def __init__(self):
        super(RateSynchroniser, self).__init__()

    def run(self):
        channel = grpc.insecure_channel('localhost:50051')
        stub = Service_pb2_grpc.ServiceStub(channel)
        request = Service_pb2.CurrencySubscription(requested=[Service_pb2.PLN, Service_pb2.USD, Service_pb2.EUR])
        for response in stub.subscribeCurrency(request):
            currency = Bank.Currency.valueOf(response.currency)
            currency_rates[currency] = response.rate
            print(currency, response.rate)


class Account(Bank.Account):
    def __init__(self, name: str, pesel: str, monthlyIncome: float, password: str):
        self.name = name
        self.pesel = pesel
        self.monthly_income = monthlyIncome
        self.balance = defaultdict(lambda: 0)
        self.loan = defaultdict(lambda: 0)
        self.password = password

    @authorise_user
    def checkBalance(self, current):
        return self.balance

    @authorise_user
    def checkRates(self, current):
        return currency_rates

    @authorise_user
    def payInto(self, currency, amount, current):
        self.balance[currency] += amount


class PremiumAccount(Account, Bank.PremiumAccount):

    @authorise_user
    def checkLoans(self, current):
        return self.loan

    @authorise_user
    def takeLoan(self, currency, amount, current):
        self.loan[currency] -= amount
        self.balance[currency] += amount

    @authorise_user
    def repayLoan(self, currency, amount, current):
        balance_remainder = self.balance[currency] - amount
        if balance_remainder >= 0:
            self.balance[currency] = balance_remainder
            loan_remainder = self.loan[currency] + amount
            if loan_remainder < 0:
                self.loan[currency] = loan_remainder
            else:
                self.loan.pop(currency)
                self.balance[currency] += loan_remainder
        else:
            print("Insufficient funds")


class AccountManager(Bank.AccountManager):

    def create(self, name: str, pesel: str, monthlyIncome: float, current):
        accountType = Bank.AccountType.STANDARD if monthlyIncome <= 1000 else Bank.AccountType.PREMIUM
        password = ''.join(choices(string.digits + string.ascii_lowercase, k=4))
        if accountType == Bank.AccountType.STANDARD:
            account = Account(name, pesel, monthlyIncome, password)
        else:
            account = PremiumAccount(name, pesel, monthlyIncome, password)
        current.adapter.add(account, Ice.stringToIdentity(str(pesel)))
        current.adapter.activate()
        return Bank.Confirmation(accountType, password)

    def access(self, pesel, current):
        return current.adapter.getCommunicator().stringToProxy(pesel + ":default -p 10000")


with Ice.initialize(sys.argv) as communicator:
    synchroniser = RateSynchroniser()
    synchroniser.start()
    signal.signal(signal.SIGINT, lambda signum, frame: synchroniser.stop())
    adapter = communicator.createObjectAdapterWithEndpoints("AccountManagerAdapter", "default -p 10000")
    adapter.add(AccountManager(), communicator.stringToIdentity("AccountManager"))
    adapter.activate()
    communicator.waitForShutdown()