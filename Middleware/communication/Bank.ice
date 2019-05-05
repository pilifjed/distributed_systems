module Bank
{
    enum Currency {EUR, USD, PLN};
    enum AccountType {STANDARD, PREMIUM};
    dictionary<Currency, double> CurrencyAmount;

    struct Confirmation
    {
        AccountType accountType;
        string password;
    };

    exception AuthorisationException
    {
        string reason = "Incorrect password or account does not exist.";
    };

    exception ForbiddenOperationException
    {
        string reason = "Loan taking is the feature available only for premium users.";
    };

    interface Account
    {
        CurrencyAmount checkBalance() throws AuthorisationException;
        CurrencyAmount checkRates() throws AuthorisationException;
        void payInto(Currency currency, double amount) throws AuthorisationException;
    };

    interface PremiumAccount extends Account
    {
        CurrencyAmount checkLoans() throws AuthorisationException;
        void takeLoan(Currency currency, double amount) throws AuthorisationException;
        void repayLoan(Currency currency, double amount) throws AuthorisationException;
    };

    interface AccountManager
    {
        Confirmation create(string name, string pesel, double monthlyIncome);
        Object* access(string pesel);
    };
}