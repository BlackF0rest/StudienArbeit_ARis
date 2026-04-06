import machine
import time
import ssd1306
import imu
import utime
import _thread

x = True

i2c = machine.I2C(sda=21, scl=22, freq=400000)
mpu = imu.MPU6050(i2c)
display = ssd1306.SSD1306_I2C(128, 64, i2c)
time.sleep(2)

display.text('Hello World', 0, 0, 1)
display.show()

led = machine.Pin(33, machine.Pin.OUT)
btn = machine.Pin(38, machine.Pin.IN, machine.Pin.PULL_DOWN)

def display_logo(oled):
    # Display the Raspberry Pi logo on the OLED
    buffer = bytearray(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00|?\x00\x01\x86@\x80\x01\x01\x80\x80\x01\x11\x88\x80\x01\x05\xa0\x80\x00\x83\xc1\x00\x00C\xe3\x00\x00~\xfc\x00\x00L'\x00\x00\x9c\x11\x00\x00\xbf\xfd\x00\x00\xe1\x87\x00\x01\xc1\x83\x80\x02A\x82@\x02A\x82@\x02\xc1\xc2@\x02\xf6>\xc0\x01\xfc=\x80\x01\x18\x18\x80\x01\x88\x10\x80\x00\x8c!\x00\x00\x87\xf1\x00\x00\x7f\xf6\x00\x008\x1c\x00\x00\x0c \x00\x00\x03\xc0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
    fb = framebuf.FrameBuffer(buffer, 32, 32, framebuf.MONO_HLSB)
    
    oled.fill(0)
    oled.blit(fb, 96, 0)
    oled.show()

def display_text(oled):
    # Display text on the OLED
    oled.text("Raspberry Pi", 5, 5)
    oled.text("Pico", 5, 15)
    oled.show()

def display_anima(oled):
    # Display a simple timer animation on the OLED
    start_time = utime.ticks_ms()

    while True:
        elapsed_time = (utime.ticks_diff(utime.ticks_ms(), start_time) // 1000) + 1
        
        # Clear the specific line by drawing a filled black rectangle
        oled.fill_rect(5, 40, oled.width - 5, 8, 0)

        oled.text("Timer:", 5, 30)
        oled.text(str(elapsed_time) + " sec", 5, 40)
        oled.show()
        utime.sleep_ms(1000)

def display_time(oled, delay):

    while True:
        oled.fill_rect(60, 5, oled.width - 5, 18, 0)

        time = utime.gmtime()
        year = (time[0] % 1000) % 100
        month = time[1]
        day = time[2]
        oled.text(str(day) + "." + str(month) + "." + str(year), 60, 5)
        hours = time[3]
        minutes = time[4]
        seconds = time[5]
        oled.text(str(hours) + ":" + str(minutes) + ":" + str(seconds), 60, 15)
        oled.show()
        utime.sleep_ms(delay)

def display_gyro(imu):
    while True:
        # Messwerte für X, Y und Z
        gyr_raw_x = round(mpu.gyro.x, 1)
        gyr_raw_y = round(imu.gyro.y, 1)
        gyr_raw_z = round(imu.gyro.z, 1)
        # Werte anzeigen in Grad pro Sekunde (°/s)
        #print('gyr_raw_x:', gyr_raw_x, "\t", 'gyr_raw_y:', gyr_raw_y, "\t", 'gyr_raw_z:', gyr_raw_z, "\t", end = "\r")
        gyr_force = gyr_raw_x * gyr_raw_y * gyr_raw_z
        print('gyr_force:', gyr_force, "\t\t\t\t", end = "\r")
        if gyr_force == 0: utime.sleep(.2)
        else: utime.sleep(1)

def btn_function():
    display.fill(0)
    _thread.start_new_thread(display_time,(display,1000))

    display_gyro(mpu)

def button_handler(pin):
    global x
    x = not x
    led.toggle()

btn.irq(trigger=machine.Pin.IRQ_RISING, handler=button_handler)

while True:
    if x:
        acc_raw_x = round(mpu.accel.x, 1)
        acc_raw_y = round(mpu.accel.y, 1)
        acc_raw_z = round(mpu.accel.z, 1)
        # Werte anzeigen in g (Gravitationsbeschleunigung)
        print('acc_raw_x:', acc_raw_x, "\t", 'acc_raw_y:', acc_raw_y, "\t", 'acc_raw_z:', acc_raw_z, "\t", end = "\r")
        time.sleep(0.2)
    else:
        btn_function()