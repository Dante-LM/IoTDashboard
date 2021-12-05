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

    mycursor.execute("CREATE TABLE users (rfid bigint(20) NOT NULL UNIQUE, userName VARCHAR(16), profilePic VARCHAR(255))")

def insert():
    mydb = connectDB()
    cursor = mydb.cursor()
    try: 
        query = ("INSERT INTO users (rfid, userName, profilePic) VALUES (%d, %s, %s)")
        val = (9996217154, 'Christian', 'Something')
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

# createDB()
# createTable()
# insert()
selectAll()
