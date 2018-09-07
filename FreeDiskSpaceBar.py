import gi
gi.require_version('Nautilus', '3.0')
gi.require_version('Gio', '2.0')
gi.require_version('GLib', '2.0')
gi.require_version('GObject', '2.0')
from gi.repository import GLib, GObject, Gio, Gtk, Nautilus

class FreeDiskSpaceBar(GObject.GObject, Nautilus.LocationWidgetProvider):
    nfb_type = None
    current_uri = None
    space_bar = None
    details_label = None

    def __init__(self):
        pass

    def orig_bar_shown(self, widget):
        self.space_bar.hide()

    def orig_bar_hidden(self, widget):
        self.set_free_space_label()
        if self.details_label != None:
            self.space_bar.show()

    def on_destroyed(self, widget):
        self.space_bar = None
        self.orig_bar = None
        self.current_uri = None
        self.details_label = None

    def set_free_space_label(self):
        self.details_label = None
        if self.current_uri.startswith("file://"):
            file = Gio.File.new_for_uri(self.current_uri)
            fileinfo = file.query_filesystem_info(Gio.FILE_ATTRIBUTE_FILESYSTEM_FREE, None)
            if fileinfo != None:
                volume_free = fileinfo.get_attribute_uint64(Gio.FILE_ATTRIBUTE_FILESYSTEM_FREE)
                if volume_free != 0:
                    self.details_label = GLib.format_size(volume_free)
        self.space_bar.set_property("details_label", self.details_label)

    def do_the_right_thing(self):
        self.set_free_space_label()
        if not self.orig_bar.get_visible():
            if self.details_label != None:
                self.space_bar.show()
                return
        self.space_bar.hide()

    def bar_init(self, widget):
        nws = widget.get_parent().get_parent()
        if GObject.type_name(nws) != "NautilusWindowSlot":
            return

        overlay = None
        for child in nws.get_children():
            type_name = GObject.type_name(child)
            if type_name == "NautilusCanvasView" or type_name == "NautilusListView":
                for grandchild in child.get_children():
                    if GObject.type_name(grandchild) == "GtkOverlay":
                        overlay = grandchild
                        break
                break
        if overlay == None:
            return

        self.orig_bar = None
        for child in overlay.get_children():
            if child.g_type_instance.g_class.g_type == self.nfb_type:
                self.orig_bar = child
                break
        if self.orig_bar == None:
            return

        self.space_bar = GObject.new(self.nfb_type, primary_label="Free space:", details_label=None, show_spinner=False, orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.space_bar.set_halign(Gtk.Align.END)
        self.space_bar.set_valign(Gtk.Align.END)
        overlay.add_overlay(self.space_bar)

        self.orig_bar.connect("hide", self.orig_bar_hidden)
        self.orig_bar.connect("show", self.orig_bar_shown)
        self.space_bar.connect("destroy", self.on_destroyed)

        self.do_the_right_thing()

    def get_widget(self, uri, window):
        if self.space_bar != None:
            if self.current_uri != uri:
                self.current_uri = uri
                self.do_the_right_thing()
            return None
        if self.nfb_type == None:
            try:
                self.nfb_type = GObject.type_from_name("NautilusFloatingBar")
            except:
                return None
        self.current_uri = uri
        if not uri.startswith("file://"):
            return None
        dummy = Gtk.Box()
        dummy.connect("realize", self.bar_init)
        return dummy
