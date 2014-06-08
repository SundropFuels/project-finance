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

class ProjFinError(Exception):
    def __init__(self,value):
        self.value = value

    def __str__(self):
        return repr(self.value)

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
        self.cf_sheet = pd.DataFrame(data = count, index = dates)

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
        output = pd.DataFrame(np.zeros(len(self.cf_sheet)), index = self.cf_sheet.index)
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
        mask = pd.DataFrame(data = np.zeros(len(self.cf_sheet)), index = self.cf_sheet.index)
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

        if key == 'Capital_expense_breakdown' and not (isinstance(value,list) or isinstance(value,dict) or isinstance(value,pd.DataFrame)) and value is not None:
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

class QuoteBasis:
    """This is the class for holding quotation information that a capital item will require to scale"""
    def __init__(self, price = None, date = None, size_basis = None, source = None):
        if price = None or date = None or size_basis = None:
            raise QuoteBasisBadInput, "QuoteBasis is underspecified"
        try:
            if price < 0:
                raise QuoteBasisBadInput, "price must be greater than zero"
        except ValueError:
                raise QuoteBasisBadInput, "price must be numeric"

        if not isinstance(date, dt.datetime):
            raise QuoteBasisBadInput, "date must be a datetime.datetime object"

        if not isinstance(source, string):
            raise QuoteBasisBadInput, "The source must be a string"

        if not isinstance(size_basis, uv.UnitVal):
            raise QuoteBasisBadInput, "The size basis must be a UnitVal"

        self.price = price
        self.date = date
        self.size_basis = size_basis 

    def scale(self, new_scale=None, method = 'linear', exponent = 1.0):
        """Scales the existing cost to a new basis and returns the value"""
        if new_scale is None:
            raise QuoteBasisBadInput, "A new scale to price to is missing"
        if not isinstance(new_scale, uv.UnitVal):
            raise QuoteBasisBadInput, "The new scale must be a unit value"

        if not new_scale.value > 0:
            raise QuoteBasisBadInput, "The new scale must be positive in value"

        try:
            return getattr(self, '_%s_scale' % method, new_scale, exponent)

        except AttributeError:
            raise QuoteBasisBadInput, "%s is not a valid scaling method" % method

    def _linear_scale(self, new_scale, exponent):  #this may be a good place for **kwargs
        """Linear price scaling"""
        return self.price * new_scale/self.scale_basis

    def _exponent_scale(self, new_scale, exponent):
        """Exponential price scaling"""
        return self.price * (new_scale/self.scale_basis)**exponent


class InstallModel:
    """Class to hold models for installed cost"""
    def __init__(self):
        pass

    def calc_installed_cost(self):
        pass

class FactoredInstallModel(InstallModel):
    def __init__(self, factor):
        self.factor = factor

    def calc_installed_cost(self, base_cost):
        return self.factor * base_cost

class FixedInstallModel(InstallModel):
    def __init__(self, fixed_amt):
        self.fixed = fixed_amt

    def calc_installed_cost(self, base_cost):
        return self.fixed + base_cost




