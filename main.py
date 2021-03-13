import json
import urllib.request
import base64
import gpiozero
import pyaudio
import wave
import os
import sys
import subprocess
from time import sleep
from bilibili_api import live

# glob status
CHUNK = 4096 
FORMAT = pyaudio.paInt16 
RATE = 48000  
WAVE_OUTPUT_FILENAME = "temp.wav"
# fill in your Google Speech to text API key here:
GAPI_KEY = "XXXXXXXXXXXXXXXXXXX"
sing_a_song_counter = 0
has_gifted = False


def play_vocal(vocal_path: str, vol=-2000):
    # subprocess.call(['omxplayer', '-o', 'local', vocal_path, '--vol', str(vol), '--no-osd'])
    subprocess.call(['vlc', vocal_path, 'vlc://quit'])

def detect_liveon():
    live_status = live.get_room_play_info(924973)['live_status']
    if live_status == 1:
        print("火西肆开始直播啦")
    else:
        play_vocal('./vocal_lib/没有没有2.wav')
        
    return

# pre-stored answers playing functions, feel free to add your function below
def hiccup10(): play_vocal('./vocal_lib/你们好怪啊.wav')

def hiccup(): play_vocal('./vocal_lib/打嗝.wav')

def meow(): play_vocal('./vocal_lib/猫叫.wav')

def financial():
    global has_gifted
    if has_gifted: play_vocal('./vocal_lib/不认识你.wav')
    else: play_vocal('./vocal_lib/我不.wav')

def captain(): 
    play_vocal('./vocal_lib/谢礼物.wav')
    global has_gifted
    has_gifted = True

def sing_a_song():
    global sing_a_song_counter
    if sing_a_song_counter > 1:
        play_vocal('./vocal_lib/你有病吧.wav')
    else:
        sleep(1.6)
        play_vocal('./vocal_lib/不嘛.wav')
        sing_a_song_counter += 1

def alarm(): play_vocal('./vocal_lib/就你睡得多.wav')
def movie_ticket(): play_vocal('./vocal_lib/没朋友.wav')
def nap(): play_vocal('./vocal_lib/你太快了.wav')
def confidence(): play_vocal('./vocal_lib/夸夸自己.wav')
# pre-stored answers playing functions, feel free to add your function above

def answer_query(voice_input):
    answer_dict = {
        '随便': sing_a_song,
        '再唱一遍': sing_a_song,
        '打嗝': hiccup, 
        '十个': hiccup10, 
        '10个': hiccup10, 
        '猫叫': meow, 
        '唱首歌': financial,
        '舰长': captain,
        '闹钟': alarm,
        '电影票': movie_ticket,
        '休息': nap,
        '开播': detect_liveon,
        '自己': confidence
    }

    for k, f in answer_dict.items():
        if k in voice_input:
            f()
            break

    return

# Courtesy of https://segmentfault.com/a/1190000014000349 for functionrec_fun, wav_to_text 

def rec_fun(btn, stream):
    frames = []
    stream.start_stream()
    print("recording...")
    while btn.is_pressed:
        data = stream.read(CHUNK)
        frames.append(data)

    print("finished")
    stream.stop_stream()

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(FORMAT))    
    # Returns the size (in bytes) for the specified sample format.
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    return

def wav_to_text():
    api_url = "https://speech.googleapis.com/v1/speech:recognize?key={}".format(GAPI_KEY)
    audio_file = open(WAVE_OUTPUT_FILENAME, 'rb')
    audio_b64 = base64.b64encode(audio_file.read())
    audio_b64str = audio_b64.decode()    
    # print(type(audio_b64))
    # print(type(audio_b64str))
    audio_file.close()

    voice = {
        "config":
        {
            #"encoding": "WAV",
            "languageCode": "cmn-Hans-CN",
            "speechContexts": [{
                "phrases": ["肆宝", "火西肆", "直播", "开播", "十个嗝", "上个舰长"]
            }]
        },

        "audio":
        {
            "content": audio_b64str
        }
    }

    voice = json.dumps(voice).encode('utf8')

    req = urllib.request.Request(api_url, data=voice, headers={'content-type': 'application/json'})
    response = urllib.request.urlopen(req)
    response_str = response.read().decode('utf8')
    # print(response_str)
    response_dic = json.loads(response_str)
    if ('results' not in response_dic.keys()):
        print('No sound in the request')
        return None

    transcript = response_dic['results'][0]['alternatives'][0]['transcript']
    confidence = response_dic['results'][0]['alternatives'][0]['confidence']
    print(transcript)
    
    return transcript

def assistant_pipeline(btn, audio_stream):
    rec_fun(btn, audio_stream)
    text = wav_to_text()
    # subprocess.call(['omxplayer', '-o', 'local', 'temp.wav', '--vol', '-2000', '--no-osd'])
    if text is not None:
        answer_query(text)

if __name__ == '__main__':
    os.close(sys.stderr.fileno())
    assistant_btn = gpiozero.Button(4)

    # To use PyAudio, first instantiate PyAudio using pyaudio.PyAudio(), which sets up the portaudio system.
    p = pyaudio.PyAudio()
    stream = p.open(format = FORMAT,
                    start = False,
                    channels = 1,
                    rate = RATE,
                    input = True,
                    frames_per_buffer = CHUNK)

    while True:
        print("hold the button to start recording")
        assistant_btn.wait_for_press()
        assistant_pipeline(assistant_btn, stream)
        sleep(0.1)

    stream.stop_stream()
    stream.close()
