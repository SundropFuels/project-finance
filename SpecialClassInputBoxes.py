from gi.repository import Gtk, GObject
from collections import OrderedDict
import UnitValues as uv


class EntryGrid(Gtk.Grid):
    def __init__(self, label_dict, type_dict, num_cols = 1, units_dict = None):
        Gtk.Grid.__init__(self)
        #now, walk through the label dict and create entries for each of the labels
        if units_dict is not None:
            self.mod_size = 3
        else:
            self.mod_size = 2

        self.type_dict = type_dict
        self.entry_dict = OrderedDict()
        self.label_dict = OrderedDict()
        self.unit_label_dict = {}

        col = 0
        row = 0
        for k, v in label_dict.items():
            self.entry_dict[k] = Gtk.Entry()
            self.label_dict[k] = Gtk.Label(v)
            self.attach(self.label_dict[k],col*self.mod_size,row,3,1)
            self.attach_next_to(self.entry_dict[k], self.label_dict[k], Gtk.PositionType.RIGHT, 3, 1)
            self.entry_dict[k].connect("focus-out-event", self.on_entry_lostfocus, k)
            if units_dict is not None and k in units_dict.keys():
                self.unit_label_dict[k] = Gtk.Label(units_dict[k])
                self.attach_next_to(self.unit_label_dict[k], self.entry_dict[k], Gtk.PositionType.RIGHT, 3, 1)
            col += 1
            if col % num_cols == 0:
                col = 0
                row += 1

    def on_entry_lostfocus(self, widget, event, entry_index):
        """This allows for type checking of the entry boxes for this tool"""
        
        if self.entry_dict[entry_index].get_text() != "" and self.type_dict[entry_index] is not None:
            try:
                a = self.type_dict[entry_index](widget.get_text())
            except ValueError:
                self.emit("bad-entry-type", self.type_dict[entry_index], self.entry_dict[entry_index])
              

    def get_entries(self):
        return_dict = {}
        for k, v in self.entry_dict.items():
            if v.get_text() == "":
                return_dict[k] = 0
            else:
                if self.type_dict[k] is None:
                    return_dict[k] = None
                else:
                    return_dict[k] = self.type_dict[k](v.get_text())
        return return_dict

    def initialize_values(self, value_dict):
        for k,v in value_dict.items():
            if v is None:
                self.entry_dict[k].set_text("")
            else:
                self.entry_dict[k].set_text(str(v))

    def freeze_name(self):
        if 'name' in self.entry_dict:
            self.entry_dict['name'].set_editable(False)
        
    def update_unit_labels(self, units_dict):
        for k in units_dict:
            if k in self.unit_label_dict:
                self.unit_label_dict[k].set_text(units_dict[k])

    def update_labels(self, label_dict):
        for k in label_dict:
            if k in self.label_dict:
                self.label_dict[k].set_text(label_dict[k])

    def update_types(self, type_dict):
        self.type_dict = type_dict

class FlexibleInputBox(Gtk.Box):
    """Labels/entries for inputting information given a dict of {names:(label,type)} -- provides access to information and input checking"""
    def __init__(self, parent_window, item_class, num_cols = 1):
        #!!! raise error if num_cols is not an int, info_class is not a class with a gl_add_info dict, and parent_window is not Gtk.Window
        

        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL, spacing = 6)
        self.info_dict = item_class.gl_add_info
        self.parent = parent_window
      
        label_dict = OrderedDict()
        type_dict = OrderedDict()
        for k, v in self.info_dict.items():
            label_dict[k] = v[0]
            type_dict[k] = v[1]
        self.grid = EntryGrid(label_dict = label_dict, type_dict = type_dict, num_cols = 1)
        self.add(self.grid)
        self.grid.connect("bad-entry-type", self.on_bad_entry)

    def on_bad_entry(self, widget, typ, entry):
        dialog = Gtk.MessageDialog(self.parent, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "TYPE ENTRY ERROR")
        dialog.format_secondary_text("The data for this entry must be of type %s" % typ)
        dialog.run()
        dialog.destroy()
        #Return the focus to the widget
        entry.grab_focus()

    def initialize_values(self, value_dict):
        
        self.grid.initialize_values(value_dict)

    def freeze_name(self):    
        
       
        self.grid.freeze_name()

    def get_entries(self):
       
        return self.grid.get_entries()


