from gi.repository import Gtk, GObject
from collections import OrderedDict

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
        

class VE_AddDialog(Gtk.Dialog):
    def __init__(self, parent, header = "Add Variable Expense"):
        Gtk.Dialog.__init__(self, header, parent, 0, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_default_size(150,100)
        self.vbox_main = Gtk.Box(orientation = Gtk.Orientation.VERTICAL, spacing = 6)
        self.hbox_name = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL, spacing = 6)
        self.hbox_unit_costs = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL, spacing = 6)
        self.hbox_prod_required = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL, spacing = 6)
        self.vbox_main.pack_start(self.hbox_name, True, True, 0)
        self.vbox_main.pack_start(self.hbox_unit_costs, True, True, 0)
        self.vbox_main.pack_start(self.hbox_prod_required, True, True, 0)        



        self.hbox_name.pack_start(Gtk.Label("Name"), True, True, 0)
        self.name = Gtk.Entry()
        self.name.set_name('name')
        self.hbox_name.pack_start(self.name, True, True, 0)

        self.hbox_unit_costs.pack_start(Gtk.Label("Unit cost"), True, True, 0)
        self.unit_costs_v_entry = Gtk.Entry()
        self.unit_costs_v_entry.set_name('unit_costs_v_entry')
        self.hbox_unit_costs.pack_start(self.unit_costs_v_entry, True, True, 0)
        self.hbox_unit_costs.pack_start(Gtk.Label("Units:  $\\"), True, True, 0)
        self.unit_costs_u_entry = Gtk.Entry()
        self.unit_costs_u_entry.set_name('unit_costs_u_entry')
        self.hbox_unit_costs.pack_start(self.unit_costs_u_entry, True, True, 0)


        self.hbox_prod_required.pack_start(Gtk.Label("Units of variable expense per unit of production"), True, True, 0)
        self.unit_prod_v_entry = Gtk.Entry()
        self.unit_prod_v_entry.set_name('unit_prod_v_entry')
        self.hbox_prod_required.pack_start(self.unit_prod_v_entry, True, True, 0)

        self.hbox_prod_required.pack_start(Gtk.Label("Units:"), True, True, 0)
        self.unit_prod_u_entry = Gtk.Entry()
        self.unit_prod_u_entry.set_name('unit_prod_u_entry')
        self.hbox_prod_required.pack_start(self.unit_prod_u_entry, True, True, 0)

        self.box = self.get_content_area()
        self.box.pack_start(self.vbox_main, True, True, 0)
        self.show_all()
        self.type_dict = {'unit_costs_v_entry':float, 'unit_costs_u_entry':str,'unit_prod_v_entry':float,'unit_prod_u_entry':str, 'name':str}

        self.name.connect("focus-out-event", self.on_entry_lostfocus)
        self.unit_prod_u_entry.connect("focus-out-event", self.on_entry_lostfocus)
        self.unit_prod_v_entry.connect("focus-out-event", self.on_entry_lostfocus)
        self.unit_costs_u_entry.connect("focus-out-event", self.on_entry_lostfocus)
        self.unit_costs_v_entry.connect("focus-out-event", self.on_entry_lostfocus)


    def on_entry_lostfocus(self, widget, event):
        print Gtk.Buildable.get_name(widget)
        """This allows for type checking of the entry boxes for this tool"""
        try:
            a = self.type_dict[Gtk.Buildable.get_name(widget)](widget.get_text())
        except ValueError:
            dialog = Gtk.MessageDialog(self.parent, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "TYPE ENTRY ERROR")
            dialog.format_secondary_text("The data for this entry must be of type %s" % self.type_dict[widget.name])
            dialog.run()
            dialog.destroy()
            #Return the focus to the widget
            widget.grab_focus()

    def get_entries(self):
        """This will return the entries in a dict {name:val} with the values converted to the appropriate type"""
        return_dict = {}
        for widget in ['unit_prod_u_entry', 'unit_prod_v_entry', 'unit_costs_v_entry', 'unit_costs_u_entry', 'name']:
            return_dict[widget] = self.type_dict[widget](getattr(self,widget).get_text())
        return return_dict

