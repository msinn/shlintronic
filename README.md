# Lintronic #

Version 0.1 beta

This is a plugin for smarthome.py. It can receive commands from a Lintonic signal converter. This plugin can receive commands, which are send by a Bang & Olufsen (B&O) remote control (e.g. Beo4). 

At the moment, only the reception of IR commands is supported. Sending commands will be added at a later date. 

Multiple Lintronic signal converters can be interconnected, but at the moment, only one Lintronic signal converter is supported by this plugin.

# Requirements

This plugin need a Lintronic TT455-RT-238 signal converter via RS232. Type '915-commands' have to be enabled In the configuration of the signal converter. Further configuration of the signal converter is not necessary.
For details look at http://www.lintronic.dk.

For communication via RS232 you need to install the Python module pyserial on your computer.

If your computer does not have a RS232 interface, you need a USB to RS232 converter. 


## Supported Hardware

* Lintronic TT455-RT-238 signal converter

# Installation

You need to install the python module pyserial. For Python3 this can be done by the following command:

<pre>
	sudo pip3 install pyserial
</pre>


# Configuration

You need to give the user under which smarthome.py is running the rights to access the serial port. On Debian, the group dealt has read/write rights to the serial port. Assuming you run smart home.py under the user smart home, the command for adding the user to the group is:

<pre>
	sudo usermod -aG dialout smarthome
</pre>

## plugin.conf

<pre>
[lintronic]
    class_name = intronic
    class_path = plugins.lintronic
    serialport = xxx
</pre>

This plugins is looking for a Lintronic signal converter gateway. By default it tries to connect thru serial port 'xxx'.

---------

With **log_mlgwtelegrams** you can control if decoded mlgw telegrams should be logged in the smarthome.log fie. The log level is raised to WARNING to ensure logging, if sh.py is running in quiet mode, its standard mode of operation.

	- 0 no telegrams are written to the log
	- 1 received telegrams that are not handled by the plugin are logged
	- 2 received telegrams are logged
	- 3 sent and received telegrams are logged
	- 4 send and received telegrams are logged, including keep alive traffic


## items.conf

The following attributes are used to **receive triggers** from a B&O remote. They can be used to define triggers to use within smarthome.py:

----------------------

### mlgw_listen
**mlgw_listen** has to be specified to listen for command telegrams from a B&O device. You can specify *LIGHT* or *CONTROL* to listen for the corresponding command set. The command to listen for has to be specified in **mlgw_cmd**.

Items ti listen for have to be defined with the datatype *bool*.

### mlgw_room
**mlgw_room** specifies the room (the B&O device is in) from which the command originated. The room numbers of the B&O devices have been specified in the Masterlink Gateway configuration. You can specify the numeric value (as defined in the masterlink gateway) or for better readability, you can specify the corresponding string (as defined in *rooms = []* in plugin.conf) 

### mlgw_cmd
**mlgw_cmd** has to be specified, if you define **mlgw_listen**. In conjunction with **mlgw_listen**, the attribute **mlgw_cmd** specifies the command from a B&O remote control to listen for (e.g.: **mlgw_cmd** = *'STEP_UP'*). 

The following commands are supported at the moment:

    Digits:
      'Digit-0', 'Digit-1', 'Digit-2', 'Digit-3', 'Digit-4', 
      'Digit-5', 'Digit-6', 'Digit-7', 'Digit-8', 'Digit-9' 
    from Source control:
      'STEP_UP', 'STEP_DW', 'REWIND', 'RETURN', 'WIND', 'Go / Play', 
      'Stop', 'Yellow', 'Green', 'Blue', 'Red' 
    Other controls:
      'BACK'
    Cursor functions:
      'SELECT', 'Cursor_Up', 'Cursor_Down', 'Cursor_Left', 'Cursor_Right'


### Example

Please provide an item configuration with every attribute and usefull settings.

<pre>
# items/my.conf
        
    [Someroom]
    
        [[bv10]]
            name = BeoVision 10
            type = str
            enforce_updates = true
            mlgw_send = cmd
            mlgw_mln = 3
        
            [[[channel]]]
                name = BeoVision 10: Channel
                type = num
                enforce_updates = true
                mlgw_send = ch
                mlgw_mln = 3
                
            [[[digit_1]]]
                name = BeoVision 10: Digit "1"
                type = bool
                enforce_updates = true
                mlgw_send = cmd
                mlgw_mln = 3
                mlgw_cmd = 'Digit-1'
                
        [[living_light0]]
            name = living room: Light "0"
            type = bool
            mlgw_listen = light
            mlgw_room = living
            mlgw_cmd = 'Digit-0'
                
        [[living_lightup]]
            name = living room: Light Step_Up
            type = bool
            mlgw_listen = light
            mlgw_room = living
            mlgw_cmd = 'Step_Up'
                
        [[living_control0]]
            name = living room: Control "0"
            type = bool
            mlgw_listen = control
            mlgw_room = 6
            mlgw_cmd = 'Digit-0'
</pre>
The attribute **name** has not to be specified. It serves in this example as a remark only.

## logic.conf
If your plugin support item triggers as well, please describe the attributes like the item attributes.


# Methodes
If your plugin provides methods for logics. List and describe them here...

## method1(param1, param2)
This method enables the logic to send param1 and param2 to the device. You could call it with `sh.my.method1('String', 2)`.

## method2()
This method does nothing.
