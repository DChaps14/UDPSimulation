"""server.py
Retrieves the current date and time, and sends a textual representation of these
to a client program using UDP
Dan Chapman, 14/08/2020
"""
import sys
import socket
import select
from datetime import datetime

#Create dicitonaries to reference needed strings in each language
#Integers represent the month values
englishDict = {1:"January", 2:"February", 3:"March", 4:"April", 5:"May", 6:"June", 7:"July", 8:"August", 9:"September", 10:"October", 11:"November", 12:"December", "date":"Today's date is {} {}, {}", "time":"The current time is {}:{}"}

germanDict = {1:"Januar", 2:"Februar", 3:"Marz", 4:"April", 5:"Mai", 6:"Juni", 7:"Juli", 8:"August", 9:"September", 10:"Oktober", 11:"November", 12:"Dezember", "date":"Heute ist der {}. {} {}", "time":"Die Uhrzeit ist {}:{}"}

maoriDict = {1:"Kohitatea", 2:"Hui-tanguru", 3:"Poutu-te-rangi", 4:"Paenga-whawha", 5:"Haratua", 6:"Pipiri", 7:"Hongongoi", 8:"Here-turi-koka", 9:"Mahuru", 10:"Whiringa-a-muku", 11:"Whiringa-a-rangi", 12:"Hakihea", "date":"Ko te ra o tenei ra ko {} {}, {}", "time":"Ko te wa o tenei wa {}:{}"}



def getSocketNumbers():
    """Gets the three socket numbers through user input"""
    #Get the passed in arguments
    stringPortNumbers = sys.argv
    intPortNumbers = []
    #First value of stringPortNumbers is the function name
    for i in range(1, len(stringPortNumbers)):
        try:
            number = int(stringPortNumbers[i])
        except:
            #If the provided input is not a number, exit
            sys.exit("Provided input cannot be converted to an integer")
        
        if number < 1024 or number > 64000:
            sys.exit("Socket number {} not within bounds".format(i+1))
        elif number in intPortNumbers:
            sys.exit("Duplicate socket number provided")
        intPortNumbers.append(number)
    
    #Ensure the right amount of ports is added
    if len(intPortNumbers) < 3:
        sys.exit("Too little numbers provided")
    elif len(intPortNumbers) > 3:
        sys.exit("Too many numbers provided")
    else:
        return intPortNumbers
    
def bindSockets(numberList):
    """Create three different sockets and attempt to bind the socket numbers to them"""
    #Attempt to create the sockets
    try:
        englishSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        maoriSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        germanSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except:
        sys.exit("Problem creating the sockets")
    
    englishPortNo = numberList[0]
    maoriPortNo = numberList[1]
    germanPortNo = numberList[2]
    #Use the special 'any' IP Address for each socket
    try:
        englishSocket.bind(("", englishPortNo))
        maoriSocket.bind(("", maoriPortNo))
        germanSocket.bind(("", germanPortNo))
    except:
        sys.exit("Problem with binding sockets with port numbers")
    
    return englishSocket, maoriSocket, germanSocket


def unpackRequestPacket(pkt):
    """Determine what parameters were passed through the request packet
    Return error codes if unpacked values are invalid"""
    if len(pkt) != 6:
        return 1, 1, 1
    
    #Get the contents of the packet, and generate bitmasks for each value
    packet = int.from_bytes(pkt, byteorder="big")
    
    magicNumMask = 0xFFFF00000000
    packetTypeMask = 0x0000FFFF0000
    requestTypeMask = 0x00000000ffff
    
    #Unpack values
    magicNumber = ((packet & magicNumMask) >> 32)
    packetType = ((packet & packetTypeMask) >> 16)
    requestType = ((packet & requestTypeMask))
    
    #Check that all values are valid, and pass back the current date and time
    if magicNumber != 0x497E:
        return 2, 2, 2
    elif packetType != 0x0001:
        return 3, 3, 3
        
    currentDate = datetime.date(datetime.now()).strftime("%Y-%m-%d")
    currentTime = datetime.time(datetime.now()).strftime("%H:%M")
    
    if requestType == 0x0001:
        return "date", currentDate, currentTime
    elif requestType == 0x0002:
        return "time", currentDate, currentTime
    else:
        return 4, 4, 4
    
