#!/usr/bin/env python3
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#
# ########################################################################
# Copyright (C) 2015 Martin Sinn
#########################################################################
# lintronic plugin is to be used with smarthome.py (http://mknx.github.io/smarthome/)
#
#  Version 0.1 develop
#
#
# lintronic plugin for smarthome.py is free software: you can 
# redistribute it and/or modify it under the terms of the GNU General 
# Public License as published by the Free Software Foundation, either 
# version 3 of the License, or (at your option) any later version.
# 

import logging
import serial
import sys
import time
from datetime import datetime, timedelta


logger = logging.getLogger('lintronic')


running_insides_smarthome = True


def _hexbyte( byte ):
    resultstr = hex( byte )
    if byte < 16:
        resultstr = resultstr[:2] + "0" + resultstr[2]
    return resultstr

def _hexword( byte1, byte2 ):
    resultstr = _hexbyte( byte2 )
    resultstr = _hexbyte( byte1 ) + resultstr[2:]
    return resultstr


#########################################################################################
###### Installation-specific data

# Dictionary to lookup room names, filled from plugin.conf
#roomdict = dict( [] )
#reverse_roomdict = {}

# Dictionary to lookup MLN names, filled from plugin.conf
#mlndict = dict( [] )
#reverse_mlndict = {}


#########################################################################################
###### Dictionaries with MLGW/Lintronic Protocol Data


beo4commanddict = dict( [
    # Source selection:
    (0x0c, "Standby"), (0x47, "Sleep"), (0x80, "TV"), (0x81, "Radio"), (0x82, "DTV2"), 
    (0x83, "Aux_A"), (0x85, "V.Mem"), (0x86, "DVD"), (0x87, "Camera"), (0x88, "Text"), 
    (0x8a, "DTV"), (0x8b, "PC"), (0x0d, "Doorcam"), (0x91, "A.Mem"), (0x92, "CD"), 
    (0x93, "N.Radio"), (0x94, "N.Music"), (0x97, "CD2"), 
    # Digits:
    (0x00, "Digit-0"), (0x01, "Digit-1"), (0x02, "Digit-2"), (0x03, "Digit-3"), 
    (0x04, "Digit-4"), (0x05, "Digit-5"), (0x06, "Digit-6"), (0x07, "Digit-7"), 
    (0x08, "Digit-8"), (0x09, "Digit-9"), 
    # Source control:
    (0x1e, "STEP_UP"), (0x1f, "STEP_DW"), (0x32, "REWIND"), (0x33, "RETURN"), 
    (0x34, "WIND"), (0x35, "Go / Play"), (0x36, "Stop"), (0xd4, "Yellow"), 
    (0xd5, "Green"), (0xd8, "Blue"), (0xd9, "Red"), 
    # Sound and picture control:
    (0x0d, "Mute"), (0x1c, "P.Mute"), (0x2a, "Format"), (0x44, "Sound / Speaker"), 
    (0x5c, "Menu"), (0x60, "Volume UP"), (0x64, "Volume DOWN"), (0xda, "Cinema_On"), 
    (0xdb, "Cinema_Off"), 
    # Other controls:
    (0x14, "BACK"), (0x7f, "Exit"), 
    # Continue functionality:
    (0x7e, "Key Release"), 
    # Functions:
    # Cursor functions:
    (0x13, "SELECT"), (0xca, "Cursor_Up"), (0xcb, "Cursor_Down"), (0xcc, "Cursor_Left"), 
    (0xcd, "Cursor_Right"), 
    #    
    (0x9b, "Light"), (0xbf, "AV"), (0x58, "(Timeout)"), (0xf7, "Stand"), (0xfa, "P-and-P"), 
    (0xc1, "Random")
    ] )

reverse_beo4commanddict = {}

lintronicmodedict = dict( [
    (  10, "TV"), (  20, "LIGHT"), (  30, "RADIO"), (  40, "DTV"), (  50, "DVD"), 
    (  60, "CD"), (  70, "V.MEM"), (  80, "A.MEM"), (  90, "SPEAKER"), ( 100, "V.AUX"),
    ( 100, "A.AUX"), ( 102, "TEXT"), ( 103, "N.MUSIC"), ( 104, "N.RADIO"), ( 110, "FORMAT"), 
    ( 111, "PC"), ( 113, "P-AND-P"), ( 116, "STAND"), ( 140, "CONTROL")
    ] )

reverse_lintronicmodedict = {}


# ########################################################################################
# ##### Decode Lintronic Protocol packet to readable string

