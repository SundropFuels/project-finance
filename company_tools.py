"""company_tools.py
Tool objects to use with the company.py library
Chris Perkins
2012-10-23
"""

import datetime
import copy

class CTException(Exception):
    def __init__(self,value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class TimePeriodError(CTException):
    pass

class FinDate(datetime.date):
    """Special instance of the datetime.date class for financial purposes"""
    
    
    def __init__(self, year, month, day):
        self.date = datetime.date(year,month,day)

    def output_date(self):
        """Output the date as a string in the indicated format"""
        return self.date.isoformat()
            

    def increment_day(self):
        dt = datetime.timedelta(days = 1)
        self.date += dt

    def increment_month(self):
        dt = datetime.timedelta(days = 1)
        d = self.date.day
        self.date += dt
        while self.date.day != d:
            self.date += dt

    def increment_year(self):
        if (self.date.year % 4 == 0 and self.date.month < 3) or (self.date.year % 4 == 3 and self.date.month > 2):
            #leap year
            dt = datetime.timedelta(days = 366)
        else:
            dt = datetime.timedelta(days = 365)
        self.date += dt

    def decrement_day(self):
        dt = datetime.timedelta(days = 1)
        self.date -= dt

    def decrement_month(self):
        dt = datetime.timedelta(days = 1)
        d = self.date.day
        self.date -= dt
        while self.date.day != d:
            self.date -= dt

    def decrement_year(self):
        dt = datetime.timedelta(days=self.num_days_forward_year())
        self.date += dt

    def num_days_forward_year(self):
        if (self.date.year % 4 == 0 and self.date.month < 3) or (self.date.year % 4 == 3 and self.date.month > 2):
            # leap year
            return 366
        else:
            return 365

    def forward_range(self, end_date):
        date_list = []
        iterator = FinDate(self.year(), self.month(), self.day())
        while iterator < end_date:
            date_list.append(iterator.output_date())
            iterator.increment_day()
        return date_list

    def forward_range_months(self, end_date):
        date_list = []
        iterator = FinDate(self.year(), self.month(), self.day())
        while iterator < end_date:
            date_list.append(iterator.output_date())
            iterator.increment_month()
        return date_list

    def year(self):
        return self.date.year

    def month(self):
        return self.date.month

    def day(self):
        return self.date.day

    def __add__(self, addend):
        if isinstance(addend, tuple) and isinstance(addend[0],int) and addend[1] in ['year', 'month', 'day']:
            s = FinDate(self.year(), self.month(), self.day())
            count = addend[0]
            while count > 0:
                getattr(s,"increment_%s" % addend[1])()
                count -= 1
            return s
        else:
            raise CTException, "Invalid addend"

    def __sub__(self, addend):
        if isinstance(addend, tuple) and isinstance(addend[0],int) and addend[1] in ['year', 'month', 'day']:
            s = FinDate(self.year(), self.month(), self.day())
            count = addend[0]
            while count > 0:
                getattr(s,"decrement_%s" % addend[1])()
                count -= 1
            return s
        else:
            raise CTException, "Invalid addend"


    def __lt__(self, period):
        
        if self.output_date() < period.output_date():
            return True
        else:
            return False

    def __gt__(self, period):
       

        if self.output_date() > period.output_date():
            return True
        else:
            return False

    def __le__(self, period):
        

        if self.output_date() <= period.output_date():
            return True
        else:
            return False

    def __ge__(self, period):
        

        if self.output_date() >= period.output_date():
            return True
        else:
            return False

    def __eq__(self, period):
        

        if period is None:
            return False

        if self.output_date() == period.output_date():
            return True
        else:
            return False

    def __deepcopy__(self, memo):
        return self

class TimePeriod:

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    def __init__(self, offset, start_period):
        """Instantiates the class.  In its abstract nature, this is just a counter"""
        if not isinstance(start_period, str):
            raise TimePeriodError, "The start period must be a string"

        if not isinstance(offset, int):
            raise TimePeriodError, "The offset must be an integer" 

        self.base_period = start_period

        self.count = offset

    def now(self):
        return str(int(self.base_period) + self.count)

    def increment(self, arg):
        self.count += arg

    def decrement(self, arg):
        self.count -= arg

class annualTimePeriod(TimePeriod):

    def __init__(self, offset, start_period):
        TimePeriod.__init__(self, offset, start_period)
        self.base_year = int(start_period)

    def now(self):
        return str(self.base_year + self.count)

class quarterlyTimePeriod(TimePeriod):

    def __init__(self, offset, start_period):
        TimePeriod.__init__(self, offset, start_period)
        if len(start_period) != 6 or start_period[4] != 'Q':
            raise TimePeriodError, "The format must be <YYYY>Q<#>, e.g. 2012Q1"

        #Strip off the first four characters to get the year
        try:
            self.base_year = int(start_period[:4])
            self.base_quarter = int(start_period[5])
        except ValueError:
            raise TimePeriodError, "The format must be <YYYY>Q<#>, e.g. 2012Q1"

        

    def now(self):
        """Return the formatted year and quarter of the current count"""
        year_increment = self.count/4
        quarter_increment = self.count % 4
        if self.base_quarter + quarter_increment > 4:
            new_quarter = self.base_quarter + quarter_increment - 4
            year_increment += 1
        else:
            new_quarter = self.base_quarter + quarter_increment
        return "%sQ%s" % (str(self.base_year + year_increment), new_quarter)

class monthlyTimePeriod(TimePeriod):

    def __init__(self, offset, start_period):
        TimePeriod.__init__(self, offset, start_period)
        if len(start_period) != 8 or start_period[3] != ' ':
            raise TimePeriodError, "The format must be <mmm> <YYYY>, e.g. Jun 2012"

        try:
            self.base_year = int(start_period[4:8])

        except ValueError:
            raise TimePeriodError, "The format must be <mmm> <YYYY>, e.g. Jun 2012"              

        try:
            self.base_month = TimePeriod.months.index(start_period[:3])
        except ValueError:
            raise TimePeriodError, "The format must be <mmm> <YYYY>, e.g. Jun 2012"

    def now(self):
        """Return the formatted month and year of the current count"""
        year_increment = self.count/12
        month_increment = self.count % 12
        if self.base_month + month_increment > 12:
            new_month = self.base_month + month_increment - 12
            year_increment += 1
        else:
            new_month = self.base_month + month_increment
        return "%s %s" % (TimePeriod.months[new_month], self.base_year + year_increment)
            
        

