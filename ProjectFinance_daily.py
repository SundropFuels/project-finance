import numpy as np
import unitConversion as uc
from cp_tools import *
import scipy.optimize as spo
import csv
from collections import OrderedDict
from lxml import etree
import UnitValues as uv
import company_tools as ct
import copy
import pandas as pd
import datetime as dt
import pandas.tseries.offsets as offs
from pandas.tseries.offsets import DateOffset
from pf_errors import *
import dataFrame_pd as df
from collections import deque


class ProjAnalyzer:
    """Base class for analyzing a single project"""
    def __init__(self):
       pass #Doesn't do anything yet...

class CapitalProject:
    """Main class that holds a single capital project"""
    def __init__(self):
        #if not isinstance(financial_parameters, FinancialParameters):
        #    raise ProjFinError, "financial_parameters MUST be a FinancialParameters object"

        #if financial_parameters.is_incomplete():
        #    raise ProjFinError, "The financial parameters MUST be completely specified to create the CapitalProject -- don't ask me why"


        #Key data members:
        #self.cf_sheet		:	Cashflow dataframe, includes all income statement objects on annual basis
        #self.fin_param		:	Financial parameters for the project simulation
        #self.capex		:	Capital costs object for the project simulation
        #self.fixed_costs	:	Fixed costs object for the project simulation
        #self.variable_costs	:	Variable costs object for the project simulation
        #self.debt		:	Debt financing vehicles for the project; any cash not in by loans is assumed to be equity
        #self.check_bits	:	These ensure that things are done in the proper order -- will eventually used only internally for QC/QA

        self.capex = None
        self.fixed_costs = None
        self.variable_costs = None
        self.debt = None

        self.fin_param = None
        self.check_bits = [False, False, False, False, False]	#Fin_param, capex, fixed, variable, debt all MUST be set before analysis can proceed

    def setFinancialParameters(self, financial_parameters):
        if not isinstance(financial_parameters, FinancialParameters):
            raise ProjFinError, "financial_parameters MUST be a FinancialParameters object"

        #Doing it this way allows one to save those parameters that are set, but not to run the analysis
        self.fin_param = financial_parameters

        if financial_parameters.is_incomplete():
            return

        else:
            self._initialize_cash_sheet()
            self.check_bits[0] = True


    def _initialize_cash_sheet(self):
        #The main cash sheet is performed daily.  I will write functions to do annual, quarterly, and monthly roll-ups.
        ip = self.fin_param['Initial_period']				#This must be a datetime object for this to work -- this assignment may be unnecessary
        dates = pd.date_range(ip, end = ip + self.fin_param['Analysis_period']*DateOffset(years=1), freq = 'D')
        count = {'Period':np.arange(len(dates))}
        self.cf_sheet = df.DataFrame(data = count, index = dates)

    def assembleFinancials(self, price):
        """Put together the financials for a given selling price of the product"""
        #Currently, price is in the format (price, mode) where price is the price in the first year, and mode is the mode of inflation -- this stuff should be coded into financial parameters!
        if False in self.check_bits:
            raise ProjFinError, "Not all of the inputs (capex, etc.) have been set yet"        
        
        self._calcCapitalCosts()
        self.setAnnualOutput()
        self.setPrices(price[0], price[1])
        self.setRevenue()
        self._calcVariableCosts()
        self._calcFixedCosts()
        self._calcDebt()
        self.setOtherFinancials()
        

    def rollUpMonthly(self):
        """Rolls up current sheet into monthly totals of each column -- also, calculates net taxes and puts credits into reserve (FUTURE)"""
        #just resample
        self.monthly_cash_sheet = self.cf_sheet.resample('M', how = 'sum')            
        

    def rollUpAnnual(self):
        """Rolls up current sheet into annual totals of each column"""
        #resample
        self.annual_cash_sheet = self.cf_sheet.resample('A', how = 'sum')
            

    def printFinancials(self, filename = None):
        """Print the financials to a file, or to the screen"""

        cols = ('Production','Sales','Salvage','Revenue','Variable_costs','Fixed_costs','Decommissioning_costs','Cost_of_sales','EBITDA','Interest','Depreciation','Taxable_income','Taxes','After-tax_income','Capital_expenditures','Principal_payments','Net_cash_flow')
        order = ['Category']
        order.extend(self.cf_sheet.index)
        

        if filename is not None:
            try:
                writer = csv.DictWriter(open(filename, 'wb'),order, extrasaction='ignore')
                #write the headers in the CSV file -- I want to do some formatting, so I can't just use csv.writeheader()
                headers = {}
                for year in order:
                    if year == 'Category':
                        new_name = ""
                    else:
                        new_name = year
                    headers[year] = new_name

                writer.writerow(headers)

                #write the actual data
                for col in cols:
                    row = self.cf_sheet.get_col(col)
                    row['Category'] = col
                    
                    writer.writerow(row)

                



            except IOError:
                raise ProjFinError, "Well, shit.  You tried to open a file that you aren't allowed to.  Don't do that."


    ###FIX THESE###
    def calcIRR(self):
        """Returns the IRR for the given cash flow of the project"""
        #Find the root of the NPV function
        return spo.brentq(self.calcNPV,0.001,1.0)
    
    def calcNPV(self, rate):
        """Returns the NPV for the given cash flow of the project"""
        
        return sum(self.cf_sheet['Net_cash_flow']/np.power(1+rate,self.cf_sheet['Period']))
    ###END FIX###

    def setPrices(self, base_price, mode, inflation_dict = None):
        """Creates the price inflation schedule we expect to see"""
        #INCOMPLETE!
        if mode == "fixed":
            #create the daily periodic inflation rate from the indicated annual rate
            daily_rate = np.power(1+self.fin_param['Inflation_rate'], 1.0/365.0) - 1.0  #explictly ignores leap years (which should have a slightly higher inflation price)
            print daily_rate
            self.cf_sheet['Sales_price'] = np.ones(len(self.cf_sheet))*base_price*np.power(1+daily_rate,self.cf_sheet['Period'])
            

        elif mode == "pre-set":
            #Inflation_dict should look like {year:year-over-year inflation} -- this must be calculated sequentially -- pass for now
            pass

        else:
            raise ProjFinError, "%s is not a recognized inflation mode" % mode

    def setAnnualOutput(self):
        """Creates the annual output column for production level, adjusted for startup considerations"""
        output = df.DataFrame(np.zeros(len(self.cf_sheet)), index = self.cf_sheet.index)
        ann_out = self.fin_param['Cap_factor'] * self.fin_param['Design_cap'].value
        daily_out = ann_out/365.0		
        end_period = self.fin_param['Startup_period'] + self.fin_param['Plant_life']*DateOffset(years=1)
        output[self.fin_param['Startup_period']:self.fin_param['Startup_period']+DateOffset(years=1)] = self.fin_param['Startup_revenue_breakdown']*daily_out
        output[self.fin_param['Startup_period']+DateOffset(years=1):end_period] = daily_out

        
        self.cf_sheet['Production'] = output
        



    def setRevenue(self):
        """Creates the sales, salvage, and revenues columns"""
        self.cf_sheet['Sales'] = self.cf_sheet['Production'] * self.cf_sheet['Sales_price']
        self.cf_sheet['Salvage'] = np.zeros(len(self.cf_sheet))
        
        try:
            self.cf_sheet['Salvage'][self.fin_param['Startup_period']+self.fin_param['Plant_life']*DateOffset(years=1)] = self.fin_param['Salvage_value']
        except KeyError:
            pass
        
        
        self.cf_sheet['Revenue'] = self.cf_sheet['Sales'] + self.cf_sheet['Salvage']

    def setCapitalCosts(self, capex):
        """Creates the capital cost data member.  Calculates the startup year.  Creates the capital expenditure and depreciation columns."""
        if not isinstance(capex, CapitalCosts):
            raise ProjFinError, "'capex' MUST be an instance of CapitalCosts"
        self.capex = capex
        self.check_bits[1] = True

    def _calcCapitalCosts(self):

        if self.capex is None:
            raise ProjFinError, "You must set the capital costs before you can calculate them"
        
        self.fin_param['Startup_period'] = self.capex.build_capex_schedule(self.fin_param['Initial_period'], self.fin_param['Capital_expense_breakdown'])
        
        self.capex.build_depreciation_schedule(starting_period = self.fin_param['Startup_period'], length = self.fin_param['Depreciation_length'], method = self.fin_param['Depreciation_type'])
        
        #Set up the columns in the cashflow sheet to be the proper length
        self.cf_sheet['Capital_expenditures'] = np.zeros(len(self.cf_sheet))
        self.cf_sheet['Depreciation'] = np.zeros(len(self.cf_sheet))
        
        #Fill the columns by year matching
        self.cf_sheet['Capital_expenditures'] = (self.cf_sheet['Capital_expenditures'] + self.capex.capex_schedule['capex']).fillna(0)
        self.cf_sheet['Depreciation'] = (self.cf_sheet['Depreciation'] + self.capex.depreciation_schedule['depreciation']).fillna(0)
            
          

    def setVariableCosts(self, VC):
        if not isinstance(VC, VariableCosts):
            raise ProjFinError, "VC must be a VariableCosts object"

        self.variable_costs = VC
        self.check_bits[3] = True

    def _calcVariableCosts(self):
        if self.variable_costs is None:
            raise ProjFinError, "You must set the variable costs before you can calculate them"
        daily_rate = np.power(1+self.fin_param['Inflation_rate'], 1.0/365.0) - 1.0
        self.cf_sheet['Variable_costs'] = np.ones(len(self.cf_sheet))*self.variable_costs.c_total_VC(self.fin_param['Design_cap'].units)*self.cf_sheet['Production']*np.power(1+daily_rate,self.cf_sheet['Period'])

    def setFixedCosts(self, FC):
        if not isinstance(FC, FixedCosts):
            raise ProjFinError, "FC must be a FixedCosts object"
        self.fixed_costs = FC
        self.check_bits[2] = True

    def _calcFixedCosts(self):
        if self.fixed_costs is None:
            raise ProjFinError, "You must set the fixed costs before you can calculate them"

        total = self.fixed_costs.c_total_fixed_costs()/365		#The fixed cost settings are on an annual basis
        mask = df.DataFrame(data = np.zeros(len(self.cf_sheet)), index = self.cf_sheet.index)
        #Could easily generalize for a startup length here
        mask[self.fin_param['Startup_period']:self.fin_param['Startup_period']+DateOffset(years=1)] = self.fin_param['Startup_fixed_cost_breakdown']
        mask[self.fin_param['Startup_period']+DateOffset(years=1):] = 1.0
  

        daily_rate = np.power(1+self.fin_param['Inflation_rate'], 1.0/365.0) - 1.0
        self.cf_sheet['Fixed_costs'] = np.ones(len(self.cf_sheet))*total*np.power(1+daily_rate,self.cf_sheet['Period'])*mask

    def setDebt(self, debt_pf):
        if not isinstance(debt_pf, DebtPortfolio):
            raise ProjFinError, "debt_pf must be a DebtPortfolio object"

        self.debt = debt_pf
        self.check_bits[4] = True

    def _calcDebt(self):
        """Calculate the debt portion of the spreadsheet"""
        if self.debt is None:
            raise ProjFinError, "You must set the debt portfolio before you can calculate the debt"

        debt_cols = self.debt.CIP(self.cf_sheet.index)
        self.cf_sheet['Loan_proceeds'] = debt_cols['cash_proceeds']
        self.cf_sheet['Interest'] = debt_cols['interest']
        self.cf_sheet['Principal_payments'] = debt_cols['principal_payment']

        
        
    def setOtherFinancials(self):
        """Sets the decommissioning cost, and calculates EBITDA, net Income, taxes, and cash flow"""
        #Need to check order bits here
        self.cf_sheet['Decommissioning_costs'] = np.zeros(len(self.cf_sheet))
        try:
            self.cf_sheet.loc[self.fin_param['Startup_period']+self.fin_param['Plant_life']*DateOffset(years=1)]['Decommissioning_costs'] = self.fin_param['Decommissioning_cost']
        except KeyError:
            pass

        self.cf_sheet['Cost_of_sales'] = self.cf_sheet['Fixed_costs'] + self.cf_sheet['Variable_costs'] + self.cf_sheet['Decommissioning_costs']
        self.cf_sheet['EBITDA'] = self.cf_sheet['Revenue'] - self.cf_sheet['Cost_of_sales']
        self.cf_sheet['Pre-depreciation_income'] = self.cf_sheet['EBITDA'] - self.cf_sheet['Interest']
        self.cf_sheet['Taxable_income'] = self.cf_sheet['Pre-depreciation_income'] - self.cf_sheet['Depreciation']
        #!!!#Taxes are wrong, wrong, wrong.  At the very least, need to make tax zero in negative revenue years.  Next would be to add loss carry-over.  Finally would be to create a reserve of credits and carryovers and correctly apply these.
        self.cf_sheet['Taxes'] = self.cf_sheet['Taxable_income'] * (self.fin_param['State_tax_rate'] + self.fin_param['Federal_tax_rate'])   
        self.cf_sheet['After-tax_income'] = self.cf_sheet['Taxable_income'] - self.cf_sheet['Taxes']
        self.cf_sheet['Net_cash_flow'] = self.cf_sheet['After-tax_income'] - self.cf_sheet['Capital_expenditures'] - self.cf_sheet['Principal_payments'] + self.cf_sheet['Loan_proceeds'] + self.cf_sheet['Depreciation']


    def outputCashFlowSheet(self, filename = None):
        """Writes the cash flow sheet (sort of a combo of an income statement and a cash flow statement), either to the screen or to a file"""
        pass


    def autodebt(self, debt_fraction, rate, term, mode = "loans"):
        """Automatically populate the debt portfolio for a given debt fraction; can use loans or bonds, but only loans implemented; rate is a scalar, but could be a vector later"""
        loans = []
        if not self.check_bits[1] or not self.check_bits[0]:
            raise projFinError, "Autodebt will not work if the total capex and financial parameters are not set and calculated"

        #get the total capital cost
        
        TIC = self.capex.c_total_capital()
        for year in range(self.fin_param['Initial_year'], self.fin_param['Initial_year'] + len(self.fin_param['Capital_expense_breakdown'])):
            principal = TIC*debt_fraction*self.fin_param['Capital_expense_breakdown'][counter]
            for existing_loan in loans:
                #the way this is written, the first year's interest is not included...I should fix this in the future
                principal += existing_loan.schedule.get_row(year)['interest']*debt_fraction+existing_loan.schedule.get_row(year)['principal_payment']
            loan = Loan(name = 'loan_%s' % counter + 1, principal = principal, term = term, rate = rate, pmt_freq = 2, strt_year = year)
            loan.generate_schedule()
            loans.append(loan)
            
        #we should borrow money to cover the startup costs as well, but this requires fixed and variable costs to be set -- it is a trickier business which we'll leave out for now
        #to do this, we need to calculate the project WITHOUT debt, then recalculate it with the new debt -- will add later
        dp = DebtPortfolio()
        for loan in loans:
            dp.add_loan(loan)

        self.set_debt(dp)
        
        



    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.fin_param == other.fin_param and self.capex == other.capex and self.fixed_costs == other.fixed_costs and self.variable_costs == other.variable_costs and self.debt == other.debt

    def __ne__(self, other):
        return not self.__eq__(other)

    def scale(self, new_scale):
        #This returns a new capital project, scaled up from the old capital project
        new_capproj = CapitalProject()
        #scale financial parameters
        new_capproj.setFinancialParameters(self.fin_param)
        new_capproj.fin_param['Design_cap'] = new_scale
        #scale capex
        self.capex.set_base_scale(self.fin_param['Design_cap'])
        new_capproj.setCapex(self.capex.scale(new_scale))
        #scale fixed_costs
        self.fixed_costs.set_base_scale(self.fin_param['Design_cap'])
        new_capproj.setFixedCosts(self.fixed_costs.scale(new_scale))
        #set the variable costs
        new_capproj.setVariableCosts(self.variable_costs)
        #scale the debt portfolio
        self.debt.set_base_scale(self.fin_param['Design_cap'])
        new_capproj.setDebt(self.debt.scale(new_scale))

        return new_capproj

        #I am going to need a function that shifts the start years -- this will affect loans and the financial parameters


