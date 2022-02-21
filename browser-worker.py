#!/usr/bin/env python
# *-* coding: utf-8 *-*

import sys
import wx
import threading
import serial
from datetime import date
import webbrowser
import urllib.request
import urllib.parse
import urllib.error
from nameparser import HumanName

import aamva


BASE_URL = "http://dawningbrooke.net/apis/admin/registration/attendeeonsite/add/"
SERIAL_DEVICE = "/dev/ttyACM0"

if len(sys.argv) == 3:
    BASE_URL = sys.argv[1]
    SERIAL_DEVICE = sys.argv[2]
else:
    print("Usage: {} <Base Add URL> <Serial port>".format(sys.argv[0]))
    print("Using defaults:\n  URL: {}\n  Port: {}\n".format(
        BASE_URL, SERIAL_DEVICE))


def xstr(s):
    return '' if s is None else str(s)


t_DATA_WAITING = wx.NewEventType()
DATA_WAITING = wx.PyEventBinder(t_DATA_WAITING, 1)
t_THREAD_ERROR = wx.NewEventType()
THREAD_ERROR = wx.PyEventBinder(t_THREAD_ERROR, 1)


class AAMVATestFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.panel = wx.Panel(self)

        vSizer = wx.BoxSizer(wx.VERTICAL)
        hSizer1 = wx.BoxSizer(wx.HORIZONTAL)

        # Row 1
        nameSt = wx.StaticText(self.panel, wx.ID_ANY, "Name")
        hSizer1.Add(nameSt, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.NameText = wx.TextCtrl(
            self.panel, wx.ID_ANY, style=wx.TE_READONLY)
        hSizer1.Add(self.NameText, 1, wx.ALL
                    | wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 5)
        middleSt = wx.StaticText(self.panel, wx.ID_ANY, "Middle")
        hSizer1.Add(middleSt, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.MiddleText = wx.TextCtrl(
            self.panel, wx.ID_ANY, style=wx.TE_READONLY)
        hSizer1.Add(self.MiddleText, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        vSizer.Add(hSizer1, 0, wx.EXPAND, 5)

        # Row 2
        hSizer2 = wx.BoxSizer(wx.HORIZONTAL)
        surnameSt = wx.StaticText(self.panel, wx.ID_ANY, "Surname")
        hSizer2.Add(surnameSt, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.SurnameText = wx.TextCtrl(
            self.panel, wx.ID_ANY, style=wx.TE_READONLY)
        hSizer2.Add(self.SurnameText, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        dobSt = wx.StaticText(self.panel, wx.ID_ANY, "DOB")
        hSizer2.Add(dobSt, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.DOBText = wx.TextCtrl(self.panel, wx.ID_ANY, style=wx.TE_READONLY)
        hSizer2.Add(self.DOBText, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        vSizer.Add(hSizer2, 0, wx.EXPAND, 5)

        # Row 3
        hSizer3 = wx.BoxSizer(wx.HORIZONTAL)
        addressSt1 = wx.StaticText(self.panel, wx.ID_ANY, "Address 1")
        hSizer3.Add(addressSt1, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.AddressText = wx.TextCtrl(
            self.panel, wx.ID_ANY, style=wx.TE_READONLY)
        hSizer3.Add(self.AddressText, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        vSizer.Add(hSizer3, 0, wx.EXPAND, 5)

        # Row 4
        hSizer4 = wx.BoxSizer(wx.HORIZONTAL)
        addressSt2 = wx.StaticText(self.panel, wx.ID_ANY, "Address 2")
        hSizer4.Add(addressSt2, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.Address2Text = wx.TextCtrl(
            self.panel, wx.ID_ANY, style=wx.TE_READONLY)
        hSizer4.Add(self.Address2Text, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        vSizer.Add(hSizer4, 0, wx.EXPAND, 5)

        # Row 5
        hSizer5 = wx.BoxSizer(wx.HORIZONTAL)
        citySt = wx.StaticText(self.panel, wx.ID_ANY, "City")
        hSizer5.Add(citySt, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.CityText = wx.TextCtrl(
            self.panel, wx.ID_ANY, style=wx.TE_READONLY)
        hSizer5.Add(self.CityText, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        stateSt = wx.StaticText(self.panel, wx.ID_ANY, "State")
        hSizer5.Add(stateSt, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.StateText = wx.TextCtrl(
            self.panel, wx.ID_ANY, style=wx.TE_READONLY)
        hSizer5.Add(self.StateText, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        ZIPSt = wx.StaticText(self.panel, wx.ID_ANY, "ZIP")
        hSizer5.Add(ZIPSt, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.ZIPText = wx.TextCtrl(self.panel, wx.ID_ANY, style=wx.TE_READONLY)
        hSizer5.Add(self.ZIPText, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        vSizer.Add(hSizer5, 0, wx.EXPAND, 5)

        # Row 6
        hSizer6 = wx.BoxSizer(wx.HORIZONTAL)
        IINSt = wx.StaticText(self.panel, wx.ID_ANY, "IIN")
        hSizer6.Add(IINSt, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.IINText = wx.TextCtrl(self.panel, wx.ID_ANY, style=wx.TE_READONLY)
        hSizer6.Add(self.IINText, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        LicenseNoSt = wx.StaticText(self.panel, wx.ID_ANY, "License #")
        hSizer6.Add(LicenseNoSt, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.LicenseNoText = wx.TextCtrl(
            self.panel, wx.ID_ANY, style=wx.TE_READONLY)
        hSizer6.Add(self.LicenseNoText, 1, wx.ALL
                    | wx.ALIGN_CENTER_VERTICAL, 5)
        vSizer.Add(hSizer6, 0, wx.EXPAND, 5)

        # Row 7
        hSizer7 = wx.BoxSizer(wx.HORIZONTAL)
        issuedSt = wx.StaticText(self.panel, wx.ID_ANY, "Issued")
        hSizer7.Add(issuedSt, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.IssuedText = wx.TextCtrl(
            self.panel, wx.ID_ANY, style=wx.TE_READONLY)
        hSizer7.Add(self.IssuedText, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        expiresSt = wx.StaticText(self.panel, wx.ID_ANY, "Expires")
        hSizer7.Add(expiresSt, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.ExpiresText = wx.TextCtrl(
            self.panel, wx.ID_ANY, style=wx.TE_READONLY)
        hSizer7.Add(self.ExpiresText, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        countrySt = wx.StaticText(self.panel, wx.ID_ANY, "Country")
        hSizer7.Add(countrySt, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.CountryText = wx.TextCtrl(
            self.panel, wx.ID_ANY, style=wx.TE_READONLY)
        hSizer7.Add(self.CountryText, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        vSizer.Add(hSizer7, 0, wx.EXPAND, 5)

        # Row 8
        hSizer8 = wx.BoxSizer(wx.HORIZONTAL)
        self.MaleRadio = wx.RadioButton(self.panel, wx.ID_ANY, "M")
        hSizer8.Add(self.MaleRadio, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.FemaleRadio = wx.RadioButton(self.panel, wx.ID_ANY, "F")
        hSizer8.Add(self.FemaleRadio, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        heightSt = wx.StaticText(self.panel, wx.ID_ANY, "Height")
        hSizer8.Add(heightSt, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.HeightText = wx.TextCtrl(
            self.panel, wx.ID_ANY, style=wx.TE_READONLY)
        hSizer8.Add(self.HeightText, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        weightSt = wx.StaticText(self.panel, wx.ID_ANY, "Weight")
        hSizer8.Add(weightSt, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.WeightText = wx.TextCtrl(
            self.panel, wx.ID_ANY, style=wx.TE_READONLY)
        hSizer8.Add(self.WeightText, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        hairSt = wx.StaticText(self.panel, wx.ID_ANY, "Hair")
        hSizer8.Add(hairSt, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.HairText = wx.TextCtrl(
            self.panel, wx.ID_ANY, style=wx.TE_READONLY)
        hSizer8.Add(self.HairText, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        vSizer.Add(hSizer8, 0, wx.EXPAND, 5)

        # Row 9
        hSizer9 = wx.BoxSizer(wx.HORIZONTAL)
        eyesSt = wx.StaticText(self.panel, wx.ID_ANY, "Eyes")
        hSizer9.Add(eyesSt, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.EyesText = wx.TextCtrl(
            self.panel, wx.ID_ANY, style=wx.TE_READONLY)
        hSizer9.Add(self.EyesText, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        endorsementsSt = wx.StaticText(self.panel, wx.ID_ANY, "Endorsements")
        hSizer9.Add(endorsementsSt, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.EndorsementsText = wx.TextCtrl(
            self.panel, wx.ID_ANY, style=wx.TE_READONLY)
        hSizer9.Add(self.EndorsementsText, 1, wx.ALL
                    | wx.ALIGN_CENTER_VERTICAL, 5)
        restrictionsSt = wx.StaticText(self.panel, wx.ID_ANY, "Restrictions")
        hSizer9.Add(restrictionsSt, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.RestrictionsText = wx.TextCtrl(
            self.panel, wx.ID_ANY, style=wx.TE_READONLY)
        hSizer9.Add(self.RestrictionsText, 1, wx.ALL
                    | wx.ALIGN_CENTER_VERTICAL, 5)
        vSizer.Add(hSizer9, 0, wx.EXPAND, 5)

        self.clearForm()

        # Bind events
        self.Bind(DATA_WAITING, self.ProcessScan)
        self.Bind(THREAD_ERROR, self.ThreadError)
        self.Bind(wx.EVT_CLOSE, self.Close)

        # Setup parser
        self.parser = aamva.AAMVA()

        # Start serial thread
        self.THREAD_EXIT_SIGNAL = threading.Event()
        self.thread = threading.Thread(target=self._serialWorkerThread,
                                       args=(SERIAL_DEVICE,))
        self.thread.start()

        self.panel.SetSizer(vSizer)
        self.panel.Layout()

    def clearForm(self):
        self.NameText.Clear()
        self.MiddleText.Clear()
        self.SurnameText.Clear()
        self.DOBText.Clear()
        self.AddressText.Clear()
        self.Address2Text.Clear()
        self.CityText.Clear()
        self.StateText.Clear()
        self.ZIPText.Clear()
        self.IINText.Clear()
        self.LicenseNoText.Clear()
        self.IssuedText.Clear()
        self.ExpiresText.Clear()
        self.CountryText.Clear()
        self.MaleRadio.SetValue(False)
        self.FemaleRadio.SetValue(False)
        self.HeightText.Clear()
        self.WeightText.Clear()
        self.HairText.Clear()
        self.EyesText.Clear()
        self.EndorsementsText.Clear()
        self.RestrictionsText.Clear()
        return

    def _serialWorkerThread(self, device):

        try:
            ser = None
            ser = serial.Serial(device, timeout=0.2)

            while True:
                charbuffer = ""
                # Read data from scanner until we see a \r\n
                while charbuffer[-2:] != '\r\n':
                    char = ser.read(1)  # blocks if no data to read
                    charbuffer += char

                    # check if we need to close the port:
                    if self.THREAD_EXIT_SIGNAL.isSet():
                        ser.close()
                        return None

                # Throw event to have the data processed
                evt = wx.PyCommandEvent(t_DATA_WAITING, self.GetId())
                evt.data = charbuffer
                self.GetEventHandler().ProcessEvent(evt)

        except serial.SerialException as e:
            # Post event to display error message
            evt = wx.PyCommandEvent(t_THREAD_ERROR, self.GetId())
            evt.message = "Error opening scanner ({0}):\n\n{1}".format(
                device, e)
            self.GetEventHandler().ProcessEvent(evt)

        finally:
            # Close the serial device if something goes wrong
            if ser:
                ser.close()
            return

    def ThreadError(self, evt):
        wx.CallAfter(self.ErrorMessage, evt.message)

    def ErrorMessage(self, message):
        dlg = wx.MessageDialog(self.panel, message,
                               'Read Error', wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()

    def InfoMessage(self, message):
        dlg = wx.MessageDialog(self.panel, message,
                               'APIS Information', wx.OK | wx.ICON_WARNING)
        dlg.ShowModal()
        dlg.Destroy()

    def ProcessScan(self, evt):
        print("Got a scan!")

        try:
            license = self.parser.decode(evt.data)
        except aamva.ReadError as e:
            # GUI interaction must be done in a thread-safe way
            wx.CallAfter(self.ErrorMessage, 'Invalid data.\n{0}'.format(e))
            return

        name = HumanName("{} {}".format(
            xstr(license['first']).lower(), xstr(license['last']).lower()))
        name.capitalize()

        query = {
            'firstName': name.first,
            'lastName': name.last,
            'address1': license['address'],
            'address2': xstr(license['address2']),
            'city': license['city'],
            'state': license['state'],
            'postalCode': xstr(license['ZIP'])[0:5]+"-"+xstr(license['ZIP'])[5:],
            'country': license['country'],
            'birthdate': license['dob']
        }

        params = urllib.parse.urlencode(query)

        if license['expiry'] <= date.today():
            wx.CallAfter(self.InfoMessage, str(
                'ID expired {}'.format(license['expiry'])))
            webbrowser.open(BASE_URL + "?" + params, new=0, autoraise=False)
        else:
            webbrowser.open(BASE_URL + "?" + params, new=0, autoraise=True)

        # clear form
        self.clearForm()

        # set the fields
        self.NameText.SetValue(license['first'])
        if license['middle'] is not None:
            self.MiddleText.SetValue(license['middle'])
        self.SurnameText.SetValue(license['last'])
        self.DOBText.SetValue(xstr(license['dob']))
        self.AddressText.SetValue(license['address'])
        self.Address2Text.SetValue(xstr(license['address2']))
        self.CityText.SetValue(license['city'])
        self.StateText.SetValue(license['state'])
        self.ZIPText.SetValue(xstr(license['ZIP'])[
                              0:5]+"-"+xstr(license['ZIP'])[5:])
        self.IINText.SetValue(license['IIN'])
        self.LicenseNoText.SetValue(license['license_number'])
        self.IssuedText.SetValue(xstr(license['issued']))
        self.ExpiresText.SetValue(xstr(license['expiry']))
        try:
            self.CountryText.SetValue(license['country'])
        except KeyError:
            self.CountryText.SetValue("???")
        if license['sex'] == aamva.MALE:
            self.MaleRadio.SetValue(True)
        elif license['sex'] == aamva.FEMALE:
            self.FemaleRadio.SetValue(True)
        self.HeightText.SetValue(xstr(license['height']))
        self.WeightText.SetValue(xstr(license['weight']))
        if license['hair'] is None:
            self.HairText.SetValue("???")
        else:
            self.HairText.SetValue(license['hair'])
        if license['eyes'] is None:
            self.EyesText.SetValue("???")
        else:
            self.EyesText.SetValue(license['eyes'])
        self.EndorsementsText.SetValue(license['endorsements'])
        self.RestrictionsText.SetValue(license['restrictions'])

    def Close(self, event):
        self.THREAD_EXIT_SIGNAL.set()
        self.thread.join()  # blocks until thread exits
        self.Destroy()


if __name__ == '__main__':
    app = wx.App()   # Error messages go to popup window
    pFrame = AAMVATestFrame(None, title="Scan a License", size=(500, 370))
    pFrame.Show()
    app.MainLoop()
