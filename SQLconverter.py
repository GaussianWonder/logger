import sqlite3, json

def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

def convert(dbPath):
    #Connect to the SQlite database
    connection = sqlite3.connect(dbPath)
    connection.row_factory = dict_factory

    cursor = connection.cursor()

    #Select all the tables from the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    #For each of the bables, select all the records from the table
    for table_name in tables:
            #Rable_name = table_name[0]
            conn = sqlite3.connect(dbPath)
            conn.row_factory = dict_factory
            
            curr = conn.cursor()
            
            curr.execute("SELECT * FROM " + table_name['name'])
            
            #Fetch all or one we'll go for all.
            results = curr.fetchall()
            
            #Generate and save JSON files with the table name for each of the database tables
            with open(table_name['name']+'.json', 'w') as the_file:
                the_file.write(json.dumps(results, indent=4, sort_keys=True))

    connection.close()

    