class FinancialParameters:
    """This is really just a kind of dictionary that is specially designed to hold important project finance parameters"""

    key_list = ['Initial_period', 'Startup_period','Target_IRR', 'Depreciation_type', 'Depreciation_length', 'Analysis_period', 'Plant_life', 'Inflation_rate', 'State_tax_rate', 'Federal_tax_rate','Design_cap','Cap_factor','Capital_expense_breakdown','Startup_revenue_breakdown','Startup_fixed_cost_breakdown','Startup_variable_cost_breakdown','Salvage_value','Decommissioning_cost']
    type_dict = {'Initial_period':dt.datetime, 'Target_IRR':float, 'Depreciation_length':int,'Analysis_period':int, 'Plant_life':int,'Inflation_rate':float,'State_tax_rate':float, 'Federal_tax_rate':float, 'Design_cap':float, 'Cap_factor':float,'Startup_revenue_breakdown':float,'Startup_fixed_cost_breakdown':float, 'Startup_variable_cost_breakdown':float, 'Salvage_value':float, 'Decommissioning_cost':float}
    


    def __init__(self):
        self.params = {}
        for key in FinancialParameters.key_list:
            self.params[key] = None

    def __getitem__(self, key):
        if key not in FinancialParameters.key_list:
            raise ProjFinError, "%s is not a valid financial parameter" % key
        return self.params[key]

    def __setitem__(self, key, value):
        if key not in FinancialParameters.key_list:
            raise ProjFinError, "%s is not a valid financial parameter" % key
        #Unless the key is for one of the list values, then make sure it is a list of numeric values!#!
        if not is_numeric(value) and key not in ['Capital_expense_breakdown','Design_cap','Depreciation_type', 'Initial_period', 'Startup_period'] and value is not None:
            raise ProjFinError, "The specific value (%s) is not numeric" % value

        if key == 'Capital_expense_breakdown' and not (isinstance(value,list) or isinstance(value,dict) or isinstance(value,df.DataFrame)) and value is not None:
            raise ProjFinError, "The capital expense breakdown is not a recognized type"

        elif key == 'Design_cap' and value is not None:
            if not (isinstance(value,uv.UnitVal)):
                raise ProjFinError, "The design capacity must be a UnitVal object"
        
        elif key in ['Initial_period', 'Startup_period'] and value is not None:
            if not (isinstance(value, dt.datetime)):
                raise ProjFinError, "All periods must be string objects (or datetime objects, not yet implemented"

        elif key == 'Depreciation_type' and not isinstance(value, str) and value is not None:
            raise ProjFinError, "The depreciation type must be a string"

        self.params[key] = value
    

    def is_incomplete(self):
        """Checks if all of the items have been specified before moving forward"""
        flag = False
        for k,v in self.params.items():
            if v is None and k is not 'Startup_period':
                flag = True
        return flag
    
    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.params == other.params

    def __ne__(self, other):
        return not self.__eq__(other)

class Scaler:
    """This is the abstract implementation of a helper class for scaling prices from one size to another"""

    def __init__(self):
        self.factor = 1.0

    def __eq__(self, other):
        if not isinstance(other, Scaler):
            raise TypeError, "Cannot compare %s to Scaler" % type(other)
        return self.__class__ == other.__class__	#for the scaler, only the sub-class matters for most of these; will be overridden and checked on parameters for subclasses

        
    def scale(self, base_scale, new_scale, base_price):
        """Abstract implementation simply does value checking"""
        if not isinstance(base_scale, uv.UnitVal):
	    raise BadScaleInput, "Base scale is of type %s; must be of type UnitVal" % type(base_scale)
        if not isinstance(new_scale, uv.UnitVal):
            raise BadScaleInput, "New scale is of type %s; must be of type UnitVal" % type(new_scale)
	try:
	    base_scale.value/1.5
            if base_scale.value <= 0.0:
                raise BadScaleInput, "Base scale must be positive"

	except TypeError:
	    raise BadScaleInput, "Base scale must be numeric"

        try:
            new_scale.value/1.5
            if new_scale.value <= 0.0:
                raise BadScaleInput, "New scale must be positive"

        except TypeError:
            raise BadScaleInput, "New scale must be numeric"

        try:
            base_price/1.5
            if base_price < 0.0:
                raise BadScaleInput, "The base price must be positive"
        except TypeError:
            raise BadScaleInput, "The base price must be numeric"


        try:
            self.factor = (new_scale/base_scale).value
            self.base_price = base_price
        except ValueError:
            raise BadScaleInput, "The units between the base scale (%s) and the new scale (%s) are not compatible." % (base_scale.units, new_scale.units)

class LinearScaler(Scaler):
    """Scales prices by the simple ratio of sizes"""
    def scale(self, **kwargs):
        """Scale the price from base_size to new_size linearly"""
        Scaler.scale(self, **kwargs)
        return self.base_price * self.factor

class ExponentialScaler(Scaler):

    def __init__(self, exponent = 1.0):
        """Scales prices by the ratio of sizes to the specified exponent"""
        Scaler.__init__(self)
        try:
            exponent/1.5
            if exponent < 0.0:
                raise BadScalerInitialization, "Exponent must be non-negative"


        except TypeError:
            raise BadScalerInitialization, "Exponent must be numeric"

        self.exponent = exponent

    def __eq__(self, other):
        if not isinstance(other, ExponentialScaler):
	    raise TypeError, "Cannot compare %s to ExponentialScaler" % type(other)
        return Scaler.__eq__(self, other) and self.exponent == other.exponent


    def scale(self, **kwargs):
	"""Scale the price from base_size to new_size exponentially"""
        Scaler.scale(self, **kwargs)
        return self.base_price * (self.factor ** self.exponent)

class NoneScaler(Scaler):
    """Scaler that always returns the base_price"""
    def scale(self, **kwargs):
        """Scale the price from the base_price to the new_price by returning the base_price"""
        Scaler.scale(self, **kwargs)
        return self.base_price

class SteppedScaler(Scaler):
    """Scaler that uses a piecewise function on price ratio to give the scaling ratio"""
    def __init__(self, steps):
        if not isinstance(steps, dict):
            raise BadScalerInitialization, "steps must be a dictionary"
        for val in steps.values():
            try:
                val/1.5
                if val <= 0.0:
                    raise BadScalerInitialization, "All of the scaling steps must be positive"
            except TypeError:
                raise BadScalerInitialization, "All of the scaling steps must be numeric"

        for key in steps:
            try:
                key/1.5
                if np.isfinite(key) and key <= 0.0:
                    raise BadScalerInitialization, "All of the scaling breakpoints must be positive"

            except TypeError:
                raise BadScalerInitialization, "All of the breakpoints must be numeric"

        Scaler.__init__(self)
        self.steps = steps

    def __eq__(self, other):
        if not isinstance(other, SteppedScaler):
            raise TypeError, "Cannot compare %s to SteppedScaler" % type(other)
        return Scaler.__eq__(self, other) and self.steps == other.steps

    def scale(self, **kwargs):
        """Scales according the the given piecewise ratio"""
        Scaler.scale(self, **kwargs)
        sorted_keys = sorted(self.steps)
        #find the right position
        N = 0
        while N < len(sorted_keys) and self.factor >= sorted_keys[N]:
            N += 1
        return self.base_price * self.steps[sorted_keys[N-1]]

class QuoteBasis(object):
    """This is the class for holding quotation information that a capital item will require to scale"""
    def __init__(self, base_price = None, date = None, size_basis = None, source = None, scaler = NoneScaler(), **kwargs):
        
        self.base_price = base_price
        self.date = date
        self.size_basis = size_basis 
	self.source = source
        self.scaler = scaler
    
    @property
    def base_price(self):
        return self._base_price

    @base_price.setter
    def base_price(self, v):
        if v is None:
            raise QuoteBasisBadInput, "QuoteBasis is underspecified"
        try:
            if v <= 0:
                raise QuoteBasisBadInput, "the price must be positive"
            b = 1.0/v
        except TypeError:
            raise QuoteBasisBadInput, "price must be numeric"

        self._base_price = v

    @property
    def date(self):
        return self._date
    @date.setter
    def date(self, v):
        if v is None:
           raise QuoteBasisBadInput, "QuoteBasis is underspecified"
        if not isinstance(v, dt.datetime):
           raise QuoteBasisBadInput, "date must be an instance of datetime.datetime, got %s " % type(v)
	self._date = v    

    @property
    def size_basis(self):
        return self._size_basis

    @size_basis.setter
    def size_basis(self, v):
        if v is None:
            raise QuoteBasisBadInput, "QuoteBasis is underspecified"
        if not isinstance(v, uv.UnitVal):
            raise QuoteBasisBadInput, "The size basis must currently be a UnitVal"
        self._size_basis = v

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, v):
        if v is not None and not isinstance(v, basestring):
            raise QuoteBasisBadInput, "source must be a string"
        self._source = v

    @property
    def scaler(self):
        return self._scaler

    @scaler.setter
    def scaler(self, v):
        if not isinstance(v, Scaler):
            raise BadScalingMethodError, "The provided scaler is of type %s, must be a sub-class of Scaler" % type(scaler)
	self._scaler = v
  
    def __eq__(self, other):
        if not isinstance(other, QuoteBasis):
            raise TypeError, "Cannot compare %s to QuoteBasis" % type(other)
        val = True
        l = ['base_price', 'date', 'size_basis', 'source', 'scaler']
        for att in l:
            val = val and (getattr(self, att) == getattr(other,att))
        return val

    def scale(self, new_scale=None):
        """Scales the existing cost to a new basis and returns the value"""
        if new_scale is None:
            raise QuoteBasisBadInput, "A new scale to price to is missing"
        if not isinstance(new_scale, uv.UnitVal):				###!!!### This should actually be of type Production, or similar -- need to keep interface the same
            raise QuoteBasisBadInput, "The new scale must be a unit value"
        try: 
             new_price = self.scaler.scale(base_price = self.base_price, base_scale = self.size_basis, new_scale = new_scale)       
             return self._returned_scaled_copy(new_price)

        except BadScaleInput:
            raise QuoteBasisBadInput, "There was an invalid parameter passed to the scaler" % method

    def _returned_scaled_copy(self, new_price):
        return QuoteBasis(base_price = new_price, date = self.date, size_basis = self.size_basis, scaler = self.scaler, source = "%s_scaled" % source)

    def cost(self):

        return self.base_price

class ProductQuoteBasis(QuoteBasis):
    """Quote basis for a given production product"""
    pass		#nothing special to add for this one

class CapitalExpenseQuoteBasis(QuoteBasis):
    """This is the class for holding quotation information that a capital item will require to scale"""
    def __init__(self, installation_model = None, lead_time = None, **kwargs):
        
        
	QuoteBasis.__init__(self, **kwargs)
   
        self.install_model = installation_model
        self.lead_time = lead_time

    @property
    def install_model(self):
        return self._install_model

    @install_model.setter
    def install_model(self, v):
        if v is not None and not isinstance(v, InstallModel):
            raise QuoteBasisBadInput, "The installation model must be an InstallModel object"
	self._install_model = v

    @property
    def lead_time(self):
        return self._lead_time

    @lead_time.setter
    def lead_time(self, v):
        if v is not None and not isinstance(v, dt.timedelta):
            raise QuoteBasisBadInput, "The lead time must be a timedelta"

        self._lead_time = v



    def __eq__(self, other):
        if not isinstance(other, QuoteBasis):
            raise TypeError, "Cannot compare %s to QuoteBasis" % type(other)
        val = True
        l = ['install_model', 'lead_time']
        for att in l:
            val = val and (getattr(self, att) == getattr(other,att))
        return val and QuoteBasis.__eq__(self, other)

    def _return_scaled_copy(self, new_price):
	"""Returns a scaled copy of itself, allowing delegation to the appropriate classes"""
	return CapitalExpenseQuoteBasis(base_price = new_price, date = self.date, size_basis = self.size_basis, scaler = self.scaler, source = "%s_scaled" % source, install_model = self.installation_model, lead_time = self.lead_time)


    def cost(self):
        if self.install_model is None:
            print "Warning: No install model specified for this quote -- returning base cost"
            return self.base_price

        else:
            return self.install_model.calc_installed_cost(self.base_price)

    
class IndirectCapitalExpenseQuoteBasis(QuoteBasis):

    def __init__(self, method = None, **kwargs):
        
	QuoteBasis.__init__(self, **kwargs)
      
        
        self.method = method

	for kw in kwargs:
            setattr(self, kw, kwargs[kw])

    @property
    def method(self):
        return self._method

    @method.setter
    def method(self, v):
        methods = ['fixed', 'fractional']
        if v not in methods:
            raise QuoteBasisBadInput, "%s is not a valid method" % v
        self._method = v

    def cost(self):
        return getattr(self, "_calc_installed_cost_%s" % self.method)()

    def _calc_installed_cost_fixed(self):
        return self.base_price

    def _calc_installed_cost_fractional(self):
        return self.base_price*self.fraction
    
                   
class FixedExpenseQuoteBasis(QuoteBasis):



    def __init__(self, freq = None, **kwargs):
        self.freq = freq
	QuoteBasis.__init__(self, **kwargs)

    @property
    def freq(self):
	return self._freq

    @freq.setter
    def freq(self, v):
        freqs = ['D','M','A']			#add the entire list of acceptable pandas frequencies

	if v not in freqs:
	    raise BadFrequencyError, "The given frequency (%s) is not accepted in this application" % v
        self._freq = v

