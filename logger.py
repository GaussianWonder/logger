import sys, time, psutil, threading, keyboard
from queue import Queue

class Event():
    pass

#Functions to get the active window
def getActiveWindow_Linux():
    try:
        import wnck
    except ImportError:
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
        print("sys.platform={platform} is unknown."
              .format(platform=sys.platform))
        print(sys.version)
         
    return None


class KeyLog(threading.Thread):
    def __init__(self, evQ, lock):
        threading.Thread.__init__(self)
        self.evQ  = evQ
        self.lock = lock

    def print_pressed_keys(self, e):
        #new key event
        keyE = Event()
        keyE.type = 'keyboard'
        keyE.name = e.name
        keyE.code = e.scan_code
        keyE.time = e.time

        #put it in the queue
        with self.lock:
            self.evQ.put(keyE)

    def run(self):
        keyboard.on_release(self.print_pressed_keys)