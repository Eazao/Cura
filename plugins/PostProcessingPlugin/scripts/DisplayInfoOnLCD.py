# Display Filename and Layer on the LCD by Amanda de Castilho on August 28, 2018
# Modified: Joshua Pope-Lewis on November 16, 2018
# Display Progress on LCD by Mathias Lyngklip Kjeldgaard, Alexander Gee, Kimmo Toivanen, Inigo Martinez on July 31, 2019
# Show Progress was adapted from Display Progress by Louis Wooters on January 6, 2020.  His changes are included here.
#---------------------------------------------------------------
# DisplayNameOrProgressOnLCD.py
# Cura Post-Process plugin
# Combines 'Display Filename and Layer on the LCD' with 'Display Progress'
# Combined and with additions by: GregValiant (Greg Foresi)
# Date:       September 8, 2023
# NOTE:  This combined post processor will make 'Display Filename and Layer on the LCD' and 'Display Progress' obsolete
# Description:  Display Filename and Layer options:
#       Status messages sent to the printer...
#           - Scrolling (SCROLL_LONG_FILENAMES) if enabled in Marlin and you aren't printing a small item select this option.
#           - Name: By default it will use the name generated by Cura (EG: TT_Test_Cube) - You may enter a custom name here
#           - Start Num: Choose which number you prefer for the initial layer, 0 or 1
#           - Max Layer: Enabling this will show how many layers are in the entire print (EG: Layer 1 of 265!)
#           - Add prefix 'Printing': Enabling this will add the prefix 'Printing'
#           - Example Line on LCD:  Printing Layer 0 of 395 3DBenchy
#       Display Progress options:
#           - Display Total Layer Count
#           - Disply Time Remaining for the print
#           - Time Fudge Factor % - Divide the Actual Print Time by the Cura Estimate.  Enter as a percentage and the displayed time will be adjusted.  This allows you to bring the displayed time closer to reality (Ex: Entering 87.5 would indicate an adjustment to 87.5% of the Cura estimate).
#           - Example line on LCD:  1/479 | ET 2h13m
#           - Time to Pauses changes the M117/M118 lines to countdown to the next pause as  1/479 | TP 2h36m
#           - 'Add M118 Line' is available with either option.  M118 will bounce the message back to a remote print server through the USB connection.
#           - Enable 'Finish-Time' Message - when enabled, takes the Print Time, adds 15 minutes for print start-up, and calculates when the print will end.  It takes into account the Time Fudge Factor.  The user may enter a print start time.  This is also available for Display Filename.

from ..Script import Script
from UM.Application import Application
from UM.Qt.Duration import DurationFormat
import UM.Util
import configparser
from UM.Preferences import Preferences
import time
import datetime
from UM.Message import Message

