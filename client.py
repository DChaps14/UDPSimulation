"""client.py
Requests and prints the current date or time from a server program using UDP
Dan Chapman, 14/08/2020
"""
import sys
import socket
import select

def closeSocket(socketToClose):
    """Closes the socket when the client program is finished or is exited"""
    #Close the socket
    socketToClose.close()

def getParameters():
    """Retrieves the inputs provided by the user through an argv call"""
    #Get the inputs from the system arguments
    inputs = sys.argv
    try:
        textType = inputs[1].lower()
        ipAddress = inputs[2]
        portNumber = int(inputs[3])
    except IndexError:
        sys.exit("Insufficient inputs provided")
        
    #Check whether the textType is appropriate
    if textType != "date" and textType != "time":
        sys.exit("'Date' or 'time' not provided")

    try:
        #IP Address will be the first value in the final entry of the first information panel returned
        foundAddress = socket.getaddrinfo(ipAddress, None)[0][-1][0]
    except:
        sys.exit("Could not get address information about provided host")
        
    #Perform checks on the portNumber input
    if portNumber > 64000 or portNumber < 1024:
        sys.exit("Port number not between 1024 and 64000")
    
    return textType, foundAddress, portNumber
    
    
def formRequestPacket(request):
    """Forms a request packet to be sent to the server"""
    magicNumber = 0x497E
    packetType = 0x0001
    #Assign the appropriate request type
    #Checks already conducted in input phase
    if request == "date":
        requestType = 0x0001
    elif request == "time":
        requestType = 0x0002
    
    #Create and fill out the bytearray
    requestPacket = bytearray(6)
    requestPacket[0:2] = magicNumber.to_bytes(2, byteorder="big")
    requestPacket[2:4] = packetType.to_bytes(2, byteorder="big")
    requestPacket[4:6] = requestType.to_bytes(2, byteorder="big")
    return requestPacket
    


def checkPacket(pkt, socketUsed):
    """Checks each value of the received packet for any transmission errors
    Returns an unpacked value for every packet header segment
    Socket is included in parameters in case it needs to be closed"""

    packetBitLength = len(pkt)*8
    
    #Generate the masks for checking information
    magicNumMask = int("0b" + "1"*16 + "0"*(packetBitLength-16), 2)
    packetTypeMask = int("0b" + "0"*16 + "1"*16 + "0"*(packetBitLength-32), 2)
    languageMask = int("0b" + "0"*32 + "1"*16 + "0"*(packetBitLength-48), 2)
    yearMask = int("0b" + "0"*48 + "1"*16 + "0"*(packetBitLength-64), 2)
    monthMask = int("0b" + "0"*64 + "1"*8 + "0"*(packetBitLength-72), 2)
    dayMask = int("0b" + "0"*72 + "1"*8 + "0"*(packetBitLength-80), 2)
    hourMask = int("0b" + "0"*80 + "1"*8 + "0"*(packetBitLength-88), 2)
    minuteMask = int("0b" + "0"*88 + "1"*8 + "0"*(packetBitLength-96), 2)
    lengthMask = int("0b" + "0"*96 + "1"*8 + "0"*(packetBitLength-104), 2)
    
    packetContents = int.from_bytes(pkt, byteorder="big")
    
    #Perform checks on each value that should be present with the corresponding mask
    magicNum = ((packetContents & magicNumMask) >> (packetBitLength-16))
    if magicNum != 0x497E:
        closeSocket(socketUsed)
        sys.exit("Magic number not correct")
        
    packetType = ((packetContents & packetTypeMask) >> (packetBitLength-32))
    if packetType != 0x0002:
        print(packetType)
        closeSocket(socketUsed)
        sys.exit("Packet type not a DT-Response packet")
    
    languageCode = ((packetContents & languageMask) >> (packetBitLength-48))
    if languageCode != 0x0001 and languageCode != 0x0002 and languageCode != 0x0003:
        closeSocket(socketUsed)
        sys.exit("Language code does not match a known language")
        
    year = ((packetContents & yearMask) >> (packetBitLength-64))
    if year > 2100:
        closeSocket(socketUsed)
        sys.exit("Year provided too great")
        
    month = ((packetContents & monthMask) >> (packetBitLength-72))
    if month > 12 or month < 1:
        closeSocket(socketUsed)
        sys.exit("Month does not exist")
        
    day = ((packetContents & dayMask) >> (packetBitLength-80))
    if day > 31 or day < 1:
        closeSocket(socketUsed)
        sys.exit("Day does not exist")
        
    hour = ((packetContents & hourMask) >> (packetBitLength-88))
    if hour < 0 or hour > 23:
        closeSocket(socketUsed)
        sys.exit("Hour is outside of 24-hour bounds")
        
    minute = ((packetContents & minuteMask) >> (packetBitLength-96))
    if minute < 0 or minute > 59:
        closeSocket(socketUsed)
        sys.exit("Minute value is not within one hour")
    
    textLength = ((packetContents & lengthMask) >> (packetBitLength-104))
    if len(pkt) != (13 + textLength):
        closeSocket(socketUsed)
        sys.exit("Total length inconsistent with provided length value")
    
       
    return [magicNum, packetType, languageCode, year, month, day, hour, minute, textLength]


def printPacketText(pkt, detailTable):
    """Prints the details of the received packet, each on an individual line"""
    #Create a mask for the text, and unpack the packet
    textLength = detailTable[-1]
    textMask = int("0b" + "0"*(13*8) + "1"*(textLength*8), 2)
    packetContents = int.from_bytes(pkt, byteorder="big")
    
    #Create a table containing strings that describe the packet's details
    titleTable = ["Magic Number: ", "Packet Type Number: ", "Language Code: ", "Current Year: ",
                  "Current month: ", "Current day: ", "Current hour: ", "Current minute: ",
                  "Byte length of text: "]
    
    #Print each detail within the packet header
    for i in range(len(titleTable)):
        print(titleTable[i] + str(detailTable[i]))
    
    #Print the textual representation of the current date/time
    text = (packetContents & textMask)
    textBytes = text.to_bytes(textLength, byteorder="big")
    print("Textual Representation: "+textBytes.decode("utf-8", "strict"))
    
def main():
    """Main method of the client program"""
    #Retrieve the user's requests
    textType, IPAddress, portNumber = getParameters()
    #Attempt to create the socket, and create the packet
    try:
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except:
        sys.exit("Problem occured while creating the socket")
    
    packet = formRequestPacket(textType)
    
    #Send the prepared packet, and wait one second for a reply
    #If the returned value is empty, no response has been received in that time
    try:
        clientSocket.sendto(packet, (IPAddress, portNumber))
    except:
        closeSocket(clientSocket)
        sys.exit("Problem occured while sending packet through socket")
        
    try:
        waitingSocket = select.select([clientSocket], [], [], 1)
    except:
        closeSocket(clientSocket)
        sys.exit("Problem occured while waiting for a response")
        
    if len(waitingSocket[0]) == 0:
        closeSocket(clientSocket)
        sys.exit("No packet received within one second")
    
    #Receive the packet from the socket
    receivingSocket = waitingSocket[0][0]
    try:
        packet, address = receivingSocket.recvfrom(1024)
    except:
        closeSocket(clientSocket)
        sys.exit("Problem occured with receiving information from socket")
        
    
    #Unpack the packet, and print its details
    detailTable = checkPacket(packet, clientSocket)
    printPacketText(packet, detailTable)
    
    #Close the socket and discard the packet and details after use
    closeSocket(clientSocket)
    del packet, detailTable

main()