class CapitalExpense:
    """Container class for capital expenditures"""
    MACRS = {}
    MACRS['3'] = np.array([0.3333, 0.4445, 0.1481, 0.0741])
    MACRS['5'] = np.array([0.2, 0.32, 0.1920, 0.1152, 0.1152, 0.0576])
    MACRS['7'] = np.array([0.1429, 0.2449, 0.1749, 0.1249, 0.0893, 0.0892, 0.0893, 0.0446])
    MACRS['10'] = np.array([0.1000, 0.18, 0.144, 0.1152, 0.0922, 0.0737, 0.0655, 0.0655, 0.0656, 0.0655, 0.0328])
    MACRS['15'] = np.array([0.05, 0.095, 0.0855, 0.0770, 0.0693, 0.0623, 0.0590, 0.0590, 0.0591, 0.0590, 0.0591, 0.0590, 0.0591, 0.0590, 0.0591, 0.0295])
    MACRS['20'] = np.array([0.0375, 0.07219, 0.06677, 0.06177, 0.05713, 0.05285, 0.04888, 0.04522, 0.04462, 0.04461, 0.04462, 0.044610, 0.04462, 0.04461, 0.04462, 0.04461, 0.04462, 0.04461, 0.04462, 0.04461, 0.02231])
   
    gl_add_info = OrderedDict([('name',('Name',str)),('uninstalled_cost',('Uninstalled cost',float)),('installation_factor',('Installation factor',float))])


    def __init__(self, tag, name, description = None, installation_model = None, size_basis = None, quote_basis = None, depreciation_type = 'straight-line'):
        self.name = name
        self.tag = tag
        self.description = description
        self.set_install_model(installation_model)
        self.set_size_basis(size_basis)
        self.set_quote_basis(quote_basis)
        self.set_depreciation_type(depreciation_type)
        self.comments = []

    def set_install_model(self, install_model):
        if not isinstance(install_model, InstallModel):
            raise BadCapitalCostInput, "install_model must be of class InstallModel"
        self.install_model = install_model

    def set_size_basis(self, size_basis):
        if not isinstance(size_basis, uv.UnitVal):
            raise BadCapitalCostInput, "The size basis must be of class UnitVal"
        if not size_basis.value > 0:
            raise BadCapitalCostInput, "The size basis must be positive"
        self.size_basis = size_basis

    def set_quote_basis(self, quote_basis):
        if not isinstance(quote_basis, QuoteBasis):
            raise BadCapitalCostInput, "The quote_basis must be of type QuoteBasis"
        self.quote_basis = quote_basis

    def set_depreciation_type(self, dep_type):
        dep_types = ['straight-line','MACRS', 'schedule']
        if depreciation_type not in dep_types:
            raise BadCapitalCostInput, "%s is not a supported depreciation type" % depreciation_type
        self.depreciation_type = dep_type



    def set_cost(self, uninstalled_cost, installation_factor):
        self.uninstalled_cost = uninstalled_cost
        self.installation_factor = installation_factor
        self.installed_cost = self.uninstalled_cost * self.installation_factor


    def add_comment(self, comment):
        if type(comment) is not str:
            raise ProjFinError, "Comments must be strings"
        self.comments.append(comment)

    def TIC(self):
        """Returns the total installed cost for the basis year -- escalation done when schedule built"""
        return self.install_model.calc_installed_cost(self.quote_basis.price)

    def build_depreciation_schedule(self, starting_period, length, escalation = 'off'):
        """Fills out the depreciation capex schedule based on the type of depreciation (straight-line, MACRS, etc.)"""
        dep_methods = ['straight-line', 'MACRS']       #Need non-deprec and schedule
        #set up the schedule Dataframe
        if self.depreciation_type not in dep_methods:
            raise BadCapitalDepreciationInput, "No depreciation method selected"

        if escalation is not 'off':
            print "I need to add the escalation function -- should this be in TIC instead?"

        #call the underlying method  ##!!## -- NEED A MODE FOR NON-DEPRECIABLE CAPTIAL -- call it non-deprec
        getattr(self, '_%s_build_depreciation_schedule' % self.depreciation_type)  #Need to pass starting period and length along for this to work

    def _straight-line_build_depreciation_schedule(self, starting_period, length):
        """Fills out a straight-line depreciation schedule"""
        #all of the days will be the same - this can easily be extended to allow for various frequencies
        dates = pd.date_range(starting_period, starting_period + length*DateOffset(years=1) - DateOffset(days=1), freq = 'D')
            
        d = {'depreciation':np.ones(len(dates))}
        self.depreciation_schedule = pd.DataFrame(data = d, index = dates)  #Should we subclass this for specific types of schedule? Maybe the cash flow one
        #!!!#This is not actually correct -- need to adjust this for leap years.  Do this annually, like in the MACRS schedule below
        deprec_value_daily = self.TIC()/len(dates)
        self.depreciation_schedule['depreciation'] *= deprec_value_daily

    def _MACRS_build_depreciation_schedule(self, starting_period, length):
        """Fills out a MACRS depreciation schedule"""
            
        dates = pd.date_range(starting_period, starting_period + (length+1)*DateOffset(years=1)-DateOffset(days=1), freq = 'D')
        d = {'depreciation': np.ones(len(dates))}
        self.depreciation_schedule = pd.DataFrame(data = d, index = dates)
        for y in range(0,length+1):
                
            dep_factor = CapitalExpense.MACRS['%s' % (length)][y]/len(self.depreciation_schedule[starting_period + y*DateOffset(years=1):starting_period+(y+1)*DateOffset(years=1)-DateOffset(days=1)])
            self.depreciation_schedule[starting_period+y*DateOffset(years=1):starting_period+(y+1)*DateOffset(years=1)-DateOffset(days=1)]['depreciation'] *= dep_factor                
 
        self.depreciation_schedule['depreciation'] *= self.c_deprec_capital()
               

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.name == other.name and self.uninstalled_cost == other.uninstalled_cost and self.installation_factor == other.installation_factor and self.comments == other.comments

    def __ne__(self, other):
        return not self.__eq__(other)
    
    def set_base_scale(self, scale):
        if not isinstance(scale, tuple):
            raise pf.ProfFinError, "scale must be a tuple of the form (value, units)"

        self.scale = scale                 #scale should be a (value, units) tuple

    def set_scale_type(self, scale_type):
        self.scale_type = scale_type

    def scale(self, new_scale):
        new_capex = CapitalExpense(name = self.name)
        new_cost = self.scale_function(new_scale, self.scale, self.uninstalled_cost)
        new_capex.set_cost(new_cost, self.installation_factor)
        new_capex.comments = self.comments
        return new_capex

    def scale_function(self, new_scale, old_scale, cost):
        #convert the scales to the same basis
        converter = uc.UnitConverter()
        scaled = converter.convert(new_scale[0], new_scale[1], old_scale[1])
        if self.scale_type == 'linear':
            return cost * scaled/old_scale[0]
        elif self.scale_type == 'six_tenths':
            return cost * np.power(scaled/old_scale[0],0.6)
        else:
            return cost * scaled/old_scale[0]   #default to linear

           

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
        self.indirect_deprec_capital = {}
        self.indirect_nondeprec_capital = {}
        self._setup_depreciable_capex_dict()
        self._setup_nondeprec_capex_dict()        


    def _setup_depreciable_capex_dict(self):
        items = ['site_prep', 'engineering_and_design', 'process_contingency', 'project_contingency', 'other', 'one-time_licensing_fees', 'up-front_permitting_costs']
        for item in items:
            self.indirect_deprec_capital[item] = 0

    def _setup_nondeprec_capex_dict(self):
        self.indirect_nondeprec_capital['Land'] = 0


    def set_base_scale(self, base_scale):
        self.base_scale = base_scale                    #This must be a (value, units) tuple
        for capex in self.direct_capital:
            capex.set_base_scale(base_scale)

    def add_capital_item(self, capital_item):
        """Adds a capital item to the direct_capital list"""
        if not isinstance(capital_item, CapitalExpense):
            raise ProjFinError, "Only capital expenses can be added to the capital expense list"

        self.direct_capital.append(capital_item)

    def c_direct_capital(self):
        direct_cap_list = []
        for cap_item in self.direct_capital:
            direct_cap_list.append(cap_item.installed_cost)
        return sum(direct_cap_list)

    def c_indirect_deprec_capital(self):
        idc_list = []
        for key in self.indirect_deprec_capital.keys():
            idc_list.append(self.indirect_deprec_capital[key])
        return sum(idc_list)

    def c_deprec_capital(self):
        return self.c_direct_capital() + self.c_indirect_deprec_capital()

    def c_indirect_nondeprec_capital(self):
        idnc_list = []
        for key in self.indirect_nondeprec_capital.keys():
            idnc_list.append(self.indirect_nondeprec_capital[key])
        return sum(idnc_list)

    def c_total_capital(self):
        return self.c_deprec_capital() + self.c_indirect_nondeprec_capital()

    def build_capex_schedule(self, starting_period, expense_breakdown):
        """Creates a schedule of capital expenditures.  Modes: simple = proportional annual schedule for total capex layout
           categorical = proportional annual schedule for direct, indirect non_deprec, and indirect_deprec -- NOT IMPLEMENTED YET
           full = annual cash layout for each specific capital item -- NOT IMPLEMENTED YET
           returns the plant startup year
        """
        if isinstance(expense_breakdown, list):
            mode = "simple"

        elif isinstance(expense_breakdown, dict):
            mode = "categorical"

        elif isinstance(expense_breakdown, pd.DataFrame):
            mode = "full"

        else:
            raise ProjFinError, "This type of expense breakdown is not recognized"


        if mode == "simple":
            try:
                if sum(expense_breakdown) != 1:
                    raise ProjFinError, "The expense_breakdown must sum to 1"
            except ValueError:
                raise ProjFinError, "The expense_breakdown list must be filled with numbers"

            
            
            
            dates = pd.date_range(starting_period, starting_period + (len(expense_breakdown))*DateOffset(years=1)-DateOffset(days=1), freq = 'D')		#OVER BY ONE?
            
            capcosts = np.ones(len(dates)) * self.c_total_capital()
            self.capex_schedule = pd.DataFrame(data = {'capex':capcosts}, index = dates)
            #The current behavior is to take the annual capital expenditure and divide it evenly over all the days; with pandas date capability, this can easily be extended to weekly, monthly, etc. charge behavior
            for y in range(0,len(expense_breakdown)):
                
                capital_factor = expense_breakdown[y]/len(self.capex_schedule[starting_period + y*DateOffset(years=1):starting_period + (y+1)*DateOffset(years=1)-DateOffset(days=1)])
                self.capex_schedule[starting_period + y*DateOffset(years=1):starting_period + (y+1)*DateOffset(years=1)-DateOffset(days=1)]['capex'] *= capital_factor
                           
            return starting_period + len(expense_breakdown)*DateOffset(years=1)


        if mode == "categorical":
            pass

        if mode == "full":
            pass

    
    def build_depreciation_schedule(self, starting_period, length, method):
        """Fills out the depreciation capex schedule based on the type of depreciation (straight-line, MACRS, etc.)"""
               
        #set up the schedule Dataframe
               

        if method == "straight-line":
            #all of the days will be the same - this can easily be extended to allow for various frequencies
            dates = pd.date_range(starting_period, starting_period + length*DateOffset(years=1) - DateOffset(days=1), freq = 'D')
            
            d = {'depreciation':np.ones(len(dates))}
            self.depreciation_schedule = pd.DataFrame(data = d, index = dates)
            #!!!#This is not actually correct -- need to adjust this for leap years.  Do this annually, like in the MACRS schedule below
            deprec_value_daily = self.c_deprec_capital()/len(dates)
            self.depreciation_schedule['depreciation'] *= deprec_value_daily
            
        elif method == "MACRS":
            
            dates = pd.date_range(starting_period, starting_period + (length+1)*DateOffset(years=1)-DateOffset(days=1), freq = 'D')
            d = {'depreciation': np.ones(len(dates))}
            self.depreciation_schedule = pd.DataFrame(data = d, index = dates)
            for y in range(0,length+1):
                
                dep_factor = CapitalCosts.MACRS['%s' % (length)][y]/len(self.depreciation_schedule[starting_period + y*DateOffset(years=1):starting_period+(y+1)*DateOffset(years=1)-DateOffset(days=1)])
                self.depreciation_schedule[starting_period+y*DateOffset(years=1):starting_period+(y+1)*DateOffset(years=1)-DateOffset(days=1)]['depreciation'] *= dep_factor                
 
            self.depreciation_schedule['depreciation'] *= self.c_deprec_capital()
            

        else:
            raise ProjFinError, "Unknown depreciation method %s" % method
               



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
        return isinstance(other, self.__class__) and self.direct_capital == other.direct_capital and self.indirect_deprec_capital == other.indirect_deprec_capital and self.indirect_nondeprec_capital == other.indirect_nondeprec_capital

    def __ne__(self, other):
        return not self.__eq__(other)


    def scale(self, new_scale):
        new_capcosts = CapitalCosts()

        for capex in self.direct_capital:
            new_capcosts.add_capital_item(capex.scale(new_scale))

        converter = uc.UnitConverter()
        scaled = converter.convert_units(new_scale[0], new_scale[1], self.base_scale[1])

        #indirects scale linearly, as they are usually percentages of total capital
        for key, cost in self.indirect_deprec_capital.items():
            new_capcosts.indirect_deprec_capital[key] = cost * scaled/self.base_scale[0]

        for key, cost in self.indirect_nondeprec_capital.items():
            new_capcosts.indirect_nondeprec_capital[key] = cost * scaled/self.base_scale[0]

