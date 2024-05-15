# Control smart glasses with Tap XR
## How to use / setup

#### Backend
/server holds all of the backend code. On an Ubuntu server, clone the repo, make a virtualenv, install the dependencies (`pip3 install -r requirements.txt`), and run it with `python3 server.py`.

#### Android app

/android_app holds all of the frontend/client code that runs on any Android 12+ device. Clone it, open in Android studio, and flash with Android studio to your Android 12+ device. This requires two local libraries, so make sure you clone with submodules. Edit the Config.java file to point to your backend domain/IP.

#### Hardware

This system requires the Vuzix Z100 smart glasses and the TapXR gesture recognition device. It's not reccomended you set this up unless you have the hardware on hand.
