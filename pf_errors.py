class ProjFinError(Exception):
    def __init__(self,value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class BadDateError(ProjFinError):
    pass

class BadEscalatorTypeError(ProjFinError):
    pass

class BadScalingMethodError(ProjFinError):
    pass

class NoScalingExponentError(ProjFinError):
    pass

class BadCapitalCostInput(ProjFinError):
    pass

class BadCapitalDepreciationInput(ProjFinError):
    pass

class BadCapitalTICInput(ProjFinError):
    pass

class QuoteBasisBadInput(ProjFinError):
    pass

class BadValue(ProjFinError):
    pass

class MissingInfoError(ProjFinError):
    pass

class BadCapitalPaymentInput(ProjFinError):
    pass

class BadCapitalPaymentTerms(ProjFinError):
    pass

class BadDirectCapitalItem(ProjFinError):
    pass

class BadIndirectCapitalItem(ProjFinError):
    pass

class BadScaleInput(ProjFinError):
    pass

class BadScalerInitialization(ProjFinError):
    pass

class BadDebtInput(ProjFinError):
    pass

class UnderspecifiedError(MissingInfoError):
    pass

class BadFrequencyError(ProjFinError):
    pass

class BadStartupDiscountError(ProjFinError):
    pass

class BadFixedExpenseInput(ProjFinError):
    pass

class BadFixedExpenseItem(ProjFinError):
    pass

class BadFixedCostType(BadFixedExpenseInput):
    pass

class BadProductInput(ProjFinError):
    pass

class BadProductionInput(ProjFinError):
    pass

class BadProductionItem(ProjFinError):
    pass

class BadVariableExpenseInput(ProjFinError):
    pass

class BadScheduleDateError(ProjFinError):
    pass

class BadVariableExpenseType(ProjFinError):
    pass

class BadVariableExpenseItem(ProjFinError):
    pass

class BadTaxInputError(ProjFinError):
    pass

class BadTaxCreditInput(ProjFinError):
    pass

class TaxUnderdefinedError(ProjFinError):
    pass

class TaxManagerError(ProjFinError):
    pass