## Get decoded string for Beo4s command
#
def _getbeo4commandstr( command ):
        result = beo4commanddict.get( command )
        if result == None:
            result = "Cmd=" + _hexbyte( command )
        return result


## Get decoded string for Lintronics mode
#
def _getlintronicmodestr( mode ):
        result = lintronicmodedict.get( mode )
        if result == None:
            result = "" + _hexbyte( mode )
        return result


def _buildpacket( dest, command ):
    result = '<' + dest + '00' + command

    result = result.encode()
    chkcalc = 0
    for i in range(1,len(result)):
        chkcalc = (chkcalc + result[i]) % 256
    chk = str( 1000+chkcalc )
    chk = chk[1:4] + '>'

    result = result + chk.encode()
    return result


def _decodepacket( packet ):
    result = b''
    cmd = 0
    if len(packet) > 0:
        chk = int(packet[len(packet)-3:len(packet)])
    
        chkcalc = 0
        for i in range(0,len(packet)-3):
            chkcalc = (chkcalc + packet[i]) % 256

        if chk != chkcalc:
            logger.warning("lintronic: Received packet with invalid checksum (calc="+str(chkcalc)+"): '"+str(packet,'ascii')+"'")
        elif packet[1:3] != b'00':
            logger.warning("lintronic: Received packet was not addressed to computer (dest='"+str(packet[1:3],'ascii')+"')")
        else:    
            result = packet[7:len(packet)-3]
            cmd = int(packet[4:7])
    return cmd, result


def _decodepacket915( packet ):
    cmd, rcvdata = _decodepacket( packet )
    if cmd != 915:
        logger.warning("lintronic: decodepacket915: Command ID ist nicht 915: '"+str(packet)+"'")
        mode=b''
        trig=b''
    else:
        vers=rcvdata[0:3]
        mode=rcvdata[3:6]
        trig=rcvdata[6:9]
        parm1=rcvdata[9:12]
        parm2=rcvdata[12:15]

    return mode.decode(), trig.decode()


#########################################################################################

## Class lintronic: Implements the plugin for smarthome.py
#
class lintronic():

    msg = []     # Buffer for reading from serial port
    _channel1digit = ''
    
    ## read packet from com port
    #
    # readpacket removes the sot and eot characters from the packet
    #
    #  @param self      The object pointer.
    #
    def readpacket(self):
        result = b''
        if self.ser.isOpen():
            readin = b'?'
            while readin:
                readin = self.ser.read(1).decode()
                if readin:
                    self.msg += readin

                if len(self.msg) >= 9:
                    if self.msg[0] != '<':
                        logger.warning("lintronic: Received packet doesn't start with an <sot>: '"+str(self.msg)+"'")
                        self.msg.pop(0)
                    else:
                        if '>' in self.msg:
                            result = ''.join(self.msg[1:self.msg.index('>')]).encode()
                            self.msg = self.msg[self.msg.index('>')+1:]
                        
                # exit readpacket's read-loop if a complete packet has been received
                if result:
                    break
        return result


    # #################################################################

    ## The constructor: Initialize plugin
    #
    # Store config parameters of plugin. Smarthome.py reads these parameters from plugin.conf
    # and hands them to the __init__ method of the plugin.
    #
    #  @param self        The object pointer.
    #  @param smarthome   Defined by smarthome.py.
    #  @param serialport  Serial port to use for communication.
    #
    def __init__(self, smarthome, serialport=''):
        global reverse_beo4commanddict
        global reverse_lintronicmodedict

        self._sh = smarthome
        self._lin_items = {}

        logger.debug("lintronic.__init__()")
        self.ser = serial.Serial()
        self.ser.baudrate = 19200
        self.ser.timeout = 0.5
        self.ser.port = serialport
        try:
