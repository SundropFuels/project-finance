from gi.repository import Gtk, GObject
from collections import OrderedDict
import SpecialClassInputBoxes as inboxes
import ProjectFinance as pf #we'll fix this later, once we know the boxes are working


class GUIApp:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("picklist_v2.glade")
        self.win = self.builder.get_object("window1")
        

        self.picklist = PickList(self.win, TestItem)
        self.win.add(self.picklist)
        self.win.connect("delete-event", Gtk.main_quit)
        self.win.show_all()



class TestItem:
    gl_add_info = OrderedDict([("name",("Name",str)), ("age", ("Age",int)), ("obj", ("Obj",str))])
    gl_type_info = OrderedDict([("name", str), ("age", int), ("obj", str)])    
    list_header = "Warriors"

    """This class holds a test item to stick in a list with the "add" function"""
    def __init__(self, name, age = None, obj = None):
        self.name = name
        self.obj = obj
        self.age = age
        
class InputDialog(Gtk.Dialog):
    """The is the abstract class for all the types of input dialogs"""
    def __init__(self, parent, instance, header = "Input"):
        Gtk.Dialog.__init__(self, header, parent, 0, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_default_size(150,100)
        self.box = self.get_content_area()
        self.show_all()

    def get_info(self):
        """Pass the instance this is supposed to define back to the controlling window"""
        pass

    def set_info(self, instance):
        """Set the appropriate input information in the box based on the attributes in the instance"""
        pass

#Set these into another module specifically for ProjectFinance

class VariableListInputDialog(InputDialog):
    def __init__(self, parent, instance, header = "Update list information", list_label = "item"):
        InputDialog.__init__(self, parent, instance, header)
        self.parent = parent
        if instance is None:
            self.list = []
        elif isinstance(instance, list):
            self.list = instance
        else:
            raise Exception, "Instance is not a list"

        self.list_label = list_label
        self.main_box = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL, spacing = 6)
        self.box.pack_start(self.main_box, True, True, 0)

        self.button_box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL, spacing = 6)
        self.main_box.pack_start(self.button_box, True, True, 0)

        self.add_button = Gtk.Button("Add item")
        self.del_button = Gtk.Button("Delete item")

        self.add_button.connect("clicked", self.on_add_clicked)
        self.del_button.connect("clicked", self.on_del_clicked)

        self.button_box.pack_start(self.add_button, True, True, 0)
        self.button_box.pack_start(self.del_button, True, True, 0)

        #My EntryGrid is not really appropriate here -- will use a grid of my own

        self.grid = Gtk.Grid()
        i = 0
        self.entry_list = []
        self.label_list = []
        for item in self.list:
            self.label_list.append(Gtk.Label("%s %s" % (list_label, i+1)))
            self.entry_list.append(Gtk.Entry())
            self.grid.attach(self.label_list[i], 0, i, 3, 1)
            self.grid.attach_next_to(self.entry_list[i], self.label_list[i], Gtk.PositionType.RIGHT, 3,1)
            i += 1

        self.set_info(self.list)
        self.grid_box = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL, spacing = 6)
        self.grid_box.add(self.grid)
        self.main_box.pack_start(self.grid_box, True, True, 0)
        self.show_all()


    def set_info(self, instance):
        
        if instance != self.list:
            self.list = instance
            if len(instance) < len(self.entry_list):
                for index in range(len(instance), len(self.entry_list)):
                    self.grid.remove(self.label_list[index])
                    self.grid.remove(self.entry_list[index])
                    self.label_list.remove(self.label_list[index])
                    self.entry_list.remove(self.entry_list[index])
            elif len(instance) > len(self.entry_list):
            
                for index in range(len(self.entry_list), len(instance)):
                    self.label_list.append(Gtk.Label("%s %s" % (self.list_label, index + 1)))
                    self.entry_list.append(Gtk.Entry())
                    self.grid.attach(self.label_list[index], 0, index, 3, 1)
                    self.grid.attach_next_to(self.entry_list[index], self.label_list[index], Gtk.PositionType.RIGHT, 3,1)
        for index in range(0,len(instance)):
            self.entry_list[index].set_text(str(instance[index]))
            

    def get_info(self, typ=str):
        """Returns everything as strings -- can cast these as you like later"""
        for index in range(0, len(self.entry_list)):
            entry = self.entry_list[index]
            self.list[index] = typ(entry.get_text())
        return self.list

    def on_add_clicked(self, widget):
        index = len(self.entry_list)
        self.entry_list.append(Gtk.Entry())
        self.label_list.append(Gtk.Label("%s %s" % (self.list_label, index + 1)))
        self.grid.attach(self.label_list[index], 0, index, 3, 1)
        self.grid.attach_next_to(self.entry_list[index], self.label_list[index], Gtk.PositionType.RIGHT, 3,1)
        self.list.append(None)
        self.show_all()
    def on_del_clicked(self, widget):
        index = len(self.entry_list) - 1
        self.grid.remove(self.label_list[index])
        self.grid.remove(self.entry_list[index])
        self.label_list.pop()
        self.entry_list.pop()
        self.list.pop()


