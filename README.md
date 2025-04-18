# IoTデジタル時計の開発

## コンセプト
バックライト付きデジタル時計に加えて天気予報（3時間ごとの天気・降水確率）・湿度・温度表示付きの  
高性能IoTデジタル時計の開発

## 機構設計
筐体はFusionを用いて設計を行い，3Dプリンタで出力を行った．  

## システム・センサ構成
CPUにはRaspberryPiPicoWを用いる．  
電力はUSB接続から得る．  
センサは，cdsセル(明るさセンサ)・温湿度計・人感センサを接続する．

常時ディスプレイに情報を表示させる必要はないため，人感センサにより  
人を検知すると30秒間ディスプレイに情報を表示する．  
表示する情報は，年月日・秒単位の時刻・温度・湿度・天気・降水確率である．  

年月日と時刻は1日毎に更新して自動的に誤差を修正する．  
温湿度はセンサをCPUに繋げることで取得する．  
天気予報はOpen weather map ( https://openweathermap.org/ ) の  
APIを用いて30分毎に更新し，3時間毎の天気ならびに降水確率を取得する．  

また，夜間はディスプレイを見ることができないため，明るさセンサを用いて   
明るさが一定以下となった時はディスプレイに付いているバックライトを制御し点灯させる．  

## その他
制作期間は約2週間
![Image](https://github.com/user-attachments/assets/90ac9135-8066-47da-8bb6-5308b8e9ab50)
