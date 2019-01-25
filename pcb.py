#!/usr/bin/python3
#Copyright 2017 Michael Kirsch

#Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"),
#to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

try:
    import time
    import os
    import RPi.GPIO as GPIO
except ImportError:
    raise ImportError('spidev or gpio not installed')

class SNES:

    def __init__(self):

        #GPIOs

        self.led_pin=7
        self.reset_pin=3
        self.power_pin=5
        self.check_pin=10

        #vars

        self.reset_hold_short = 100
        self.reset_hold_long = 500
        self.debounce_time = 0.1
        self.counter_time = 0.01
        self.delay_until_reset = 2

        #Set the GPIOs

        GPIO.setmode(GPIO.BOARD)  # Use the same layout as the pins
        GPIO.setwarnings(False)
        GPIO.setup(self.led_pin, GPIO.OUT)  # LED Output
        GPIO.setup(self.power_pin, GPIO.IN)  # set pin as input
        GPIO.setup(self.reset_pin, GPIO.IN,
                   pull_up_down=GPIO.PUD_UP)  # set pin as input and switch on internal pull up resistor
        GPIO.setup(self.check_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def power_interrupt(self, channel):
        time.sleep(self.debounce_time)  # debounce
        if GPIO.input(self.power_pin) == GPIO.HIGH and GPIO.input(
                self.check_pin) == GPIO.LOW:  # shutdown function if the powerswitch is toggled
            self.led(0)  # led and fan off
            os.system("killall emulationstation") #end emulationstation
            self.blink(30, 0.1) #wait for the metadata to be safed
            self.fan(0)
            os.system("sudo shutdown -h now")

    def reset_interrupt(self, channel):
        if GPIO.input(self.reset_pin) == GPIO.LOW:  # reset function
            reset_counter = 0  # counter for the time funktion
            time.sleep(self.debounce_time)  # debounce time
            while GPIO.input(self.reset_pin) == GPIO.LOW:  # while the button is hold the counter counts up
                reset_counter = reset_counter + 1
                time.sleep(self.counter_time)
            if reset_counter > self.reset_hold_short:  # check if its hold more that one second
                if reset_counter <= self.reset_hold_long:  # if you hold it less than 5 sec it will toggle the fan
                    self.change_config_value("fan")
                    self.blink(3, 0.5)
                    self.led(1)
            else:
                os.system("killall emulationstation")
                self.blink(15, 0.1)
                os.system("sudo reboot")

    def pcb_interrupt(self, channel):
        GPIO.cleanup()  # when the pcb is pulled clean all the used GPIO pins

    def temp(self):     #returns the gpu temoperature
        res = os.popen(self.temp_command).readline()
        return float((res.replace("temp=", "").replace("'C\n", "")))

    def led(self,status):  #toggle the led on of off
        if status == 0:       #the led is inverted
            GPIO.output(self.led_pin, GPIO.LOW)
        if status == 1:
            GPIO.output(self.led_pin, GPIO.HIGH)

    def blink(self,amount,interval): #blink the led
        for x in range(amount):
            self.led(1)
            time.sleep(interval)
            self.led(0)
            time.sleep(interval)

    def attach_interrupts(self):
        if GPIO.input(self.check_pin) == GPIO.LOW:  # check if there is an pcb and if so attach the interrupts
            GPIO.add_event_detect(self.check_pin, GPIO.RISING,callback=self.pcb_interrupt)  # if not the interrupt gets attached
            if GPIO.input(self.power_pin) == GPIO.HIGH: #when the system gets startet in the on position it gets shutdown
                os.system("sudo shutdown -h now")
            else:
                self.led(1)
                GPIO.add_event_detect(self.reset_pin, GPIO.FALLING, callback=self.reset_interrupt)
                GPIO.add_event_detect(self.power_pin, GPIO.RISING, callback=self.power_interrupt)
        else:       #no pcb attached so lets exit
            GPIO.cleanup()
            exit()

snes = SNES()

snes.attach_interrupts()

while True:
    time.sleep(5)
    snes.led(1)