class DictInputDialog(InputDialog):
    def __init__(self, parent, instance, header = "Update dictionary information"):
        InputDialog.__init__(self, parent, instance, header)
        self.parent = parent
        if instance is None:
            self.dict = {}
        elif isinstance(instance, dict) or isinstance(instance, OrderedDict):
            self.dict = instance

        else:
            raise Exception, "Instance is not a dictionary"

        self.main_box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL, spacing = 6)
        self.box.pack_start(self.main_box, True, True, 0)

        #add the grid of entries -- by default, the dictionary version will not connect up the type dictionary -- we'll totally ignore it
        label_dict = {}
        type_dict = {}
        for key in self.dict:
            label_dict[key] = key
            type_dict[key] = None
        self.grid = inboxes.EntryGrid(label_dict = label_dict, type_dict = type_dict)
        self.main_box.add(self.grid)
        self.set_info(self.dict)
        self.show_all()

    def get_info(self):
        return self.grid.get_entries()

    def set_info(self, instance):
        self.grid.initialize_values(instance)

class IndirectCapitalCostsInputDialog(DictInputDialog):
    def __init__(self, parent, instance, header = "Update indirect capital costs", depreciable = True):
        DictInputDialog.__init__(self, parent, instance, header)
        if depreciable:
            labels = pf.CapitalCosts.id_labels
            types = pf.CapitalCosts.id_types

        else:
            labels = pf.CapitalCosts.ind_labels
            types = pf.CapitalCosts.ind_types

        self.grid.update_labels(labels)
        self.grid.update_types(types)

class CapitalCostsInputDialog(InputDialog):
    def __init__(self, parent, instance, header = "Capital costs input"):
        InputDialog.__init__(self, parent, instance, header)
        self.parent = parent
        if instance is None:
            self.capex = pf.CapitalCosts()

        elif isinstance(instance, pf.CapitalCosts):
            self.capex = instance

        else:
            raise Exception, "Instance is not a CapitalCosts instance!"

        self.main_box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL, spacing = 6)
        self.box.pack_start(self.main_box, True, True, 0)

        #Add the picklist
        self.picklist = PickList(self.parent, pf.CapitalExpense, object_list = self.capex.direct_capital, included_list = self.capex.direct_capital)
        self.main_box.pack_start(self.picklist, True, True, 0)

        #Add buttons to adjust the indirect capital costs
        self.indirect_depreciable_button = Gtk.Button("Edit indirect depreciable costs")
        self.main_box.pack_start(self.indirect_depreciable_button, False, False, 0)
        self.indirect_depreciable_button.connect("clicked", self.on_di_button_clicked)

        self.indirect_nondepreciable_button = Gtk.Button("Edit non-depreciable indirect capital costs")
        self.main_box.pack_start(self.indirect_nondepreciable_button, False, False,0)
        self.indirect_nondepreciable_button.connect("clicked", self.on_ndi_button_clicked)

        self.set_info(self.capex)
        self.show_all()

    def on_di_button_clicked(self, widget):
        
        #create a dialog for this, then send info down to the capex item
        
        edit_box = IndirectCapitalCostsInputDialog(self.parent, self.capex.indirect_deprec_capital, depreciable = True)
        response = edit_box.run()
        if response == Gtk.ResponseType.OK:
            self.capex.indirect_deprec_capital = edit_box.get_info()
        edit_box.destroy()


    def on_ndi_button_clicked(self, widget):
        
        #create a dialog for this, then send info down to the capex item
        edit_box = IndirectCapitalCostsInputDialog(self.parent, self.capex.indirect_nondeprec_capital, depreciable = False)
        response = edit_box.run()
        if response == Gtk.ResponseType.OK:
            self.capex.indirect_deprec_capital = edit_box.get_info()
        edit_box.destroy()


    def set_info(self, instance):
        if not isinstance(instance, pf.CapitalCosts):
            raise Exception, "Instance needs to be an instance of CapitalCosts"

        self.capex = instance
        

    def get_info(self):
        
        #grab the selected capital item list from the picklist
        self.capex.direct_capital = self.picklist.get_included()
        #return the main capex item
        return self.capex

        