class gl_AddDialog(Gtk.Dialog):
    def __init__(self, parent, item_dict, header = "Add item"):
        Gtk.Dialog.__init__(self, header, parent, 0, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))

        
        #self.type_dict = type_dict
        self.set_default_size(150,100)
        self.hbox = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL, spacing = 6)
        self.input_box = FlexibleInputBox(parent, item_dict)
        
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
    def __init__(self, parent, item_dict, value_dict):
        gl_AddDialog.__init__(self, parent, item_dict)
        for k, v in value_dict.items():
            self.input_box.entry_dict[k].set_text(str(value_dict[k]))
            
        self.input_box.entry_dict['name'].set_editable(False)   #Can't change the name, or else problems occur
        
class FlexibleInputBox(Gtk.Box):
    """Labels/entries for inputting information given a dict of {names:(label,type)} -- provides access to information and input checking"""
    def __init__(self, parent_window, info_dict, num_cols = 1):
        #!!! raise error if num_cols is not an int, info_dict is not a dict, and parent_window is not Gtk.Window
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.HORIZONTAL, spacing = 6)
        self.info_dict = info_dict
	self.parent = parent_window
        self.vbox_labels = Gtk.Box(orientation = Gtk.Orientation.VERTICAL, spacing = 6)
        self.vbox_entries = Gtk.Box(orientation = Gtk.Orientation.VERTICAL, spacing = 6)
        self.entry_dict = OrderedDict()
        self.label_dict = OrderedDict()
        

        for k, v in self.info_dict.items():

            
            self.entry_dict[k] = Gtk.Entry()
            self.label_dict[k] = Gtk.Label(v[0])
            self.vbox_labels.pack_start(self.label_dict[k], True, True, 0)
            self.vbox_entries.pack_start(self.entry_dict[k], True, True, 0)
            self.entry_dict[k].connect("focus-out-event", self.on_entry_lostfocus, k)

        self.pack_start(self.vbox_labels, True, True, 0)
        self.pack_start(self.vbox_entries, True, True, 0)

    def on_entry_lostfocus(self, widget, event, entry_index):
        """This allows for type checking of the entry boxes for this tool"""
        try:
            a = self.info_dict[entry_index][1](widget.get_text())
        except ValueError:
            dialog = Gtk.MessageDialog(self.parent, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "TYPE ENTRY ERROR")
            dialog.format_secondary_text("The data for this entry must be of type %s" % self.info_dict[entry_index][1])
            dialog.run()
            dialog.destroy()
            #Return the focus to the widget
            widget.grab_focus()

    def get_entries(self):
        """This will return the entries in a dict {name:val} with the values converted to the appropriate type"""
        return_dict = {}
        for k,v in self.entry_dict.items():
            return_dict[k] = self.info_dict[k][1](v.get_text())
        return return_dict


class GraphicalList(Gtk.Box):
    """Creates an Add/Edit/Delete list in GNOME -- rudimentary in current form: needs error checking, etc., but does work for general items"""
    def __init__(self, parent_window, list_class):
        Gtk.Box.__init__(self,orientation=Gtk.Orientation.HORIZONTAL, spacing = 6)
        if hasattr(list_class, "list_header"):
            self.list_header = getattr(list_class, "list_header")
        else:
            self.list_header = "List items"

        self.list = {}     #I know, this is a dict, but I'm tired, and need to get at these later
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


        self.list_model = Gtk.ListStore(str, bool)
        self.view = Gtk.TreeView(self.list_model)
        self.renderer = Gtk.CellRendererText()
        self.column = Gtk.TreeViewColumn(self.list_header, self.renderer, text = 0)
        self.view.append_column(self.column)
        self.pack_start(self.view, True, True, 0)

    
    def on_add_clicked(self, button):
        add_box = gl_AddDialog(self.parent_window, self.list_class.gl_add_info)  
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
        for k in self.list_class.gl_add_info.keys():
            val_dict[k] = getattr(self.list[model[m_iter][0]],k)

        edit_box = gl_EditDialog(self.parent_window, self.list_class.gl_add_info, val_dict)
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


