import time, os, sys
from machine import TOUCH
from machine import Pin
from machine import FPIOA
from media.sensor import *
from media.display import *
from media.media import *

lcd_flag = 0
rst_flag = 0
back_flag = 0
confirm_flag = 0
invert_flag = 0
DEFAULT_L1, DEFAULT_L2 = 0, 100
DEFAULT_A1, DEFAULT_A2 = -128, 128
DEFAULT_B1, DEFAULT_B2 = -128, 128
save_file = "/sdcard/threshold.dat"
#用于保存进入调节界面前的参数
prev_L1, prev_L2 = 0, 100
prev_A1, prev_A2 = -128, 128
prev_B1, prev_B2 = -128, 128

#尝试从文件加载参数，若文件不存在则使用默认值
try:
    with open(save_file, 'r') as f:
        data = f.read().split(',')
        L1, L2 = int(data[0]), int(data[1])
        A1, A2 = int(data[2]), int(data[3])
        B1, B2 = int(data[4]), int(data[5])
except:
    L1, L2 = 0, 100
    A1, A2 = -128, 128
    B1, B2 = -128, 128

threshold = [(L1, L2, A1, A2, B1, B2)]

sensor = Sensor()
sensor.reset()
sensor.set_framesize(width=800,height=480) #设置帧大小800x480,LCD专用,默认通道0
sensor.set_pixformat(Sensor.RGB565)

Display.init(Display.ST7701, to_ide=True) #通过01Studio 3.5寸mipi显示屏显示图像
MediaManager.init()

fpioa = FPIOA()
fpioa.set_function(52,FPIOA.GPIO52)
fpioa.set_function(21,FPIOA.GPIO21)
LED=Pin(52,Pin.OUT)
KEY=Pin(21,Pin.IN,Pin.PULL_UP)
state=0

sensor.run()
clock = time.clock()
touch = TOUCH(0)

def save_parameters():
    global L1, L2, A1, A2, B1, B2
    try:
        with open(save_file, 'w') as f:
            f.write(f"{L1},{L2},{A1},{A2},{B1},{B2}")
        print("参数已保存")
    except Exception as e:
        print(f"保存参数失败: {e}")

def ui_1():
    img.draw_string_advanced(0,0,24,f"FPS: {clock.fps():.2f}",color = (0,0,255))
    img.draw_string_advanced(0,25,24,f"Threshold:[{L1},{L2},{A1},{A2},{B1},{B2}]", (0, 0, 255))
    img.draw_string_advanced(750,450,24,"调试",(0, 0, 255))
    Display.show_image(img)

def ui_2():
    binary = img.binary(threshold)
    top_buttons = [
        (0, 0, 24, "返回", (0, 0, 255)),
        (375, 0, 24, "反转", (0, 0, 255)),
        (750, 0, 24, "确认", (0, 0, 255)),
        (375, 450, 24, "复位", (0, 0, 255))
    ]
    for x, y, size, text, color in top_buttons:
        img.draw_string_advanced(x, y, size, text, color)
    img.draw_string_advanced(200, 25, 30, f"Threshold:[{L1},{L2},{A1},{A2},{B1},{B2}]",
        (0, 0, 255))
    y_positions = [80, 150, 220, 290, 360, 430]
    for y in y_positions:
        img.draw_string_advanced(0, y, 30, "+1", (0, 0, 255))
        img.draw_string_advanced(90, y, 30, "+10", (0, 0, 255))
        img.draw_string_advanced(670, y, 30, "-10", (0, 0, 255))
        img.draw_string_advanced(770, y, 30, "-1", (0, 0, 255))
    Display.show_image(binary)

def invert_threshold():
    global L1, L2, A1, A2, B1, B2, threshold
    orig_L1, orig_L2 = L1, L2
    orig_A1, orig_A2 = A1, A2
    orig_B1, orig_B2 = B1, B2
    L1 = 0
    L2 = orig_L1 - 1 if orig_L1 > 0 else 0
    if orig_L2 < 100:
        L1 = orig_L2 + 1
        L2 = 100
    A1 = -128
    A2 = orig_A1 - 1 if orig_A1 > -128 else -128
    if orig_A2 < 127:
        A1 = orig_A2 + 1
        A2 = 127
    B1 = -128
    B2 = orig_B1 - 1 if orig_B1 > -128 else -128
    if orig_B2 < 127:
        B1 = orig_B2 + 1
        B2 = 127
    if L1 > L2:
        L1, L2 = 0, 100
    if A1 > A2:
        A1, A2 = -128, 127
    if B1 > B2:
        B1, B2 = -128, 127
    threshold[0] = (L1, L2, A1, A2, B1, B2)

def update_threshold():
    global threshold, L1, L2, A1, A2, B1, B2
    L1 = max(0, min(100, L1))
    L2 = max(0, min(100, L2))
    A1 = max(-128, min(127, A1))
    A2 = max(-128, min(127, A2))
    B1 = max(-128, min(127, B1))
    B2 = max(-128, min(127, B2))
    threshold[0] = (L1, L2, A1, A2, B1, B2)

