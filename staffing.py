#staffing.py
#set of classes to model and optimize a labor force

import random
import copy

class WorkUnit:
    """Basic unit of work (FTE for a period of time) in the labor model"""

    def __init__(self, value = 1):
        self.value = value

class Finance_WorkUnit(WorkUnit):

    def __init__(self, value = 1):
        WorkUnit.__init__(self, value)

class ProjectFinancing_WorkUnit(Finance_WorkUnit):

    def __init__(self, value = 1):
        Finance_WorkUnit.__init__(self, value)

class FinanceExecutive_WorkUnit(Finance_WorkUnit):

    def __init__(self, value = 1):
        Finance_WorkUnit.__init__(self, value)

class FinancialAnalysis_WorkUnit(Finance_WorkUnit):

    def __init__(self, value = 1):
        Finance_WorkUnit.__init__(self, value)

class Accounting_WorkUnit(WorkUnit):

    def __init__(self, value = 1):
        WorkUnit.__init__(self, value)

class AccountsReceivable_WorkUnit(Accounting_WorkUnit):

    def __init__(self, value = 1):
        Accounting_WorkUnit.__init__(self, value)

class AccountsPayable_WorkUnit(Accounting_WorkUnit):

    def __init__(self, value = 1):
        Accounting_WorkUnit.__init__(self, value)

class Purchasing_WorkUnit(Accounting_WorkUnit):

    def __init__(self, value = 1):
        Accounting_WorkUnit.__init__(self, value)

class Controller_WorkUnit(Accounting_WorkUnit):

    def __init__(self, value = 1):
        Accounting_WorkUnit.__init__(self, value)

class Strategic_WorkUnit(WorkUnit):

    def __init__(self, value = 1):
        WorkUnit.__init__(self, value)

class CorporateStrategy_WorkUnit(Strategic_WorkUnit):

    def __init__(self, value = 1):
        Strategic_WorkUnit.__init__(self, value)

class Engineering_WorkUnit(WorkUnit):

    def __init__(self, value = 1):
        WorkUnit.__init__(self, value)

class ProcessEngineering_WorkUnit(Engineering_WorkUnit):

    def __init__(self, value = 1):
        Engineering_WorkUnit.__init__(self, value)

class MechanicalEngineering_WorkUnit(Engineering_WorkUnit):

    def __init__(self, value = 1):
        Engineering_WorkUnit.__init__(self, value)

class CivilEngineering_WorkUnit(Engineering_WorkUnit):

    def __init__(self, value = 1):
        Engineering_WorkUnit.__init__(self, value)

class ElectricalEngineering_WorkUnit(Engineering_WorkUnit):

    def __init__(self, value = 1):
        Engineering_WorkUnit.__init__(self, value)

class BusinessDevelopment_WorkUnit(WorkUnit):

    def __init__(self, value = 1):
        WorkUnit.__init__(self, value)

class Administrative_WorkUnit(WorkUnit):

    def __init__(self, value = 1):
        WorkUnit.__init__(self, value)

class Operations_WorkUnit(WorkUnit):

    def __init__(self, value = 1):
        WorkUnit.__init__(self, value)

class Legal_WorkUnit(WorkUnit):

    def __init__(self, value = 1):
        WorkUnit.__init__(self, value)

class IPLaw_WorkUnit(Legal_WorkUnit):

    def __init__(self, value = 1):
        Legal_WorkUnit.__init__(self, value)

class IPReview_WorkUnit(IPLaw_WorkUnit):

    def __init__(self, value = 1):
        IPLaw_WorkUnit(self, value)

class ContractLaw_WorkUnit(Legal_WorkUnit):

    def __init__(self, value = 1):
        Legal_WorkUnit.__init__(self, value)

class Sales_WorkUnit(WorkUnit):

    def __init__(self, value = 1):
        WorkUnit.__init__(self, value)

class ResearchAndDevelopment_WorkUnit(WorkUnit):

    def __init__(self, value = 1):
        WorkUnit.__init__(self, value)

class ResearchPlanning_WorkUnit(ResearchAndDevelopment_WorkUnit):

    def __init__(self, value = 1):
        ResearchAndDevelopment_WorkUnit.__init__(self, value)