class VariableExpenseQuoteBasis(QuoteBasis):
    """Quote Basis for variable expense objects"""
    pass

	
class InstallModel:
    """Class to hold models for installed cost"""
    def __init__(self):
        pass

    def calc_installed_cost(self):
        pass

    def __eq__(self, other):
        if not isinstance(other, InstallModel):
            raise TypeError, "Cannot compare %s to InstallModel" % type(other)

class FactoredInstallModel(InstallModel):
    def __init__(self, factor):
        self.factor = factor

    def calc_installed_cost(self, base_cost):
        return self.factor * base_cost

    def __eq__(self, other):
        InstallModel.__eq__(self, other)
        return self.factor == other.factor

class FixedInstallModel(InstallModel):
    def __init__(self, fixed_amt):
        self.fixed = fixed_amt

    def calc_installed_cost(self, base_cost):
        return self.fixed + base_cost

    def __eq__(self, other):
        InstallModel.__eq__(self, other)
        return self.fixed == other.fixed


class Escalator:
    """The cost escalation class.  It takes an input date and escalates to a future date based on a variety of subclasses"""

    def __init__(self):
        self.factor = 1.0			#When it comes down to it, all escalators increase their underlying values by a given factor

    def escalate(self, basis_date, new_date):
        #do checking on the basis date and the new date
        #if not isinstance(basis_date, dt.datetime) or not isinstance(new_date, dt.datetime):
        #    raise BadDateError, "The basis date and the new date both need to be of class datetime.datetime"

        #test for validity of cost
	"""
        try:
            if cost < 0:
                raise BadValue, "The cost must be a non-negative number"
            if cost != 0:
                a = 23.0/cost
        except TypeError:
            raise BadValue, "The cost must be numeric"
	"""

        return self.factor #OK, I just broke a lot of shit!

class NoEscalationEscalator(Escalator):
    """Scales to a constant value"""
    def escalate(self, **kwargs):
	#need to make sure we have all of the days
	if 'new_date' in kwargs:
	    try:
                days = kwargs['new_date'] - kwargs['basis_date']
	    except TypeError:
                raise BadDateError, "A bad date type has been passed"
	    if isinstance(days, dt.timedelta):
		days = np.timedelta64(days)
            n = days/np.timedelta64(1,'D')
	    self.factor = 1**n

	else:
            self.factor = 1.0
        return Escalator.escalate(self, **kwargs)    


class InflationRateEscalator(Escalator):
    """Uses a fixed inflation rate (annual, effective) to determine the final cost"""
    def __init__(self, rate = None):
        Escalator.__init__(self)
        self.rate = rate

    def escalate(self, **kwargs):

        try:
	    c = 1/self.rate
            if self.rate < 0:
                raise BadValue, "The rate must be positive"
            dpr = np.power(1+self.rate, 1/365.0)-1
	    
	    try:
                days = kwargs['new_date'] - kwargs['basis_date']
	    except TypeError:
	        raise BadDateError, "The dates passed are not of an acceptable type"
            if isinstance(days, dt.timedelta):
                days = np.timedelta64(days)		#cast this up to allow the necessary division
            #n = (kwargs['new_date']-kwargs['basis_date']).days	#number of days between intervening periods
            n = days/np.timedelta64(1,'D')
            self.factor = (1+dpr)**n
            return Escalator.escalate(self, **kwargs)
        except KeyError:
            raise MissingInfoError, "We are missing some data from the escalate function"
        except TypeError or ValueError:
            raise BadValue, "The values used for the inflation rate are invalid"

class CPIindexEscalator(Escalator):
    """Uses the CPI index to determine the final cost"""
    #Need a pandas timeseries with values of the CPI index hardcoded

    def escalate(self):
        #Determine the basis CPI Index
        
        #Determine the new CPI Index using interpolation (linear, or spline???)

        #Calculate a factor
        pass
        
class DepreciationSchedule:
    """A timeseries-indexed dataframe that holds the depreciation schedule"""

    def __init__(self, starting_period, length):
	#create an empty dataframe, if nothing else
	self.check_inputs(starting_period, length)
	self.length = length
	self.starting_period = starting_period

	#Any creation of an actual schedule will require creation of the DataFrame in the __init__ member function

    def build(self):
        """Fills in the depreciation schedule"""
	pass

    def check_inputs(self, starting_period, length):
        if not isinstance(starting_period, dt.datetime):
            raise BadCapitalDepreciationInput, "starting_period must be a datetime.datetime object; found %s instead" % type(starting_period)

        try:
            f = 9.3/length
            if length < 0:
                raise BadCapitalDepreciationInput, "length must be positive"
        except TypeError or ValueError:
            raise BadCapitalDepreciationInput, "length must be numeric and positive"    
        
    def __getitem__(self, key):
        return self.frame[key]

    def __setitem__(self, key, val):
        self.frame[key] = val

    def value(self, date):
	return self.frame.loc[date]['depreciation']



class NonDepreciableDepreciationSchedule(DepreciationSchedule):
    def __init__(self, starting_period=None, length=None, **kwargs):
        
        DepreciationSchedule.__init__(self, starting_period, length)
        dates = pd.date_range(self.starting_period, self.starting_period + self.length*DateOffset(years=1) - DateOffset(days=1), freq = 'D')
	d = {'depreciation':np.zeros(len(dates))}
	self.frame = df.DataFrame(index = dates, data = d)
        
	


    def build(self, cost):
        """Nothing to do here -- the schedule should be filled with zeros"""
        pass

    

class StraightLineDepreciationSchedule(DepreciationSchedule):

    def __init__(self, starting_period=None, length=None,**kwargs):
        
        DepreciationSchedule.__init__(self, starting_period, length)
        dates = pd.date_range(self.starting_period, self.starting_period + self.length*DateOffset(years=1) - DateOffset(days=1), freq = 'D')
        d = {'depreciation':np.zeros(len(dates))}
        self.frame = df.DataFrame(index = dates, data = d)
	

    def build(self, cost):
        """Fills out a straight-line depreciation schedule"""
        self['depreciation'] += 1.0
        deprec_value_daily = cost/len(self.frame.index)
        self['depreciation'] *= deprec_value_daily


class MACRSDepreciationSchedule(DepreciationSchedule):
    MACRS = {}
    MACRS['3'] = np.array([0.3333, 0.4445, 0.1481, 0.0741])
    MACRS['5'] = np.array([0.2, 0.32, 0.1920, 0.1152, 0.1152, 0.0576])
    MACRS['7'] = np.array([0.1429, 0.2449, 0.1749, 0.1249, 0.0893, 0.0892, 0.0893, 0.0446])
    MACRS['10'] = np.array([0.1000, 0.18, 0.144, 0.1152, 0.0922, 0.0737, 0.0655, 0.0655, 0.0656, 0.0655, 0.0328])
    MACRS['15'] = np.array([0.05, 0.095, 0.0855, 0.0770, 0.0693, 0.0623, 0.0590, 0.0590, 0.0591, 0.0590, 0.0591, 0.0590, 0.0591, 0.0590, 0.0591, 0.0295])
    MACRS['20'] = np.array([0.0375, 0.07219, 0.06677, 0.06177, 0.05713, 0.05285, 0.04888, 0.04522, 0.04462, 0.04461, 0.04462, 0.044610, 0.04462, 0.04461, 0.04462, 0.04461, 0.04462, 0.04461, 0.04462, 0.04461, 0.02231])
   
    def __init__(self, starting_period=None, length=None,**kwargs):
        DepreciationSchedule.__init__(self, starting_period, length)
        
        dates = pd.date_range(self.starting_period, self.starting_period + (self.length+1)*DateOffset(years=1)-DateOffset(days=1), freq = 'D')
        d = {'depreciation': np.zeros(len(dates))}
        self.frame = df.DataFrame(index = dates, data = d)
	

    def build(self, cost):
        self['depreciation'] += 1.0
        for y in range(0,self.length+1):
                
            dep_factor = MACRSDepreciationSchedule.MACRS['%s' % (self.length)][y]/len(self[self.starting_period + y*DateOffset(years=1):self.starting_period+(y+1)*DateOffset(years=1)-DateOffset(days=1)])
            self[self.starting_period+y*DateOffset(years=1):self.starting_period+(y+1)*DateOffset(years=1)-DateOffset(days=1)]['depreciation'] *= dep_factor                
 
        self['depreciation'] *= cost


class ScheduleDepreciationSchedule(DepreciationSchedule):
    """A fixed schedule of fractional write-downs should be passed in"""
    def __init__(self, starting_period=None, length=None, schedule=None):
	DepreciationSchedule.__init__(self, starting_period, length)
	if not isinstance(schedule, df.DataFrame) or not isinstance(schedule.index, pd.tseries.index.DatetimeIndex):
	    raise BadCapitalDepreciationInput, "The schedule must be a pandas dataframe with a timeseries index"
        if schedule.index[0] < starting_period:
            raise BadCapitalDepreciationInput, "The schedule starts before the given starting period"

        if 'depreciation' not in schedule.columns:
            raise BadCapitalDepreciationInput, "The depreciation schedule must have a 'depreciation' column"

        self.frame = df.DataFrame(schedule)

    def build(self, cost):
        self['depreciation'] *= cost

class CapitalExpense:
    """Container class for capital expenditures"""
    
    gl_add_info = OrderedDict([('name',('Name',str)),('uninstalled_cost',('Uninstalled cost',float)),('installation_factor',('Installation factor',float))])

    def __init__(self, tag, name, description = None, quote_basis = None, escalation_type = None, depreciation_type = 'StraightLine', payment_terms = None):
        self.name = name
        self.tag = tag
        self.description = description
        if quote_basis is not None:
            self.set_quote_basis(quote_basis)
        else:
           self.quote_basis = None
        
        self.set_depreciation_type(depreciation_type)
        self.set_escalator(escalation_type)
        self.comments = []
        self.payment_terms = payment_terms
	self.payment_label = 'direct_costs'
	self.depreciation_args = {}		#allow for the schedule generation to be automated
	self.payment_args = {}			#allows for the schedule generation to be automated    



    def set_quote_basis(self, quote_basis):
        if not isinstance(quote_basis, CapitalExpenseQuoteBasis):
            raise BadCapitalCostInput, "The quote_basis must be of type CapitalExpenseQuoteBasis"
        self.quote_basis = quote_basis

    def set_depreciation_type(self, dep_type):
        dep_types = ['StraightLine','MACRS', 'Schedule', 'NonDepreciable']
        if dep_type is None:
            dep_type = 'NonDepreciable'
        if dep_type not in dep_types:
            raise BadCapitalCostInput, "%s is not a supported depreciation type" % dep_type
        self.depreciation_type = dep_type

    def set_escalator(self, esc_type):
        esc_types = ['InflationRate','CPIindex']
        if esc_type is None:
            self.escalator = NoEscalationEscalator()

        elif esc_type in esc_types:
            self.escalator = globals()["%sEscalator" % esc_type]()

        else:
            raise BadEscalatorTypeError, "%s is not a supported escalator type" % esc_type

    def set_inflation_rate(self, rate):
        self.escalator.rate = rate  #This only really does anything if it is an inflation escalator -- there is probably a better overall way to handle this, but I do not care

    
    def add_comment(self, comment):
        if type(comment) is not str:
            raise ProjFinError, "Comments must be strings"
        self.comments.append(comment)

    def TIC(self, date, **kwargs):
        """Returns the total installed cost for the given date, applying the internal escalator and inflation functions"""
        if self.quote_basis is None:
            raise BadCapitalTICInput, "A quote basis must be defined to give a total installed cost"
        
        return self.escalator.escalate(basis_date = self.quote_basis.date, new_date = date, **kwargs) * self.quote_basis.cost()
 
    def build_capex_schedule(self):
        """Aggregates the payment schedule and depreciation schedule into the total_schedule dataframe"""
	#Need to build the depreciation and payment schedules -- use the internal dictionaries of arguments for these, which must be set up first
	self.build_depreciation_schedule(**self.depreciation_args)
	self.calc_payment_schedule(**self.payment_args)


	#Let's use the merge SQL-like feature of the pandas dataframe to do this
	self.total_schedule = self.depreciation_schedule.frame.join(self.payment_schedule, how = 'outer').fillna(0.0)


    def build_depreciation_schedule(self, starting_period, length, **kwargs):
        """Fills out the depreciation capex schedule based on the type of depreciation (straight-line, MACRS, etc.)"""
        dep_methods = ['StraightLine', 'MACRS', 'Schedule', 'NonDepreciable']       #Need non-deprec and schedule
        #set up the schedule Dataframe
        if self.depreciation_type not in dep_methods:
            raise BadCapitalDepreciationInput, "No depreciation method selected"
        
        self.depreciation_schedule = globals()["%sDepreciationSchedule" % self.depreciation_type](starting_period = starting_period, length = length, **kwargs)
       
        self.depreciation_schedule.build(cost = self.TIC(starting_period))

    def calc_payment_schedule(self, **kwargs):
	accepted_terms = ['LumpSumDelivered','LumpSumOrdered','EqualPeriodic','FractionalSchedule','FixedSchedule']
        if self.payment_terms not in accepted_terms:
            raise BadCapitalPaymentTerms, "%s is not a supported set of payment terms" % self.payment_terms
        

        getattr(self, "_calc_payment_schedule_%s" % self.payment_terms)(**kwargs)
        

    def _calc_payment_schedule_LumpSumOrdered(self, order_date = None):
        if not isinstance(order_date, dt.datetime):
            raise BadCapitalPaymentInput, "order_date must be datetime.datetime; got %s instead)" % type(order_date)
        dates = [order_date]
        data = {self.payment_label:np.array([self.TIC(order_date)])}
        self.payment_schedule = df.DataFrame(index = dates, data = data)

    def _calc_payment_schedule_LumpSumDelivered(self, order_date = None):
        if not isinstance(order_date, dt.datetime):
            raise BadCapitalPaymentInput, "order_date must be datetime.datetime, got %s instead)" % type(order_date)
        dates = [order_date + self.quote_basis.lead_time]
	data = {self.payment_label:np.array([self.TIC(order_date)])}
        self.payment_schedule = df.DataFrame(index = dates, data = data)

    def _calc_payment_schedule_EqualPeriodic(self, order_date = None, freq = 'M'):
        if not isinstance(order_date, dt.datetime):
            raise BadCapitalPaymentInput, "order_date must be datetime.datetime, got %s instead)" % type(order_date)
        dates = pd.date_range(start = order_date, end = order_date + self.quote_basis.lead_time, freq = freq)
	pmts = np.ones(len(dates))
	pmts *= self.TIC(order_date)/len(pmts)
        data = {self.payment_label:pmts}
	self.payment_schedule = df.DataFrame(index = dates, data = data)
	
	

    def _calc_payment_schedule_FractionalSchedule(self, order_date = None, schedule = None):
        if not isinstance(order_date, dt.datetime):
            raise BadCapitalPaymentInput, "order_date must be datetime.datetime, got %s instead)" % type(order_date)
	if not isinstance(schedule, df.DataFrame) or not isinstance(schedule.index, pd.tseries.index.DatetimeIndex):
            raise BadCapitalPaymentInput, "schedule must be a pandas DataFrame with a DatetimeIndex"
        if not self.payment_label in schedule.columns:
            raise BadCapitalPaymentInput, "schedule must have a '%s' column" % self.payment_label
        
        if not abs(sum(schedule[self.payment_label])-1.0) < 0.0001:
            raise BadCapitalPaymentInput, "The schedule payments column must sum to 1.0"

        schedule[self.payment_label]*=self.TIC(order_date)
        self.payment_schedule = schedule

    def _calc_payment_schedule_FixedSchedule(self, order_date = None, schedule = None):
        if not isinstance(order_date, dt.datetime):
            raise BadCapitalPaymentInput, "order_date must be datetime.datetime, got %s instead)" % type(order_date)
	if not isinstance(schedule, df.DataFrame) or not isinstance(schedule.index, pd.tseries.index.DatetimeIndex):
            raise BadCapitalPaymentInput, "schedule must be a pandas DataFrame with a DatetimeIndex"
        if not self.payment_label in schedule.columns:
            raise BadCapitalPaymentInput, "schedule must have a '%s' column" % self.payment_label

        if not sum(schedule[self.payment_label]) == self.TIC(order_date):
            raise BadCapitalPaymentInput, "The schedule payments column must sum to the total installed cost (escalated)"
        
        self.payment_schedule = schedule
               

    def __eq__(self, other):
        if not isinstance(other, CapitalExpense):
            raise TypeError, "Cannot compare CapitalExpense with %s" % type(other)
        l = ['tag', 'name', 'description', 'quote_basis', 'escalation_type', 'depreciation_type']
        val = True
        for att in l:
            val = val and getattr(self, att) == getattr(other, att)
        return val
        
    def __ne__(self, other):
        return not self.__eq__(other)
    
    
    def scale(self, tag, name, new_scale):
        """Returns a new CapitalExpense, scaled from the current capital expense using the scaling method in the quote basis"""
        newQB = self.quote_basis.scale(new_scale)
        return CapitalExpense(tag, name, description = self.description, installation_model = self.installation_model, size_basis = self.size_basis, quote_basis = newQB, escalation_type = self.escalation_type, depreciation_type = self.depreciation_type)
              