#            self.ser = serial.Serial(serialport, 19200, timeout=1)
            self.ser.open()
        except:
            logger.error("lintronic: Unable to open serial port '"+serialport+"'")
        else:
            logger.info("lintronic: Serial port "+self.ser.name+" opened")
            packet = self.readpacket()
            self.ser.timeout = 5
            command = _buildpacket( '98', '023' )
            self.ser.write(command)
            packet = b''
            while not packet:
                packet = self.readpacket()
            command, rcvdata = _decodepacket( packet )
            if command == 23:
                logger.info("lintronic: Communication established, with Lintronic device (type="+str(rcvdata,'ascii')+")")
            else:
                logger.warning("lintronic: Communication established, could not determine Lintronic device type!")

        reverse_beo4commanddict = {v.upper(): k for k, v in beo4commanddict.items()}
        logger.info("lintronic: beo4commanddict=" + str(beo4commanddict))
        logger.info("lintronic: reverse_beo4commanddict=" + str(reverse_beo4commanddict))

        reverse_lintronicmodedict = {v.upper(): k for k, v in lintronicmodedict.items()}
        logger.info("lintronic: lintronicmodedict=" + str(lintronicmodedict))
        logger.info("lintronic: reverse_lintronicmodedict=" + str(reverse_lintronicmodedict))


    ## Handle channel: Entry of channel number is complete
    #
    # _handle_channel calls this routine if the entry of the channel number is complete.
    # This function is also be called by timeout functgion of the scheduler
    #
    #  @param self      The object pointer.
    #  @param lin_item  item to handle
    #
    def _handle_channelcomplete(self, lin_item):
        self._sh.scheduler.remove('lintr_{}'.format(lin_item))
        if lin_item._channeldigits != '':
            channel = int(lin_item._channeldigits)
            logger.info("lintronic: handle_channelcomplete set, item: {0}".format(lin_item) + ", type=" + lin_item._type + ", value=" + str(channel) )
            lin_item(channel, 'lintronic', '_handle_channelcomplete')
            lin_item._channeldigits = ''


    ## Handle channel: Handle timeout while entering a channel number
    #
    # This function is called by the scheduler to complete the channel selection,
    # if no second digit is entered.
    #
    #  @param self      The object pointer.
    #  @param **kwargs  argument list
    #
    def _handle_channelcompletetimeout(self, **kwargs):
        lin_item = kwargs['lin_item']
        self._handle_channelcomplete(lin_item)


    ## Handle channel
    #
    # _update_values calls this routine if the item is defined a channel number
    # (lin_channel = true)
    #
    #  @param self      The object pointer.
    #  @param lin_item  item to handle
    #  @param mode      lintronic mode of received packet.
    #  @param trigger   trigger of reveived packet.
    #
    def _handle_channel(self, lin_item, mode, trigger):
        if lin_item._type == 'num':
            # Channel +1
            if (int(trigger) == 30) or (int(trigger) == 202):    # STEP_UP or Cursor_Up
                channel = int(lin_item())+1
                logger.info("lintronic: handle_channel up, item: {0}".format(lin_item) + ", type=" + lin_item._type + ", value=" + str(channel) )
                lin_item(channel, 'lintronic', _getlintronicmodestr( int(mode) ))
                lin_item._channeldigits = ''
            # Channel -1
            elif (int(trigger) == 31) or (int(trigger) == 203):    # STEP_DW or Cursor_Down
                channel = int(lin_item())-1
                if channel == 0:
                    channel = 1
                logger.info("lintronic: handle_channel down, item: {0}".format(lin_item) + ", type=" + lin_item._type + ", value=" + str(channel) )
                lin_item(channel, 'lintronic', _getlintronicmodestr( int(mode) ))
                lin_item._channeldigits = ''
            # Digits entered
            elif int(trigger) < 10:
                if lin_item._channeldigits == '':
                    lin_item._channeldigits = trigger[2]
                    _timeout = (datetime.now()+timedelta(seconds=1.5)).replace(tzinfo=self._sh.tzinfo())
                    self._sh.scheduler.add('lintr_{}'.format(lin_item), self._handle_channelcompletetimeout, value={'lin_item': lin_item}, next=_timeout)
                    
                else:
                    lin_item._channeldigits += trigger[2]
                    self._handle_channelcomplete(lin_item)
