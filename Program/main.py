import machine
import network
import ntptime
import utime, time
import ustruct
import urequests as requests
from machine import Pin, I2C
from esp8226_i2c_lcd import I2cLcd
from dht20 import DHT20
import admin


sda_lcd = machine.Pin(0)
scl_lcd = machine.Pin(1)
sda_tmperature = machine.Pin(2)
scl_tmperature = machine.Pin(3)
cds = machine.ADC(2)
backLight = Pin(5, Pin.OUT)
feelHuman = Pin(6, Pin.IN)
led = machine.Pin("LED", machine.Pin.OUT)


i2c_lcd = machine.I2C(0, sda=sda_lcd, scl=scl_lcd, freq=400000)
lcd = I2cLcd(i2c_lcd, 0x27, 4, 20)

i2c_tmperature = I2C(1, sda=sda_tmperature, scl=scl_tmperature, freq=400000)
dht20 = DHT20(0x38, i2c_tmperature)

#--------------------------------------------admin---------------------------------------------------------------
ssid = admin.ssid
password = admin.ssid_pass

api_key = admin.api_key
city = "Osaka"
country_code = "jp"
url = "http://api.openweathermap.org/data/2.5/forecast?q={},{}&appid={}".format(city, country_code, api_key)
#----------------------------------------------------------------------------------------------------------------


#天気と時間の同期間隔[minutes]
sysMinutes = 60
#次のループへの待機時間
delay = 0.2
#cdsセンサの閾値[V]
thresholdLight = 1.2
#人感センサの閾値[0～10]
thresholdFeelhuman = 3
#表示する時間[s]
displayTime = 30
#1つの天気予報を表示する時間
displayTime_wea = 2
#天気を取得する回数/3時間ごと(2だったら9時と12時みたいな)
getWeather_num = 3
#配列の宣言/天気情報格納
weatherInfo = [""] * getWeather_num
wea_normal = [""] * getWeather_num
wea_detail = [""] * getWeather_num
temp_now = [""] * getWeather_num
temp_min = [""] * getWeather_num
temp_max = [""] * getWeather_num
temp_feel = [""] * getWeather_num
humidity = [""] * getWeather_num
clouds = [""] * getWeather_num
wind_speed = [""] * getWeather_num
rain_chance = [""] * getWeather_num
wea_time = [""] * getWeather_num
arrayDay = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]



def main():
    global weatherInfo, sysMinutes
    delay = 0.4
    secondPrev = 99
    count = 0
    synState = False
    displayWrite = [""]*4
    #-----------------------------------------------------------------------------------------------
    #初期化,ネットワークタイムと気象情報を同期
    displaySyn()
    synNetwork()
    lcd.clear()
    while True:
        #人感センサが反応したら
        if getFeelhuman()==True:
            #温湿度を取得
            temperture, humidity = getTemperature()
            #ループ中に同期時間が来たらstatusをTrueに
            synState = False
            start_time = time.time()
            #30[s]ループする
            while (time.time() - start_time) < displayTime:
                year, month, date, hour, minutes, second, day, intHour, intMinutes, intSecond = getTime()
                #ディスプレイ更新の処理(条件:秒数が進んだとき)
                if secondPrev != intSecond:
                    listNum = ( int(count/displayTime_wea)) % getWeather_num
                    spaceNum = 8 - (len(weatherInfo[1][listNum])) - (len(weatherInfo[2][listNum]) )
                    if spaceNum < 0:
                        spaceNum = 0
                    displayWrite[0] = year + "/" + month + "/" + date + " " + arrayDay[day]
                    displayWrite[1] = "      " + hour + ":" + minutes + ":" + second
                    displayWrite[2] = "TEMP:" + temperture + "C" + "  " + weatherInfo[0][listNum][0] + "\xc6\xc1" + weatherInfo[0][listNum][1] + "\xbc\xde"
                    displayWrite[3] = " HUM:" + humidity + "%" + " " + weatherInfo[1][listNum] +\
                                      " " * spaceNum + weatherInfo[2][listNum] + "%"
                    lcd.clear()
                    lcd.move_to(0, 0)
                    lcd.putstr(displayWrite[0])
                    lcd.move_to(0, 1)
                    lcd.putstr(displayWrite[1])
                    lcd.move_to(0, 2)
                    lcd.putstr(displayWrite[2])
                    lcd.move_to(0, 3)
                    lcd.putstr(displayWrite[3])
                    count += 1
                else:
                    pass
                secondPrev = intSecond
                #バックライトの処理(False:暗,True:明)
                if getLight() == False:
                    backLight.value(1)
                else:
                    backLight.value(0)
                #同期の時間か確認
                if (intMinutes % sysMinutes) == 0 and intSecond == 0:
                    synState = True
                else:
                    pass
                time.sleep(delay)
        #人感センサが反応しなかったとき   
        else:
            #初期化
            lcd.clear()
            backLight.value(0)
            count = 0
            year, month, date, hour, minutes, second, day, intHour, intMinutes, intSecond = getTime()
            if ((intMinutes % sysMinutes) == 0 and intSecond == 0) or synState == True:
                synNetwork()
                synState = False
            else:
                pass
            time.sleep(delay)
            
                
                
   