class IndirectCapitalExpense(CapitalExpense):

    def __init__(self, **kwargs):
        CapitalExpense.__init__(self, **kwargs)
	self.payment_label = 'indirect_costs'


    def set_quote_basis(self, quote_basis):
        if not isinstance(quote_basis, IndirectCapitalExpenseQuoteBasis):
            raise BadCapitalCostInput, "The quote_basis must be of type IndirectCapitalExpenseQuoteBasis"
        self.quote_basis = quote_basis

    #def build_depreciation_schedule(self):
    #    self.depreciation_schedule = df.DataFrame()		#for indirect costs, which are not (??) depreciable -- check this, actually -- we create an empty dataframe


    def calc_payment_schedule(self, **kwargs):
	accepted_terms = ['FixedSchedule']
        if self.payment_terms not in accepted_terms:
            raise BadCapitalPaymentTerms, "%s is not a supported set of payment terms" % self.payment_terms
        

        getattr(self, "_calc_payment_schedule_%s" % self.payment_terms)(**kwargs)



class CapitalCosts:
    

    #Stuff for GUI
    id_labels = {'site_prep':'Site preparation', 'engineering_and_design':'Engineering and design', 'process_contingency':'Process contingency', 'project_contingency':'Project contingency', 'other':'Other', 'one-time_licensing_fees':'One time licensing fees', 'up-front_permitting_costs':'Up-front permitting costs'}
    id_types = {}
    for k in id_labels:
        id_types[k] = float

    ind_labels = {'Land':'Land'}
    ind_types = {'Land':float}

    """Holds (and calculates) all depreciable and non-depreciable capex for the project"""
    def __init__(self):
        self.direct_capital = []
        self.indirect_capital = []
              

    def add_direct_capital_item(self, capital_item):
        """Adds a capital item to the direct_capital list"""
        if not isinstance(capital_item, CapitalExpense) and not isinstance(capital_item, CapitalCosts):
            raise BadDirectCapitalItem, "Only capital expenses can be added to the capital expense list"

        self.direct_capital.append(capital_item)

    def add_indirect_capital_item(self, indirect_capital_item):
        """Adds an indirect capital item to the indirect_capital list"""
        if not isinstance(indirect_capital_item, IndirectCapitalExpense):
            raise BadIndirectCapitalItem, "Only indirect capital expenses can be added to the indirect capital expense list"

        self.indirect_capital.append(indirect_capital_item)


    def build_capex_schedule(self):
        """Calculates all of the payments and depreciation and aggregates these into a pandas dataframe"""
	#Call the aggregation functions on all of the directs

        self.total_schedule = df.DataFrame()
	
        for dc in self.direct_capital:
	    dc.build_capex_schedule()		#if some of these items are CapitalCosts, then the schedule will contain indirects -- this handles itself seamlessly
	    #shit, now we need to actually deal with the data mismatch problems -- going to do this the brute force way
	    if len(self.total_schedule) == 0:	#base case
	        self.total_schedule = self.total_schedule.join(dc.total_schedule, how = 'outer').fillna(0.0)
		#print self.total_schedule
	    else:
		self.total_schedule = self.total_schedule.add(dc.total_schedule, fill_value = 0.0)
	        

	#create the indirect costs column, if it is not already there
	if 'indirect_costs' not in self.total_schedule.columns:
	    self.total_schedule['indirect_costs'] = np.zeros(len(self.total_schedule.index))

	for ic in self.indirect_capital:
            
	    ic.build_capex_schedule()
	    self.total_schedule = self.total_schedule.add(ic.total_schedule, fill_value = 0.0)

            
    ##############################################
    """
    def _setup_depreciable_capex_dict(self):
        items = ['site_prep', 'engineering_and_design', 'process_contingency', 'project_contingency', 'other', 'one-time_licensing_fees', 'up-front_permitting_costs']
        for item in items:
            self.indirect_deprec_capital[item] = 0
    #SAVE THIS FOR THE OVERALL PROJECT AS "TYPICAL" ITEMS 
    """

    
    def costs_and_depreciation(self, period):
        """Accessor method to hide the internal baseball of the capital costs object -- all I really want from this thing, at this point, are the costs for a given day"""
        capex = 0.0
        deprec = 0.0

        if period in self.capex_schedule.index:
            capex = self.capex_schedule.loc[period]['capex']

        if period in self.depreciation_schedule.index:
            deprec = self.depreciation_schedule.loc[period]['depreciation']
        
        return (capex, deprec)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.direct_capital == other.direct_capital and self.indirect_capital == other.indirect_capital

    def __ne__(self, other):
        return not self.__eq__(other)


    def scale(self, new_scale):
        pass


class StartupDiscounter(object):
    """Class to encapsulate discounting of startup fixed costs, variable costs, and production at the beginning of a plant life"""

    def __init__(self):
        pass

    def discount_factors(self, time_series):
        """Returns discount factors in a timeseries indexed series"""
        if not isinstance(time_series, pd.Series):
            raise BadStartupDiscountError, "time_series must be a variant of a pandas series, got %s" % type(time_series)
        
class NoneStartupDiscounter(StartupDiscounter):
    """Returns 1x factors for the entire passed time series"""

    def discount_factors(self, time_series):
        StartupDiscounter.discount_factors(self, time_series)
        return df.DataFrame({'factors':np.ones(len(time_series))}, index = time_series)


class dtFractionalStartupDiscounter(StartupDiscounter):
    """Discounts the first delta_t of a startup period at a fixed rate"""

    def __init__(self, time_span, fraction):
        self.deltat = time_span
        self.fraction = fraction

    @property
    def fraction(self):
        return self._fraction

    @fraction.setter
    def fraction(self, v):
        try:
             v/12.5
             if v < 0:
                 raise BadStartupDiscountError, "The fraction for this startup function must be non-negative"
        except TypeError:
             raise BadStartupDiscountError, "The fraction must be numeric"
        self._fraction = v

    @property
    def deltat(self):
        return self._dt

    @deltat.setter
    def deltat(self, v):
        if not isinstance(v, dt.timedelta):
            raise BadStartupDiscountError, "time_span must be a datetime.timedelta object"

        self._dt = v
    
    
    def discount_factors(self, time_series):
        StartupDiscounter.discount_factors(self, time_series)
        f = df.DataFrame(index = time_series)
        f['factors'] = np.ones(len(time_series))
        f['factors'][f.index < time_series[0] + self.deltat] = self.fraction
	return f
        


class FixedExpense(object):
    """Models a fixed (non-production related) expense."""

    def __init__(self, name, description = None, quote_basis = None, escalator = None, pmt_type = None, startup_discounter = None):
	self.name = name
	self.description = description
	self.quote_basis = quote_basis
	self.escalator = escalator
	self.pmt_type = pmt_type
	self.startup_discounter = startup_discounter
        self.pmt_args = {}


    @property
    def name(self):
	return self._name

    @name.setter
    def name(self, value):
	if value is not None and not isinstance(value, basestring):
	    raise BadFixedExpenseInput, "name must be of type string, got %s" % type(value)

	self._name = value

    @property
    def description(self):
	return self._description

    @description.setter
    def description(self, v):
	if v is not None and not isinstance(v, basestring):
	    raise BadFixedExpenseInput, "description must be of type string, got %s" % type(v)

	self._description = v

    @property
    def quote_basis(self):
	return self._quote_basis

    @quote_basis.setter
    def quote_basis(self, v):
        if v is not None and not isinstance(v, FixedExpenseQuoteBasis):
	    raise BadFixedExpenseInput, "quote_basis must be of type FixedExpenseQuoteBasis, got %s" % type(v)

	self._quote_basis = v

    @property
    def escalator(self):
	return self._escalator

    @escalator.setter
    def escalator(self, v):
        if v is not None and not isinstance(v, Escalator):
            raise BadFixedExpenseInput, "escalator must be a derivative of Escalator, got %s" % type(v)

	self._escalator = v

    @property
    def pmt_type(self):
        return self._pmt_type

    @pmt_type.setter
    def pmt_type(self, v):
	if v is not None and not isinstance(v, basestring):
	    raise BadFixedExpenseInput, "pmt_type must be a string, got %s" % type(v)

        if v is not None and v not in ['simple']:
            raise BadFixedExpenseInput, "%s is not an acceptable payment type" % type(v)

	self._pmt_type = v


    @property
    def startup_discounter(self):
	return self._startup_discounter

    @startup_discounter.setter
    def startup_discounter(self, v):
        if v is None:
            v = NoneStartupDiscounter()
        elif not isinstance(v, StartupDiscounter):
             raise BadFixedExpenseInput, "The startup discounter must be of type StartupDiscounter, got type %s" % type(v)

        self._startup_discounter = v

    def build_fex_schedule(self):
	"""This is the wrapper function that matches the name in the container class"""
        self.calc_payment_schedule(**self.pmt_args)


    def calc_payment_schedule(self, **kwargs):
	accepted_terms = ['simple', 'fixed_schedule']
        if self.pmt_type not in accepted_terms:
            raise BadFixedExpensePaymentType, "%s is not a supported kind of payment schedule" % self.payment_terms
        

        getattr(self, "_calc_payment_schedule_%s" % self.pmt_type)(**kwargs)

    def _calc_payment_schedule_simple(self, term, **kwargs):
        """Applies the escalated fixed cost at equal intervals; the fixed cost quote MUST be on the same interval as the freq"""
	if not isinstance(term, dt.timedelta):
	    raise BadFixedCostScheduleInput, "term must be a datetime.timedelta object, got %s" % type(term)
	dates = pd.date_range(self.init_date, self.init_date+term, freq = self.quote_basis.freq)
	self.schedule = df.DataFrame(index = dates)
        esc_factors = self.escalator.escalate(basis_date = self.quote_basis.date, new_date  = pd.Series(self.schedule.index))
	esc_factors.index = self.schedule.index

        self.schedule['fixed_costs'] = np.ones(len(self.schedule.index))*esc_factors*self.quote_basis.base_price
	self.schedule['fixed_costs'] *= self.startup_discounter.discount_factors(time_series = pd.Series(self.schedule.index))

    def _calc_payment_schedule_fixed_schedule(self, schedule, **kwargs):
	"""Applies the costs at a given fixed schedule.  No escalation -- this is a brute force override method"""
	if not isinstance(schedule, df.DataFrame) or not isinstance(schedule.index, pandas.tseries.index.DatetimeIndex) or 'fixed_costs' not in schedule.columns:
	    raise BadFixedCostScheduleInput, "The given schedule does not conform to the requirements for this dataframe"
	self.schedule = schedule.loc[:,'fixed_costs']		#trim any superfluous columns

    def _calc_payment_schedule_fractional_schedule(self, schedule):
	"""This takes a given fraction of the planned schedule, and allows for simple startup functions to be applied.  More of the scheduling has to be done outside, though"""
	pass


class FixedCosts(object):
    gl_add_info = OrderedDict([('project_staff',('Project staff',float)),('g_and_a',('General and Administrative',float)),('prop_tax_and_insurance',('Property tax and insurance',float)),('rent_or_lease',('Rent or Lease',float)),('licensing_permits_fees',('Licensing, permits, and fees',float)),('mat_cost_maint_repair',('Material costs for maintenance and repairs',float)),('other_fees',('Other fees',float)),('other_fixed_op_and_maint',('Other fixed operational and maintenance costs',float))])
    labels = OrderedDict([('project_staff','Project staff'),('g_and_a','General and Administrative'),('prop_tax_and_insurance','Property tax and insurance'),('rent_or_lease','Rent or Lease'),('licensing_permits_fees','Licensing, permits, and fees'),('mat_cost_maint_repair','Material costs for maintenance and repairs'),('other_fees','Other fees'),('other_fixed_op_and_maint','Other fixed operational and maintenance costs')])
    types = OrderedDict([('project_staff',float),('g_and_a',float),('prop_tax_and_insurance',float),('rent_or_lease',float),('licensing_permits_fees',float),('mat_cost_maint_repair',float),('other_fees',float),('other_fixed_op_and_maint',float)])

    """Holds the fixed costs for a project (not a company)"""
    def __init__(self):

        self.fixed_costs = []
        
    def add_fixed_cost(self, fixed_cost):
        if not isinstance(fixed_cost, FixedExpense) and not isinstance(fixed_cost, FixedCosts):
            raise BadFixedCostType, "fixed_cost must be of type FixedExpense, got %s" % type(fixed_cost)
        self.fixed_costs.append(fixed_cost)

    def del_fixed_cost(self, fixed_cost):			###!!!### all of these deletions should be done with ids instead -- much cleaner, as I would not need the acutal object to remove it
        for fc in self.fixed_costs:
            if fc.name == fixed_cost.name:
                self.fixed_costs.remove(fixed_cost)

    def build_fex_schedule(self):
	self.schedule = df.DataFrame()
        for fc in self.fixed_costs:
            fc.build_fex_schedule()
            if len(self.schedule) == 0:
                self.schedule = self.schedule.join(fc.schedule, how = 'outer').fillna(0.0)

	    else:
		self.schedule = self.schedule.add(fc.schedule, fill_value = 0.0)
	        
 

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.fixed_costs == other.fixed_costs

    def __ne__(self, other):
        return not self.__eq__(other)

   