class FixedCosts:
    gl_add_info = OrderedDict([('project_staff',('Project staff',float)),('g_and_a',('General and Administrative',float)),('prop_tax_and_insurance',('Property tax and insurance',float)),('rent_or_lease',('Rent or Lease',float)),('licensing_permits_fees',('Licensing, permits, and fees',float)),('mat_cost_maint_repair',('Material costs for maintenance and repairs',float)),('other_fees',('Other fees',float)),('other_fixed_op_and_maint',('Other fixed operational and maintenance costs',float))])
    labels = OrderedDict([('project_staff','Project staff'),('g_and_a','General and Administrative'),('prop_tax_and_insurance','Property tax and insurance'),('rent_or_lease','Rent or Lease'),('licensing_permits_fees','Licensing, permits, and fees'),('mat_cost_maint_repair','Material costs for maintenance and repairs'),('other_fees','Other fees'),('other_fixed_op_and_maint','Other fixed operational and maintenance costs')])
    types = OrderedDict([('project_staff',float),('g_and_a',float),('prop_tax_and_insurance',float),('rent_or_lease',float),('licensing_permits_fees',float),('mat_cost_maint_repair',float),('other_fees',float),('other_fixed_op_and_maint',float)])

    """Holds the fixed costs for a project (not a company)"""
    def __init__(self, project_staff = None, G_A_exp = None, prop_tax_ins = None, rent = None, licensing_permits_fees = None, maintenance_cost = None, other_fees = None, other_fixed = None):
        self.fixed_costs = {}
        self.fixed_costs['project_staff'] = project_staff
        self.fixed_costs['g_and_a'] = G_A_exp
        self.fixed_costs['prop_tax_and_insurance'] = prop_tax_ins
        self.fixed_costs['rent_or_lease'] = rent
        self.fixed_costs['licensing_permits_fees'] = licensing_permits_fees
        self.fixed_costs['mat_cost_maint_repair'] = maintenance_cost
        self.fixed_costs['other_fees'] = other_fees
        self.fixed_costs['other_fixed_op_and_maint'] = other_fixed

        self.mode = "direct"

    def c_total_fixed_costs(self, TDC = None):
        fixed_list = []
        for key in self.fixed_costs.keys():
            if self.fixed_costs[key] is not None:
                if self.mode == "direct":
                    fixed_list.append(self.fixed_costs[key])
		elif self.mode == "pct":
                    fixed_list.append(self.fixed_costs[key]*TDC)
        return sum(fixed_list)

    def  __getitem__(self, index):
        """Returns the item with the index name"""
        try:
            return self.fixed_costs[index]
        except KeyError:
            raise ProjFinError, "The desired column was not existent"

    def __setitem__(self,key,item):
        if key not in self.fixed_costs:
	    raise ProjFinError, "%s is not an acceptable fixed cost" % key
        self.fixed_costs[key] = item

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.fixed_costs == other.fixed_costs

    def __ne__(self, other):
        return not self.__eq__(other)

    def set_base_scale(self, base_scale):
        self.base_scale = base_scale

    def scale(self, new_scale):
        new_fc = FixedCosts()
        converter = uc.UnitConverter()
        scaled = converter.convert_units(new_scale[0], new_scale[1], self.base_scale[1])
        #everything EXCEPT labor scales linearly; labor scales logarithmically
        for key in self.fixed_costs:
            if key != 'project_staff':
                new_fc.fixed_costs[key] = self.fixed_costs[key] * scaled/self.base_scale[0]
            else:
                new_fc.fixed_costs[key] = self.fixed_costs[key] * np.log(scaled/self.base_scale[0])
        return new_fc