class DisplayInfoOnLCD(Script):

    def getSettingDataString(self):
        return """{
            "name": "Display Info on LCD",
            "key": "DisplayInfoOnLCD",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "display_option":
                {
                    "label": "LCD display option...",
                    "description": "Display Filename and Layer was formerly 'Display Filename and Layer on LCD' post-processor.  The message format on the LCD is 'Printing Layer 0 of 15 3D Benchy'.  Display Progress is similar to the former 'Display Progress on LCD' post-processor.  The display format is '1/16 | ET 2hr28m'.  Display Progress includes a fudge factor for the print time estimate.",
                    "type": "enum",
                    "options": {
                        "display_progress": "Display Progress",
                        "filename_layer": "Filename and Layer"
                        },
                    "default_value": "display_progress"
                },
                "format_option":
                {
                    "label": "Scroll enabled/Small layers?",
                    "description": "If SCROLL_LONG_FILENAMES is enabled in your firmware select this setting.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "display_option == 'filename_layer'"
                },
                "file_name":
                {
                    "label": "Text to display:",
                    "description": "By default the current filename will be displayed on the LCD. Enter text here to override the filename and display something else.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "display_option == 'filename_layer'"
                },
                "startNum":
                {
                    "label": "Initial layer number:",
                    "description": "Choose which number you prefer for the initial layer, 0 or 1",
                    "type": "int",
                    "default_value": 0,
                    "minimum_value": 0,
                    "maximum_value": 1,
                    "enabled": "display_option == 'filename_layer'"
                },
                "maxlayer":
                {
                    "label": "Display max layer?:",
                    "description": "Display how many layers are in the entire print on status bar?",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "display_option == 'filename_layer'"
                },
                "addPrefixPrinting":
                {
                    "label": "Add prefix 'Printing'?",
                    "description": "This will add the prefix 'Printing'",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "display_option == 'filename_layer'"
                },
                "display_total_layers":
                {
                    "label": "Display total layers",
                    "description": "This setting adds the 'Total Layers' to the LCD message as '17/234'.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "display_option == 'display_progress'"
                },
                "display_remaining_time":
                {
                    "label": "Display remaining time",
                    "description": "This will add the remaining printing time to the LCD message.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "display_option == 'display_progress'"
                },
                "add_m118_line":
                {
                    "label": "Add M118 Line",
                    "description": "Adds M118 in addition to the M117.  It will bounce the message back through the USB port to a computer print server (if a printer server is enabled).",
                    "type": "bool",
                    "default_value": false
                },
                "speed_factor":
                {
                    "label": "Time Fudge Factor %",
                    "description": "When using 'Display Progress' tweak this value to get better estimates. ([Actual Print Time]/[Cura Estimate]) x 100 = Time Fudge Factor.  If Cura estimated 9hr and the print actually took 10hr30min then enter 117 here to adjust any estimate closer to reality.  This Fudge Factor is also used to calculate the time that the print will end if you were to start it 15 minutes after slicing.",
                    "type": "float",
                    "unit": "%",
                    "default_value": 100,
                    "enabled": "enable_end_message or display_option == 'display_progress'"
                },
                "countdown_to_pause":
                {
                    "label": "Countdown to Pauses",
                    "description": "Instead of layer number and remaining print time the LCD will show 'layers remaining before pause' and 'Est Time to Pause' (ETP).",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "display_option == 'display_progress'"
                },
                "enable_end_message":
                {
                    "label": "Enable 'Finish-Time' Message",
                    "description": "Get a message when you save a fresh slice.  It will show the estimated date and time that the print would finish (with a 15 minute lag from the end of slicing to the start of the print).",
                    "type": "bool",
                    "default_value": true,
                    "enabled": true
                },
                "print_start_time":
                {
                    "label": "Print Start Time (Ex 16:45)",
                    "description": "Use 'Military' time.  16:45 would be 4:45PM.  09:30 would be 9:30AM.  If you leave this blank it will be assumed that the print start will 15 minutes after slicing.",
                    "type": "str",
                    "default_value": "",
                    "unit": "hrs  ",
                    "enabled": "enable_end_message"
                }

            }
        }"""

    def execute(self, data):
        display_option = self.getSettingValueByKey("display_option")
        add_m118_line = self.getSettingValueByKey("add_m118_line")

    # This is Display Filename and Layer on LCD---------------------------------------------------------
        if display_option == "filename_layer":
            max_layer = 0
            lcd_text = "M117 "
            if self.getSettingValueByKey("file_name") != "":
                file_name = self.getSettingValueByKey("file_name")
            else:
                file_name = Application.getInstance().getPrintInformation().jobName
            if self.getSettingValueByKey("addPrefixPrinting"):
                lcd_text += "Printing "
            if not self.getSettingValueByKey("scroll"):
                lcd_text += "Layer "
            else:
                lcd_text += file_name + " - Layer "
            i = self.getSettingValueByKey("startNum")
            for layer in data:
                display_text = lcd_text + str(i)
                layer_index = data.index(layer)
                lines = layer.split("\n")
                for line in lines:
                    if line.startswith(";LAYER_COUNT:"):
                        max_layer = line
                        max_layer = max_layer.split(":")[1]
                        if self.getSettingValueByKey("startNum") == 0:
                            max_layer = str(int(max_layer) - 1)
                    if line.startswith(";LAYER:"):
                        if self.getSettingValueByKey("maxlayer"):
                            display_text = display_text + " of " + max_layer
                            if not self.getSettingValueByKey("scroll"):
                                display_text = display_text + " " + file_name
                        else:
                            if not self.getSettingValueByKey("scroll"):
                                display_text = display_text + " " + file_name + "!"
                            else:
                                display_text = display_text + "!"
                        line_index = lines.index(line)
                        lines.insert(line_index + 1, display_text)
                        if add_m118_line:
                            lines.insert(line_index + 2, str(display_text.replace("M117", "M118", 1)))
                        i += 1
                final_lines = "\n".join(lines)
                data[layer_index] = final_lines
            if bool(self.getSettingValueByKey("enable_end_message")):
                message_str = self.message_to_user(self.getSettingValueByKey("speed_factor") / 100)
                Message(title = "Display Info on LCD - Estimated Finish Time", text = message_str[0] + "\n\n" + message_str[1] + "\n" + message_str[2] + "\n" + message_str[3]).show()
            return data

    # Display Progress (from 'Show Progress' and 'Display Progress on LCD')---------------------------------------
        elif display_option == "display_progress":
        # get settings
            display_total_layers = self.getSettingValueByKey("display_total_layers")
            display_remaining_time = self.getSettingValueByKey("display_remaining_time")
            speed_factor = self.getSettingValueByKey("speed_factor") / 100
        # initialize global variables
            first_layer_index = 0
            time_total = 0
            number_of_layers = 0
            time_elapsed = 0
        # if at least one of the settings is disabled, there is enough room on the display to display "layer"
            first_section = data[0]
            lines = first_section.split("\n")
            for line in lines:
                if line.startswith(";TIME:"):
                    tindex = lines.index(line)
                    cura_time = int(line.split(":")[1])
                    print_time = cura_time*speed_factor
                    hhh = print_time/3600
                    hr = round(hhh // 1)
                    mmm = round((hhh % 1) * 60)
                    orig_hhh = cura_time/3600
                    orig_hr = round(orig_hhh // 1)
                    orig_mmm = round((orig_hhh % 1) * 60)
                    if add_m118_line: lines.insert(tindex+1,"M118 Adjusted Print Time " + str(hr) + "hr " + str(mmm) + "min")
                    lines.insert(tindex+1,"M117 ET " + str(hr) + "hr " + str(mmm) + "min")
                    # This line goes in to convert seconds to hours and minutes
                    lines.insert(tindex+1, f";Cura Time:  {orig_hr}hr {orig_mmm}min")
                    data[0] = "\n".join(lines)
                    data[len(data)-1] += "M117 Orig Cura Est " + str(orig_hr) + "hr " + str(orig_mmm) + "min\n"
                    if add_m118_line: data[len(data)-1] += "M118 Est w/FudgeFactor  " + str(speed_factor * 100) + "% was " + str(hr) + "hr " + str(mmm) + "min\n"
            if not display_total_layers or not display_remaining_time:
                base_display_text = "layer "
            else:
                base_display_text = ""
            layer = data[len(data)-1]
            data[len(data)-1] = layer.replace(";End of Gcode" + "\n", "")
            data[len(data)-1] += ";End of Gcode" + "\n"
        # Search for the number of layers and the total time from the start code
            for index in range(len(data)):
                data_section = data[index]
        # We have everything we need, save the index of the first layer and exit the loop
                if ";LAYER:" in data_section:
                    first_layer_index = index
                    break
                else:
                    for line in data_section.split("\n"):
                        if line.startswith(";LAYER_COUNT:"):
                            number_of_layers = int(line.split(":")[1])
                        elif line.startswith(";TIME:"):
                            time_total = int(line.split(":")[1])
        # for all layers...
            current_layer = 0
            for layer_counter in range(len(data)-2):
                current_layer += 1
                layer_index = first_layer_index + layer_counter
                display_text = base_display_text
                display_text += str(current_layer)
        # create a list where each element is a single line of code within the layer
                lines = data[layer_index].split("\n")
                if not ";LAYER:" in data[layer_index]:
                    current_layer -= 1
                    continue
        # add the total number of layers if this option is checked
                if display_total_layers:
                    display_text += "/" + str(number_of_layers)
        # if display_remaining_time is checked, it is calculated in this loop
                if display_remaining_time:
                    time_remaining_display = " | ET "  # initialize the time display
                    m = (time_total - time_elapsed) // 60  # estimated time in minutes
                    m *= speed_factor  # correct for printing time
                    m = int(m)
                    h, m = divmod(m, 60)  # convert to hours and minutes
        # add the time remaining to the display_text
                    if h > 0:  # if it's more than 1 hour left, display format = xhxxm
                        time_remaining_display += str(h) + "h"
                        if m < 10:  # add trailing zero if necessary
                            time_remaining_display += "0"
                        time_remaining_display += str(m) + "m"
                    else:
                        time_remaining_display += str(m) + "m"
                    display_text += time_remaining_display
        # find time_elapsed at the end of the layer (used to calculate the remaining time of the next layer)
                    if not current_layer == number_of_layers:
                        for line_index in range(len(lines) - 1, -1, -1):
                            line = lines[line_index]
                            if line.startswith(";TIME_ELAPSED:"):
        # update time_elapsed for the NEXT layer and exit the loop
                                time_elapsed = int(float(line.split(":")[1]))
                                break
        # insert the text AFTER the first line of the layer (in case other scripts use ";LAYER:")
                for l_index, line in enumerate(lines):
                    if line.startswith(";LAYER:"):
                        lines[l_index] += "\nM117 " + display_text
                        if add_m118_line:
                            lines[l_index] += "\nM118 " + display_text
                        break
        # overwrite the layer with the modified layer
                data[layer_index] = "\n".join(lines)

        # If enabled then change the ET to TP for 'Time To Pause'
            if bool(self.getSettingValueByKey("countdown_to_pause")):
                time_list = []
                time_list.append("0")
                time_list.append("0")
                this_time = 0
                pause_index = 1

        # Get the layer times
                for num in range(2,len(data) - 1):
                    layer = data[num]
                    lines = layer.split("\n")
                    for line in lines:
                        if line.startswith(";TIME_ELAPSED:"):
                            this_time = (float(line.split(":")[1]))*speed_factor
                            time_list.append(str(this_time))
                            if "PauseAtHeight.py" in layer:
                                for qnum in range(num - 1, pause_index, -1):
                                    time_list[qnum] = str(float(this_time) - float(time_list[qnum])) + "P"
                                pause_index = num-1

        # Make the adjustments to the M117 (and M118) lines that are prior to a pause
                for num in range (2, len(data) - 1,1):
                    layer = data[num]
                    lines = layer.split("\n")
                    for line in lines:
                        if line.startswith("M117") and "|" in line and "P" in time_list[num]:
                            M117_line = line.split("|")[0] + "| TP "
                            alt_time = time_list[num][:-1]
                            hhh = int(float(alt_time) / 3600)
                            if hhh > 0:
                                hhr = str(hhh) + "h"
                            else:
                                hhr = ""
                            mmm = ((float(alt_time) / 3600) - (int(float(alt_time) / 3600))) * 60
                            sss = int((mmm - int(mmm)) * 60)
                            mmm = str(round(mmm)) + "m"
                            time_to_go = str(hhr) + str(mmm)
                            if hhr == "": time_to_go = time_to_go + str(sss) + "s"
                            M117_line = M117_line + time_to_go
                            layer = layer.replace(line, M117_line)
                        if line.startswith("M118") and "|" in line and "P" in time_list[num]:
                            M118_line = line.split("|")[0] + "| TP " + time_to_go
                            layer = layer.replace(line, M118_line)
                    data[num] = layer
            setting_data = ""
            if bool(self.getSettingValueByKey("enable_end_message")):
                message_str = self.message_to_user(speed_factor)
                Message(title = "[Display Info on LCD] - Estimated Finish Time", text = message_str[0] + "\n\n" + message_str[1] + "\n" + message_str[2] + "\n" + message_str[3]).show()
        return data

    def message_to_user(self, speed_factor: float):
        # Message the user of the projected finish time of the print (figuring a 15 minute delay from end-of-slice to start-of-print
        print_time = Application.getInstance().getPrintInformation().currentPrintTime.getDisplayString(DurationFormat.Format.ISO8601)
        print_start_time = self.getSettingValueByKey("print_start_time")
        # If the user entered a print start time make sure it is in the correct format or ignore it.
        if print_start_time == "" or print_start_time == "0" or len(print_start_time) != 5 or not ":" in print_start_time:
            print_start_time = ""
        # Change the print start time to proper time format, or, use the current time
        if print_start_time != "":
            hr = int(print_start_time.split(":")[0])
            min = int(print_start_time.split(":")[1])
            sec = 0
            fifteen_minute_delay = 0
        else:
            hr = int(time.strftime("%H"))
            min = int(time.strftime("%M"))
            sec = int(time.strftime("%S"))
            fifteen_minute_delay = 900

        #Get the current data/time info
        yr = int(time.strftime("%Y"))
        day = int(time.strftime("%d"))
        mo = int(time.strftime("%m"))

        date_and_time = datetime.datetime(yr, mo, day, hr, min, sec)
        #Split the Cura print time
        pr_hr = int(print_time.split(":")[0])
        pr_min = int(print_time.split(":")[1])
        pr_sec = int(print_time.split(":")[2])
        #Adjust the print time if none was entered
        print_seconds = pr_hr*3600 + pr_min*60 + pr_sec + fifteen_minute_delay
        #Adjust the total seconds by the Fudge Factor
        adjusted_print_time = print_seconds * speed_factor
        #Break down the adjusted seconds back into hh:mm:ss
        adj_hr = int(adjusted_print_time/3600)
        print_seconds = adjusted_print_time - (adj_hr * 3600)
        adj_min = int(print_seconds) / 60
        adj_sec = int(print_seconds - (adj_min * 60))
        #Get the print time to add to the start time
        time_change = datetime.timedelta(hours=adj_hr, minutes=adj_min, seconds=adj_sec)
        new_time = date_and_time + time_change
        #Get the day of the week that the print will end on
        week_day = str(["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][int(new_time.strftime("%w"))])
        #Get the month that the print will end in
        mo_str = str(["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"][int(new_time.strftime("%m"))-1])
        #Make adjustments from 24hr time to 12hr time
        if int(new_time.strftime("%H")) > 12:
            show_hr = str(int(new_time.strftime("%H")) - 12) + ":"
            show_ampm = " PM"
        elif int(new_time.strftime("%H")) == 0:
            show_hr = "12:"
            show_ampm = " AM"
        else:
            show_hr = str(new_time.strftime("%H")) + ":"
            show_ampm = " AM"
        if print_start_time == "":
            start_str = "and a 15 minute lag between saving the file and starting the print."
        else:
            start_str = "and your entered 'print start time' of " + print_start_time + "hrs."
        if print_start_time != "":
            print_start_str = "Print Start Time................." + str(print_start_time) + "hrs"
        else:
            print_start_str = "Print Start Time.................15 minutes from now."
        estimate_str = "Cura Time Estimate.........." + str(print_time)
        adjusted_str = "Adjusted Time Estimate..." + str(time_change)
        finish_str = week_day + " " + str(mo_str) + " " + str(new_time.strftime("%d")) + ", " + str(new_time.strftime("%Y")) + " at " + str(show_hr) + str(new_time.strftime("%M")) + str(show_ampm)
        return finish_str, estimate_str, adjusted_str, print_start_str