#                    self._handle_channelcompletetimeout({'lin_item': lin_item})


    ## Update values 
    #
    # Update values in smarthome.py if they have been changed through the device
    # which is controlled by this plugin
    #
    #  @param self      The object pointer.
    #  @param mode      lintronic mode of received packet.
    #  @param trigger   trigger of reveived packet.
    #
    def _update_values(self, mode, trigger):
        for lin_item in self._lin_items:
            if self._lin_items[lin_item] == 'ALL':
                if lin_item._type == 'str':
                    lin_item(_getbeo4commandstr(int(trigger)), 'lintronic', 'ALL')
                elif lin_item._type == 'num':
                    lin_item(trigger, 'lintronic', 'ALL')
                logger.info("lintronic: update_values (ALL) item: {0}".format(lin_item) + ", type=" + lin_item._type + ", value=" + str(lin_item()) )
            elif self._lin_items[lin_item] == 'MODE':
                if lin_item._type == 'str':
                    lin_item(_getlintronicmodestr(int(mode)), 'lintronic', 'MODE')
                elif lin_item._type == 'num':
                    lin_item(mode, 'lintronic', 'MODE')
                logger.info("lintronic: update_values (MODE) item: {0}".format(lin_item) + ", type=" + lin_item._type + ", value=" + str(lin_item()) )

            elif not('channel' in self._lin_items[lin_item]):
                if self._lin_items[lin_item] == _getlintronicmodestr( int(mode) ):
                    if lin_item._type == 'str':
                        lin_item(_getbeo4commandstr(int(trigger)), 'lintronic', _getlintronicmodestr( int(mode) ))
                    elif lin_item._type == 'num':
                        lin_item(trigger, 'lintronic', _getlintronicmodestr( int(mode) ))
                    logger.info("lintronic: update_values ("+_getlintronicmodestr( int(mode) )+") item: {0}".format(lin_item) + ", type=" + lin_item._type + ", value=" + str(lin_item()) )

            # preset/channel handling 
            else:
                if self._lin_items[lin_item] == _getlintronicmodestr( int(mode) )+'channel':
                    self._handle_channel(lin_item, mode, trigger)


    ## Run plugin
    #
    #  @param self      The object pointer.
    #
    def run(self):
        if not self.ser.isOpen():
            return

        logger.debug("lintronic.run()")
        logger.info("lintronic: handling items=" + str(self._lin_items))
        self.alive = True
        nlneeded = False
        while self.alive:
            try:
                l = self.readpacket()
            except KeyboardInterrupt:
                self.alive = False
                logger.info("lintronic: KeyboardInterrupt, terminating...")
                l = b''

            if l:
                mode, trigger = _decodepacket915( l )
                logger.info("lintronic: Received Beo4 command: mode="+mode+", trigger="+trigger+"  (Mode="+_getlintronicmodestr( int(mode) )+", "+_getbeo4commandstr( int(trigger) )+")" )

                if running_insides_smarthome:
                    self._update_values(mode, trigger)
                else:
                    if nlneeded:
                        print()
                        nlneeded = False
                    print("lintronic: Received Beo4 command: mode="+mode.decode()+", trigger="+trigger.decode()+"  (Mode="+_getlintronicmodestr( int(mode) )+", "+_getbeo4commandstr( int(trigger) )+")" )

            elif not running_insides_smarthome:
                print('.', end="",flush=True)
                nlneeded = True


    ## Stop plugin
    #
    #  @param self      The object pointer.
    #
    def stop(self):
        logger.debug("lintronic.stop()")
        self.alive = False
        if self.ser.isOpen():
            self.ser.close()
            logger.info("lintronic: serial port closed")


    ## Parse item configuration (not yet implemented)
    #
    # parse item definition on startup of smarthome.py
    #
    # @param self      The object pointer.
    # @param item      Pointer to item configuration.
    #
    def parse_item(self, item):
        global reverse_lintronicmodedict

        if 'lin_mode' not in item.conf:
            return

        mode = item.conf['lin_mode'].upper()

        logger.info("lintronic: parse item: {0}".format(item) + ", type=" + item._type + ", item.conf=" + str(item.conf) )
        if mode == 'ALL':
            pass
        elif mode == 'MODE':
            pass
        else:
            modet = reverse_lintronicmodedict.get(mode)
            if modet == None:
                logger.error("lintronic: parse item: {0}".format(item) + " - lin_mode '"+mode+"' is unkonown")
                return None

        if 'lin_channel' in item.conf:
            if item.conf['lin_channel'].upper() == 'TRUE':
                mode = mode + 'channel'
            item._channeldigits = ''
        # add item to list of lintronic items
        self._lin_items[item] = mode
        return self.update_item


    ## Update item
    #
    # update items via the plugin, if value has changed in smarthome.py
    #
    # @param self      The object pointer.
    # @param item      Pointer to item configuration.
    # @param caller    Calling class (e.g. plugin name).
    # @param source    Calling source (e.g. ip / port of visu)
    # @param dest      ???.
    #
    def update_item(self, item, caller=None, source=None, dest=None):
        if caller != 'lintronic':
            pass


#########################################################################################
#########################################################################################

if __name__ == '__main__':
    logging.basicConfig(filename='lintronic.log',level=logging.DEBUG)
    running_insides_smarthome = False
    
    # name of serial port
    # - on OSX: /dev/tty.usbserial-AH02ZHW1	(after driver installation)
    # - on debian: /dev/ttyUSB0	(no driver installation necessary)
    #
    myplugin = lintronic('lintronic', serialport='/dev/tty.usbserial-AH02ZHW1' )
    myplugin.run()
    myplugin.stop()

