import numpy as np
import dataFrame_v2 as df
import unitConversion as uc
from cp_tools import *
import scipy.optimize as spo
import csv
from collections import OrderedDict
from lxml import etree
import UnitValues as uv


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

        years = range(self.fin_param['Initial_year'],self.fin_param['Initial_year']+self.fin_param['Analysis_period'])
        count = {'Period':np.arange(len(years))}
        self.cf_sheet = df.Dataframe(array_dict = count, rows_list = years)

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

    def printFinancials(self, filename = None):
        """Print the financials to a file, or to the screen"""

        cols = ('Production','Sales','Salvage','Revenue','Variable_costs','Fixed_costs','Decommissioning_costs','Cost_of_sales','EBITDA','Interest','Depreciation','Taxable_income','Taxes','After-tax_income','Capital_expenditures','Principal_payments','Net_cash_flow')
        order = ['Category']
        order.extend(self.cf_sheet.rows())
        

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



    def calcIRR(self):
        """Returns the IRR for the given cash flow of the project"""
        #Find the root of the NPV function
        return spo.brentq(self.calcNPV,0.001,1.0)
    
    def calcNPV(self, rate):
        """Returns the NPV for the given cash flow of the project"""
        
        return sum(self.cf_sheet['Net_cash_flow']/np.power(1+rate,self.cf_sheet['Period']))


    def setPrices(self, base_price, mode, inflation_dict = None):
        """Creates the price inflation schedule we expect to see"""
        #INCOMPLETE!
        if mode == "fixed":
            self.cf_sheet['Sales_price'] = np.ones(self.fin_param['Analysis_period'])*base_price*np.power(1+self.fin_param['Inflation_rate'],self.cf_sheet['Period'])
            

        elif mode == "pre-set":
            #Inflation_dict should look like {year:year-over-year inflation} -- this must be calculated sequentially -- pass for now
            pass

        else:
            raise ProjFinError, "%s is not a recognized inflation mode" % mode

    def setAnnualOutput(self):
        """Creates the annual output column for production level, adjusted for startup considerations"""
        output = np.zeros(self.fin_param['Analysis_period'])
        ann_out = self.fin_param['Cap_factor'] * self.fin_param['Design_cap'].value
        for year in self.cf_sheet.rows():
            if year < self.fin_param['Startup_year'] or year > self.fin_param['Startup_year'] + self.fin_param['Plant_life']:
                #zeros are fine here...do nothing
                pass

            elif year == self.fin_param['Startup_year']:
                output[self.cf_sheet.row_num(year)] = self.fin_param['Startup_revenue_breakdown']*ann_out
        
            else:
                output[self.cf_sheet.row_num(year)] = ann_out

        self.cf_sheet['Production'] = output
        self.cf_sheet.units['Production'] = self.fin_param['Design_cap'].units
        #Currently, not using units, although I certainly could and us the unit conversion engine to get correct revenues



    def setRevenue(self):
        """Creates the sales, salvage, and revenues columns"""
        self.cf_sheet['Sales'] = self.cf_sheet['Production'] * self.cf_sheet['Sales_price']
        self.cf_sheet['Salvage'] = np.zeros(self.fin_param['Analysis_period'])
        try:
            self.cf_sheet['Salvage'][self.cf_sheet.row_num(self.fin_param['Plant_life'] + self.fin_param['Startup_year'])] = self.fin_param['Salvage_value']
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

        self.fin_param['Startup_year'] = self.capex.build_capex_schedule(self.fin_param['Initial_year'], self.fin_param['Capital_expense_breakdown'])
        self.capex.build_depreciation_schedule(starting_year = self.fin_param['Startup_year'], length = self.fin_param['Depreciation_length'], method = self.fin_param['Depreciation_type'])

        #Set up the columns in the cashflow sheet to be the proper length
        self.cf_sheet['Capital_expenditures'] = np.zeros(self.fin_param['Analysis_period'])
        self.cf_sheet['Depreciation'] = np.zeros(self.fin_param['Analysis_period'])

        #Fill the columns by year matching

        for year in self.cf_sheet.rows():
            (self.cf_sheet['Capital_expenditures'][self.cf_sheet.row_num(year)],self.cf_sheet['Depreciation'][self.cf_sheet.row_num(year)]) = self.capex.costs_and_depreciation(year)
	
    def setVariableCosts(self, VC):
        if not isinstance(VC, VariableCosts):
            raise ProjFinError, "VC must be a VariableCosts object"

        self.variable_costs = VC
        self.check_bits[3] = True

    def _calcVariableCosts(self):
        if self.variable_costs is None:
            raise ProjFinError, "You must set the variable costs before you can calculate them"

        self.cf_sheet['Variable_costs'] = np.ones(self.fin_param['Analysis_period'])*self.variable_costs.c_total_VC(self.cf_sheet.units['Production'])*self.cf_sheet['Production']*np.power(1+self.fin_param['Inflation_rate'],self.cf_sheet['Period'])

    def setFixedCosts(self, FC):
        if not isinstance(FC, FixedCosts):
            raise ProjFinError, "FC must be a FixedCosts object"
        self.fixed_costs = FC
        self.check_bits[2] = True

    def _calcFixedCosts(self):
        if self.fixed_costs is None:
            raise ProjFinError, "You must set the fixed costs before you can calculate them"

        total = self.fixed_costs.c_total_fixed_costs()
        mask = np.zeros(self.fin_param['Analysis_period'])

        for year in self.cf_sheet.rows():
            if year == self.fin_param['Startup_year']:
                mask[self.cf_sheet.row_num(year)] = self.fin_param['Startup_fixed_cost_breakdown']
            elif year > self.fin_param['Startup_year'] and year <= self.fin_param['Startup_year']+self.fin_param['Plant_life']:
                mask[self.cf_sheet.row_num(year)] = 1


        self.cf_sheet['Fixed_costs'] = np.ones(self.fin_param['Analysis_period'])*total*np.power(1+self.fin_param['Inflation_rate'],self.cf_sheet['Period'])*mask

    def setDebt(self, debt_pf):
        if not isinstance(debt_pf, DebtPortfolio):
            raise ProjFinError, "debt_pf must be a DebtPortfolio object"

        self.debt = debt_pf
        self.check_bits[4] = True

    def _calcDebt(self):
        """Calculate the debt portion of the spreadsheet"""
        if self.debt is None:
            raise ProjFinError, "You must set the debt portfolio before you can calculate the debt"


        self.cf_sheet['Loan_proceeds'] = np.zeros(self.fin_param['Analysis_period'])
        self.cf_sheet['Interest'] = np.zeros(self.fin_param['Analysis_period'])
        self.cf_sheet['Principal_payments'] = np.zeros(self.fin_param['Analysis_period'])

        for year in self.cf_sheet.rows():
            (self.cf_sheet['Loan_proceeds'][self.cf_sheet.row_num(year)],self.cf_sheet['Interest'][self.cf_sheet.row_num(year)],self.cf_sheet['Principal_payments'][self.cf_sheet.row_num(year)]) = self.debt.CIP(year)
        
    def setOtherFinancials(self):
        """Sets the decommissioning cost, and calculates EBITDA, net Income, taxes, and cash flow"""
        #Need to check order bits here
        self.cf_sheet['Decommissioning_costs'] = np.zeros(self.fin_param['Analysis_period'])
        try:
            self.cf_sheet['Decommissioning_costs'][self.cf_sheet.row_num(self.fin_param['Plant_life'] + self.fin_param['Startup_year'])] = self.fin_param['Decommissioning_cost']
        except KeyError:
            pass

        self.cf_sheet['Cost_of_sales'] = self.cf_sheet['Fixed_costs'] + self.cf_sheet['Variable_costs'] + self.cf_sheet['Decommissioning_costs']
        self.cf_sheet['EBITDA'] = self.cf_sheet['Revenue'] - self.cf_sheet['Cost_of_sales']
        self.cf_sheet['Pre-depreciation_income'] = self.cf_sheet['EBITDA'] - self.cf_sheet['Interest']
        self.cf_sheet['Taxable_income'] = self.cf_sheet['Pre-depreciation_income'] - self.cf_sheet['Depreciation']
        self.cf_sheet['Taxes'] = self.cf_sheet['Taxable_income'] * (self.fin_param['State_tax_rate'] + self.fin_param['Federal_tax_rate'])*(self.cf_sheet['Taxable_income']>0)   
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

    key_list = ['Initial_year', 'Startup_year','Target_IRR', 'Depreciation_type', 'Depreciation_length', 'Analysis_period', 'Plant_life', 'Inflation_rate', 'State_tax_rate', 'Federal_tax_rate','Design_cap','Cap_factor','Capital_expense_breakdown','Startup_revenue_breakdown','Startup_fixed_cost_breakdown','Startup_variable_cost_breakdown','Salvage_value','Decommissioning_cost']
    type_dict = {'Initial_year':int, 'Target_IRR':float, 'Depreciation_length':int,'Analysis_period':int, 'Plant_life':int,'Inflation_rate':float,'State_tax_rate':float, 'Federal_tax_rate':float, 'Design_cap':float, 'Cap_factor':float,'Startup_revenue_breakdown':float,'Startup_fixed_cost_breakdown':float, 'Startup_variable_cost_breakdown':float, 'Salvage_value':float, 'Decommissioning_cost':float}
    


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
        if not is_numeric(value) and key not in ['Capital_expense_breakdown','Design_cap','Depreciation_type'] and value is not None:
            raise ProjFinError, "The specific value (%s) is not numeric" % value

        if key == 'Capital_expense_breakdown' and not (isinstance(value,list) or isinstance(value,dict) or isinstance(value,df.Dataframe)) and value is not None:
            raise ProjFinError, "The capital expense breakdown is not a recognized type"

        elif key == 'Design_cap' and value is not None:
            if not (isinstance(value,uv.UnitVal)):
                raise ProjFinError, "The design capacity must be a UnitVal object"
  

        elif key == 'Depreciation_type' and not isinstance(value, str) and value is not None:
            raise ProjFinError, "The depreciation type must be a string"

        self.params[key] = value
    

    def is_incomplete(self):
        """Checks if all of the items have been specified before moving forward"""
        flag = False
        for k,v in self.params.items():
            if v is None and k is not 'Startup_year':
                flag = True
        return flag
    
    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.params == other.params

    def __ne__(self, other):
        return not self.__eq__(other)