class VariableExpense:
    """Holds a single variable expense, indexed to the production of a given unit of capacity"""
    #gl_add_info = OrderedDict([('name',('Name',str)),('unit_cost_val',('Unit Cost',float)),('unit_cost_units',('Unit Cost Units',str)),('prod_req_val',('Production required',float)),('prod_req_var_units',('Variable Expense Units',str)),('prod_req_prod_units',('Production Units', str))])
    value_map = ['name', 'unit_cost', 'prod_req']

    def __init__(self, name, unit_cost = None, prod_required = None):
        self.name = name
        self.unit_cost = unit_cost                              #Cost per unit of variable expense - unit bearing value
        
        self.prod_req = prod_required				#Number of units required per unit of production - unit bearing value
        self.converter = uc.UnitConverter()		        #Used to convert non-standard units

    def annual_cost(self, production):
        """Returns the annual variable cost for this unit, given the a production level in (value, unit) format"""
        #prod_val = self.converter.convert_units(production[0], production[1], self.prod_req[2])
        
        #cost_req = 1/self.converter.convert_units(1/self.unit_cost[0], self.unit_cost[1], self.prod_req[1])
	
        return self.converter.convert_units(self.unit_cost.value*self.prod_req.value*production.value, '%s*%s*%s' % (self.unit_cost.units, self.prod_req.units, production.units), "$")

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.name == other.name and self.unit_cost == other.unit_cost and self.prod_req == other.prod_req

    def __ne__(self, other):
        return not self.__eq__(other)


