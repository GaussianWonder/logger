# Required python modules:
* psutil
* keyboard
* mouse (LATEST FROM GIT)
* Platform dependent:
    * win32process, win32gui (WINDOWS)
    * AppKit (MAC)
    * wnck or gi or (ewmh or Xlib)

# What does it do?
* Logs keypresses (requires sudo on linux, see keypress lib)
* Logs mouse movement, clicks and wheel turns (requires sudo on linux, see mouse lib)
* Keeps track of time spent on each app

# Accepted args:
* 'debug': prints errors and stuff on the console
* 'json': converts the sqlite3 db to json formatted files
    * $ sudo python main.py debug (activates debug)

The data.db.zip file containes an empty sqlite3 db with every table required

Almost cross platform, no mouse support for mac