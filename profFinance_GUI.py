from gi.repository import Gtk, GObject
from collections import OrderedDict
from picklist_ve import *
import ProjectFinance as pf
import copy
import UnitValues as uv

class PF_GUI:

    def __init__(self, glade_filename):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(glade_filename)
        self.win = self.builder.get_object("main_window")

        self.win.connect("delete-event", Gtk.main_quit)
        self._setup_costs_tab()        
        self._setup_menus()
        self._setup_financing_tab()
        self.file = None

       


        self.go()

    def go(self):
        self.win.show()

    def _setup_costs_tab(self):

        
        self.capex_button = self.builder.get_object("button_capex")
        self.capex_button.connect("clicked", self.on_capex_button_clicked)

        self.varex_button = self.builder.get_object("button_varex")
        self.varex_button.connect("clicked", self.on_varex_button_clicked)


        self.fc_button = self.builder.get_object("button_fixed_costs")
        self.fc_button.connect("clicked", self.on_fc_button_clicked)

    def _setup_financing_tab(self):
        self.auto_debt_radio = self.builder.get_object("auto_debt_radio")
        self.auto_debt_radio.set_active(True)
        self.manual_debt_radio = self.builder.get_object("manual_debt_radio")
        self.manual_debt_radio.set_sensitive(False)


        
	
    #Setup the items in the menu bar
        
    def _setup_menus(self):

        self.FileNewAction = self.builder.get_object("FileNewAction")
        self.FileNewAction.connect("activate", self.on_FileNew_activate)

        self.FileSaveAction = self.builder.get_object("FileSaveAction")
        self.FileSaveAction.connect("activate", self.on_FileSave_activate)

        self.FileSaveAsAction = self.builder.get_object("FileSaveAsAction")
        self.FileSaveAsAction.connect("activate", self.on_FileSaveAs_activate)

        self.FileOpenAction = self.builder.get_object("FileOpenAction")
        self.FileOpenAction.connect("activate", self.on_FileOpen_activate)

    def on_FileNew_activate(self, widget):
        self.win.show_all()   #Need to add functions to clear all of the data from the forms here for a new file
        #Need to generate a new project
        self.project = pf.CapitalProject()
        self.project.setFinancialParameters(pf.FinancialParameters())
        


        self._connect_gen_assumptions()
        self.design_capacity = [None, None]

    def on_FileOpen_activate(self, widget):
        dialog = Gtk.FileChooserDialog("Load project", self.win, Gtk.FileChooserAction.OPEN, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.file = dialog.get_filename()
        elif response == Gtk.ResponseType.CANCEL:
            dialog.destroy()
            return

        dialog.destroy()
        print "loading..."

        try:
            loader = pf.PF_FileLoader(self.file)
            self.project = loader.load()
        except Exception:
            raise Exception, "Bad filename?? I really need to improve this exception!"

        self.win.show_all()
        self._connect_gen_assumptions()
        self.design_capacity = [self.project.fin_param['Design_cap'].value, self.project.fin_param['Design_cap'].units]

        #at this point, the PROJECT will be appropriate, but none of the dialogs will be updated with the project information; need to do that

    def on_FileSave_activate(self, widget):
        #currently no overwrite protection!
        if self.file is None:
            dialog = Gtk.FileChooserDialog("Save file", self.win, Gtk.FileChooserAction.SAVE, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                self.file = dialog.get_filename()
            elif response == Gtk.ResponseType.CANCEL:
                dialog.destroy()
                return			#if you cancel saving, stop trying to save

            dialog.destroy()

        
        print "saving..."
        #This is the easy one -- will want a file dialog box, but let's test the easy way first
        

        saver = pf.PF_FileSaver(self.project, self.file)
        saver.save()
    
    def on_FileSaveAs_activate(self, widget):
        #currently no overwrite protection
        dialog = Gtk.FileChooserDialog("Save file", self.win, Gtk.FileChooserAction.SAVE, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.file = dialog.get_filename()
        elif response == Gtk.ResponseType.CANCEL:
            dialog.destroy()
            return

        dialog.destroy()

        print "saving as %s..." % self.file
        saver = pf.PF_FileSaver(self.project, self.file)
        saver.save()

    def _connect_gen_assumptions(self):
        key_list = copy.deepcopy(pf.FinancialParameters.key_list)
        key_list.remove('Startup_year')
        key_list.remove('Depreciation_type')
        key_list.remove('Capital_expense_breakdown')
        key_list.remove('Design_cap')
        for key in key_list:
            entry = self.builder.get_object("entry_%s" % key)
            
            entry.connect("focus-out-event", self.on_GenAssumptionField_lostfocus)
            if self.project.fin_param[key] is not None:
                entry.set_text(str(self.project.fin_param[key]))
            else:
                entry.set_text("")
        combo = self.builder.get_object("combo_depreciation_type")
        combo.connect("changed", self.on_depreciation_changed)

        deps = ['straight-line', 'MACRS']
        if self.project.fin_param['Depreciation_type'] is not None:
            combo.set_active(deps.index(self.project.fin_param['Depreciation_type']))
        else:
           combo.set_active(-1)
        entry = self.builder.get_object("entry_Design_cap")
        entry.connect("focus-out-event", self.on_design_capacity_lostfocus)
        dc = False
        if self.project.fin_param['Design_cap'] is not None:
            entry.set_text(str(self.project.fin_param['Design_cap'].value))
            dc = True
        else:
            entry.set_text("")


        entry = self.builder.get_object("entry_design_cap_units")
        entry.connect("focus-out-event", self.on_design_capacity_units_lostfocus)
        if dc:
            entry.set_text(str(self.project.fin_param['Design_cap'].units))
        else:
            entry.set_text("")

        if self.project.fin_param['Capital_expense_breakdown'] is None:
            self.project.fin_param['Capital_expense_breakdown'] = []
        self.ceb_button = self.builder.get_object("cap_expense_button")
        self.ceb_button.connect("clicked", self.on_ceb_button_clicked)


    def on_depreciation_changed(self, widget):
        deps = ['straight-line', 'MACRS']
        self.project.fin_param['Depreciation_type'] = deps[widget.get_active()] 

    def on_design_capacity_lostfocus(self, widget, event):
        self.design_capacity[0] = float(widget.get_text())
        if None not in self.design_capacity:
            self.project.fin_param['Design_cap'] = uv.UnitVal(self.design_capacity[0], self.design_capacity[1])

    def on_design_capacity_units_lostfocus(self, widget, event):
        self.design_capacity[1] = str(widget.get_text())
        if None not in self.design_capacity:
            self.project.fin_param['Design_cap'] = uv.UnitVal(self.design_capacity[0], self.design_capacity[1])

    def on_ceb_button_clicked(self, widget):
        edit_box = VariableListInputDialog(self.win, self.project.fin_param['Capital_expense_breakdown'], header = "Enter capital expense breakdown", list_label = "Year")
        response = edit_box.run()
        if response == Gtk.ResponseType.OK:
            
            self.project.fin_param['Capital_expense_breakdown'] = edit_box.get_info(typ = float)
        edit_box.destroy()

    def on_GenAssumptionField_lostfocus(self, widget, event):
        """General function to handle changes in most of the inputs on the General Assumptions tab"""
        #need to check if the type is correct, return the focus if not
        name = Gtk.Buildable.get_name(widget)[len("entry_"):]
        if name in ['Cap_factor', 'Target_IRR', 'Inflation_rate', 'Federal_tax_rate', 'State_tax_rate', 'Startup_revenue_breakdown', 'Startup_fixed_cost_breakdown', 'Startup_variable_cost_breakdown']:
            factor = 0.01
        else:
            factor = 1
        try:
            if widget.get_text() == "":
                self.project.fin_param[name] = None
            else:
                
                self.project.fin_param[name] = pf.FinancialParameters.type_dict[name](widget.get_text())*factor
        except ValueError:
            #Create the error dialog box
            dialog = Gtk.MessageDialog(self.win,0,Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "TYPE ENTRY ERROR")
            dialog.format_secondary_text("The data for this entry must be of type %s" % pf.FinancialParameters.type_dict[name])
            dialog.run()
            dialog.destroy()
            #Return the focus to the widget
            widget.grab_focus()

    def on_fc_button_clicked(self, widget):
    

        edit_box = FixedCostsInputDialog(self.win, self.project.fixed_costs)
        response = edit_box.run()

        if response == Gtk.ResponseType.OK:
            self.project.fixed_costs = edit_box.get_info()
        
        edit_box.destroy()

    def on_capex_button_clicked(self, widget):
        edit_box = CapitalCostsInputDialog(self.win, self.project.capex)
        response = edit_box.run()
        if response == Gtk.ResponseType.OK:
            self.project.capex = edit_box.get_info()
        edit_box.destroy()

    def on_varex_button_clicked(self, widget):
        edit_box = VariableCostsInputDialog(self.win, self.project.variable_costs)
        response = edit_box.run()
        if response == Gtk.ResponseType.OK:
            self.project.variable_costs = edit_box.get_info()
        edit_box.destroy()

    def on_ic_button_clicked(self, widget):
        print "clicked"


    def on_InitialYear_change(self, widget):
        pass


if __name__ == "__main__":
    app = PF_GUI("projFinance2.glade")
    Gtk.main()