class CapitalExpense:
    """Container class for capital expenditures"""
    
    gl_add_info = OrderedDict([('name',('Name',str)),('uninstalled_cost',('Uninstalled cost',float)),('installation_factor',('Installation factor',float))])


    def __init__(self, name, uninstalled_cost = None, installation_factor = None):
        self.name = name
        self.uninstalled_cost = uninstalled_cost
        self.installation_factor = installation_factor
        if self.uninstalled_cost is not None and installation_factor is not None:
            self.installed_cost = self.uninstalled_cost * installation_factor

        self.comments = []

    def set_cost(self, uninstalled_cost, installation_factor):
        self.uninstalled_cost = uninstalled_cost
        self.installation_factor = installation_factor
        self.installed_cost = self.uninstalled_cost * self.installation_factor


    def add_comment(self, comment):
        if type(comment) is not str:
            raise ProjFinError, "Comments must be strings"
        self.comments.append(comment)

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
    MACRS = {}
    MACRS['3'] = np.array([0.3333, 0.4445, 0.1481, 0.0741])
    MACRS['5'] = np.array([0.2, 0.32, 0.1920, 0.1152, 0.1152, 0.0576])
    MACRS['7'] = np.array([0.1429, 0.2449, 0.1749, 0.1249, 0.0893, 0.0892, 0.0893, 0.0446])
    MACRS['10'] = np.array([0.1000, 0.18, 0.144, 0.1152, 0.0922, 0.0737, 0.0655, 0.0655, 0.0656, 0.0655, 0.0328])
    MACRS['15'] = np.array([0.05, 0.095, 0.0855, 0.0770, 0.0693, 0.0623, 0.0590, 0.0590, 0.0591, 0.0590, 0.0591, 0.0590, 0.0591, 0.0590, 0.0591, 0.0295])
    MACRS['20'] = np.array([0.0375, 0.07219, 0.06677, 0.06177, 0.05713, 0.05285, 0.04888, 0.04522, 0.04462, 0.04461, 0.04462, 0.044610, 0.04462, 0.04461, 0.04462, 0.04461, 0.04462, 0.04461, 0.04462, 0.04461, 0.02231])
   

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

    def build_capex_schedule(self, initial_year, expense_breakdown):
        """Creates a schedule of capital expenditures.  Modes: simple = proportional annual schedule for total capex layout
           categorical = proportional annual schedule for direct, indirect non_deprec, and indirect_deprec -- NOT IMPLEMENTED YET
           full = annual cash layout for each specific capital item -- NOT IMPLEMENTED YET
           returns the plant startup year
        """
        if isinstance(expense_breakdown, list):
            mode = "simple"

        elif isinstance(expense_breakdown, dict):
            mode = "categorical"

        elif isinstance(expense_breakdown, df.Dataframe):
            mode = "full"

        else:
            raise ProjFinError, "This type of expense breakdown is not recognized"


        if mode == "simple":
            try:
                if sum(expense_breakdown) != 1:
                    raise ProjFinError, "The expense_breakdown must sum to 1"
            except ValueError:
                raise ProjFinError, "The expense_breakdown list must be filled with numbers"

            years = range(initial_year, initial_year + len(expense_breakdown))
            
            capcosts = np.ones(len(years)) * expense_breakdown * self.c_total_capital()
            self.capex_schedule = df.Dataframe(array_dict = {'capex':capcosts}, rows_list = years)
            return initial_year + len(years)


        if mode == "categorical":
            pass

        if mode == "full":
            pass




    def build_depreciation_schedule(self, starting_year, length, method):
        """Fills out the depreciation capex schedule based on the type of depreciation (straight-line, MACRS, etc.)"""
        years = range(starting_year, starting_year+length)
        if method == "straight-line":
            deprec_value = self.c_deprec_capital()/length
            d = {'depreciation':np.ones(length)*deprec_value}
            self.depreciation_schedule = df.Dataframe(array_dict = d, rows_list = years)
            
        elif method == "MACRS":
            years.append(starting_year+length)
            d = {'depreciation': np.ones(length+1) * CapitalCosts.MACRS['%s' % (length)] * self.c_deprec_capital()}
            self.depreciation_schedule = df.Dataframe(array_dict = d, rows_list = years)
            

        else:
            raise ProjFinError, "Unknown depreciation method %s" % method

    def costs_and_depreciation(self, year):
        """Accessor method to hide the internal baseball of the capital costs object -- all I really want from this thing, at this point, are the costs for a given year"""
        capex = 0.0
        deprec = 0.0

        if year in self.capex_schedule.rows():
            capex = self.capex_schedule.get_row(year)['capex']

        if year in self.depreciation_schedule.rows():
            deprec = self.depreciation_schedule.get_row(year)['depreciation']
        
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
                if self.mode = "direct":
                    fixed_list.append(self.fixed_costs[key])
		elif self.mode = "pct":
                    fixed_list.append(self.fixed_costs[key]*TDC)
        return sum(fixed_list)

    def  __getitem__(self, index):
        """Returns the item with the index name"""
        try:
            return self.fixed_costs[index]
        except KeyError:
            raise ProjFinError, "The desired column was not existent"

    def __setitem__(self,key,item):
        if key not in self.fixed_costs.keys():
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

    def CIP(self, year):
        """Calculates the cash proceeds, interest, and principal payment for all loans in the portfolio for a given year"""
        if not self.loan_schedule_bit:
            self.calculate_loans()
        cash = 0.0
        interest = 0.0
        principal = 0.0

        for loan in self.loans:
           if year in loan.schedule.rows():
               cash += loan.schedule.get_row(year)['cash_proceeds']
               interest += loan.schedule.get_row(year)['interest']
               principal += loan.schedule.get_row(year)['principal_payment']
       
        return (cash, interest, principal)

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

    def __init__(self, name, principal = None, term = None, rate = None, pmt_freq = None, strt_year = None):
        self.name = name
        self.principal = principal
        self.term = term
        self.rate = rate
        self.pmt_freq = pmt_freq    #number of times per year a payment is made
        self.strt_year = strt_year
        
        
        self.scheduled = False

    def generate_schedule(self):
        """Generates the loan schedule from appropriate information"""
        #Should add the ability to do extra payments if desired -- just place on a separate line of the schedule, and add these in when calculating

        self.schedule = df.Dataframe()
        self.pmt = self.principal*(self.rate/self.pmt_freq)*np.power(1+self.rate/self.pmt_freq,self.term*self.pmt_freq)/(np.power(1+self.rate/self.pmt_freq,self.term*self.pmt_freq)-1)

        for item in [self.principal, self.term, self.rate, self.pmt_freq, self.strt_year]:
            if item == None:
                raise ProjFinError, "You need to set %s before generating the loan schedule" % item

        #Create the loan row by row until the term is complete
        year = self.strt_year
        P = self.principal
        
        
        #To start, this will only work for annual coupon payments...I will generalize a bit later (it just requires a sub-loop)
        while year < self.strt_year + self.term:
            row_dict = {}        
            row_name = year
            row_dict['principal'] = P
            row_dict['interest'], row_dict['principal_payment'] = self._acc_int_principal(P)
            
            
            self.schedule.append(row_dict, row_name = year)
            
            P = P - row_dict['principal_payment']
            year += 1

        #Add the cash borrowed in the first year
        cash = np.zeros(self.schedule.numrows())
        cash[0] = self.principal

        self.schedule['cash_proceeds'] = cash

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
        names = ['name', 'principal', 'term', 'rate', 'pmt_freq', 'strt_year']
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
        integers = ['Initial_year', 'Analysis_period', 'Depreciation_length', 'Plant_life']
        fin_params = self.docroot.find("financial_parameters")
        for fin_param in fin_params:
            if fin_param.tag == "Design_cap":				#reflects new naming convention NOT yet in use
                new_fin_params[fin_param.tag] = uv.UnitVal(self._cast_special(fin_param.text,float), fin_param.attrib["units"])
            elif fin_param.tag == "Depreciation_type":
                new_fin_params[fin_param.tag] = fin_param.text
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
                it = ['principal', 'term', 'rate', 'pmt_freq', 'strt_year']
                for name in it:
                    tag = etree.SubElement(loan_tag, name)
                    tag.text = str(getattr(loan, name))

    def _save_fin_params(self):
        fp = etree.SubElement(self.root, 'financial_parameters')
        exceptions = ['Design_cap', 'Capital_expense_breakdown']
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
    
 


