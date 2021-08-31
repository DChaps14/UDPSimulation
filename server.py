import sys
import socket
import select

germanDict = {"January":"Januar", "February":"Februar", "March":"Marz", "April":"April", "May":"Mai", "June":"Juni", "July":"Juli", "August":"August", "September":"September", "October":"Oktober", "November":"November", "December":"Dezember", "Date":"Heute ist der {}. {} {}"}

maoriDict = {"January":"Kohitatea", "February":"Hui-tanguru", "March":"Poutu-te-rangi", "April":"Paenga-whawha", "May":"Haratua", "June":"Pipiri", "July":"Hongongoi", "August":"Here-turi-koka", "September":"Mahuru", "October":"Whiringa-a-muku", "November":"Whiringa-a-rangi", "December":"Hakihea", "Date":"Ko te ra o tenei ra ko {} {}, {}"}


def getSocketNumbers():
    numbers = input("Please input three different socket numbers (between 1,024 and 64,000): ")
    stringList = numbers.split()
    numberList = []
    for i in range(len(stringList)):
        try:
            number = int(stringList[i])
        except:
            sys.exit("Provided input cannot be converted to an integer")
        
        if number < 1024 or number > 64000:
            sys.exit("Socket number {} not within bounds".format(i+1))
        elif number in numberList:
            sys.exit("Duplicate socket number provided")
        numberList.append(number)
        
    if len(numberList) < 3:
        sys.exit("Too little numbers provided")
    elif len(numberList) > 3:
        sys.exit("Too many numbers provided")
    else:
        return numberList
    
def bindSockets(numberList):
    try:
        englishSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        maoriSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        germanSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except:
        sys.exit("Problem creating the sockets")
    
    englishPortNo = numberList[0]
    maoriPortNo = numberList[1]
    germanPortNo = numberList[2]
    try:
        englishSocket.bind(("", englishPortNo))
        maoriSocket.bind(("", maoriPortNo))
        germanSocket.bind(("", germanPortNo))
    except:
        sys.exit("Problem with binding sockets with port numbers")
    
    return englishSocket, maoriSocket, germanSocket


def unpackRequestPacket(pkt):
    
    #TODO: Every return -1 needs to be print an error statement
    
    if len(pkt) != 6:
        return -1
    
    packet = int.from_bytes(pkt, byteorder="big")
    
    magicNumMask = 0xFFFF00000000
    packetTypeMask = 0x0000FFFF0000
    requestTypeMask = 0x00000000ffff
    
    magicNumber = ((packet & magicNumMask) >> 32)
    packetType = ((packet & packetTypeMask) >> 16)
    requestType = ((packet * requestTypeMask))
    
    if magicNumber != 0x497E or packetType != 0x0001:
        return -1
    
    if requestType == 0x0001:
        return 1
    elif requestType == 0x0002:
        return 2
    else:
        return -1
    
def generateResponsePacket():
    """Generate a response packet as a bytearray"""
    packet = bytearray()
    
    magicNumber = 0x497E
    packetType = 0x0002
    
    
    
def main():
    socketNumbers = getSocketNumbers()
    englishSocket, maoriSocket, germanSocket = bindSockets(socketNumbers)
    while True:
        print("waiting")
        ready = select.select([englishSocket, maoriSocket, germanSocket], [], [])
        readySockets = ready[0]
        print(readySockets)
        

main()