class ExperimentOperation_WorkUnit(ResearchAndDevelopment_WorkUnit):

    def __init__(self, value = 1):
        ResearchAndDevelopment_WorkUnit.__init__(self, value)

class Worker:
    """Holds an abstract worker, who will have various abilities"""
    
    base_skills = []
    base_salary = 0.0       #Generic worker does not have a salary
    base_benefits = 0.0

    def __init__(self, salary = None, benefits = None):
        if salary == None:
            salary = self.__class__.base_salary
        self.salary = salary
        self.capacity = 1.0			
	self.tasks = []				#start out completely unassigned
        self.skills = []
        self._add_skills()
        if benefits == None:
            self.benefits = self.__class__.base_benefits

    def _add_skills(self):
        self.skills.extend(self.base_skills)

    def add_skill(self, skill):
        self.skills.append(skill)

    def capable(self, workunit):
        """Return True if this Worker is capable of doing the job represented by workunit"""
        if not isinstance(workunit, WorkUnit):
            raise Exception, "workunit must be an instance of WorkUnit or a derived class"

        for skill in self.skills:
            if isinstance(workunit, globals()['%s_WorkUnit' % skill]):
                return True

        return False

    def empty_capacity(self):
        self.capacity = 1.0

    def total_load(self):
        return self.salary + self.benefits

class Executive(Worker):
    base_skills = copy.deepcopy(Worker.base_skills)
    base_skills.extend([])
    def __init__(self, salary = 100000):
        Worker.__init__(self, salary)

class CEO(Executive):

    base_skills = copy.deepcopy(Executive.base_skills)
    base_skills.extend(['Strategic', 'CorporateStrategy'])

    def __init__(self, salary = 250000):
        Executive.__init__(self, salary)

class CFO(Executive):
    base_skills = copy.deepcopy(Executive.base_skills)
    base_skills.extend(['Finance', 'FinanceExecutive', 'FinancialAnalysis'])

    def __init__(self, salary = 200000):
        Executive.__init__(self, salary)

class CTO(Executive):
    base_skills = copy.deepcopy(Executive.base_skills)
    base_skills.extend(['ResearchAndDevelopment'])

    def __init__(self, salary = 200000):
        Executive.__init__(self, salary)

class COO(Executive):
    base_skills = copy.deepcopy(Executive.base_skills)
    base_skills.extend(['Operations'])

    def __init__(self, salary = 200000):
        Executive.__init__(self, salary)

class FinancialAnalyst(Worker):
    base_skills = copy.deepcopy(Worker.base_skills)
    base_skills.extend(['Finance', 'FinancialAnalysis'])
    def __init__(self, salary = 55000):
        Worker.__init__(self, salary)

class Accountant(Worker):
    base_skills = copy.deepcopy(Worker.base_skills)
    base_skills.extend([])
    def __init__(self, salary = 45000):
        Worker.__init__(self, salary)

class PurchasingAgent(Accountant):
    base_skills = copy.deepcopy(Worker.base_skills)
    base_skills.extend(['Purchasing'])

    def __init__(self, salary = 35000):
        Accountant.__init__(self, salary)

class ResearchAndDevelopmentWorker(Worker):
    base_skills = copy.deepcopy(Worker.base_skills)
    base_skills.extend([])


    def __init__(self, salary):
        Worker.__init__(self, salary)

class ResearchScientist(ResearchAndDevelopmentWorker):
    base_skills = copy.deepcopy(ResearchAndDevelopmentWorker.base_skills)
    base_skills.extend([])
    def __init__(self, salary = 100000):
        ResearchAndDevelopmentWorker.__init__(self, salary)