def button_touch():
    global lcd_flag, invert_flag, rst_flag, back_flag, confirm_flag, L1, L2, A1, A2, B1, B2
    global prev_L1, prev_L2, prev_A1, prev_A2, prev_B1, prev_B2

    p = touch.read()
    if p != ():
        for i in range(len(p)):
            touch_x = p[i].x
            touch_y = p[i].y

            # 进入调试模式时保存当前参数
            if touch_x >= 750 and touch_y >= 450 and lcd_flag == 0:
                prev_L1, prev_L2 = L1, L2
                prev_A1, prev_A2 = A1, A2
                prev_B1, prev_B2 = B1, B2
                lcd_flag = 1

            if lcd_flag == 1:
                if 0 <= touch_x <= 30 and 80 <= touch_y <= 120:
                    L1 += 1
                elif 90 <= touch_x <= 140 and 80 <= touch_y <= 120:
                    L1 += 10
                elif 670 <= touch_x <= 720 and 80 <= touch_y <= 120:
                    L1 -= 10
                elif touch_x >= 760 and 80 <= touch_y <= 120:
                    L1 -= 1

                elif 0 <= touch_x <= 30 and 150 <= touch_y <= 190:
                    L2 += 1
                elif 90 <= touch_x <= 140 and 150 <= touch_y <= 190:
                    L2 += 10
                elif 670 <= touch_x <= 720 and 150 <= touch_y <= 190:
                    L2 -= 10
                elif touch_x >= 760 and 150 <= touch_y <= 190:
                    L2 -= 1

                elif 0 <= touch_x <= 30 and 220 <= touch_y <= 260:
                    A1 += 1
                elif 90 <= touch_x <= 140 and 220 <= touch_y <= 260:
                    A1 += 10
                elif 670 <= touch_x <= 720 and 220 <= touch_y <= 260:
                    A1 -= 10
                elif touch_x >= 760 and 220 <= touch_y <= 260:
                    A1 -= 1

                elif 0 <= touch_x <= 30 and 290 <= touch_y <= 330:
                    A2 += 1
                elif 90 <= touch_x <= 140 and 290 <= touch_y <= 330:
                    A2 += 10
                elif 670 <= touch_x <= 720 and 290 <= touch_y <= 330:
                    A2 -= 10
                elif touch_x >= 760 and 290 <= touch_y <= 330:
                    A2 -= 1

                elif 0 <= touch_x <= 30 and 360 <= touch_y <= 400:
                    B1 += 1
                elif 90 <= touch_x <= 140 and 360 <= touch_y <= 400:
                    B1 += 10
                elif 670 <= touch_x <= 720 and 360 <= touch_y <= 400:
                    B1 -= 10
                elif touch_x >= 760 and 360 <= touch_y <= 400:
                    B1 -= 1

                elif 0 <= touch_x <= 30 and 430 <= touch_y <= 470:
                    B2 += 1
                elif 90 <= touch_x <= 140 and 430 <= touch_y <= 470:
                    B2 += 10
                elif 670 <= touch_x <= 720 and 430 <= touch_y <= 470:
                    B2 -= 10
                elif touch_x >= 760 and 430 <= touch_y <= 470:
                    B2 -= 1

                elif 370 <= touch_x <= 430 and touch_y <= 40:
                    invert_flag = 1
                elif 370 <= touch_x <= 430 and touch_y >= 450:
                    rst_flag = 1
                elif touch_x <= 55 and touch_y <= 40:
                    back_flag = 1
                elif touch_x >= 750 and touch_y <= 40:
                    confirm_flag = 1

                update_threshold()

while True:
    clock.tick()
    img = sensor.snapshot()

    button_touch()

    if invert_flag == 1:
        invert_threshold()
        invert_flag = 0

    if rst_flag == 1:
        L1, L2 = DEFAULT_L1, DEFAULT_L2
        A1, A2 = DEFAULT_A1, DEFAULT_A2
        B1, B2 = DEFAULT_B1, DEFAULT_B2
        update_threshold()
        print("已复位到默认值")
        rst_flag = 0

    if back_flag == 1:
        L1, L2 = prev_L1, prev_L2
        A1, A2 = prev_A1, prev_A2
        B1, B2 = prev_B1, prev_B2
        lcd_flag = 0
        update_threshold()
        print("返回界面1，不保存参数")
        back_flag = 0

    if confirm_flag == 1:
        save_parameters()
        lcd_flag = 0
        threshold[0] = (L1, L2, A1, A2, B1, B2)
        print("已保存参数并返回界面1")
        confirm_flag = 0

    if lcd_flag == 0:
        ui_1()
    else:
        ui_2()

    if KEY.value() == 0:
        time.sleep_ms(10)  #消除抖动
        if KEY.value() == 0:
            state = not state
            LED.value(state)
            print('KEY pressed')
            while not KEY.value():
                pass
