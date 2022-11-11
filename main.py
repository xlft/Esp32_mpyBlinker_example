#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''

元件：
    ESP32 DevkitV1
    128*64 SSD1306 OLED SPI/IIC
    全彩RGB灯 供电脚不够接的话，可以接gpio2供电,跟板载LED电平一致
    DHT22
功能：
    BlinkerAPP远程获取DHT22温湿度数据、远程控制RGB颜色亮度、oled本地实时显示时间+温度和湿度。
'''
from dht import DHT22
from machine import Pin,PWM,SoftSPI,Timer
from Blinker.Blinker import Blinker, BlinkerButton, BlinkerNumber, BlinkerRGB
from Blinker.BlinkerDebug import *
from ssd1306 import SSD1306_SPI


#软SPI，初始化oled 
spi = SoftSPI(baudrate=80000000, polarity=0, phase=0, sck=Pin(18,Pin.OUT), mosi=Pin(23,Pin.OUT), miso=Pin(33)) #sck(D0)=18 mosi(D1)=23 miso=unused
oled = SSD1306_SPI(128, 64, spi, Pin(4),Pin(5), Pin(32)) #4=DC 5=RST unused=CS

#初始化RGB灯珠引脚，复用PWM，设置频率
led_r = Pin(25, Pin.OUT)
led_b = Pin(26, Pin.OUT)
led_g = Pin(27, Pin.OUT)
pwm_led_r = PWM(led_r)
pwm_led_r.freq(1000)
pwm_led_g = PWM(led_g)
pwm_led_g.freq(1000)
pwm_led_b = PWM(led_b)
pwm_led_b.freq(1000)

dht = DHT22(Pin(13))	#设置DHT22引脚

p2 = Pin(2, Pin.OUT)	#板载led


auth = 'Your Device Secret Key'   #Blinker设备秘钥
ssid = 'Your WiFi network SSID or name'  #SSID：WiFi名称
pswd = 'Your WiFi network WPA password or WEP key'       #WIFI 密码



#Debug
BLINKER_DEBUG.debugAll()
#初始化硬件Wifi接入
Blinker.mode('BLINKER_WIFI')
Blinker.begin(auth, ssid, pswd)
#数字组件, 用于发送数据到APP/显示数字数据
HUMI = BlinkerNumber('humi')
TEMP = BlinkerNumber('temp')
#按键组件在App中可以设置 按键/开关/自定义 三种模式
button1 = BlinkerButton('led0')
#颜色组件, 用于读取/设置RGB及亮度值
rgb1 = BlinkerRGB("RGBKey")

humi_read = 0	#读取湿度
temp_read = 0	#读取温度

def heartbeat_callback():
    """心跳包回调函数，用户在线时每分钟触发一次"""
    #清屏
    oled.fill(0)
    #dht22测量一次
    dht.measure()
    temp_read = dht.temperature()	#读取温度
    humi_read = dht.humidity()		#读取湿度
    
    #时间+温度+湿度
    time_tex = str(Blinker.year())+'-'+str(Blinker.month())+'-'+str(Blinker.mday())+' '+str(Blinker.hour())+':'+('0'+str(Blinker.minute()))[-2:]
    t_tex = "T:"+str(temp_read)+"C"
    h_tex = "H:"+str(humi_read)[:4]+'%'
    #oled显示时间+温度+湿度
    oled.text(time_tex,0,6)
    oled.text(t_tex, 40, 16)
    oled.text(h_tex, 40, 26)
    oled.show()			#OLED显示
    BLINKER_LOG('||Humidity:',humi_read,"||Temperature:",temp_read,"||")	#串口Blinker输出日志
    HUMI.print(humi_read)	#发送湿度数据到APP/显示数字数据
    TEMP.print(temp_read)	#发送温度数据到APP/显示数字数据


def button1_callback(state):
    '''按键回调（内置led的开关）'''
    BLINKER_LOG('get button state: ', state)	#串口Blinker输出日志
    button1.print(state)		#发送button1状态
    p2.value(1-p2.value())		#按键翻转电平
    #根据电平设置app按键的图标
    if(p2.value()):
        button1.icon("fad fa-siren")
        button1.text("Turn ON")    
    else:
        button1.icon("fad fa-siren-on")
        button1.text("Turn OFF")
    

def rgb1_callback(r_value, g_value, b_value, bright_value):
    """根据RGB组件返回值设置R/G/B占空比"""
    """无亮度情况"""
    #pwm_led_r.duty(1023 - int(r_value / 255 * 1023))
    #pwm_led_g.duty(1023 - int(g_value / 255 * 1023))
    #pwm_led_b.duty(1023 - int(b_value / 255 * 1023))  
    """有亮度情况"""
    pwm_led_r.duty(1023 - int(r_value * bright_value* 1023 / 65025 ))
    pwm_led_g.duty(1023 - int(g_value * bright_value* 1023 / 65025 ))
    pwm_led_b.duty(1023 - int(b_value * bright_value* 1023 / 65025 ))
    

#定时器0回调函数
def mycallback(callback_timer):
    """"实现Oled屏本地实时显示时间/温度/湿度信息"""
    oled.fill(0)
    #dht22测量一次
    dht.measure()
    temp_read = dht.temperature()	#读取温度
    humi_read = dht.humidity()		#读取湿度
    try:
        ntptime.settime()
    except:
        pass
    time_tex = time.localtime()
    time_tex = '%d-%d-%d %d:%02d'%(time_tex[0],time_tex[1],time_tex[2],time_tex[3],time_tex[4])
    #时间+温度+湿度
    t_tex = "T:"+str(temp_read)+"C"
    h_tex = "H:"+str(humi_read)[:4]+'%'
    #oled显示时间+温度+湿度
    oled.text(time_tex,0,6)
    oled.text(t_tex, 40, 16)
    oled.text(h_tex, 40, 26)
    oled.show()			#OLED显示
    


if __name__ == '__main__':
    #注册回调函数，当有设备收到APP发来的数据时会调用对应的回调函数
    rgb1.attach(rgb1_callback)
    button1.attach(button1_callback)
    Blinker.attachHeartbeat(heartbeat_callback)
    
    tim0 = Timer(0)
    tim0.init(period=60000, mode=Timer.PERIODIC, callback=mycallback) #周期为1分钟，无限执行。
    while True:
        Blinker.run()
            
        