def generateResponsePacket(pkt, text, textLen, language, dateNums, timeNums):
    """Generate a response packet as a bytearray""" 
    magicNumber = 0x497E
    packetType = 0x0002
    #Determine the appropriate language code
    if language == "english":
        languageCode = 0x0001
    elif language == "maori":
        languageCode = 0x0002
    elif language == "german":
        languageCode = 0x0003
    
    #Create a table containing all the values that are to be stored in 2 bytes
    twoByteTable = [magicNumber, packetType, languageCode, dateNums[0]]
    
    #Create a table containing all values to be stored in 1 byte
    oneByteTable = dateNums[1:] + timeNums + [textLen]
    
    #Convert each value in those tables to the appropriate number of bytes
    #Place these bytes in the appropriate place in the packet
    startPos = 0
    endPos = 2
    for num in twoByteTable:
        pkt[startPos:endPos] = num.to_bytes(2, byteorder="big")
        startPos += 2
        endPos += 2
    
    #Adjust the end position for the one-byte values
    endPos -= 1
    for num in oneByteTable:
        pkt[startPos:endPos] = num.to_bytes(1, byteorder="big")
        startPos += 1
        endPos += 1
        
    pkt[startPos:startPos+textLen] = text
    return pkt


def generateInfo(requestType, currentDate, currentTime, languageDict, language):
    """Retrieves and fills in the textual representation of the current date or time
    Also returns individual integer values representing the date or time"""
    
    #Find the seperate values of the current date and time
    dateParts = currentDate.split("-")
    yearNum = int(dateParts[0])
    monthNum = int(dateParts[1])
    dayNum = int(dateParts[2])

    timeParts = currentTime.split(":")
    hourNum = int(timeParts[0])
    minuteNum = int(timeParts[1])
    
    #Generate the appropriate text string depending on the client's request
    #requestType will always either be date or time - checked before passing into function
    if requestType == "date":
        dateString = languageDict.get("date")
        monthString = languageDict.get(int(dateParts[1]))
        #Change the formatting of the text slightly for a German representation
        if language == "german":
            returnString = dateString.format(dayNum, monthString, yearNum)
        else:
            returnString = dateString.format(monthString, dayNum, yearNum)
    else:
        timeString = languageDict.get("time")
        #Add an additional 0 for presentation purposes if the minute is small enough
        if minuteNum < 10:
            returnString = timeString.format(hourNum, "0"+str(minuteNum))
        else:
            returnString = timeString.format(hourNum, minuteNum)
    
    return returnString, [yearNum, monthNum, dayNum], [hourNum, minuteNum]
    

def main():
    """Main function of the server
    Contains the infinite loop for receiving requests"""
    
    #Get the socket numbers form the user and attempt to bind these to three sockets
    socketNumbers = getSocketNumbers()
    englishSocket, maoriSocket, germanSocket = bindSockets(socketNumbers)
    
    #Infinite loop for receiving requests
    while True:
        #Wait for a socket to receive a request indefinitely
        try:
            ready = select.select([englishSocket, maoriSocket, germanSocket], [], [])
            readySocket = ready[0][0]
        except:
            print("Problem occured while waiting for a socket to receive a request")
            continue
        
        #Determine what langauge to use, depending on the receiving socket
        if readySocket == englishSocket:
            language = "english"
            languageDict = englishDict
        elif readySocket == maoriSocket:
            language = "maori"
            languageDict = maoriDict
        elif readySocket == germanSocket:
            language = "german"
            languageDict = germanDict
        
        #Receive the packet and sender address from the socket
        try:
            packet, address = readySocket.recvfrom(6)
            #Create a bytearray to store the packet in
            message = bytearray(6)
            message[0:6] = packet
        except:
            print("Problem receiving information from the socket")
            continue
        
        #Unpack the message and retrieve the relevant information
        requestType, currentDate, currentTime = unpackRequestPacket(message)
        #Error checks - discard the packet and its associated IP address if checks fail
        if requestType == 1:
            print("Packet a bigger size than expected (>6 bytes)")
            del message, address
            continue
        elif requestType == 2:
            print("Magic number doesn't match up")
            del message, address
            continue            
        elif requestType == 3:
            print("Unacceptable packet type")
            del message, address
            continue            
        elif requestType == 4:
            print("Request type not available")
            del message, address           
            continue            
        
        #Get the requested textual representation, and get integer values of the current date and time
        textString, dateNums, timeNums = generateInfo(requestType, currentDate, currentTime, languageDict, language)
        
        #Encode the text, and ensure it isn't too large
        textBytes = textString.encode('utf-8')
        textLen = len(textBytes)
        if textLen > 255:
            print("Text length is too large")
            del message, address #Discard packet and address
            continue
        
        #Create the response packet buffer, and fill it with relevant information
        responseBuffer = bytearray(13 + textLen)
        sendingPacket = generateResponsePacket(responseBuffer, textBytes, textLen, language, dateNums, timeNums)
        #Send the filled packet to the client through the original socket
        try:
            readySocket.sendto(sendingPacket, address)
        except:
            print("Problem sending the prepared packet to the user's address")
            del sendingPacket, responseBuffer, address #Discard the prepared packet, and the sending address
            continue
        

main()