class VariableCosts:
    """Holds the variable costs for a project (not a company)"""
    #Needs to be able to calculate total costs for total production -- should be pretty easy, but may want unit conversion here
    def __init__(self):
        self.variable_exps = []

    def add_variable_exp(self, VE):
        if not isinstance(VE, VariableExpense):
            raise ProjFinError, "VE must be a VariableExpense object"

        self.variable_exps.append(VE)

    def c_total_VC(self, production_units):
        total_VC = 0.0
        for VE in self.variable_exps:
            total_VC += VE.annual_cost(uv.UnitVal(1.0,production_units))

        return total_VC

    def del_variable_exp(self, name):
        """Removes a given variable expense from the list of variable expenses"""
        for VE in self.variable_exps:
            if VE.name == name:
                self.variable_exps.remove(VE)

    def variable_exp_names(self):
        """Returns a list of the names of the variable expenses"""
        name_list = []
        for VE in self.variable_exps:
            name_list.append(VE.name)
        return name_list

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.variable_exps == other.variable_exps

    def __ne__(self, other):
        return not self.__eq__(other)

class DebtPortfolio:
    """Holds all of the loans, bonds, etc. for a given project"""
    def __init__(self):
        self.loans = []
        self.loan_schedule_bit = False
        self.bonds = []

    def add_loan(self, loan):
        """Add a loan to the list of loans"""
        if not isinstance(loan, Loan):
            raise ProjFinError, "loan must be an instance of class Loan; it was not passed as such"

        for item in self.loans:
            if item.name == loan.name:
                raise ProjFinError, "%s is already a loan in the debt portfolio" % loan.name

        self.loans.append(loan)
        self.loan_schedule_bit = False

    def del_loan(self, name):
        """Removes the loan with the given name.  If the name is not in the list, does nothing."""
        for loan in self.loans:
            if loan.name == name:
                self.loans.remove(loan)

    def calculate_loans(self):
        """Calculates all the schedules for all of the given loans"""
        for loan in self.loans:
            if not loan.scheduled:
                loan.generate_schedule()

        self.loan_schedule_bit = True

    def CIP(self, date_range):
        """Calculates the cash proceeds, interest, and principal payment for all loans in the portfolio for a given date range"""
        if not self.loan_schedule_bit:
            self.calculate_loans()
        
        #date_range should be a timeseries object for this to work
        output = pd.DataFrame(index = date_range)
        
        names = ['cash_proceeds','principal_payment','interest']
        for name in names:
            output[name] = np.zeros(len(output))
        for loan in self.loans:
            output = output.add(loan.schedule, fill_value=0)
               
        output = pd.DataFrame(output, index = date_range, columns = names)
        
        return output   


    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.loans == other.loans and self.bonds == other.bonds

    def __ne__(self, other):
        return not self.__ne__(other)

    def set_base_scale(self, base_scale):
        self.base_scale = base_scale
        for loan in self.loans:
            loan.set_base_scale(base_scale)

    def scale(self, new_scale):
        new_dpf = DebtPortfolio()
        for loan in self.loans:
            new_dpf.add_loan(loan.scale(new_scale))
        return new_dpf

