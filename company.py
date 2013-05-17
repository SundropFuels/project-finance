class Company:
    """Object that represents a corporation in the corporate simulation
    Has the following data members:
    -R_D_assets: list of research and development assets
    -st_assets: short term assets
    -projects: list of capital and R&D projects
    -staff: list of employees in the company
    -balance_sheet: the company balance sheet
    -stock_outstanding: company stock outstanding (# of shares)
    """

    def __init__(self, name):
        self.name = name


    def set_current_period(self, time_period):
        self.current_period = time_period


