import sys
import socket

def getParameters():
    textType = input("Please specify whether you wish for the date or the time: ")
    textType = textType.lower()
    if textType != "date" and textType != "time":
        sys.exit()
    ipAddress = input("Please provide either the hostname or IP address: ")
    #Determine whether address is by host or dotted decimal
    ipComponents = ipAddress.split()
    addressType = "Dotted"
    for comp in ipComponents:
        if not comp.isdigit():
            addressType = "Host"
            
    if addressType == "Host":
        ipAddress = socket.gethostbyname(ipAddress)
        
    portNumber = input("Please provide the port number you wish to use: ")
    if portNumber > 64000 or portNumber < 1024:
        sys.exit("Port number not between 1024 and 64000")
    
    return textType, ipAddress, portNumber
    
    
def formRequestPacket(request):
    magicNumber = 0x497E
    packetType = 0x0002
    if request == "date":
        requestType = 0x0001
    elif request == "time":
        requestType = 0x0002
        
    requestPacket = bytearray()
    requestPacket += magicNumber.to_bytes(2, byteorder="big")
    requestPacket += packetType.to_bytes(2, byteorder="big")
    requestPacket += requestType.to_bytes(2, byteorder="big")
    return requestPacket
    
def checkPacket(pkt):
    packetBitLength = len(pkt)*8
    
    #Generate the masks for checking information
    magicNumMask = "0b" + "1"*16 + "0"*(packetBitLength-16)
    packetTypeMask = "0b" + "0"*16 + "1"*16 + "0"*(packetBitLength-32)
    langaugeMask = "0b" + "0"*32 + "1"*16 + "0"*(packetBitLength-48)
    yearMask = "0b" + "0"*48 + "1"*16 + "0"*(packetBitLength-64)
    monthMask = "0b" + "0"*64 + "1"*8 + "0"*(packetBitLength-72)
    dayMask = "0b" + "0"*72 + "1"*8 + "0"*(packetBitLength-80)
    hourMask = "0b" + "0"*80 + "1"*8 + "0"*(packetBitLength-88)
    minuteMask = "0b" + "0"*88 + "1"*8 + "0"*(packetBitLength-96)
    lengthMask = "0b" + "0"*96 + "1"*8 + "0"*(packetBitLength-104)
    
    pktContents = int.from_bytes(pkt, byteorder="big")
    
    magicNum = ((packetContents & magicNumMask) >> (packetBitLength-16))
    if magicNum != 0x497E:
        sys.exit("Magic number not correct")
        
    packetType = ((packetContents & packetTypeMask) >> (packetBitLength-32))
    if packetType != 0x0002:
        sys.exit("Packet type not a DT-Response packet")
    
    langaugeCode = ((packetContents & languageMask) >> (packetBitLength-48))
    if languageCode != 0x0002 and languageCode != 0x0001 and languageCode != 0x0003:
        sys.exit("Language code does not match a known language")
        
    year = ((packetContents & yearMask) >> (packetBitLength-64))
    if year > 2100:
        sys.exit("Year provided too great")
        
    month = ((packetContents & monthMask) >> (packetBitLength-72))
    if month > 12 or month < 1:
        sys.exit("Month does not exist")
        
    day = ((packetContents & dayMask) >> (packetBitLength-80))
    if day > 31 or day < 1:
        sys.exit("Day does not exist")
        
    hour = ((packetContents & hourMask) >> (packetBitLength-88))
    if hour < 0 or hour > 23:
        sys.exit("Hour is outside of 24-hour bounds")
        
    minute = ((packetContents & minuteMask) >> (packetBitLength-96))
    if minute < 0 or minute > 59:
        sys.exit("Minute value is not within one hour")
    
    textLength = ((packetContents & lengthMask) >> (packetBitLength-104))
    if len(pkt) != (13 + textLength):
        sys.exit("Total length inconsistent with provided length value")
        
    return textLength

def printPacketText(pkt, textLength):
    textMask = "0b" + "0"*(13*8) + "1"*(textLength*8)
    packetContents = int.from_bytes(pkt, byteOrder="big")
    text = (packetContent & textMask)
    print(text)
    
    
    
def main():
    textType, IPAddress, portNumber = getParameters()
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    packet = formPacket()
    
    clientSocket.sendto(packet, (IPAddress, portNumber))
