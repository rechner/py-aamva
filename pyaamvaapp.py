from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import mainthread
from kivy.lang import Builder
from kivy.graphics import Rectangle
from kivy.uix.label import Label
from kivy.properties import ListProperty
from kivy.factory import Factory

import aamva
import threading
import time
import serial
from datetime import datetime as date

import test

Builder.load_file('main.kv')

class LabelB(Label):
    bcolor = ListProperty((1, 1, 1, 1))

class BoxLayoutB(BoxLayout):
    bcolor = ListProperty((1, 1, 1, 1))

class RootWidget(BoxLayout):
    # Use to signal the barcode reader thread that we are exiting
    stop = threading.Event()

    parser = aamva.AAMVA()

    def scanner_thread(self):
        ser = None
        try:
            ser = serial.Serial('/dev/ttyUSB0', timeout=0.5)
        except:
            while True:
                input()
                if self.stop.is_set():
                    return
                self.process_scan(test.PDF417.va)
                time.sleep(10)
                self.process_scan(test.PDF417.va_under21)

        while True:
            charbuffer = ""
            while charbuffer[-2:] != '\r\n':
                charbuffer += ser.read(1)
                if self.stop.is_set():
                    ser.close()
                    return

            # Parse and update display
            self.process_scan(charbuffer)

    def start_scanner_thread(self, *args):
        scan_thread = threading.Thread(target=self.scanner_thread)
        scan_thread.start()

    @mainthread
    def process_scan(self, raw):
        # TODO: Add exception handling aamva.ReaderError
        # Display message if didn't decode correctly
        data = self.parser.decode(raw)
        import pprint; pprint.pprint(data)

        age = self.calculate_age(data['dob'])
        # TODO: If over 18, show "OVER 18" icon and message
        # (cigarette icon)
        expired = (self.calculate_age(data['expiry']) > 0)
        expired_text = ""
        if expired:
            expired_text = "[color=#ff0000][b]Expired {0}[/b][/color]\n".format(str(data['expiry']))
        print(data['expiry'])

        # TODO: Show name fields

        over21_text = "[color=#ff0000][b]Under 21[/b][/color]"
        over18_text = "[color=#ff0000][b]Under 18[/b][/color]"
        if age > 21:
            self.set_left_color((0, 1, 0, 1))
            over21_text = "Over 21"
        else:
            self.set_left_color((1, 0, 0, 1))
        if age >= 18:
            self.set_right_color((0, 1, 0, 1))
            over18_text = "Over 18"
        else:
            self.set_right_color((1, 0, 0, 1))

        self.vlayout.top_layout.status.text = ('{3}[b]Age:[/b] {0}\n\n{1}\n{2}'.format(age, over21_text, over18_text, expired_text))

        zipcode = "{0}-{1}".format(data['ZIP'][0:5], data['ZIP'][-4:])
        status = "[b]Name:[/b] {0}, {1} {2}\n[b]DOB: [/b]{3}\n".format(data['last'][:20], data['first'][:20], data['middle'][:20], data['dob'])
        status += "[b]Address:[/b]\n    {0}\n    {1}, {2} {3}\n".format(data['address'], data['city'], data['state'], zipcode)
        status += "[b]Issued:[/b] {0}".format(data['issued'])

        self.vlayout.low_layout.status.text = (status)

        self.canvas.ask_update()

    @mainthread
    def set_left_color(self, color):
        self.vlayout.top_layout.left_status.bcolor = color

    @mainthread
    def set_right_color(self, color):
        self.vlayout.top_layout.right_status.bcolor = color

    @staticmethod
    def calculate_age(dob):
        today = date.today()
        years_difference = today.year - dob.year
        is_before_birthday = (today.month, today.day) < (dob.month, dob.day)
        elapsed_years = years_difference - int(is_before_birthday)
        return elapsed_years

class Pyaamvaapp(App):

    def on_stop(self):
        self.root.stop.set()

    def build(self):
        root = RootWidget()
        root.start_scanner_thread()
        return root


#Factory.register('KivyB', module='LabelB')
Factory.register('KivyB', module='BoxLayoutB')

if __name__ == "__main__":
    Pyaamvaapp().run()