class VariableCostsInputDialog(InputDialog):
    """Returns a VariableCosts object back, with information conveniently filled in!"""
    def __init__(self, parent, instance, header = "Variable costs input"):
        InputDialog.__init__(self, parent, instance, header)
        self.parent = parent
        if instance is None:
            self.vc = pf.VariableCosts()

        elif isinstance(instance, pf.VariableCosts):
            self.vc = instance

        else:
            raise Exception, "Instance is not a VariableCosts instance!"

        self.main_box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL, spacing = 6)
        self.box.pack_start(self.main_box, True, True, 0)

        #Add the picklist
        self.picklist = PickList(self.parent, pf.VariableExpense, object_list = self.vc.variable_exps, included_list = self.vc.variable_exps)
        self.main_box.pack_start(self.picklist, True, True, 0)

        self.set_info(self.vc)
        self.show_all()



    def set_info(self, instance):
        pass

    def get_info(self):
        
        #grab the selected variable item list from the picklist
        self.vc.variable_exps = self.picklist.get_included()
        #return the main VariableCosts item
        return self.vc
        

class FixedCostsInputDialog(InputDialog):
    def __init__(self, parent, instance, header = "Fixed costs input"):
        InputDialog.__init__(self, parent, instance, header)
        self.parent = parent
        if instance is None:
            self.fc = pf.FixedCosts()

        elif isinstance(instance, pf.FixedCosts):
            self.fc = instance
            
        else:
            raise Exception, "Instance is not a FixedCosts instance!"

        self.main_box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL, spacing = 6)
        self.box.pack_start(self.main_box, True, True, 0)
        #Add the grid.  For these custom classes, it is easy to grow these together; this in no way limits the ability to auto-detect with introspection, just not choosing to do it now
        unit_labels = {}
        for k in pf.FixedCosts.labels:
            unit_labels[k] = '$'
        
        self.grid = inboxes.EntryGrid(label_dict = pf.FixedCosts.labels, type_dict = pf.FixedCosts.types, units_dict = unit_labels)
        self.main_box.add(self.grid)
        self.grid.connect("bad-entry-type", self.on_bad_entry_type)

        #Pack in the radio buttons here
        self.pct_radio = Gtk.RadioButton(label = "Entered as a percent of total direct capital")
        self.direct_radio = Gtk.RadioButton.new_with_label_from_widget(self.pct_radio, "Entered as a direct amount of money")
        self.radio_button_box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL, spacing = 6)
        self.main_box.pack_start(self.radio_button_box, True, True, 0)
        self.radio_button_box.pack_start(self.pct_radio, True, True, 0)
        self.radio_button_box.pack_start(self.direct_radio, True, True, 0)
        self.pct_radio.connect("toggled", self.on_radio_buttons_toggled, "pct")
        self.direct_radio.connect("toggled", self.on_radio_buttons_toggled, "direct")

        self.set_info(self.fc)

        self.show_all()



    def get_info(self):
        for k,v in self.grid.get_entries().items():
            self.fc.fixed_costs[k] = float(v)
                        
        return self.fc

    def set_info(self, instance):
        self.grid.initialize_values(instance.fixed_costs)
        getattr(self, '%s_radio' % instance.mode).set_active(True)

    def on_radio_buttons_toggled(self, widget, name):
        
        
        if widget.get_active():
            unit_labels = {}
            
            if name == "pct":
                
                self.fc.mode = "pct"
                for k in pf.FixedCosts.labels:
                    unit_labels[k] = "%"
                
            elif name == "direct":
                self.fc.mode = "direct"
                for k in pf.FixedCosts.labels:
                    unit_labels[k] = "$"
            
            self.grid.update_unit_labels(unit_labels)

    def on_bad_entry_type(self, widget, typ, entry):
        dialog = Gtk.MessageDialog(self.parent, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "TYPE ENTRY ERROR")
        dialog.format_secondary_text("The data for this entry must be of type %s" % typ)
        dialog.run()
        dialog.destroy()
        #Return the focus to the widget
        entry.grab_focus()