class VariableExpense(object):
    """Holds a single instance of a variable expense"""

    def __init__(self, name, description = None, quote_basis = None, production = None, rate = None, escalator = None):
        self.name = name
        self.description = description
	self.quote_basis = quote_basis
	self.production = production
	self.rate = rate
	self.escalator = escalator
	self.preferred_units = {}
	self.preferred_units['variable_consumption'] = None
	self.preferred_units['variable_costs'] = None

    @property
    def name(self):
	return self._name

    @name.setter
    def name(self, v):
        if not isinstance(v, basestring):
	    raise BadVariableExpenseInput, "name must be a string"

        self._name = v

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, v):
        if v is not None and not isinstance(v, basestring):
            raise BadVariableExpenseInput, "description must be a string"

        self._description = v

    @property
    def quote_basis(self):
        return self._quote_basis

    @quote_basis.setter
    def quote_basis(self, v):
        if v is not None and not isinstance(v, VariableExpenseQuoteBasis):
            raise BadVariableExpenseInput, "quote_basis must be a QuoteBasis object, got %s" % type(v)
        self._quote_basis = v

    @property
    def production(self):
        return self._production

    @production.setter
    def production(self,v):
        if v is not None and not isinstance(v, Production):
            raise BadVariableExpenseInput, "production must be a Production object, got %s" % type(v)
        self._production = v

    @property
    def rate(self):
        return self._rate

    @rate.setter
    def rate(self, v):
        if v is not None and not isinstance(v, uv.UnitVal):
            raise BadVariableExpenseInput, "rate must be a UnitVal"
        self._rate = v

    @property
    def escalator(self):
        return self._escalator

    @escalator.setter
    def escalator(self, v):
        if v is None:
            self._escalator = NoEscalationEscalator()
        elif not isinstance(v, Escalator):
            raise BadVariableExpenseInput, "escalator must be an Escalator"
        else:
            self._escalator = v

    def build_vex_schedule(self, end_date):
        if not isinstance(end_date, dt.datetime):
            raise BadScheduleDateError, "end_date must be a dt.datetime object"

	#build the production schedule, you'll need it
	self.production.build_production_schedule(end_date)
	self.schedule = df.DataFrame(index = self.production.schedule.index)  #match dates
	
	
	#escalate the quote basis
	esc_factors = self.escalator.escalate(basis_date = self.quote_basis.date, new_date  = pd.Series(self.schedule.index))  #lots of reach through -- do we want to put an accessor in Product?
	esc_factors.index = self.schedule.index
	self.schedule['variable_consumption'] = self.rate.value * self.production.schedule['rate']

	self.schedule.units['variable_consumption'] = (self.rate * uv.UnitVal(1.0, self.production.schedule.units['rate'])).units
	if self.preferred_units['variable_consumption'] is not None:
	    self.schedule.convert_units('variable_consumption', self.preferred_units['variable_consumption'])	#This should throw an error on unit mismatch, but should happen at the DataFrame level
	else:
	    self.schedule.simplify_units('variable_consumption')

	self.schedule['variable_costs'] = esc_factors * self.quote_basis.base_price * self.schedule['variable_consumption']
	self.schedule.units['variable_costs'] = (self.quote_basis.size_basis * uv.UnitVal(1.0,self.schedule.units['variable_consumption'])).units
	if self.preferred_units['variable_costs'] is not None:
	    self.schedule.convert_units('variable_costs', self.preferred_units['variable_costs'])
	else:
	    self.schedule.simplify_units('variable_costs')
	
	
class VariableCosts:
    """Class to hold the set of variable costs""" 

    def __init__(self):

        self.variable_costs = []
	self.detailed = False
        
    def add_variable_expense(self, vex):
        if not isinstance(vex, VariableExpense) and not isinstance(vex, VariableCosts):
            raise BadVariableExpenseItem, "vex must be of type VariableExpense, got %s" % type(vex)
        self.variable_costs.append(vex)

    def del_variable_expense(self, vex):			###!!!### all of these deletions should be done with ids instead -- much cleaner, as I would not need the acutal object to remove it
        for vc in self.variable_costs:
            if vc.name == vex.name:
                self.variable_costs.remove(vc)

    def build_vex_schedule(self, end_date):
	self.schedule = df.DataFrame()

	for vc in self.variable_costs:
            vc.build_vex_schedule(end_date)
            if len(self.schedule) == 0:
                self.schedule = self.schedule.join(vc.schedule, how = 'outer').fillna(0.0)
	        self.schedule = df.DataFrame(self.schedule)

	    else:
		self.schedule = self.schedule.add(vc.schedule, fill_value = 0.0)			#This assumes a common currency in all the sheets ###!!!###

	    if self.detailed:
		self.schedule['%s_variable_consumption' % vc.name] = vc.schedule['variable_consumption']
		self.schedule.units['%s_variable_consumption'] = vc.schedule.units['variable_consumption']
		self.schedule['%s_variable_costs' % vc.name] = vc.schedule['variable_costs']
		self.schedule.units['%s_variable_costs' % vc.name] = vc.schedule.units['variable_costs']
 
    
    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.variable_costs == other.variable_costs

    def __ne__(self, other):
        return not self.__eq__(other)


class Product(object):
    """Holds a product and its pricing information"""
    def __init__(self, name, description=None, quote_basis=None, escalator=None):
	self.name = name
	self.description = description
	self.quote_basis = quote_basis
	self.escalator = escalator

    @property
    def name(self):
	return self._name

    @name.setter
    def name(self, v):
        if not isinstance(v, basestring):
	    raise BadProductInput, "name must be a string"

        self._name = v

    @property
    def description(self):
	return self._description

    @description.setter
    def description(self, v):
        if v is not None and not isinstance(v, basestring):
	   raise BadProductInput, "description must be a string"
        self._description = v

    @property
    def quote_basis(self):
	return self._quote_basis
    
    @quote_basis.setter
    def quote_basis(self, v):
        if v is not None and not isinstance(v, QuoteBasis):
	    raise BadProductInput, "quote basis must be a QuoteBasis object, got %s" % type(v)
	self._quote_basis = v

    @property
    def escalator(self):
        return self._escalator

    @escalator.setter
    def escalator(self,v):
        if v is None:
            self._escalator = NoEscalationEscalator()
	elif not isinstance(v, Escalator):
	    raise BadProductInput, "escalator must be an Escalator object, got %s" % type(v)
	else:
	    self._escalator = v

    @property
    def price(self):
        return self.quote_basis.base_price * self.quote_basis.size_basis

    def escalate_price(self, new_dates):
	esc_price = self.escalator.escalate(basis_date = self.quote_basis.date, new_date  = pd.Series(new_dates)) * self.quote_basis.base_price
	esc_price.index = new_dates
	return esc_price


class Production(object):
    """Holds a product and a rate of production"""

    freqs = {'D':'day'}			#daily is the only frequency currently supported

    def __init__(self, name, product = None, rate = None, startup_discounter = None, init_date = None, comment = None, method = None, freq = None):
        self.name = name
	self.product = product
	self.rate = rate
	self.startup_discounter = startup_discounter
	self.init_date = init_date
	self.comment = comment
	self.method = method
	self.freq = freq
        self.sch_args = {}
	self.preferred_units = {}
	self.preferred_units['rate'] = None
	self.preferred_units['price'] = None
	self.preferred_units['revenue'] = None	


    @property
    def name(self):
	return self._name

    @name.setter
    def name(self, v):
        if not isinstance(v, basestring):
	    raise BadProductionInput, "name must be a string"

        self._name = v

    @property
    def product(self):
	return self._product

    @product.setter
    def product(self, v):
        if v is not None and not isinstance(v, Product):
	    raise BadProductionInput, "product must be a Product, got %s" % type(v)
	self._product = v

    @property
    def rate(self):
	return self._rate
    @rate.setter
    def rate(self, v):
        if v is not None and not isinstance(v, uv.UnitVal):	#should really check that rate has a time unit in it, but whatever
	    raise BadProductionInput, "rate must be a UnitVal object, got %s" % type(v)

	self._rate = v

    @property
    def startup_discounter(self):
	return self._startup_discounter

    @startup_discounter.setter
    def startup_discounter(self, v):
        if v is None:
            self._startup_discounter = NoneStartupDiscounter()
	elif not isinstance(v, StartupDiscounter):
	    raise BadProductionInput, "startup_discounter must be a StartupDiscounter, got %s" % type(v)
        else:
            self._startup_discounter = v
	
    @property
    def init_date(self):
	return self._init_date

    @init_date.setter
    def init_date(self, v):
        if v is not None and not isinstance(v, dt.datetime):
	    raise BadProductionInput, "init_date must be a datetime.datetime object, got %s" % type(v)
        self._init_date = v

    @property
    def comment(self):
        return self._comment

    @comment.setter
    def comment(self, v):
        if v is not None and not isinstance(v, basestring):
	    raise BadProductionInput, "comment must be a string"

        self._comment = v

    @property
    def method(self):
        return self._method

    @method.setter
    def method(self, v):
        methods = ['simple']
	if v is None:
	    self._method = 'simple'
	elif v not in methods:
	    raise BadProductionInput, "Unsupported method selected"
	else:
	    self._method = v

    @property
    def freq(self):
	return self._freq

    @freq.setter
    def freq(self, v):
	
        if v is None:
	    self._freq = 'D'	#default to daily payment method
	    self.freq_dummy_uv = uv.UnitVal(1, Production.freqs['D'])
        elif v not in Production.freqs.keys():
	    raise BadProductionInput, "Unsupported frequency selected"
	else:
	    self._freq = v
            self.freq_dummy_uv = uv.UnitVal(1, Production.freqs[v])

    def build_production_schedule(self, end_date):
	"""This is the wrapper function that matches the name in the container class"""
	#dispatch to the right function
	getattr(self, "_calc_schedule_%s" % self.method)(end_date)
 

    def _calc_schedule_simple(self, end_date, **kwargs):
        """Applies the escalated fixed cost at equal intervals; the fixed cost quote MUST be on the same interval as the freq"""
	conv = uc.UnitConverter()
	if not isinstance(end_date, dt.datetime):
	    raise BadFixedCostScheduleInput, "end_date must be a datetime.datetime object, got %s" % type(end_date)
	dates = pd.date_range(self.init_date, end_date, freq = self.freq)
	self.schedule = df.DataFrame(index = dates)

	#This is the non-unit-val approach
	self.schedule['price'] = self.product.escalate_price(new_dates = self.schedule.index)
	self.schedule.units['price'] = self.product.quote_basis.size_basis.units
	if self.preferred_units['price'] is not None:
	    self.schedule.convert_units('price', self.preferred_units['price'])
	else:
	    self.schedule.simplify_units('price')

	#want to create the base unit for the entry, then scale
	self.schedule['rate'] = self.rate.value*self.startup_discounter.discount_factors(time_series = pd.Series(self.schedule.index))
	self.schedule.units['rate'] = (self.rate*self.freq_dummy_uv).units
	if self.preferred_units['rate'] is not None:
	    self.schedule.convert_units('rate', self.preferred_units['rate'])
	else:
	    self.schedule.simplify_units('rate')

	#For the revenue column to work, we need equivalent units, right?  Or do we just need to multiply the series values, then simplify units?
	self.schedule['revenue'] = self.schedule['price'] * self.schedule['rate']
	self.schedule.units['revenue'] = (uv.UnitVal(1.0, self.schedule.units['price'])*uv.UnitVal(1.0, self.schedule.units['rate'])).units
	if self.preferred_units['revenue'] is not None:
	    self.schedule.convert_units('revenue', self.preferred_units['revenue'])
	else:
            self.schedule.simplify_units('revenue')

	

class ProductionPortfolio:
    """Class to hold the set of production items""" 

    def __init__(self):

        self.production = []
	self.detailed = False
        
    def add_production(self, production):
        if not isinstance(production, Production) and not isinstance(production, ProductionPortfolio):
            raise BadProductionItem, "production must be of type Production, got %s" % type(production)
        self.production.append(production)

    def del_production(self, production):			###!!!### all of these deletions should be done with ids instead -- much cleaner, as I would not need the acutal object to remove it
        for p in self.production:
            if p.name == production.name:
                self.production.remove(p)

    def build_production_schedule(self, end_date):
	self.schedule = df.DataFrame()

	for p in self.production:
            p.build_production_schedule(end_date)
            if len(self.schedule) == 0:
	                
		self.schedule = self.schedule.join(p.schedule, how = 'outer').fillna(0.0)
	        self.schedule = df.DataFrame(self.schedule)	#need to cast this back up to a unit containing dataframe -- oh, shit, the units are gone -- only really a problem with currency
	    else:
		
		self.schedule = self.schedule.add(p.schedule, fill_value = 0.0)

	    if self.detailed:
		self.schedule['%s_rate' % p.name] = p.schedule['rate']
		self.schedule.units['%s_rate' % p.name] = p.schedule.units['rate']
		self.schedule['%s_price' % p.name] = p.schedule['price']
		self.schedule.units['%s_price' % p.name] = p.schedule.units['price']
	        self.schedule['%s_revenue' % p.name] = p.schedule['revenue']
		self.schedule.units['%s_revenue' % p.name] = p.schedule.units['revenue']

 		
        #drop the extraneous columns - cleanest to do it here, and the extra math won't cost much above


    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.production == other.production

    def __ne__(self, other):
        return not self.__eq__(other)