#時間と天気を同期
def synNetwork():
    global wlan, intHour
    connectRouter()
    time.sleep(0.01)
    #NTPと同期
    ntptime.settime()
    #天気を更新
    getWeather()
    time.sleep(0.01)
    wlan.disconnect()

#天気予報APIの関数
def getWeather():
    global weatherInfo, intHour
    year, month, date, hour, minutes, second, day, intHour, intMinutes, intSecond = getTime()
    response = requests.get(url)
    data = response.json()
    #jsonファイルを取得できたとき
    if data:
        for n in range(getWeather_num):
            #天気の情報/天気の詳細情報
            wea_normal[n] = str(data["list"][n]["weather"][0]["main"])
            wea_detail[n] = str(data["list"][n]["weather"][0]["description"])
            #現在の気温/最高気温/最低気温/体感温度[℃]
            temp_now[n] = str(round(data["list"][n]["main"]["temp"] - 273.15, 1))
            temp_min[n] = str(round(data["list"][n]["main"]["temp_min"] - 273.15, 1))
            temp_max[n] = str(round(data["list"][n]["main"]["temp_max"] - 273.15, 1))
            temp_feel[n] = str(round(data["list"][n]["main"]["feels_like"] - 273.15, 1))
            #湿度[%]
            humidity[n] = str(round(data["list"][n]["main"]["humidity"]))
            #雲量[%]
            clouds[n] = str(round(data["list"][n]["clouds"]["all"]))
            #風速[m/s]
            wind_speed[n] = str(round(data["list"][n]["wind"]["speed"]))
            #降水確率
            rain_chance[n] = str(round(data["list"][n]["pop"] * 100))
            #その天気の時刻を変換
            wea_day, wea_hour = exUnixtime(data["list"][n]["dt"])
            wea_time[n] = [str(wea_day), str(wea_hour)] 
            #表示する気象情報を格納
            #天気の情報/降水確率/気温
        weatherInfo = [wea_time, wea_normal, rain_chance]
    #jsonを取得できなかったとき
    else:
        None

#unix時間を変換するプログラム
def exUnixtime(unixTime):
    tm = utime.localtime(unixTime + 32400)
    #year = tm[0]
    #month = tm[1]
    day = tm[2]
    hour = tm[3]
    #minute = tm[4]
    #second = tm[5]
    #microsecond = machine.RTC().datetime()[6]
    return day, '{:02d}'.format(hour)

#日付と時間の関数
def getTime():
    #getNtp[7] = [year, month, date, hour, minutes, second, day, 経過日]
    getNtp = utime.localtime(utime.time() + 32400)
    #return[9] = [strでyear, month, date, hour, minutes(2桁), second(2桁), day, intでhour, minutes, second]
    return  str(getNtp[0]), str(getNtp[1]), str(getNtp[2]), str(getNtp[3]), '{:02d}'.format(getNtp[4]), '{:02d}'.format(getNtp[5]), getNtp[6], getNtp[3], getNtp[4], getNtp[5]

#温湿度センサの値を取得する関数
def getTemperature():
    time.sleep(0.15)
    measurements = dht20.measurements
    get_temperture = str(round(measurements['t'], 1))
    get_humidity = str(round(measurements['rh'], 1))
    #strで温度とと湿度をreturn
    return get_temperture, get_humidity

#cdsセルの関数
def getLight():
    n = 3
    unit = 0.00005035477
    cdsArray = [0] * n
    for i in range(n):
        voltRaw = cds.read_u16()
        volt = voltRaw * unit
        cdsArray[i] = volt
        time.sleep(0.001)
    #明るかったらTrueをreturn
    if (sum(cdsArray) / len(cdsArray) ) >= thresholdLight:
        return True
    #暗かったらFalseをreturn
    else:
        return False
    
#人感センサーの関数
def getFeelhuman():
    n = 5
    feelhumanArray = [0] * n
    for i in range(n):
        feelhumanArray[i] = feelHuman.value()
        time.sleep(0.001)
    #人がいたらTrueをreturn
    if sum(feelhumanArray) >= thresholdFeelhuman:
        return True
    #人がいなかったらFalseをreturn
    else:
        return False
    
#ルーターと接続する関数
def connectRouter():
    global wlan
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        time.sleep(0.5)
        print("conect..")
    print("completed!!")

#最初の画面を表示する関数
def displaySyn():
    lcd.clear()
    lcd.move_to(5, 0)
    lcd.putstr("\xc8\xaf\xc4\xdc-\xb8\xc0\xb2\xd1 \xc4")
    lcd.move_to(1, 1)
    lcd.putstr("open wheather map")
    lcd.move_to(14, 2)
    lcd.putstr("API \xb6\xd7 ")
    lcd.move_to(0, 3)
    lcd.putstr("\xbc\xde\xb6\xdd \xc4 \xc3\xdd\xb7 \xa6 \xc4\xde\xb3\xb7\xc1\xad\xb3")
    
    

if __name__=="__main__":
    main()