class gl_AddDialog(Gtk.Dialog):
    def __init__(self, parent, item_class, header = "Add item"):
        Gtk.Dialog.__init__(self, header, parent, 0, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))

        
        #self.type_dict = type_dict
        self.set_default_size(150,100)
        self.hbox = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL, spacing = 6)
        try:
            
            self.input_box = getattr(inboxes, '%sInputBox' % item_class.__name__)(parent, item_class)
            
        except AttributeError:

            self.input_box = inboxes.FlexibleInputBox(parent, item_class)
        
        self.hbox.pack_start(self.input_box, True, True, 0)
        self.box = self.get_content_area()
        self.box.pack_start(self.hbox, True, True, 0)
        self.show_all()

    def print_entries(self):
        for k in self.entry_dict.keys():
            print self.entry_dict[k].get_text()
    
    def get_entries(self):
        
        return self.input_box.get_entries()
    
  
class gl_EditDialog(gl_AddDialog):
    def __init__(self, parent, item_class, value_dict):
        gl_AddDialog.__init__(self, parent, item_class)

        self.input_box.initialize_values(value_dict)
        
        self.input_box.freeze_name()    
        
        



class GraphicalList(Gtk.Box):
    """Creates an Add/Edit/Delete list in GNOME -- rudimentary in current form: needs error checking, etc., but does work for general items"""
    def __init__(self, parent_window, list_class, object_list = None):
        Gtk.Box.__init__(self,orientation=Gtk.Orientation.HORIZONTAL, spacing = 6)
        if hasattr(list_class, "list_header"):
            self.list_header = getattr(list_class, "list_header")
        else:
            self.list_header = "List items"

        #self.list = {}     #I know, this is a dict, but I'm tired, and need to get at these later
        self.list_class = list_class
        self.parent_window = parent_window

        #Pack the two vertical structures
        self.button_box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL, spacing = 6)
        self.pack_start(self.button_box, True, True, 0)
        
        self.add_button = Gtk.Button("Add")
        self.edit_button = Gtk.Button("Edit")
        self.del_button = Gtk.Button("Delete")

        self.add_button.connect("clicked", self.on_add_clicked)
        self.edit_button.connect("clicked", self.on_edit_clicked)
        self.del_button.connect("clicked", self.on_del_clicked)

        self.button_box.pack_start(self.add_button, True, True, 0)
        self.button_box.pack_start(self.edit_button, True, True, 0)
        self.button_box.pack_start(self.del_button, True, True, 0)

        """
        self.list_model = Gtk.ListStore(str, bool)
        self.view = Gtk.TreeView(self.list_model)
        self.renderer = Gtk.CellRendererText()
        self.column = Gtk.TreeViewColumn(self.list_header, self.renderer, text = 0)
        self.view.append_column(self.column)
        self.pack_start(self.view, True, True, 0)
        """
        self.initialize_values(object_list)
    
    def on_add_clicked(self, button):
        add_box = gl_AddDialog(self.parent_window, self.list_class)  
        response = add_box.run()
      
        if response == Gtk.ResponseType.OK:
            entries = add_box.get_entries()
            self.list[entries['name']] = self.list_class(entries['name'])      
            for k, v in entries.items():
                setattr(self.list[entries['name']],k,v)                          
                

            #Now need to update the tree model
            self.list_model.append((entries['name'],False))
            
        
        elif response == Gtk.ResponseType.CANCEL:
            print "You clicked CANCEL"

        add_box.destroy()

    def on_edit_clicked(self, button):
        model, m_iter = self.view.get_selection().get_selected()
        

        val_dict = {}
        
        try:
            
            for k in self.list_class.value_map:
                
                val_dict[k] = getattr(self.list[model[m_iter][0]], k)
            
        except AttributeError:
            for k in self.list_class.gl_add_info.keys():    
                val_dict[k] = getattr(self.list[model[m_iter][0]],k)

        edit_box = gl_EditDialog(self.parent_window, self.list_class, val_dict)
        response = edit_box.run()

        if response == Gtk.ResponseType.OK:
            entries = edit_box.get_entries()
            for k,v in entries.items():
                setattr(self.list[entries['name']],k,v)

        elif response == Gtk.ResponseType.CANCEL:
            print "You clicked CANCEL"

        edit_box.destroy()

    def on_del_clicked(self, button):
        #Need to get the data from the treeview selection, then use it to find the right item and remove it from the list (and the tree model!)
        model, m_iter = self.view.get_selection().get_selected()
        #Might add an "are you sure?" dialog here to prevent easy clicking

        del self.list[model[m_iter][0]]
        model.remove(m_iter)

    #need some initialization_functions
    def initialize_values(self, object_list):
        self.list = {}
        self.list_model = Gtk.ListStore(str, bool)
        self.view = Gtk.TreeView(self.list_model)
        self.renderer = Gtk.CellRendererText()
        self.column = Gtk.TreeViewColumn(self.list_header, self.renderer, text = 0)
        self.view.append_column(self.column)
        self.pack_start(self.view, True, True, 0)


        self.set_list(object_list)

    def set_list(self, object_list):
        if object_list is not None:
            for item in object_list:
                try:
                    if item.name not in self.list:
                        self.list[item.name] = item
                except KeyError:
                    raise Exception, "Graphical/pick lists can only be used for items that have keyword 'name'"
                self.list_model.append((item.name, False))

    def get_list(self):
        return self.list.values()

