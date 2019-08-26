import sys, psutil, threading, keyboard, mouse
from time import sleep, time
from queue import Queue

DEBUG = None

args  = sys.argv[1:]
try:
    DEBUG = args.index('debug')
except:
    DEBUG = None
    pass

#Functions to get the active window
def getActiveWindow_Linux():
    try:
        import wnck
    except ImportError:
        if DEBUG is not None:
            print("wnck is not installed")
        wnck = None
    
    if wnck is not None:                #TRY WITH WNCK
        screen = wnck.screen_get_default()
        # Recommended per wnck documentation
        screen.force_update()
        window = screen.get_active_window()
        if window is not None:
            return psutil.Process(window.get_pid()).name()
    else:                               
        try:
            import gi
            gi.require_version("Gtk", "3.0")
            from gi.repository import Gtk, Wnck
            G = "Installed"
        except ImportError:
            if DEBUG is not None:
                print("gi.repository not installed")
            G = None
        
        if G is not None:               #TRY WITH GTK WNCK
            # Necessary if not using a Gtk.main() loop
            Gtk.init([]) 
            screen = Wnck.Screen.get_default()
            # Recommended per Wnck documentation
            screen.force_update()
            active_window = screen.get_active_window()
            pid = active_window.get_pid()
            return psutil.Process(pid).name()
        else:                           
            try:
                from ewmh import EWMH
                ewmh = EWMH()
            except ImportError:
                if DEBUG is not None:
                    print("EWMH not installed")
                ewmh = None
            
            if ewmh is not None:        #TRY WITH EXTENDED XLib
                win = ewmh.getActiveWindow()
                return psutil.Process(ewmh.getWmPid(win)).name()
            else:                       
                try:
                    import Xlib.display
                    X = "Installed"
                except ImportError:
                    X = None
                
                if X is not None:       #TRY WITH Xlib (different result)
                    display = Xlib.display.Display()
                    window = display.get_input_focus().focus
                    pid = window.get_wm_pid
                    wmname = window.get_wm_name()
                    wmclass = window.get_wm_class()
                    if wmclass is None and wmname is None:
                        window = window.query_tree().parent
                        wmname = window.get_wm_name()
                    
                    return wmname
    #If nothing happened
    return None

def getActiveWindow_Windows():
    try:
        import win32process, win32gui
        win = "Installed"
    except ImportError:
        if DEBUG is not None:
            print("win32process || win32gui is not installed")
        win = None

    if win is not None:
        try:
            # This produces a list of PIDs active window relates to
            pid = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())
            # pid[-1] is the most likely to survive last longer
            return psutil.Process(pid[-1]).name()
        except:
            pass
    return None

# NOT TESTED, i don't own a freqing mac
def getActiveWindow_Mac():
    # NOT TESTED, i don't own a freqing mac
    try:
        from AppKit import NSWorkspace
        return (NSWorkspace.sharedWorkspace()
                            .activeApplication()['NSApplicationName'])
    except ImportError:
        if DEBUG is not None:
            print("I think AppKit is missing but idk")
    return None

def getActiveWindow():
    if sys.platform in ['linux', 'linux2']:
        return getActiveWindow_Linux()
    elif sys.platform in ['Windows', 'win32', 'cygwin']:
        return getActiveWindow_Windows()
    elif sys.platform in ['Mac', 'darwin', 'os2', 'os2emx']:
        return getActiveWindow_Mac()
    else:
        if DEBUG is not None:
            print("sys.platform={platform} is unknown."
              .format(platform=sys.platform))
        if DEBUG is not None:
            print(sys.version)
         
    return None


class KeyLog(threading.Thread):
    def __init__(self, evQ, lock):
        threading.Thread.__init__(self, daemon=True)
        self.evQ  = evQ
        self.lock = lock

    def pushToQueue(self, e):
        #new key event
        keyE = {
            'type':     'keyboard',
            'name':     e.name,
            'code':     e.scan_code,
            'window':   getActiveWindow()
        }

        #put it in the queue
        with self.lock:
            self.evQ.put(keyE)

    def run(self):
        keyboard.on_release(self.pushToQueue)

class MouseLog(threading.Thread):
    def __init__(self, evQ, lock):
        threading.Thread.__init__(self, daemon=True)
        self.evQ  = evQ
        self.lock = lock
    
    def pushToQueue(self, e):
        mouseE = {
            'type': 'mouse',
            'button': '',
            'x': '',
            'y': '',
            'delta': '',
        }

        if type(e) is mouse.MoveEvent:
            mouseE['x'] = e.x
            mouseE['y'] = e.y
        elif type(e) is mouse.ButtonEvent:
            if e.event_type == 'down':
                return None
            mouseE['button'] = e.button
        else:
            mouseE['delta']   = e.delta

        #put it in the queue
        with self.lock:
            self.evQ.put(mouseE)

    def run(self):
        mouse.hook(self.pushToQueue)

class ActivityLog(threading.Thread):
    def __init__(self, evQ, lock):
        threading.Thread.__init__(self, daemon=True)
        self.evQ  = evQ
        self.lock = lock
        self.currentActivity = ''
        self.stamp = -1
    
    def pushToQueue(self, e):
        actE = {
            'type'  : 'app',
            'name'  : e[0],
            'start' : e[1],
            'end'   : e[2]
        }

        with self.lock:
            self.evQ.put(actE)

    def run(self):
        self.currentActivity = getActiveWindow()
        self.stamp = time()

        while True:
            act = getActiveWindow()

            #new activity is focused
            if self.currentActivity != act: 
                self.pushToQueue((self.currentActivity, self.stamp, time()))

                self.currentActivity = act
                self.stamp = time()
                
            sleep(3)