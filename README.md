# Open Baby Monitor

My passion project as a new parent! Rather than buying more gear, why not repurpose old tech into a baby monitor that fits my needs? Here's the scoop:

- Web Access: Keep an eye on her crib from anywhere, on any device.  
- Sleep Tracker: A deep-learning model checks whether she is in the crib and tracks her sleep quality.  
- Camera Control: Swap video feeds for different lighting conditions, or even flash on some light.  
- Secure: Password-protected.  
- Wallet-friendly: All you need is an old Android phone and a computer.

[Demo video](https://www.youtube.com/watch?v=y23ytcYdjw0&ab_channel=CYXu)

<img src="assets/interface_demo.jpg" alt="web interface" width="500px">

### Goals:
 - [x] A password protected live video feed of the baby's crib
 - [x] Detects the baby's movement using temporal information
 - [x] Simple camera control, like auto-focus, toggle flashlight, save image.
 - [x] Detects if the baby is in the crib
 - [x] Automatically logs her sleep duration and quality
 - [ ] Detects if the baby's airway is obstructed (face down or covered)
 - [ ] Tracks the room temperature and humidity, so I can analyze any correlation with the baby's sleep quality
 - [ ] ~~Detects the baby's movement using depth information~~


## Setup

### Install requirements
```bash
python -m pip install -r requirements.txt
```

### Run

```bash
python streaming_server.py
# ./ngrok http 5000
# gunicorn --workers 1 --threads 1 --bind 0.0.0.0:5000 streaming_server:app
```

### TODO:
 - [x] Password protect the web app (flask_httpauth)
 - [x] Broadcast to the internet with ngrok
 - [x] Multi-camera switching
 - [x] Use uuid to store session specific data like selected camera
 - [x] Support Android phone's better low-light camear via IP Webcam
 - [x] Now handles disconnection and automatic reconnection
 - [x] Image data collection now works
 - [x] Add a button to take a picture
 - [x] "baby in crib" detection model via Google's [Teachable Machine](https://teachablemachine.withgoogle.com/)
 - [x] The light now turns off after 10 seconds
 - [ ] Add a button to record a video
 - [ ] An infrared camera for the dark would be nice


### References:
 - [DepthAI to support the OAK-D stereo camera](https://docs.luxonis.com/en/latest/pages/tutorials/first_steps/#first-steps-with-depthai)
 - [DroidCam controls](https://github.com/AiueoABC/Play_with_DroidCam/blob/master/capture.py)
 - [IP Webcam control](https://community.home-assistant.io/t/android-ip-webcam-as-a-camera-plus-sensors/10566)
 - [A small arm I used to mount the phone to the crib (Amazon)](https://www.amazon.com/gp/product/B089FWTFNX/ref=ppx_yo_dt_b_asin_title_o08_s00?ie=UTF8&psc=1)

### License


### Notes:

 - The OAK-D stereo camera is nice to have, but the depth info is too noisy in the dark. My old Pixel 2, on the other hand, provides a much better low-light performance, so I switched.

 - user name and pin are saved in the environment variables (.env), add this file to .gitignore to avoid saving sensitive information in the code repository

 - Mac OS Catalina ssh issue: https://discussions.apple.com/thread/253932000. In Terminal, type in and execute the following: `sudo launchctl load -w /System/Library/LaunchDaemons/ssh.plist`
