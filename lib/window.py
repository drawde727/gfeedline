#
# gfeedline - A Social Networking Client
#
# Copyright (c) 2012, Yoshizumi Endo.
# Licence: GPL3

from twisted.internet import reactor
from gi.repository import Gtk

from preferences.preferences import Preferences
from view import Theme
from updatewindow import UpdateWindow
from notification import StatusNotification
from utils.settings import SETTINGS, SETTINGS_GEOMETRY
from constants import VERSION, SHARED_DATA_FILE, Column


class MainWindow(object):

    def __init__(self, liststore):
        self.liststore = liststore

        self.gui = gui = Gtk.Builder()
        gui.add_from_file(SHARED_DATA_FILE('gfeedline.glade'))

        self.window = window = gui.get_object('main_window')
        self.column = MultiColumnDict(gui) # multi-columns for Notebooks
        self.theme = Theme()
        self.notification = StatusNotification('GFeedLine')

        SETTINGS.connect("changed::window-sticky", self.on_settings_sticky_change)
        self.on_settings_sticky_change(SETTINGS, 'window-sticky')

        SETTINGS.connect("changed::theme", self.on_settings_theme_change)
        self.on_settings_theme_change(SETTINGS, 'theme')

        is_multi_column = SETTINGS.get_boolean('multi-column')
        menuitem_multicolumn = gui.get_object('menuitem_multicolumn')
        menuitem_multicolumn.set_active(is_multi_column)

        x, y, w, h = self._get_geometry_from_settings()

        if x >=0 and y >= 0:
            window.move(x, y)

        window.resize(w, h)
        window.show()

        gui.connect_signals(self)

    def get_notebook(self, group_name):
        if not SETTINGS.get_boolean('multi-column'):
            group_name = 'dummy for single column'

        if group_name in self.column:
            notebook = self.column.get(group_name)
        else:
            notebook = FeedNotebook(self.column, group_name)
            self.column.add(group_name, notebook)
        
        return notebook

    def toggle_multicolumn_mode(self):
        for row in self.liststore:
            notebook = self.get_notebook(row[Column.GROUP])
            view = row[Column.API].view
            view.remove()
            view.append(notebook, -1)

        timeout = reactor.callLater(0.1, self._jump_all_tabs_to_bottom, 
                                    self.theme.is_descend())

    def _jump_all_tabs_to_bottom(self, is_bottom=True):
        for notebook in self.column.values():
            notebook.jump_all_tabs_to_bottom(is_bottom)

    def _get_geometry_from_settings(self):
        x = SETTINGS_GEOMETRY.get_int('window-x')
        y = SETTINGS_GEOMETRY.get_int('window-y')
        w = SETTINGS_GEOMETRY.get_int('window-width')
        h = SETTINGS_GEOMETRY.get_int('window-height')
        return x, y, w, h

    def on_window_leave_notify_event(self, widget, event):
        ox, oy, ow, oh = self._get_geometry_from_settings()

        x, y = widget.get_position()
        w, h = widget.get_size()

        if x != ox or y != oy:
            SETTINGS_GEOMETRY.set_int('window-x', x)
            SETTINGS_GEOMETRY.set_int('window-y', y)

        if w != ow or h != oh:
            SETTINGS_GEOMETRY.set_int('window-width', w)
            SETTINGS_GEOMETRY.set_int('window-height', h)

    def on_stop(self, *args):
        reactor.stop()
        #self.window.destroy()

    def on_menuitem_quit_activate(self, menuitem):
        self.on_stop()

    def on_menuitem_update_activate(self, menuitem):
        prefs = UpdateWindow(self)

    def on_menuitem_prefs_activate(self, menuitem):
        prefs = Preferences(self)

    def on_menuitem_multicolumn_toggled(self, menuitem):
        is_multi_column = menuitem.get_active()
        SETTINGS.set_boolean('multi-column', is_multi_column)
        self.toggle_multicolumn_mode()

    def on_menuitem_about_activate(self, menuitem):
        about = AboutDialog(self.window)

    def on_menuitem_top_activate(self, menuitem=None):
        self._jump_all_tabs_to_bottom(False)

    def on_menuitem_bottom_activate(self, menuitem=None):
        self._jump_all_tabs_to_bottom()

    def on_settings_sticky_change(self, settings, key):
        if settings.get_boolean(key):
            self.window.stick()
        else:
            self.window.unstick()

    def on_settings_theme_change(self, settings, key):
        top = self.gui.get_object('menuitem_top')
        bottom = self.gui.get_object('menuitem_bottom')

        if not self.theme.is_descend():
            top, bottom = bottom, top

        top.hide()
        bottom.show()

class MultiColumnDict(dict):

    def __init__(self, gui):
        super(MultiColumnDict, self).__init__()
        self.hbox = gui.get_object('hbox1')
        self.welcome = gui.get_object('label_welcome')

    def add(self, group_name, notebook):
        self[group_name] = notebook
        self.hbox.add(notebook)
        self.welcome.hide()

    def remove(self, group_name):
        del self[group_name]

        if not self:
            self.welcome.show()

class FeedNotebook(Gtk.Notebook):

    def __init__(self, column, group_name):
        self.column = column
        self.group_name = group_name

        super(FeedNotebook, self).__init__()
        self.set_scrollable(True)
        self.popup_enable()

        self.connect('switch-page', self.on_update_tablabel_sensitive)
        self.connect('button-press-event', self.on_update_tablabel_sensitive)
        # self.connect('page-reordered', self.on_page_reordered)

        self.show()

    def on_update_tablabel_sensitive(self, notebook, *args):
        page = notebook.get_current_page() # get previous page
        feedview = notebook.get_nth_page(page) # get child
        if hasattr(feedview, 'tab_label'):
            feedview.tab_label.set_sensitive(False)

    def append_page(self, child, name, page=-1):
        super(FeedNotebook, self).append_page(
            child, Gtk.Label.new_with_mnemonic(name))
        self.reorder_child(child, page)
        # self.set_tab_reorderable(child, True)

        tab_label = self.get_tab_label(child)
        return tab_label

    def remove_page(self, page):
        super(FeedNotebook, self).remove_page(page)

        if self.get_n_pages() == 0:
            self.destroy()
            self.column.remove(self.group_name)

    def jump_all_tabs_to_bottom(self, is_bottom=True):
        for feedview in self.get_children():
            feedview.jump_to_bottom(is_bottom)

class AboutDialog(object):

    def __init__(self, parent):
        gui = Gtk.Builder()
        gui.add_from_file(SHARED_DATA_FILE('gfeedline.glade'))
        about = gui.get_object('aboutdialog')
        about.set_transient_for(parent)
        about.set_property('version', VERSION)
        # about.set_program_name('GFeedLine')

        about.run()
        about.destroy()
