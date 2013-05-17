import ProjectFinance as pf




class Business:
    """Holds the concept of a business"""

    def __init__(self, name):
        """Set up the business"""
        self.name = name

        #other key components to define
        self.strategies		#Holds strategic capital project plans
        self.financial_statements  #Holds the financial statements for the company
        self.admin_costs	#Holds the administrative (non-project) costs for the company
        self.employees		#Holds the staff for the company



class WorkUnit:
    """Basic tracking mechanism for assigning indirect costs associated with maintaining strategic initiatives"""

    def __init__(self, cost):

        self.cost = cost	#Defines the cost basis for a given work unit