class Loan:
    """Container class for debt financing instruments"""

    #payment schedules in (month, day) format
    #schedule_1 = ((1,1),)
    #schedule_2 = ((1,1), (7,1))
    #schedule_4 = ((1,1), (4,1), (7,1), (10,1))
    #schedule_12 = ((1,1), (2,1), (3,1), (4,1), (5,1), (6,1), (7,1), (8,1), (9,1), (10,1), (11,1), (12,1))
    #Assumes end of period payments -- will need a special case to deal with bi-annual frequencies, which are not covered (yet) in the pandas distribution
    scheds = {1:'A', 12:'M', 4:'Q'}
    
    

    def __init__(self, name, principal = None, term = None, rate = None, pmt_freq = None, strt_period = None):
        self.name = name
        self.principal = principal
        self.term = term
        self.rate = rate
        self.pmt_freq = pmt_freq    #number of times per year a payment is made
        self.strt_period = strt_period #should be a datetime instance
        
        
        self.scheduled = False

    def generate_schedule(self):
        """Generates the loan schedule from appropriate information"""
        #Should add the ability to do extra payments if desired -- just place on a separate line of the schedule, and add these in when calculating
        if self.pmt_freq in Loan.scheds:
            sched = pd.date_range(self.strt_period, periods = self.term*self.pmt_freq, freq = Loan.scheds[self.pmt_freq])	#so, this could also be done with an end date -- may need to do it that way
	    
        elif self.pmt_freq == 2:
            sched = pd.date_range(self.strt_period, periods = self.term*self.pmt_freq*2, freq = 'Q')
            sched = sched[1::2] 

        else:
            raise ProjFinError, "%s is an unrecognized frequency for loan payments" % self.pmt_freq

        
        #Need to add on the initial payment date -- money will always be delivered on the first day
        d = sched[0] - DateOffset(months = 12/self.pmt_freq)
        d_n = pd.date_range(d, freq = 'MS', periods = 1)
        sched = d_n.append(sched)

	       
        self.schedule = pd.DataFrame(index = sched)
        
        self.pmt = self.principal*(self.rate/self.pmt_freq)*np.power(1+self.rate/self.pmt_freq,self.term*self.pmt_freq)/(np.power(1+self.rate/self.pmt_freq,self.term*self.pmt_freq)-1)
        
        for item in [self.principal, self.term, self.rate, self.pmt_freq, self.strt_period]:
            if item == None:
                raise ProjFinError, "You need to set %s before generating the loan schedule" % item

        
        #Now we just need to step through the payment dates to calculate the schedule 

        #set up the dataframe columns
        self.schedule['principal'] = np.zeros(len(self.schedule))
        self.schedule['interest'] = np.zeros(len(self.schedule))
        self.schedule['principal_payment'] = np.zeros(len(self.schedule))
        self.schedule['cash_proceeds'] = np.zeros(len(self.schedule))

        self.schedule['cash_proceeds'][0] = self.principal		#get the cash up-front

        #The iterative but straight-forward way
        
        P = self.principal
        
        for y in range(1, len(self.schedule)):
            self.schedule['interest'][y] = self.rate/self.pmt_freq*P
            self.schedule['principal_payment'][y] = self.pmt - self.schedule['interest'][y]
            self.schedule['principal'][y] = P - self.schedule['principal_payment'][y]
            P = self.schedule['principal'][y]
            
          
        self.scheduled = True
        

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

    def __eq__(self, other):
        verity = isinstance(other, self.__class__)
        names = ['name', 'principal', 'term', 'rate', 'pmt_freq', 'strt_period']
        if verity:
            for name in names:
                verity = verity and getattr(self, name) == getattr(other, name)
        return verity

    def __ne__(self, other):
        return not self.__eq__(other)

    def set_base_scale(self, base_scale):
        self.base_scale = base_scale

    def scale(self, new_scale):
        converter = uc.UnitConverter()
        scaled = converter.convert_units(new_scale[0], new_scale[1], self.base_scale[1])
        new_loan = Loan(name = self.name, term = self.term, rate = self.rate, pmt_freq = self.pmt_freq, strt_year = self.strt_year)
        new_loan.principal = self.principal * scaled/self.base_scale[0]
        return new_loan
        
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
    
 


