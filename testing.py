import pyodbc


server = 'SQL-SSRS'
database = 'Appz'
try:

    cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';Trusted_Connection=yes')
    cursor = cnxn.cursor()
    query = "SELECT [Server] as serv,Description FROM Onestock_Clients"
    cursor.execute(query)
    clients = {}
    for row in cursor.fetchall():
        clients[row[1]] = row[0]
    print(clients)
except Exception as e:
    print(e)