class DebtPortfolio:
    """Holds all of the loans, bonds, etc. for a given project"""
    def __init__(self):
        self.debts = []
        self.loan_schedule_bit = False


    def add_debt(self, debt):
        """Add a loan to the list of loans"""
        if not isinstance(debt, Debt):
            raise ProjFinError, "New debt security must be an instance of class Debt; it was not passed as such"

        for item in self.debts:
            if item.name == debt.name:
                raise ProjFinError, "%s is already a loan in the debt portfolio" % debt.name

        self.debts.append(debt)
        self.loan_schedule_bit = False

    def del_debt(self, name):
        """Removes the loan with the given name.  If the name is not in the list, does nothing."""
        for debt in self.debts:
            if debt.name == name:
                self.debts.remove(debt)

	###!!!###Throw a warning if this is not in here

    def build_debt_schedule(self):
        """Rolls up the debt schedules for all of the given loans"""
	self.schedule = df.DataFrame()
	
        for d in self.debts:
	    try:
	        d.build_debt_schedule()		#if some of these items are CapitalCosts, then the schedule will contain indirects -- this handles itself seamlessly

	    except MissingInfoError:
		raise UnderspecifiedError, "Debt item %s is underspecified; cannot calculate its schedule" % d.name

	    if len(self.schedule) == 0:	#base case
	        self.schedule = self.schedule.join(d.schedule, how = 'outer').fillna(0.0)

	    else:
		self.schedule = self.schedule.add(d.schedule, fill_value = 0.0)


    def calculate_loans(self):
        """Calculates all the schedules for all of the given loans"""
        for loan in self.loans:
            if not loan.scheduled:
                loan.generate_schedule()

        self.loan_schedule_bit = True

    ###This is no longer relevant -- the general loan schedule already does this

    def CIP(self, date_range):
        """Calculates the cash proceeds, interest, and principal payment for all loans in the portfolio for a given date range"""
        if not self.loan_schedule_bit:
            self.calculate_loans()
        
        #date_range should be a timeseries object for this to work
        output = df.DataFrame(index = date_range)
        
        names = ['cash_proceeds','principal_payment','interest']
        for name in names:
            output[name] = np.zeros(len(output))
        for loan in self.loans:
            output = output.add(loan.schedule, fill_value=0)
               
        output = df.DataFrame(output, index = date_range, columns = names)
        
        return output   


    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.loans == other.loans and self.bonds == other.bonds

    def __ne__(self, other):
        return not self.__ne__(other)
    

class DebtPmtScheduler:
    """Schedules debt payments for all types of debt"""
    scheds = {1:'A', 4:'Q', 12:'M'}


    def __init__(self):
        pass

    def pmt_normal_amortization(self, amt, term, pmt_freq, init_date, rate):

        #we work from annualized rates, so the term has to be worked from an annualized basis
	#pmt_freq is number of payments annually
	y = term.days/365	#The term is a timedelta, so we'll always work it in days, on a 365 annual basis.  Leap years will just have to deal
	pmt = amt*(rate/pmt_freq)*np.power(1+rate/pmt_freq,y*pmt_freq)/(np.power(1+rate/pmt_freq,y*pmt_freq)-1)

	if pmt_freq in DebtPmtScheduler.scheds:
            sched = pd.date_range(init_date, periods = y*pmt_freq, freq = DebtPmtScheduler.scheds[pmt_freq])	
	    
        elif pmt_freq == 2:
            sched = pd.date_range(init_date, periods = y*pmt_freq*2, freq = 'Q')
            sched = sched[1::2] 

        else:
	    sched = pd.date_range(init_date, periods = y*pmt_freq, freq = '%01dD' % 365/pmt_freq)


	#we really just want to return a schedule of payments -- the debt instrument will calculate the interest and principal contributions
	frame = df.DataFrame(index = sched)
	frame['payments'] = np.ones(len(sched))*pmt
	return frame

    def pmt_balloon(self, amt, term, init_date):
	sched = pd.date_range(init_date+term, periods = 1, freq = 'D')
	frame = df.DataFrame(index = sched)
	frame['payments'] = np.ones(len(sched))*amt
	return frame

    def cash_upfront(self, amt, init_date):
	sched = pd.date_range(init_date, periods = 1, freq = 'D')
	frame = df.DataFrame(index = sched)
	frame['proceeds'] = np.ones(len(sched))*amt
	return frame
	

class Debt:
    """Abstract class for all debt instruments"""

    def __init__(self, name, principal = None, init_date = None, comment = None,term = None, rate = None, pmt_freq = None):
	if name is not None and not isinstance(name, basestring):
	    raise BadDebtInput, "name must be a string"

	if principal is not None:
	    try:
		principal/23.5
		if principal < 0.0:
		    raise BadDebtInput, "principal must be non-negative"
	    except TypeError:
		    raise BadDebtInput, "principal must be numeric"

	if init_date is not None and not isinstance(init_date, dt.datetime):
	    raise BadDebtInput, "init_date of type %s, must be of type datetime.datetime" % type(init_date)

	if comment is not None and not isinstance(comment, basestring):
	    raise BadDebtInput, "comment must be of type basestring, got type %s" % type(comment)

	if term is not None and not isinstance(term, dt.timedelta):   #This breaks EVERYTHING
	    raise BadDebtInput, "The loan term must be a dt.timedelta object"

	if rate is not None:
	    try:
		rate/12.5
		if rate < 0.0:
		    raise BadDebtInput, "The loan rate must be non-negative"
	    except TypeError:
		raise BadDebtInput, "The loan rate must be numeric"

        if pmt_freq is not None:
	    try:
		pmt_freq/12.5
		if pmt_freq <= 0.0:
		    raise BadDebtInput, "The payment frequency must be positive"

	    except TypeError:
	        raise BadDebtInput, "The payment frequency must be numeric"

	self.name = name
	self.principal = principal
	self.init_date = init_date
	self.term = term
	self.rate = rate
	self.pmt_freq = pmt_freq		
	self.comment = comment


	self.scheduler = DebtPmtScheduler()	#This is a helper class
	self.pmt_schedules = []
	self.cash_schedules = []

    def check_defined(self):
	for item in [self.principal, self.term, self.rate, self.pmt_freq, self.init_date]:
            if item == None:
                raise MissingInfoError, "You need to set %s before generating the debt schedule" % item 


    def build_debt_schedule(self):
	self.check_defined()      

	#create the schedule of interest accumulation/calculation -- works around the interspersed payments
	
	s = df.DataFrame()

	for ps in self.pmt_schedules:
	    s = s.join(ps, how = 'outer').fillna(0.0)

	for cs in self.cash_schedules:
	    s = s.join(cs, how = 'outer').fillna(0.0)
	
        self.schedule = df.DataFrame(index = s.index)
        
        #Now we just need to step through the payment dates to calculate the schedule 

	

        #set up the principal column
        self.schedule['principal'] = np.zeros(len(self.schedule))
	self.schedule['interest'] = np.zeros(len(self.schedule))
	self.schedule['cash_proceeds'] = np.zeros(len(self.schedule))
	self.schedule['principal_payment'] = np.zeros(len(self.schedule))

	


	all_but_first = self.schedule.index[1:]

	#do the first row
	self.schedule['principal'][0] = s['proceeds'][0] - s['payments'][0]
	P = self.schedule['principal'][0]
	self.schedule['cash_proceeds'][0] = s['proceeds'][0]
	self.schedule['principal_payment'][0] = s['payments'][0]
	
	#iterate through the rest of the rows
	for i in all_but_first:

	    if i in self.interest_dates:						
	         self.schedule.loc[i,'interest'] = self.rate/self.pmt_freq*P

	    self.schedule.loc[i,'principal'] = P + s.loc[i,'proceeds'] + self.schedule.loc[i,'interest'] - s.loc[i,'payments']
	    self.schedule.loc[i,'principal_payment'] = s.loc[i,'payments'] - self.schedule.loc[i,'interest']
	    self.schedule.loc[i,'cash_proceeds'] = s.loc[i,'proceeds']
	    P = self.schedule.loc[i,'principal']

	    if P <= 0:
	        break		#stop when there is no principal left to pay

          
        
        self.scheduled = True


    def __eq__(self, other):
        verity = isinstance(other, self.__class__)
        names = ['name', 'principal', 'term', 'rate', 'pmt_freq', 'init_date']
        if verity:
            for name in names:
                verity = verity and getattr(self, name) == getattr(other, name)
        return verity

    def __ne__(self, other):
        return not self.__eq__(other)


class Loan(Debt):
    """Container class for debt financing instruments"""

       

    def __init__(self, **kwargs):
	

	Debt.__init__(self,**kwargs)
		
              
        self.scheduled = False

    def build_debt_schedule(self):
        """Generates the loan schedule from appropriate information"""
	self.check_defined()
        #This is a normally amortized loan; if the payment schedules[] object contains an additional payment schedule, we'll add that in
        self.scheduler.pmt_normal_amortization(amt=self.principal, term=self.term, pmt_freq=self.pmt_freq, init_date = self.init_date, rate=self.rate)
	nml_amt = self.scheduler.pmt_normal_amortization(amt = self.principal, term = self.term, pmt_freq = self.pmt_freq, init_date = self.init_date, rate = self.rate)
	self.pmt_schedules.append(nml_amt)
	self.cash_schedules.append(self.scheduler.cash_upfront(amt = self.principal, init_date = self.init_date))
        self.interest_dates = nml_amt.index
	
	Debt.build_debt_schedule(self)


	
        

    def _acc_int_principal(self, principal):
        """Helper function to calculate annual accumulated interest and principal payments"""
        interest = 0.0
        pp = 0.0
        P = principal
        pmt_num = self.pmt_freq
        
        while pmt_num > 0:
            interest += P * self.rate/self.pmt_freq
            pp += self.pmt - P*self.rate/self.pmt_freq
            
            P -= self.pmt - P*self.rate/self.pmt_freq
            pmt_num -= 1
            
        return (interest, pp)

    ###!!!###The function above should be eliminated -- it is ugly


class Tax(object):
    """Main class for Tax objects"""

    def __init__(self, name = None, basis = None, deductions = None, credits = None, carryover_years = 10, carryback_years = 2, **kwargs):
        self.name = name
	self.basis = basis
	self.deductions = deductions
	self.credits = credits
	self.carryover_years = carryover_years
	self.carryback_years = carryback_years

    @property
    def name(self):
	return self._name

    @name.setter
    def name(self, v):
        if not isinstance(v,basestring):
            raise BadTaxInputError, "name must be a string"

	self._name = v

    @property
    def basis(self):
        return self._basis

    @basis.setter
    def basis(self, v):
	if v is None:
            v = df.DataFrame()

        elif not isinstance(v, pd.DataFrame):
            raise BadTaxInputError, "basis must be a dataframe containing the income bases"
        self._basis = v

    @property
    def deductions(self):
        return self._deductions

    @deductions.setter
    def deductions(self, v):
        if v is None:
            v = df.DataFrame()
        elif not isinstance(v, pd.DataFrame):
            raise BadTaxInputError, "deductions must be a dataframe containing the deductions as columns"
        self._deductions = v
        

    @property
    def credits(self):
	return self._credits

    @credits.setter
    def credits(self, v):
        if v is None:
            v = []

        elif not isinstance(v, list):
            raise BadTaxInputError, "credits must be a list of credits"

	for c in v:
	    if not isinstance(c, TaxCredit):
	        raise BadTaxInputError, "credits can only contain TaxCredits, got %s" % type(c)

	self._credits = v

    @property
    def carryover_years(self):
	return self._carryover_years

    @carryover_years.setter
    def carryover_years(self, v):
        try:
            v/100.0
            if not isinstance(v, int):
                raise BadTaxInputError, "The number of carryover years must be an integer, got %s" % type(v)

	except TypeError:
 		raise BadTaxInputError, "The number of carryover years must be numeric"

	self._carryover_years = v

    @property
    def carryback_years(self):
        return self._carryback_years

    @carryback_years.setter
    def carryback_years(self, v):
        try:
            v/100.0
            if not isinstance(v, int):
                raise BadTaxInputError, "The number of carryback years must be an integer, got %s" % type(v)

        except TypeError:
             raise BadTaxInputError, "The number of carryback years must be numeric"

        self._carryback_years = v

    def aggregate(self, dataframe, freq = 'Y'):
	"""Aggregate a dataframe by a frequency subset of its index.  Returns the aggregated dataframe.  Right now, frequency does nothing and is unadjustable--only annual"""
	key = lambda x: x.year
	dataframe['year'] = key(dataframe.index)
	agg_dataframe = (dataframe.groupby('year')).aggregate(np.sum)		#This is the aggregated dataframe
	return agg_dataframe

    def build_tax_schedule(self):
        """Creates the schedule of taxes"""
	if len(self.basis.index) == 0:
	    raise TaxUnderdefinedError, "The basis must be set for a tax to be calculated"


