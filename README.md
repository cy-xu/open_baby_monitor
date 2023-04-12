# Open Baby Monitor

An open-source baby monitor that uses a stereo camera to provide a live video feed of the baby's crib, so I can keep an eye on the little thing while working. I also want to track the baby's sleep and send out alerts if necessary.

Goals:
 - A live video feed of the baby's crib
 - Tracks the baby's movement using both temporal and depth information
 - Detects if the baby is in the crib and logs her sleep time and quality
 - Detects the baby's face and send an alert if the baby is face down
 - Tracks the room temperature and humidity and check if there is a correlation with the baby's sleep quality

DepthAI


## Setup

### Install DepthAI to support the OAK-D stereo camera
https://docs.luxonis.com/en/latest/pages/tutorials/first_steps/#first-steps-with-depthai

### Install requirements
```bash
python -m pip install -r requirements.txt
```

### Run

```bash
python streaming_server.py
gunicorn --workers 1 --threads 1 --bind 0.0.0.0:5000 streaming_server:app
```


### TODO:
 - [ ] An infrared camera to see in the dark would be nice


### References:
 -

### License


### Notes:

Mac OS Catalina ssh issue: https://discussions.apple.com/thread/253932000
In Terminal, type in and execute the following:
sudo launchctl load -w /System/Library/LaunchDaemons/ssh.plist
