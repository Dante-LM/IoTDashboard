import mariadb 

    # Host name of the database server
Host = "localhost"
    
    # User name of the database server
User = "root"       
      
    # Password for the database user
Password = ""  
 
def createDB():
    conn  = mariadb.connect(host=Host, user=User, password=Password)

    cur  = conn.cursor()
      
    # creating database 
    cur.execute("CREATE DATABASE IoT")

def createTable():
    mydb = mariadb.connect(
      host="localhost",
      user="root",
      password="",
      database="IoT"
    )

    mycursor = mydb.cursor()

    mycursor.execute("CREATE TABLE users (rfid bigint(20) NOT NULL UNIQUE, userName VARCHAR(16), lightThreshhold int(3), tempThreshhold int(2))")

def insert():
    mydb = connectDB()
    cursor = mydb.cursor()
    try: 
        query = ("INSERT INTO users (rfid, userName, lightThreshhold, tempThreshhold) VALUES (%d, %s, %d, %d)")
        val = (9996217154, 'Dante', 30, 50)
        cursor.execute(query, val)
    except mariadb.Error as e: 
        print(f"Error: {e}")
    mydb.commit()

def connectDB():
    conn = mariadb.connect(
    user="root",
    password="",
    host="localhost",
    database="IoT")
    return conn

def selectAll():
    mydb = connectDB()
    cursor = mydb.cursor()
    rfidValue = 9996217154
    cursor.execute("SELECT * FROM users WHERE rfid =?", (rfidValue,))
    record = cursor.fetchone()
    print(record[0])
    print(record[1])
    print(record[2])
    print(record[3])

def dropTable():
    mydb = connectDB()
    cursor = mydb.cursor()
    try:
        cursor.execute("DROP TABLE users")
    except mariadb.Error as e: 
        print(f"Error: {e}")
    mydb.commit()

dropTable()
createTable()
insert()
selectAll()