class GraduatedFractionalTax(Tax):
    """Proportional tax on a rate schedule"""

    def __init__(self, rate = None, **kwargs):
        self.rate = rate
        super(GraduatedFractionalTax,self).__init__(**kwargs)

    @property
    def rate(self):
        return self._rate

    @rate.setter
    def rate(self, v):
        if v is None:
            v = {}
        elif not isinstance(v, dict):
            raise BadTaxInputError, "rate must be a dictionary of max_val:tax_rate pairs"
        for key in v:
            try:
                key/100.0
	        v[key]/100.0
	    except TypeError:
                raise BadTaxInputError, "rate dict key and its value must both be numeric"
            if v[key] < 0.0:
	        raise BadTaxInputError, "The tax rate must be non-negative"

	self._rate = v

    def build_tax_schedule(self):
	#The graduated schedule should be anchored with zero: {0:rate0, bracket1:rate1, ...}
	#we will tack on np.inf to the end to make sure that we don't overrun
	super(GraduatedFractionalTax,self).build_tax_schedule()
	if not self.rate:
	    raise TaxUnderdefinedError, "The rate is not fully prescribed"

        self.schedule = self.basis.join(self.deductions, how = "outer").fillna(0.0)
	self.schedule['taxable_income'] = np.zeros(len(self.schedule.index))
	self.schedule['gross_income'] = np.zeros(len(self.schedule.index))	
	for col in self.basis:
	    self.schedule['taxable_income'] += self.schedule[col]
	    self.schedule['gross_income'] += self.schedule[col]
	for col in self.deductions:
	    self.schedule['taxable_income'] -= self.schedule[col]

	#group and aggregate by year -- this is the default behavior of 
     	
	self.schedule_agg = self.aggregate(self.schedule)
        self.schedule_agg['tax'] = np.zeros(len(self.schedule_agg.index))

	


	#we actually need to do carryover up here
	#walk through the taxable income sheet and apply carryover/carryback as appropriate
	carryover = deque(maxlen = self.carryover_years)
	for i in self.schedule_agg.index:
	   
	    if self.schedule_agg.loc[i,'taxable_income'] < 0.0:
		amt = -1 * self.schedule_agg.loc[i, 'taxable_income']
	        #carryback first
		for j in range(0,self.carryback_years):
		    try:
			inc = self.schedule_agg.loc[i - (self.carryback_years -j),'taxable_income']
		        if inc > 0.0:
			    if amt <= inc:
                                self.schedule_agg.loc[i- (self.carryback_years -j),'taxable_income'] -= amt
				amt = 0.0
			    else:
				amt -= inc
				self.schedule_agg.loc[i - (self.carryback_years -j), 'taxable_income'] = 0.0
		    except KeyError:
                        pass #This is here for the case where there are fewer years to look at in the project than allowed in carryback

		#carryforward now
		carryover.append(amt)		#this works, because deque just discards objects to the left when it is full
		#set the taxable income in this year to zero, now that we are done with it, so that we don't have negative taxes
		self.schedule_agg.loc[i, 'taxable_income'] = 0.0


            else:
		while carryover and self.schedule_agg.loc[i,'taxable_income'] > 0.0:
		    amt = carryover.popleft()
		    if amt <= self.schedule_agg.loc[i,'taxable_income']:
			self.schedule_agg.loc[i,'taxable_income'] -= amt
		    else:
		        amt -= self.schedule_agg.loc[i,'taxable_income']
			self.schedule_agg.loc[i,'taxable_income'] = 0.0
			carryover.appendleft(amt)			#stick the remainder back in the deque
		if carryover:
		    carryover.append(0.0)				#this was a profitable year, so need to move the deque along a year -- enough profitable years will push the carryover over the end
	
	sorted_brackets = sorted(self.rate)
	sorted_brackets.append(np.inf)

	found_bracket_mask = df.DataFrame({'mask':np.array([True]*len(self.schedule_agg.index))}, index = self.schedule_agg.index)
	#comparisons must be made on slices, of course

	for n in range(1,len(sorted_brackets)):
	    self.schedule_agg['tax'][self.schedule_agg['taxable_income']>=sorted_brackets[n]] += (sorted_brackets[n]-sorted_brackets[n-1])*self.rate[sorted_brackets[n-1]]
	    self.schedule_agg['tax'][np.logical_and(self.schedule_agg['taxable_income']<sorted_brackets[n],found_bracket_mask['mask'])] += (self.schedule_agg['taxable_income']-sorted_brackets[n-1])*self.rate[sorted_brackets[n-1]]
            
	    found_bracket_mask['mask'][self.schedule_agg['taxable_income']<sorted_brackets[n]] = False	#When you find the right tax bracket, stop adding to these columns

	#THIS ASSUMES THAT CREDITS ARE IN THE PRIORITY ORDER!!!

	for credit in self.credits:
	    credit.build_credit_schedule()
	    agg_credit_schedule = self.aggregate(credit.schedule)
	    if credit.refundable:
		self.schedule_agg['tax'] -= agg_credit_schedule['credits']
	    else:
                self.schedule_agg['tax'][self.schedule_agg['tax']>agg_credit_schedule['credits']] -= agg_credit_schedule['credits']
	        self.schedule_agg['tax'][np.logical_and(self.schedule_agg['tax']<=agg_credit_schedule['credits'], self.schedule_agg['tax']>0.0)] = 0.0


	#now we need to build the schedule by apportioning the tax according to the income
	self.schedule['tax'] = np.zeros(len(self.schedule.index))
	for year in self.schedule_agg.index:
	    if self.schedule_agg.loc[year, 'tax'] == 0:
		self.schedule['tax'][self.schedule.index.year == year] = 0.0
	    else:
	        self.schedule['tax'][self.schedule.index.year == year] = self.schedule_agg.loc[year, 'tax'] * self.schedule['gross_income']/self.schedule_agg.loc[year,'gross_income']
	

	
class FractionalTax(GraduatedFractionalTax):
    """Proportional tax at a fixed rate"""

    def __init__(self, rate = None, **kwargs):
	self.rate = rate
	super(FractionalTax, self).__init__(rate = rate, **kwargs)

    @property
    def rate(self):
	return self._rate

    @rate.setter
    def rate(self, v):
	if v is None:
	    self._rate = {}
	else:
            try:
                v/100.0
                if v < 0.0:
                    raise BadTaxInputError, "The rate must be non-negative"
            except TypeError:
		    raise BadTaxInputError, "The rate must be numeric, got %s" % type(v)
	    #using a special case of the GraduatedFractionalTax
            self._rate = {0.0:v}	

class GraduatedFixedTax(GraduatedFractionalTax):
    """Fixed tax payments throughout a year, with no proportion based on when the income was incurred"""

    def build_tax_schedule(self):
        super(GraduatedFixedTax,self).build_tax_schedule()
	if not self.rate:
	    raise TaxUnderdefinedError, "The rate dictionary is empty, need it to calculate the tax."
	self.schedule = self.basis.join(self.deductions, how = "outer").fillna(0.0)
	self.schedule['taxable_income'] = np.zeros(len(self.schedule.index))
	for col in self.basis:
	    self.schedule['taxable_income'] += self.schedule[col]
	for col in self.deductions:
	    self.schedule['taxable_income'] -= self.schedule[col]

	#group and aggregate by year -- this is the default behavior of 
        self.schedule_agg = self.aggregate(self.schedule)
	#we actually need to do carryover up here
	#walk through the taxable income sheet and apply carryover/carryback as appropriate
	carryover = deque(maxlen = self.carryover_years)
	for i in self.schedule_agg.index:
	   
	    if self.schedule_agg.loc[i,'taxable_income'] < 0.0:
		amt = -1 * self.schedule_agg.loc[i, 'taxable_income']
	        #carryback first
		for j in range(0,self.carryback_years):
		    try:
			inc = self.schedule_agg.loc[i - (self.carryback_years -j),'taxable_income']
		        if inc > 0.0:
			    if amt <= inc:
                                self.schedule_agg.loc[i- (self.carryback_years -j),'taxable_income'] -= amt
				amt = 0.0
			    else:
				amt -= inc
				self.schedule_agg.loc[i - (self.carryback_years -j), 'taxable_income'] = 0.0
		    except KeyError:
                        pass #This is here for the case where there are fewer years to look at in the project than allowed in carryback

		#carryforward now
		carryover.append(amt)		#this works, because deque just discards objects to the left when it is full
		#set the taxable income in this year to zero, now that we are done with it, so that we don't have negative taxes
		self.schedule_agg.loc[i, 'taxable_income'] = 0.0


            else:
		while carryover and self.schedule_agg.loc[i,'taxable_income'] > 0.0:
		    amt = carryover.popleft()
		    if amt <= self.schedule_agg.loc[i,'taxable_income']:
			self.schedule_agg.loc[i,'taxable_income'] -= amt
		    else:
		        amt -= self.schedule_agg.loc[i,'taxable_income']
			self.schedule_agg.loc[i,'taxable_income'] = 0.0
			carryover.appendleft(amt)			#stick the remainder back in the deque
		if carryover:
		    carryover.append(0.0)				#this was a profitable year, so need to move the deque along a yea	



	self.schedule_agg['tax'] = np.zeros(len(self.schedule_agg.index))
	sorted_brackets = sorted(self.rate)
	sorted_brackets.append(np.inf)
	n = 0
	while n < len(sorted_brackets)-1:
	    self.schedule_agg['tax'][np.logical_and(self.schedule_agg['taxable_income']>=sorted_brackets[n],self.schedule_agg['taxable_income']<sorted_brackets[n+1])] = self.rate[sorted_brackets[n]]
            n += 1
	#now we need to build the schedule by apportioning the tax according to the income
	
	for credit in self.credits:
	    credit.build_credit_schedule()
	    agg_credit_schedule = self.aggregate(credit.schedule)
	    if credit.refundable:
		self.schedule_agg['tax'] -= agg_credit_schedule['credits']
	    else:
                self.schedule_agg['tax'][self.schedule_agg['tax']>agg_credit_schedule['credits']] -= agg_credit_schedule['credits']
	        self.schedule_agg['tax'][np.logical_and(self.schedule_agg['tax']<=agg_credit_schedule['credits'], self.schedule_agg['tax']>0.0)] = 0.0

	self.schedule['tax'] = np.zeros(len(self.schedule.index))
	for year in self.schedule_agg.index:
	    if year % 4 == 0:			#leap year
		self.schedule['tax'][self.schedule.index.year == year] = self.schedule_agg.loc[year,'tax']/366.0
	    else:
		self.schedule['tax'][self.schedule.index.year == year] = self.schedule_agg.loc[year,'tax']/365.0

    

class FixedTax(GraduatedFixedTax):
    """Fixed tax with a single flat amount"""

    @property
    def rate(self):
        return self._rate

    @rate.setter
    def rate(self,v):
	if v is None:
	    self._rate = {}
	else:        
	    try:
                v/100.0
                if v < 0.0:
                    raise BadTaxInputError, "The fixed tax rate must be non-negative (otherwise, use a credit)"
            except TypeError:
                raise BadTaxInputError, "The fixed tax must be numeric, got %s" % type(v)
        
            self._rate = {0.0:v}


class TaxCredit(object):
    """Main class for tax credits"""

    def __init__(self, refundable = False, kind = 'Fixed', **kwargs):
	self.refundable = refundable
	self.kind = kind
	self.name = kwargs['name']
	try:
	    self.credit = globals()['%sTax' % self.kind](**kwargs)
	except NameError:
	    raise BadTaxCreditInput, "%s is not a valid kind of TaxCredit" % self.kind

    @property
    def refundable(self):
        return self._refundable

    @refundable.setter
    def refundable(self, v):
        if not isinstance(v, bool):
            raise BadTaxCreditInput, "refundable must be a boolean value, got %s" % type(v)
        self._refundable = v

    @property
    def kind(self):
        return self._kind

    @kind.setter
    def kind(self, v):
        if not isinstance(v, basestring):
            raise BadTaxCreditInput, "kind must be a string"
        self._kind = v

    @property
    def basis(self):
	return self.credit.basis

    @basis.setter
    def basis(self, v):
        self.credit.basis = v


    def build_credit_schedule(self):
        self.credit.build_tax_schedule()

	self.schedule = df.DataFrame({'credits':self.credit.schedule['tax']})