class FixedCostsInputBox(FlexibleInputBox):
    
    def __init__(self, parent_window, item_class):
        
        FlexibleInputBox.__init__(self, parent_window, item_class)
        

        #pack in the percent vs. direct entry radio button
        self.pct_radio = Gtk.RadioButton(label = "Entered as a percent of total direct capital")
        self.direct_radio = Gtk.RadioButton.new_with_label_from_widget(self.pct_radio, "Entered as a direct amount of money")
        self.radio_button_box = Gtk.Box(orientation = Gtk.Orientation.VERTICAL, spacing = 6)
        self.pack_start(self.radio_button_box, True, True, 0)
        self.radio_button_box.pack_start(self.pct_radio, True, True, 0)
        self.radio_button_box.pack_start(self.direct_radio, True, True, 0)
        self.pct_radio.connect("toggled", self.on_radio_buttons_toggled, "pct")
        self.direct_radio.connect("toggled", self.on_radio_buttons_toggled, "direct")

        
        #pack in the additional labels that will switch on selection of the radio button
        self.unit_labels = {}
        for k in self.entry_dict:
            self.unit_labels[k] = Gtk.Label("%")
            self.grid.attach_next_to(self.unit_labels[k], self.entry_dict[k], Gtk.PositionType.RIGHT, 1,1)

    def freeze_name(self):
        pass

    def get_entries(self):
        return_dict = FlexibleInputBox.get_entries(self)
        if self.pct_radio.get_active():
            return_dict['mode'] = 'pct'
        else:
            return_dict['mode'] = 'direct'

        return return_dict

    def initialize_values(self, value_dict):
        mode = value_dict['mode']
        del value_dict['mode']
        getattr(self, '%s_radio' % mode).set_active(True)

        for k in value_dict:
            if value_dict[k] is None:
                self.entry_dict[k].set_text("")
            else:
                self.entry_dict[k].set_text(str(value_dict[k]))
            
    def on_radio_buttons_toggled(self, widget, name):
        if widget.get_active():
            if name == "pct":
                self.fc_mode = "pct"
                for v in self.unit_labels.values():
                    v.set_text("$")
                
            elif name == "direct":
                self.fc_mode = "direct"
                for v in self.unit_labels.values():
                    v.set_text("%")


class VariableExpenseInputBox(Gtk.Box):
    """Input box for the VariableExpense class item"""
    def __init__(self, parent_window, item_class):
        Gtk.Box.__init__(self, orientation = Gtk.Orientation.VERTICAL, spacing = 6)
        #So these could be MUCH more elegant if I supplied a template to build it, but I don't feel like writing the function right now

        
        self.parent = parent_window
        
        #This one has these things to enter: a name, the number and units for the unit cost, the value and units for the production required, and the class of variable expense
        name_hbox = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL, spacing = 6)
        cost_hbox = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL, spacing = 6)
        prod_hbox = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL, spacing = 6)

        self.pack_start(name_hbox, True, True, 0)
        self.pack_start(cost_hbox, True, True, 0)
        self.pack_start(prod_hbox, True, True, 0)

        name_hbox.pack_start(Gtk.Label("Name"), True, True, 0)
        self.name_entry = Gtk.Entry()
        name_hbox.pack_start(self.name_entry, True, True, 0)

        cost_hbox.pack_start(Gtk.Label("Cost"), True, True, 0)
        self.cost_v_entry = Gtk.Entry()
        cost_hbox.pack_start(self.cost_v_entry, True, True, 0)
        cost_hbox.pack_start(Gtk.Label("Units: $\\"),True, True, 0)
        self.cost_u_entry = Gtk.Entry()
        cost_hbox.pack_start(self.cost_u_entry, True, True, 0)

        prod_hbox.pack_start(Gtk.Label("Production requirement"), True, True, 0)
        self.prod_v_entry = Gtk.Entry()
        prod_hbox.pack_start(self.prod_v_entry, True, True, 0)
        prod_hbox.pack_start(Gtk.Label("Units"), True, True, 0)
        self.prod_u_entry = Gtk.Entry()
        prod_hbox.pack_start(self.prod_u_entry, True, True, 0)
        
        class_hbox = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL, spacing = 6)
        self.pack_start(class_hbox, True, True, 0)

        #class_hbox.pack_start(Gtk.Label("Type of variable expense"), True, True, 0)
        #self.class_combo = Gtk.combo_box_new_text()
        #self.class_combo.append_text("Feedstock")
        #self.class_combo.append_text("Utility")
        #class_hbox.pack_start(self.class_combo, True, True, 0)
        

    def initialize_values(self, value_dict):
        self.name_entry.set_text(value_dict['name'])
        self.cost_v_entry.set_text(str(value_dict['unit_cost'].value))
        self.cost_u_entry.set_text(value_dict['unit_cost'].units)    #!!need to actually strip these units by doing some text processing
        self.prod_v_entry.set_text(str(value_dict['prod_req'].value))
        self.prod_u_entry.set_text(value_dict['prod_req'].units)
        #set the combo box as well

    def freeze_name(self):
        self.name_entry.set_editable(False)
            
    def on_entry_lostfocus(self, widget, event):
        pass

    def get_entries(self):
        """Returns a map of variable name:value -- not as elegant as the FlexibleInputBox"""
        return_map = {}
        return_map['name'] = self.name_entry.get_text()
        return_map['unit_cost'] = uv.UnitVal(float(self.cost_v_entry.get_text()),self.cost_u_entry.get_text())#!! need to fix units here -- requires adding ( ) processing to the converter!
        return_map['prod_req'] = uv.UnitVal(float(self.prod_v_entry.get_text()),self.prod_u_entry.get_text())
        #put on in for the combo box as well
        return return_map


GObject.type_register(EntryGrid)
GObject.signal_new("bad-entry-type", EntryGrid, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,GObject.TYPE_PYOBJECT))
