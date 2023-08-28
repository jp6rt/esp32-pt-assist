import machine
import dht
import network
import ntptime
from machine import Pin, SoftI2C, ADC, RTC
from lcd_api import LcdApi
from i2c_lcd import I2cLcd
from time import sleep
from secrets import wlan_ssid, wlan_password

I2C_ADDR = 0x27
totalRows = 2
totalColumns = 16
i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=10000)
lcd = I2cLcd(i2c, I2C_ADDR, totalRows, totalColumns)

rtc = RTC()
sensor = dht.DHT11(Pin(14))

pomodoro_btn_start = Pin(17, Pin.IN)
pomodoro_btn_reset = Pin(16, Pin.IN)
pomodoro_cntr = 0
# pomodoro time in seconds
pomodoro = 1500
pomodoro_state = False
is_clock_sync = False

daily_clk_btn_start = Pin(18, Pin.IN)
daily_clk_btn_pause = Pin(19, Pin.IN)
daily_clk_cntr = 0
daily_clk_is_counting = False

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

def to_str_pad(i):
    return "0{}".format(i) if len(str(i)) == 1 else str(i)

def get_hms_str():
    """
    Return the hh:mm:ss in this format from RTC
    """
    
    # remove seconds to make room for daily counter
    # hms = rtc.datetime()[4:7]
    hms = rtc.datetime()[4:6]
    
    return ':'.join(list(map(to_str_pad, hms)))

def pomodoro_disp():
    t_remaining = pomodoro - pomodoro_cntr
    minutes = int(t_remaining / 60)
    seconds = t_remaining % 60
    return "{}:{}".format(to_str_pad(minutes), to_str_pad(seconds))

def daily_clk_disp():
    hours = int(daily_clk_cntr / 3600)
    minutes = int((daily_clk_cntr % 3600) / 60)
    seconds = daily_clk_cntr % 60
    return "{}:{}:{}".format(to_str_pad(hours), to_str_pad(minutes), to_str_pad(seconds))

def get_sensor_disp():
    sensor.measure()
    sensor_disp = "{}c{}h".format(sensor.temperature(), sensor.humidity())
    return sensor_disp
    
def get_wlan_disp():
    status = "1" if wlan.isconnected() else "0"
    return f"wl{status}"
    
def update_display(force_update=False):
    # For some reason instead of clearing the lcd which causes an animation when
    # writing characters to the cursors, writing to the x=0, y=0 cursor appears to
    # work without issues
    # lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr("{} {} {}\n{} {}".format(get_hms_str(),
                                     get_sensor_disp(),
                                     get_wlan_disp(),
                                     pomodoro_disp(),
                                     daily_clk_disp()))

while True:
    if not wlan.isconnected():
        try:
            wlan.connect(wlan_ssid, wlan_password)
        except Exception as err:
            print("wlan error={}".format(err))
        
    if not is_clock_sync and wlan.isconnected():
        try:
            ntptime.settime()
            is_clock_sync = True
        except Exception as err:
            print("ntptime error={}".format(err))
    
    if pomodoro_btn_start.value() == 1:
        pomodoro_state = True
        update_display(True)
        
    if pomodoro_btn_reset.value() == 1:
        pomodoro_state = False
        pomodoro_cntr = 0
        update_display(True)
    
    if pomodoro_cntr >= pomodoro:
        pomodoro_state = False
        pomodoro_cntr = 0
        update_display(True)
    
    if daily_clk_btn_start.value() == 1:
        daily_clk_is_counting = True
        update_display(True)
        
    if daily_clk_btn_pause.value() == 1:
        daily_clk_is_counting = False
        update_display(True)
    
    if pomodoro_state:
        pomodoro_cntr = pomodoro_cntr + 1
        
    if daily_clk_is_counting:
        daily_clk_cntr = daily_clk_cntr + 1
        
    update_display()