class LaborPool:
    """Data structure to hold the types and amounts of each worker"""

    def __init__(self):
        self.staff = []         #list of worker instances actually employed
        self.pool = []		#list of worker prototype instances available
	self.benefits = 0	#benefit load per employee

    def annual_optimize(self, work):
        """Stochastically optimizes the staffing for a given set of work, given the pool.  If the work cannot be done, it raises an error"""
        pass

    def calc_total_load(self):
        load = 0.0
        for worker in self.staff:
            
            load += worker.salary		
        return load

    def _build_staff_simple(self, work):		#here, work is a list of WorkUnit instances
        """Builds staff from a pool of available workers.  Current staff is not sticky (hiring/firing each year)"""    
        current_worker = None
        self.staff = []                                 #Current staff not sticky.  Clear the entire staff and hire an appropriate one each year.
        w = work
        while w != []:
            task_index = random.randint(0,len(w)-1)
            #print task_index
            task = w[task_index]
            it = 0
            while task.value > 0:
                it += 1
                if it > 100000:
                    raise Exception, "Maximum number of iterations reached without finding capable worker"
                #print current_worker.__class__
                if current_worker is None:
                    current_worker = copy.deepcopy(self.pool[random.randint(0,len(self.pool)-1)])
                    #print "The new worker is a(n) %s" % current_worker.__class__.__name__
                if current_worker.capable(task):
                    #add the task to the worker's list
                    if task.value >= current_worker.capacity:
                        task.value -= current_worker.capacity
                        self.staff.append(current_worker)
                        current_worker = None
                    else:
                        current_worker.capacity -= task.value
                        task.value = -1
                else:
                    current_worker = None
            del w[task_index]
        if not current_worker is None:
            self.staff.append(current_worker)		#need to add the last worker to the list

    def _build_staff_sticky(self, work):		#here, work is a list of WorkUnit instances
        """Builds staff from a pool of available workers.  Current staff is sticky (kept on, whether there is work for them or not)"""    
        
        current_worker = None
        #need to de-work the staff; there is probably a better allocation of resources than the projects they are on
        for worker in self.staff:
            worker.empty_capacity()
        
        w = work
        while w != []:
            task_index = random.randint(0,len(w)-1)
            #print task_index
            task = w[task_index]
            it = 0
            while task.value > 0:
                it += 1
                if it > 100000:
                    raise Exception, "Maximum number of iterations reached without finding capable worker"
                #print current_worker.__class__
                if current_worker is None:
                    #want to draw the worker from random sample of the current staff and the new staff pool
                    cw_index = random.randint(0, len(self.pool) + len(self.staff) -1)
                    if cw_index < len(self.staff):
                        current_worker = self.staff[cw_index]
                        
                    else:
                        cw_index = cw_index - len(self.staff)
                        current_worker = copy.deepcopy(self.pool[cw_index])
                        
                if current_worker.capacity > 0.0 and current_worker.capable(task):
                    #add the task to the worker's list
                    if task.value >= current_worker.capacity:
                        task.value -= current_worker.capacity
                        current_worker.capacity = 0.0
                        if current_worker not in self.staff:
                            self.staff.append(current_worker)
			    
                        current_worker = None
                    else:
                        current_worker.capacity -= task.value
                        task.value = -1
                else:
                    current_worker = None
            del w[task_index]
        if not current_worker is None and current_worker not in self.staff:
            self.staff.append(current_worker)		#need to add the last worker to the list



    def optimize_staff(self, work, iterations = 10000, mode = 'simple'):
        min_load = None
        orig_staff = copy.deepcopy(self.staff)
        while iterations > 0:
            getattr(self, '_build_staff_%s' % mode)(copy.deepcopy(work))
            curr_load = self.calc_total_load()
            if min_load is None or curr_load < min_load:
                min_staff = copy.deepcopy(self.staff)
                min_load = curr_load
            self.staff = copy.deepcopy(orig_staff)
            iterations -= 1
        self.staff = min_staff
        print "The minimum load is: %s" % min_load


            
if __name__ == "__main__":
    #Test the staff building tools
    lp = LaborPool()
    lp.pool = [CEO(), CFO(), Accountant(), PurchasingAgent(), FinancialAnalyst()]
    lp.staff = [CEO()]
    work = [Finance_WorkUnit(1), Strategic_WorkUnit(1), Purchasing_WorkUnit(3.5), FinanceExecutive_WorkUnit(1)]
    """for worker in lp.pool:
        for task in work:
             print "Is %s capable of %s?: %s" % (worker.__class__, task.__class__, worker.capable(task))
    """
    lp.optimize_staff(work, mode = 'sticky')
    #print lp.staff
    #lp._build_staff_sticky(copy.deepcopy(work))
       
    staff_dict = {}
    for worker in lp.staff:
        if worker.__class__.__name__ in staff_dict.keys():
            staff_dict[worker.__class__.__name__] += 1
        else:
            staff_dict[worker.__class__.__name__] = 1
    print staff_dict