class PickList(GraphicalList):
    """A PickList is a kind of GraphicalList that contains a second view, in which we hold the names of items that are "selected" for analysis
       The ListStore model is more complicated for this object, as it contains two booleans for "visible" attributes for the second view"""
    def __init__(self, parent_window, list_class):
        GraphicalList.__init__(self,parent_window, list_class)

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

class VE_Picklist(PickList):
    """Picklist for variable expenses -- different handlers for the add dialog and edit dialog"""
    def __init__(self, parent_window, list_class):
        PickList.__init__(self, parent_window, list_class)

    def on_add_clicked(self, button):
        add_box = VE_AddDialog(self.parent_window)  
        response = add_box.run()
      
        if response == Gtk.ResponseType.OK:
            entries = add_box.get_entries()
            self.list[entries['name']] = self.list_class(entries['name'])      
            
            self.list[entries['name']].unit_cost = uv.UnitVal(entries['unit_costs_v_entry'],entries['unit_costs_u_entry'])
            self.list[entries['name']].prod_req = uv.UnitVal(entries['unit_prod_v_entry'],entries['unit_prod_u_entry'])
                          
                

            #Now need to update the tree model
            self.list_model.append((entries['name'],False))
            
        
        elif response == Gtk.ResponseType.CANCEL:
            print "You clicked CANCEL"

        add_box.destroy()

    def on_edit_clicked(self, button):
        model, m_iter = self.view.get_selection().get_selected()
        

        val_dict = {}
        for k in self.list_class.gl_add_info.keys():
            val_dict[k] = getattr(self.list[model[m_iter][0]],k)

        edit_box = gl_EditDialog(self.parent_window, self.list_class.gl_add_info, val_dict)
        response = edit_box.run()

        if response == Gtk.ResponseType.OK:
            entries = edit_box.get_entries()
            for k,v in entries.items():
                setattr(self.list[entries['name']],k,v)

        elif response == Gtk.ResponseType.CANCEL:
            print "You clicked CANCEL"

        edit_box.destroy()

class ListTestWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title = "Test window for editable lists and pick lists")

        graphlist = PickList(self, TestItem)
        self.add(graphlist)        

class SimpleTree(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title = "Simple Tree/List View Example")
        

        vbox = Gtk.Box(orientation = Gtk.Orientation.VERTICAL, spacing = 6)
        self.add(vbox)

        self.wine_list = Gtk.ListStore(str, str, int)
        t_iter = self.wine_list.append(["M. Chapoultier", "Cotes du Rhone", 2009])
        t_iter = self.wine_list.append(["Guigal", "Gigonadas", 2004])
        t_iter = self.wine_list.append(["Barbi", "Brunello di Montepulciano", 2003])

        self.wine_view = Gtk.TreeView(self.wine_list)
        rend1 = Gtk.CellRendererText()
       
        rend2 = Gtk.CellRendererText()
        
        

        rend3 = Gtk.CellRendererText()
        col1 = Gtk.TreeViewColumn("Producer", rend1, text = 0)
        col2 = Gtk.TreeViewColumn("Appellation", rend2, text = 1)
        col3 = Gtk.TreeViewColumn("Vintage", rend3, text = 2)
        self.wine_view.append_column(col1)
        self.wine_view.append_column(col2)
        self.wine_view.append_column(col3)
        
        select = self.wine_view.get_selection()
        select.connect("changed", self.on_tree_selection_changed)

        vbox.pack_start(self.wine_view, True, True, 0)

    def on_tree_selection_changed(self, selection):
        model, treeiter = selection.get_selected()
        if treeiter != None:
            print "You selected", model[treeiter][:]



class EntryWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title = "Entry Demo")
        self.set_size_request(200,100)

        self.timeout_id = None

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing = 6)
        self.add(vbox)

        self.entry = Gtk.Entry()
        self.entry.set_text("Hello World")
        vbox.pack_start(self.entry, True, True, 0)
     
        hbox = Gtk.Box(spacing = 6)
        vbox.pack_start(hbox, True, True, 0)

        self.check_editable = Gtk.CheckButton("Editable")
        self.check_editable.connect("toggled", self.on_editable_toggled)
        self.check_editable.set_active(True)
        hbox.pack_start(self.check_editable	,True,True,0)

        self.check_visible = Gtk.CheckButton("Visible")
        self.check_visible.connect("toggled",self.on_visible_toggled)
        self.check_visible.set_active(True)
        hbox.pack_start(self.check_visible,True,True,0)

        self.pulse = Gtk.CheckButton("Pulse")
        self.pulse.connect("toggled",self.on_pulse_toggled)
        self.pulse.set_active(False)
        hbox.pack_start(self.pulse,True,True,0)

        self.icon = Gtk.CheckButton("Icon")
        self.icon.connect("toggled",self.on_icon_toggled)
        self.icon.set_active(False)
        hbox.pack_start(self.icon,True,True,0)

    def on_editable_toggled(self,button):
        value = button.get_active()
        self.entry.set_editable(value)

    def on_visible_toggled(self,button):
        value = button.get_active()
        self.entry.set_visibility(value)

    def on_pulse_toggled(self,button):
        if button.get_active():
            self.entry.set_progress_pulse_step(0.2)
            self.timeout_id = GObject.timeout_add(100,self.do_pulse,None)

        else:
            GObject.source_remove(self.timeout_id)
            self.timeout_id = None
            self.entry.set_progress_pulse_step(0)

    def do_pulse(self,user_data):
        self.entry.progress_pulse()
        return True

    def on_icon_toggled(self,button):
        if button.get_active():
            stock_id = Gtk.STOCK_FIND
        else:
            stock_id = None

        self.entry.set_icon_from_stock(Gtk.EntryIconPosition.PRIMARY,stock_id)

class TableWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title = "Table Example")
        
        table = Gtk.Table(3,3,True)
        self.add(table)
 

        button1 = Gtk.Button(label = "Button 1")
        button2 = Gtk.Button(label = "Button 2")
        button3 = Gtk.Button(label = "Button 3")
        button4 = Gtk.Button(label = "Button 4") 
        button5 = Gtk.Button(label = "Button 5")
        button6 = Gtk.Button(label = "Button 6")

        table.attach(button1, 0, 1, 0, 1)
        table.attach(button2, 1, 3, 0, 1)
        table.attach(button3, 0,1,1,3)
        table.attach(button4, 1,3,1,2)
        table.attach(button5, 1,2,2,3)
        table.attach(button6, 2,3, 2, 3)

class MyWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title = "Hello World")
        
 

        self.box = Gtk.Box(spacing = 6)
        self.add(self.box)

        

        self.button1 = Gtk.Button(label="Hello")
        self.button1.connect("clicked",self.on_button1_clicked)
        self.box.pack_start(self.button1, True, True, 0)

        self.button2 = Gtk.Button(label = "Goodbye")
        self.button2.connect("clicked",self.on_button2_clicked)
        self.box.pack_start(self.button2, True, True, 0)

        
    def on_button1_clicked(self,widget):
        print "Hello"

    def on_button2_clicked(self,widget):
        print "Goodbye"



def print_tree_store(store):
    rootiter = store.get_iter_first()
    print_rows(store, rootiter, "")

def print_rows(store, treeiter, indent_char):
    while treeiter != None:
        print indent_char + str(store[treeiter][:])
        if store.iter_has_child(treeiter):
            childiter = store.iter_children(treeiter)
            print_rows(store, childiter, indent_char + "\t")
        treeiter = store.iter_next(treeiter)




if __name__ == "__main__":
    """
    store = Gtk.TreeStore(str)
    treeiter = store.append(None,['Greg'])
    child_iter = store.append(treeiter, ['Erin'])
    store.append(child_iter, ['Caroline'])
    store.append(child_iter, ['Carter'])
    child_iter = store.append(treeiter, ['Chris'])
    store.append(child_iter, ['Jane'])
    store.append(treeiter, ['David'])
    store.append(treeiter, ['Jeff'])
    store.append(treeiter, ['Mark'])
    treeiter = store.append(None,['Jeff'])
    store.append(treeiter, ['Maria'])
    store.append(treeiter, ['Stephen'])
    store.append(treeiter, ['Drew'])

    print_tree_store(store)
    """

    win = ListTestWindow()
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()
    #app = GUIApp()
    Gtk.main()
