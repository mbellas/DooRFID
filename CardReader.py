import pymysql
import MFRC522
import signal
from time import sleep

continue_reading = True
MIFAREReader = MFRC522.MFRC522()


def end_read(signal, frame):
    global continue_reading
    continue_reading = False
    print("Ctrl+C captured, ending read.")
    MIFAREReader.GPIO_CLEEN()


def connect_to_db(host, port, user, passwd, db):
    return pymysql.connect(host=host, port=port, user=user, passwd=passwd, db=db)


def disconnect_from_db(con):
    return con.close();


def authenticate_card(con, uid):
    cur = con.cursor()
    cur.execute("SELECT * FROM `rfidoordb`.`RfidCards` as card WHERE card.id=" + uid)

    if cur.rowcount == 1:
        print("AUTHENTICATION GRANTED")
        row = cur.fetchone();
        log_access(conn, row[0], row[1], '', int(row[2]))
        cur.close()
        sleep(5)
        return True
    else:
        print("AUTHENTICATION FAILURE")
        log_access(conn, uid, 'UNAUTHORIZED ACCESS', 'AUTHENTICATION FAILURE', -1)
        cur.close()
        sleep(0.5)
        return False


def log_access(con, card, name, err, counter):
    cur = con.cursor()
    cur.execute("INSERT INTO `rfidoordb`.`AccLog` (`card`, `acc`, `nam`, `err`) VALUES (" + card + ",NOW(),'" + name + "','" + err + "')")
    if counter != -1:
        count = update_counter(con, card, int(counter))
        countmsg = "{} has accessed {} times"
        print(countmsg.format(name, count))

    for row in cur:
        print(row)

    cur.close()
    con.commit()


def update_counter(con, uid, counter):
    counter = int(counter) + 1
    cur = con.cursor()
    cur.execute("""UPDATE `rfidoordb`.`RfidCards` card SET card.counter = %s WHERE card.id=%s""",(counter, uid))
    cur.close()
    con.commit()

    return counter


signal.signal(signal.SIGINT, end_read)

conn = connect_to_db('192.168.2.8', 3306, 'root', 'root', 'rfidoordb')

while continue_reading:
    (status, TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)
    if status == MIFAREReader.MI_OK:
        print("Card detected")
    (status, backData) = MIFAREReader.MFRC522_Anticoll()
    if status == MIFAREReader.MI_OK:
        # print ("Card read UID:
        # "+str(backData[0])+","+str(backData[1])+","+str(backData[2])+","+str(backData[3])+","+str(backData[4]))
        uid = ''.join(str(e) for e in backData)

        if authenticate_card(conn, uid):
            print("the auth is real")
        else:
            print("well this is embarrassing")
