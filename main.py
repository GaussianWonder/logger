# Main event loop
import threading, signal, sys, sqlite3
from time import sleep
from queue import Queue
from logger import getActiveWindow, KeyLog, MouseLog, ActivityLog
from SQLconverter import convert as SQLconvert

#Open connection to db
conn = sqlite3.connect('data.db')

#Event queue
eventQueue = Queue()

#Thread locks
keyLock     = threading.Lock()
mouseLock   = threading.Lock()
procLock    = threading.Lock()

#Loggers
# keyLogger   = KeyLog(eventQueue, keyLock)
# keyLogger.start()
# mouseLogger = MouseLog(eventQueue, mouseLock)
# mouseLogger.start()
# actLogger = ActivityLog(eventQueue, procLock)
# actLogger.start()

def prepareArray(evt, arr, fv):
    #See if evt is already in the list
    try:
        #if so add 1 to count
        fv[arr.index(evt)] += 1
    except:
        #otherwise make a new evt with count = 1
        arr.append(evt)
        fv.append(1)

#template -> range(0, n) => index; -1 => count
def insertArray(arr, fv, query, template):
    records = []
    for rIndex, record in enumerate(arr):
        records.append(tuple(
            [ record[index] if index >= 0 else fv[rIndex] for index in template ]
        ))

    c = conn.cursor()
    c.executemany(query, records)

    conn.commit()
    pass

def main():
    while True:
        #empty and process the event queue
        keyList     = []
        keyFv       = []

        mMoveList  = []
        mMoveFv    = []

        mWheelList  = []
        mWheelFv    = []

        mClickList  = []
        mClickFv    = []

        appAdd      = []
        with keyLock, mouseLock, procLock:
            while eventQueue.empty() == False:
                #process each event
                evt = eventQueue.get()
                if evt['type'] == 'keyboard':       #Keyboard
                    prepareArray(
                        [evt['name'], evt['code'], evt['window']],
                        keyList,
                        keyFv
                    )
                elif evt['type'] == 'mouse':
                    if evt['x'] is not '':          #MouseMove
                        prepareArray(
                            #The coresponding 25x25 pixel square
                            [int(evt['x'] / 25), int(evt['y'] / 25)],
                            mMoveList,
                            mMoveFv
                        )
                    elif evt['button'] is not '':   #MouseClick
                        prepareArray(
                            [evt['button']],
                            mClickList,
                            mClickFv
                        )
                    elif evt['delta'] is not '':    #MouseWheel
                        prepareArray(
                            [evt['delta']],
                            mWheelList,
                            mWheelFv
                        )
                elif evt['type'] == 'app':
                    prepareArray(
                        [evt['name'], evt['start'], evt['end']],
                        appAdd,
                        []
                    )
        
        # Insert prepared arrays to db
        if len(keyFv) > 0:
            insertArray(
                keyList,
                keyFv,
                """
                    INSERT OR REPLACE INTO keystrokes (id, cnt, name, code, window) 
                    VALUES (
                        (
                            SELECT id
                            FROM keystrokes
                            WHERE code = ? AND window = ?
                        ), 
                        COALESCE(
                            (
                                SELECT cnt
                                FROM keystrokes
                                WHERE code = ? AND window = ?
                            ) + ?,
                            ?
                        ),
                        lower(?),
                        ?,
                        ?
                    );
                """,
                (1, 2, 1, 2, -1, -1, 0, 1, 2)
            )
        if len(mMoveList) > 0:
            insertArray(
                mMoveList,
                mMoveFv,
                """
                    INSERT OR REPLACE INTO mMove (id, x, y, cnt) 
                    VALUES (
                        (
                            SELECT id
                            FROM mMove
                            WHERE x = ? AND y = ?
                        ),
                        ?,
                        ?,
                        COALESCE(
                            (
                                SELECT cnt
                                FROM mMove
                                WHERE x = ? AND y = ?
                            ) + ?,
                            ?
                        )
                    );
                """,
                (0, 1, 0, 1, 0, 1, -1, -1)
            )
        if len(mClickList) > 0:
            insertArray(
                mClickList,
                mClickFv,
                """
                    INSERT OR REPLACE INTO mClick (id, button, cnt) 
                    VALUES (
                        (
                            SELECT id
                            FROM mClick
                            WHERE button = ?
                        ),
                        ?,
                        COALESCE(
                            (
                                SELECT cnt
                                FROM mClick
                                WHERE button = ?
                            ) + ?,
                            ?
                        )
                    );
                """,
                (0, 0, 0, -1, -1)
            )
        if len(mWheelList) > 0:
            insertArray(
                mWheelList,
                mWheelFv,
                """
                    INSERT OR REPLACE INTO mWheel (id, delta, cnt) 
                    VALUES (
                        (
                            SELECT id
                            FROM mWheel
                            WHERE delta = ?
                        ),
                        ?,
                        COALESCE(
                            (
                                SELECT cnt
                                FROM mWheel
                                WHERE delta = ?
                            ) + ?,
                            ?
                        )
                    );
                """,
                (0, 0, 0, -1, -1)
            )
        if len(appAdd) > 0:
            insertArray(
                appAdd,
                [],
                """
                    INSERT INTO apps (name, start_time, end_time) 
                    VALUES (?, ?, ?);
                """,
                (0, 1, 2)
            )

        #wait 10 seconds until processing the next event stack
        sleep(10)

def exit_gracefully(signum, frame):
    #Original SIGINT handler
    signal.signal(signal.SIGINT, original_sigint)
    try:
        if input("\nDo you really want to quit? (y/N)> ").lower().startswith('y'):
            sys.exit(1)
    except KeyboardInterrupt:
        print("Ok ok, quitting")
        try:
            conn.commit()
            conn.close()
        except:
            pass
        sys.exit(1)

    #Restore the exit gracefully handler here    
    signal.signal(signal.SIGINT, exit_gracefully)

if __name__ == '__main__':
    try:
        JSON = sys.argv[1:].index("json")
        #Request to convert sqlite3 db to json file
        if JSON >= 0:
            SQLconvert("data.db")
            sys.exit(0)
    except:
        pass

    #Store the original SIGINT handler
    original_sigint = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, exit_gracefully)
    main()

    # UNNECESSARY
    # keyLogger.join()
    # mouseLogger.join()
    # actLogger.join()