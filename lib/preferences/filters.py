import time
from datetime import datetime, timedelta

from gi.repository import Gtk
from ..constants import SHARED_DATA_FILE
from ..filterliststore import FilterColumn
from feedsource import FeedSourceAction


class FilterDialog(object):
    """Filter Dialog"""

    def __init__(self, parent, liststore_row=None):
        self.gui = Gtk.Builder()
        self.gui.add_from_file(SHARED_DATA_FILE('filters.glade'))

        self.parent = parent
        self.liststore_row = liststore_row

        self.combobox_target = ComboboxTarget(self.gui)
        self.entry_word = self.gui.get_object('entry_word')
        self.spinbutton_expiry = self.gui.get_object('spinbutton_expiry')
        self.combobox_expire_unit = ComboboxExpireUnit(self.gui)

        self.gui.connect_signals(self)

    def run(self):
        dialog = self.gui.get_object('filter_dialog')
        dialog.set_transient_for(self.parent)

        if self.liststore_row:
            self.combobox_target.set_active_text(
                self.liststore_row[FilterColumn.TARGET])
            self.entry_word.set_text(self.liststore_row[FilterColumn.WORD])
            self.spinbutton_expiry.set_value(
                int(self.liststore_row[FilterColumn.EXPIRE_TIME] or 0))
            self.combobox_expire_unit.set_active_text(
                self.liststore_row[FilterColumn.EXPIRE_UNIT])

        # run
        response_id = dialog.run()

        expire = ExpireValues(self.spinbutton_expiry.get_value_as_int(), 
                              self.combobox_expire_unit)

        v = [
            self.combobox_target.get_active_text(),
            self.entry_word.get_text().decode('utf-8'),
            expire.value, 
            expire.unit, 
            expire.epoch,
        ]

#        print v
        dialog.destroy()
#        if response_id == Gtk.ResponseType.OK:
#            SETTINGS_RECENTS.set_string('source', v['source'])
        return response_id , v

class ExpireValues(object):

    def __init__(self, spinbutton_value, combobox_expire_unit):
        is_hours = combobox_expire_unit.get_active()

        if spinbutton_value:
            self.value = str(spinbutton_value)
            self.unit = combobox_expire_unit.get_active_text()
            self.epoch = self._get_epoch(spinbutton_value, is_hours)
        else:
            self.value = ''
            self.unit = ''
            self.epoch =0

    def _get_epoch(self, expire_timedelta, is_hours):
        if not is_hours:
            expire_timedelta *= 24

        now = datetime.now()
        future = now + timedelta(hours=expire_timedelta)
        expire_epoch = int(time.mktime(future.timetuple()))
        return expire_epoch 

class ComboboxTarget(object):

    WIDGET = 'comboboxtext_target'

    def __init__(self, gui):
        self.widget = gui.get_object(self.WIDGET)
        self.widget.set_active(0) # glade bug
        self.model = self.widget.get_model()

    def get_active(self):
        return self.widget.get_active()

    def get_active_text(self):
        return self.model[self.widget.get_active()][0]

    def set_active_text(self, text):
        labels = [i[0] for i in self.model]
        target = labels.index(text) if text in labels else 0
        self.widget.set_active(target)

class ComboboxExpireUnit(ComboboxTarget):

    WIDGET = 'comboboxtext_expire_unit'

class FilterAction(FeedSourceAction):

    DIALOG = FilterDialog
    BUTTON_PREFS = 'button_filter_prefs'
    BUTTON_DEL = 'button_filter_del'