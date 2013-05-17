"""research_project.py
Library of classes and functions to handle R&D projects
Chris Perkins
2012-10-23
"""

import dataFrame_v2 as df
import numpy as np


class ResearchProject:
    """Class the represents a research project.  R&D projects have:
        - A schedule of work unit requirements
        - A schedule of equipment requirements
        - A schedule of operating expenses

        The schedule is a Dataframe, with columns of objects and rows representing each time period.  A TimePeriod object is used with a duration (# of periods).

    """

    def __init__(self, name, starting_time, duration):
        self.name = name
        self.start_time = starting_time
        self.duration = duration
        #need a dummy counter row for the Dataframe -- this may be handy
        counter = np.arange(0,self.duration)
        rows = []
        for i in [0:duration]:
            rows.append(starting_time.now())
            starting_time.increment(1)
        self.schedule = df.Dataframe(array_dict = {'counter':counter}, rows_list = rows)


    def set_work_requirements(self, work):
        """Set the task requirements.  work should be a numpy array of TaskList objects corresponding to the periods in the project"""
        if len(work) != self.duration:
            raise RPError, "There must be entries for %s years in the work plan, but %s years were indicated" % (self.duration, len(work))
        self.schedule['work'] = work

    def set_equip_requirements(self, equip_needs):
        """Set the equipment requirements.  equip_needs should be a numpy array of EquipList objects corresponding to the periods in the project"""
        if len(equip_needs) != self.duration:
            raise RPError, "There must be entries for %s years in the equipment plan, but %s years were indicated" % (self.duration, len(equip_needs))
        self.schedule['equip'] = equip_needs

    def set_opex_requirements(self, opex):
        """Set the operating expense requirements.  opex should be a numpy array of RDOperatingExpense objects corresponding to the periods in the project"""
        if len(opex) != self.duration:
            raise RPError, "There must be entries for %s years in the operating expense plan, but %s years were indicated" % (self.duration, len(opex))
        self.schedule['opex'] = opex

    def get_requirements(self, time_period):
        """For the time period of interest, return all of the research project requirements as a dictionary"""
        try:
            return self.schedule.get_row(time_period.now())
        except df.dfException:
            raise RPError, "There is no row for the time period %s", % time_period.now()

class ResearchEquipment:
    """Holds a research capital item, and controls allocation of this resource"""
    #decision to be made here -- do I subclass the hell out of this, and use an "is a" structure to see if it is capable of doing what we want?  Or do I make very specific demands on equipment?