class PickList(GraphicalList):
    """A PickList is a kind of GraphicalList that contains a second view, in which we hold the names of items that are "selected" for analysis
       The ListStore model is more complicated for this object, as it contains two booleans for "visible" attributes for the second view"""
    def __init__(self, parent_window, list_class, object_list = None, included_list = None):
        GraphicalList.__init__(self,parent_window, list_class, object_list)

        if included_list is None:
            included_list = []

        #Add the button boxes and the other view
        
        self.arrow_box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL, spacing = 6)
        self.pack_start(self.arrow_box, True, True, 0)

        self.include_button = Gtk.Button()
        self.exclude_button = Gtk.Button()
        inc_img = Gtk.Image()
        inc_img.set_from_stock(Gtk.STOCK_GO_FORWARD, 1)
        exc_img = Gtk.Image()
        exc_img.set_from_stock(Gtk.STOCK_GO_BACK, 1)        

        self.include_button.add(inc_img)
        self.exclude_button.add(exc_img)
        self.include_button.connect("clicked", self.on_include_clicked)
        self.exclude_button.connect("clicked", self.on_exclude_clicked)

        
        self.arrow_box.pack_start(self.include_button, True, True, 0)
        self.arrow_box.pack_start(self.exclude_button, True, True, 0)



        self.included_view = Gtk.TreeView(self.list_model)
        self.included_renderer = Gtk.CellRendererText()
        self.included_column = Gtk.TreeViewColumn(self.list_header, self.included_renderer, text = 0)
        self.included_column.add_attribute(self.included_renderer, "visible", 1)
        self.included_view.append_column(self.included_column)
        self.pack_start(self.included_view, True, True, 0)

        self.set_included(included_list)
        
    def on_include_clicked(self, button):
        #Get selection
        model, m_iter = self.view.get_selection().get_selected()
        model[m_iter][1] = True

    def on_exclude_clicked(self, button):
        model, m_iter = self.included_view.get_selection().get_selected()
        model[m_iter][1] = False

    def get_included(self):
        """Returns a list of those items that are designated as included"""
        
        return_list = []
        for row in self.list_model:
            if row[1]:
                return_list.append(self.list[row[0]])
        return return_list        

    def set_included(self, item):
        """Sets the included flag for the item(s).  Can handle a single object or a list"""
        #There is some inherent bugginess here, because if the object is not in the original list, it does not throw an exception
        if isinstance(item, self.list_class):
            for row in self.list_model:
                if item.name == row[0]:
                    row[1] = True
            

        elif isinstance(item, list):
            for entry in item:
                self.set_included(entry)

        else:
            raise Exception, "Item must be an instance of %s.  It was an instance of %s." % (self.list_class, item.__class__.__name__)

class ListTestWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title = "Test window for editable lists and pick lists")

        graphlist = PickList(self, TestItem)
        self.add(graphlist)        





if __name__ == "__main__":
    
    win = ListTestWindow()
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()
    #app = GUIApp()
    Gtk.main()