class TaxManager(object):
    """General aggregator for taxes"""

    def __init__(self, revenue = None, deductions = None, credits = None, taxes = None):
	#Main containers
	self.revenue = df.DataFrame()
	self.deductions = df.DataFrame()        
	self.taxes = {}
	self.credits = {}

	#correspondence dictionaries
	self.revenue_dict = {}
	self.deductions_dict = {}
	self.credits_dict = {}
	self.deductible_taxes = {}

	self.add_revenue(revenue)
	self.add_deductions(deductions)
	self.add_credits(credits)
	self.add_taxes(taxes)
	
    def add_revenue(self, revenue, name = "", columns = None):
        """Adds revenue streams from a dataframe"""

	if revenue is None:
	    return

        elif not isinstance(revenue, df.DataFrame):
            raise TaxManagerError, "revenue must be an instance of DataFrame, got %s" % type(revenue)

        else:
	    rn_revenue = revenue.rename(columns = lambda x: "%s_%s" % (name,x))

            if columns is None:
                columns = rn_revenue.columns
	    elif isinstance(columns, basestring):
		columns = ["%s_%s" % (name, columns)]
	    elif isinstance(columns, list):
		columns = ["%s_%s" % (name, c) for c in columns]
	    else:
		raise TaxManagerError, "columns must be a string or a list, got %s" % type(columns)
            for col in columns:
                if not col in rn_revenue.columns:
		    raise TaxManagerError, "%s is not a column in the given revenue dataframe" % col
	        if col in self.revenue.columns:
		    raise TaxManagerError, "%s already exists in the revenue dataframe" % col
	    self.revenue = self.revenue.join(rn_revenue[columns],how='outer').fillna(0.0)

    def add_deductions(self, deductions, name = "", columns = None):
        """Adds deduction streams from a dataframe"""
	if deductions is None:
	    return

        elif not isinstance(deductions, df.DataFrame):
	    raise TaxManagerError, "deductions must be an instance of DataFrame, got %s" % type(deductions)

	else:
	    rn_deductions = deductions.rename(columns = lambda x: "%s_%s" % (name,x))
	    
	    if columns is None:
		columns = rn_deductions.columns

	    elif isinstance(columns, basestring):
		columns = ["%s_%s" % (name, columns)]
	    elif isinstance(columns, list):
		columns = ["%s_%s" % (name, c) for c in columns]
	    else:
		raise TaxManagerError, "columns must be a string or a list, got %s" % type(columns)


	    for col in columns:
		if not col in rn_deductions.columns:
		    raise TaxManagerError, "%s is not a column in the given deduction dataframe" % col
		if col in self.deductions.columns:
		    raise TaxManagerError, "%s already exists in the deductions dataframe" % col
            self.deductions = self.deductions.join(rn_deductions[columns], how='outer').fillna(0.0)

    
    def add_taxes(self, taxes=None, revenue_associations=None, deduction_associations=None, credit_associations = None):
	"""Adds a set of taxes to the TaxManager"""
	if taxes is None:
	    return

	elif isinstance(taxes, Tax):
	    taxes = [taxes]
	elif not isinstance(taxes, list):
	    raise TaxManagerError, "taxes must be either a Tax object or a list of tax objects, got %s" % type(col)
	for tax in taxes:
	    if not isinstance(tax, Tax):
		raise TaxManagerError, "taxes must only contain Tax objects, got %s" % type(col)


	for tax in taxes:
	    if tax.name in self.taxes or tax.name in self.credits:
		raise TaxManagerError, "This tax (%s) has a name conflict" % tax.name
	    self.taxes[tax.name] = tax

	    if tax.basis is not None:
		self.add_revenue(tax.basis)
		assc_cols = ["%s_%s" % (tax.name, col) for col in tax.basis.columns] 
		self.associate_revenue(tax.name, assc_cols)
            if tax.deductions is not None:
		self.add_deductions(tax.deductions)
		assc_cols = ["%s_%s" % (tax.name, col) for col in tax.basis.columns]
		self.associate_deductions(tax.name, assc_cols)

	    if tax.credits is not None:
		self.add_credits(tax.credits)
		assc_credits = [c.name for c in tax.credits]
		self.associate_credits(tax.name, assc_credits)

	    self.associate_revenue(tax.name, revenue_associations)
	    self.associate_deductions(tax.name, deduction_associations)
	    self.associate_credits(tax.name, credit_associations)

    def add_credits(self, credits = None, revenue_associations = None):
	if credits is None:
	    return

        elif isinstance(credits, TaxCredit):
	    credits = [credits]
	elif not isinstance(credits, list):
	    raise TaxManagerError, "credits must be either a TaxCredit object for a list of TaxCredit objects"
	for credit in credits:
	    if not isinstance(credit, TaxCredit):
		raise TaxManagerError, "not a TaxCredit object, got %s" % type(credit)
        for credit in credits:
	    if credit.name in self.credits or credit.name in self.taxes:
	        raise TaxManagerError, "This credit (%s) has a name conflict" % credit.name
	    self.credits[credit.name] = credit

            if credit.basis is not None:
	        self.add_revenue(credit.basis)
	        assc_cols = ["%s_%s" % (credit.name, col) for col in credit.basis.columns]
	        self.associate_revenue(credit.name, assc_cols)
	    self.associate_revenue(credit.name, revenue_associations)


    def associate_revenue(self, name, revenue_associations):
	self._associate('revenue_dict', name, revenue_associations, ['taxes','credits'], 'revenue')

    def associate_deductions(self, name, deduction_associations):
	self._associate('deductions_dict', name, deduction_associations, ['taxes'],'deductions')

    def associate_credits(self, name, credit_associations):
	self._associate('credits_dict', name, credit_associations, ['taxes'],'credits')

    def associate_deductible_taxes(self, name, tax_associations):
	self._associate('deductible_taxes', name, tax_associations, ['taxes'], 'taxes')

    def _associate(self, index, name, assc, containers, df):

	if assc is None:
 	    return

	m = True
	for c in containers:
	    if name in getattr(self,c):
		m = False
	        break
	if m:
	    raise TaxManagerError, "%s does not exist in either the tax or credit dictionaries" % name 
	
	if not name in getattr(self, index):
	        getattr(self,index)[name] = []

	if isinstance(assc, basestring):
	        
	    assc = [assc]	    
	
	elif isinstance(assc, dict):
	    if not name in assc:
		raise TaxManagerError, "%s does not exist in the association dictionary" % name
	    elif not isinstance(assc[name], list):
	        raise TaxManagerError, "If assc is a dictionary, the values must be lists of associations"
	    assc = assc[name]

	elif not isinstance(assc, list):
	    raise TaxManagerError, "assc must be either a string, a dictionary, or a list"

	d = getattr(self, df)

        for n in assc:
            if isinstance(d, pd.DataFrame):
	        if n not in d.columns:
		    raise TaxManagerError, "%s does not exist in the relevant dataframe" % n
	    elif isinstance(d, dict):
		if n not in d:
		    raise TaxManagerError, "%s does not exist in the relevant dataframe" % n
	getattr(self,index)[name].extend(assc)


    def create_tax(self, kind, revenue = None, deductions = None, credits = None, **kwargs):
	try:
	    new_tax = globals()['%sTax' % kind](**kwargs)
	except KeyError:
	    raise TaxManagerError, "%s is not a valid type of Tax" % kind

	self.add_taxes(new_tax, revenue_associations = revenue, deduction_associations = deductions, credit_associations = credits)
	

    def create_tax_credit(self, kind, revenue = None, **kwargs):
	try:
	    kwargs['kind'] = kind
	    new_credit = globals()['TaxCredit'](**kwargs)
	except KeyError:
	    raise TaxManagerError, "%s is not a valid type of TaxCredit" % kind
        self.add_credits(new_credit, revenue_associations = revenue)

    def build_tax_schedule(self):
	"""Builds the aggregated tax schedule"""
	#Create the overall schedule
	#For each of the taxes, reset the basis, deductions, and credits
	#loop on a convergence criterion
	master = self.revenue.join(self.deductions, how = 'outer').fillna(0.0)

	self.schedule = df.DataFrame(index = master.index)
	self.schedule['tax'] = np.zeros(len(self.schedule.index))

	#set the bases, deductions, and credits for each of the taxes
	last = df.DataFrame(index = self.schedule.index)

	for credit in self.credits:
	    try:
		self.credits[credit].basis = master[self.revenue_dict[credit]]
	    except KeyError:
		raise TaxManagerError, "%s is underdefined.  Need to link a basis to this credit" % credit
	
	for tax in self.taxes:
	    try:
	        self.taxes[tax].basis = master[self.revenue_dict[tax]]
	        self.taxes[tax].deductions = master[self.deductions_dict[tax]]
	    except KeyError:
                raise TaxManagerError, "%s is underdefined.  Need to link a basis and a deduction" % tax
	    self.taxes[tax].credits = None
	    if tax in self.credits_dict:
	        for credit in self.credits_dict[tax]:
		    self.taxes[tax].credits.append(self.credits[credit])
	    if tax in self.deductible_taxes:
		for d_tax in self.deductible_taxes[tax]:
		    self.taxes[tax].deductions[d_tax] = np.zeros(len(self.taxes[tax].deductions.index))
	    last[tax] = np.zeros(len(self.schedule.index))
	converged = False
	N = 0

	while not converged and N < 5:
	    for tax in self.taxes:
		self.taxes[tax].build_tax_schedule()
	        #determine convergence
	        self.schedule['%s_tax'%tax] = self.taxes[tax].schedule['tax']
	        self.schedule.fillna(0.0)
		converged = ((self.schedule['%s_tax' % tax] - last[tax])<0.01).all()	#using absolute convergence here
	    for tax in self.taxes:
		if tax in self.deductible_taxes:
		   for d_tax in self.deductible_taxes[tax]:
			self.taxes[tax].deductions[d_tax] = self.taxes[d_tax].schedule['tax']
		   tax.deductions.fillna(0.0) 	#deal with mismatches

	    N += 1

	self.schedule['tax'] = np.zeros(len(self.schedule.index))
	for tax in self.taxes:
	    self.schedule['tax'] += self.schedule['%s_tax' % tax]


class PF_FileLoader:
    """Reads the XML save file for a given project"""
    def __init__(self, source):
        if isinstance(source, str):
	    self.doc = etree.parse(source)	#Should do some error checking here in the future
        elif isinstance(source, etree.Element):
            pass        #This is here so that a portion of a larger ElementTree can be passed in, for VentureStrategy 
        self.project = CapitalProject()         #This will not work just yet -- need to have a name for the project, too
        self.docroot = self.doc.getroot()



    def _load_data(self):
        self._load_fin_params()
        self._load_cap_costs()
        self._load_fixed_costs()
        self._load_variable_costs()
        self._load_debt()
        

    def _load_cap_costs(self):
        capcosts = self.docroot.find("capital_costs")
        new_capcosts = CapitalCosts()
        for cap_exp in capcosts[0]:
            new_cap_exp = CapitalExpense(cap_exp.attrib['name'])
            for prop in cap_exp:
                if prop.tag != "comment":
                    setattr(new_cap_exp, prop.tag, float(prop.text))
                else:
                    new_cap_exp.comment.append(prop.text)
            new_capcosts.add_capital_item(new_cap_exp)
        
        for cap_exp in capcosts[1]:                  #OK, this could be more introspective, but bleh for now
            if cap_exp.attrib['depreciable'] == 'True':
                new_capcosts.indirect_deprec_capital[cap_exp.tag] = self._cast_special(cap_exp.text,float)
            else:
                new_capcosts.indirect_nondeprec_capital[cap_exp.tag] = self._cast_special(cap_exp.text,float)
        self.project.setCapitalCosts(new_capcosts)


    def _load_variable_costs(self):
        new_variable_costs = VariableCosts()
        var_costs = self.docroot.find("variable_costs")
        for var_exp in var_costs:
            new_var_exp = VariableExpense(var_exp.attrib["name"])
            for prop in var_exp:
                if prop.tag == "unit_cost":
                    new_var_exp.unit_cost = uv.UnitVal(self._cast_special(prop.text,float),prop.attrib["units"])
                elif prop.tag == "prod_req":
                    new_var_exp.prod_req = uv.UnitVal(self._cast_special(prop.text,float), prop.attrib["units"])
                else:
                    pass
            new_variable_costs.add_variable_exp(new_var_exp)
        self.project.setVariableCosts(new_variable_costs)

    def _load_fixed_costs(self):
        new_fixed_costs = FixedCosts()
        fixed_costs = self.docroot.find("fixed_costs")
        for fixed_cost in fixed_costs:
            #again, error checking needed here to make this robust to bad XML
            new_fixed_costs[fixed_cost.tag] = self._cast_special(fixed_cost.text, float)
        self.project.setFixedCosts(new_fixed_costs)

    def _load_fin_params(self):
        new_fin_params = FinancialParameters()
        integers = ['Analysis_period', 'Depreciation_length', 'Plant_life']
        fin_params = self.docroot.find("financial_parameters")
        for fin_param in fin_params:
            if fin_param.tag == "Design_cap":				#reflects new naming convention NOT yet in use
                new_fin_params[fin_param.tag] = uv.UnitVal(self._cast_special(fin_param.text,float), fin_param.attrib["units"])
            elif fin_param.tag == "Depreciation_type":
                new_fin_params[fin_param.tag] = fin_param.text
            elif fin_param.tag == "Initial_period":
                new_fin_params[fin_param.tag] = dt.datetime.strptime(fin_param.text,"%Y-%m-%d")
            elif fin_param.tag == "Capital_expense_breakdown":
                if fin_param.attrib["type"] == "simple":
                    breakdown = []
                    for item in fin_param:
                        breakdown.append(float(item.text))
                    new_fin_params[fin_param.tag] = breakdown
                else:
                    pass						#include cases for other types of capital cost breakdowns here
                    
            elif fin_param.tag in integers:
                new_fin_params[fin_param.tag] = self._cast_special(fin_param.text,int)
            else:
                new_fin_params[fin_param.tag] = self._cast_special(fin_param.text,float)
        self.project.setFinancialParameters(new_fin_params)		#This function does not yet exist, so this won't work right now

    def _load_debt(self):
        new_debt_portfolio = DebtPortfolio()
        securities = self.docroot.find("debt_portfolio")
        for security in securities:
            if security.tag == "loan":
                new_loan = Loan(security.attrib['name'])
                for prop in security:
                    if prop.tag == 'strt_year' or prop.tag == 'pmt_freq':
                        setattr(new_loan, prop.tag, self._cast_special(prop.text,int))
                    else:
                        setattr(new_loan, prop.tag, self._cast_special(prop.text,float))
                new_debt_portfolio.add_loan(new_loan)
            elif security.tag == "bond":
                pass

        self.project.setDebt(new_debt_portfolio)


    def load(self):
        self._load_data()
        return self.project

    def _cast_special(self, text, typ):
        if text == 'None':
            return None
        else:
            return typ(text)            

class PF_FileSaver:
    def __init__(self, project, filename):
        self.file = open(filename, "w")
        self.root = etree.Element('project')
        self.doc = etree.ElementTree(self.root)
        self.project = project

    def _save_capex(self):
        capex = etree.SubElement(self.root, 'capital_costs')
        #write the direct capital costs
        d_capex = etree.SubElement(capex, 'direct_capital_costs')
        if self.project.capex is not None:
            for dc in self.project.capex.direct_capital:
                cap = etree.SubElement(d_capex, 'capital_expense', name=dc.name)
                ui = etree.SubElement(cap, 'uninstalled_cost')
                ui.text = str(dc.uninstalled_cost)
                inst_fac = etree.SubElement(cap, 'installation_factor')
                inst_fac.text = str(dc.installation_factor)
        #write the indirect capital costs
        i_capex = etree.SubElement(capex, 'indirect_capital_costs')
        if self.project.capex is not None:
            for ic,val in self.project.capex.indirect_deprec_capital.items():
                cap = etree.SubElement(i_capex, ic, depreciable = 'True')
                cap.text = str(val)
            for ic, val in self.project.capex.indirect_nondeprec_capital.items():
                cap = etree.SubElement(i_capex, ic, depreciable = 'False')
                cap.text = str(val)
            

    def _save_variable_costs(self):
        v = etree.SubElement(self.root, 'variable_costs')
        if self.project.variable_costs is not None:
            for ve in self.project.variable_costs.variable_exps:
                vexp = etree.SubElement(v, 'variable_expense', name = ve.name)
                uc = etree.SubElement(vexp, 'unit_cost', units = ve.unit_cost.units)
                uc.text = str(ve.unit_cost.value)
                pr = etree.SubElement(vexp, 'prod_req', units = ve.prod_req.units)
                pr.text = str(ve.prod_req.value)
            

    def _save_fixed_costs(self):
        f = etree.SubElement(self.root, 'fixed_costs')
        if self.project.fixed_costs is not None:
            for fc, val in self.project.fixed_costs.fixed_costs.items():
                tag = etree.SubElement(f, fc)
                tag.text = str(val)

    def _save_debt(self):
        d = etree.SubElement(self.root, 'debt_portfolio')
        if self.project.debt is not None:
            for loan in self.project.debt.loans:
                loan_tag = etree.SubElement(d, 'loan', name = loan.name)
                it = ['principal', 'term', 'rate', 'pmt_freq', 'strt_period']
                for name in it:
                    tag = etree.SubElement(loan_tag, name)
                    tag.text = str(getattr(loan, name))

    def _save_fin_params(self):
        fp = etree.SubElement(self.root, 'financial_parameters')
        exceptions = ['Design_cap', 'Capital_expense_breakdown', 'Initial_period']
        if self.project.fin_param is not None:
            for par, val in self.project.fin_param.params.items():
                if par not in exceptions:
                    par_tag = etree.SubElement(fp, par)
                    par_tag.text = str(val)
                elif par == 'Design_cap':
                    if val is None:
                        par_tag = etree.SubElement(fp, par, units = 'None')
                        par_tag.text = 'None'
                    else:
                        par_tag = etree.SubElement(fp, par, units = val.units)
                        par_tag.text = str(val.value)           
                elif par == 'Capital_expense_breakdown':
                    if val is None:
                        par_tag = etree.SubElement(fp, par)
                        par_tag.text = 'None'
                    elif isinstance(val, list):
                        par_tag = etree.SubElement(fp, par, type = 'simple')
                        index = 0
                        for item in val:
                            it_tag = etree.SubElement(par_tag, 'item', index = str(index))
                            index += 1
                            it_tag.text = str(item)
                    else:
                        print "Not implemented yet!"

                elif par == 'Initial_period':
                    if val is None:
                        par_tag = etree.SubElement(fp, par)
                        par_tag.text = 'None'
                    elif isinstance(val, str):
                        par_tag = etree.SubElement(fp, par)
                        par_tag.text = val.strftime("%Y-%m-%d")
                    else:
                        raise ProjFinError, "Initial period is an instance of %s, it should be an instance of str" % type(val)

    def save(self):
        self._save_capex()
        self._save_variable_costs()
        self._save_fixed_costs()
        self._save_debt()
        self._save_fin_params()
        self.doc.write(self.file, pretty_print=True)
        self.file.close()


if __name__ == "__main__":
    loader = PF_FileLoader('proj_fin_test.xml')
    project = loader.load()
    saver = PF_FileSaver(project, 'save_test.xml')
    saver.save()
    loader2 = PF_FileLoader('save_test.xml')
    project2 = loader2.load()
    print project == project2
    
 


