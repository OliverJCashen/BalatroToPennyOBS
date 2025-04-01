import time
import math
import keyboard
import easyocr
import pyautogui
import os
from obswebsocket import obsws, requests

# !!Set this to your OBS WebSocket password!!
password = ""  

# !!Set these to your respective OBS Sources!! (Defaults correspond to provided OBS Scene)
chipsSource = "ChipsText" 
volumeSource = "VolumeText"
diameterSource = "DiameterText"
massSource = "MassText"
comparisonSource = "ComparisonText"

reader = easyocr.Reader(['en']) # Load the EasyOCR Model into Memory

host = "localhost"
port = 4455  # Default WebSocket port

currentBoxCoordinates = []
calculationBool = False # Prevents Calculating Penny before Box defined

# ------------------------------------------------------------------------------------------------

def ScientificFormat(n): # For Dealing with Bigger Numbers
    if n > 1e6:
        n="{:.2e}".format(n)
    return n

# ------------------------------------------------------------------------------------------------

def CalibrateBox():
    
    global calculationBool # The "global" keyword allows these variables to edited by other functions
    global currentBoxCoordinates
    
    currentBoxCoordinates = []
        
    print("Move your mouse to the top left corner of the score box, then press Shift.")       
    GetCoordinates(False) # The Boolean here designates whether it's getting the Coordinates for the bottom-right corner or not.
            
    time.sleep(0.1)
        
    print("Move your mouse to the bottom right corner of the score box, then press Shift.")            
    GetCoordinates(True)   

    print("You can now press F2 to calculate the Size of the Penny.")    
    calculationBool = True # Now allows for Penny Calculations
        
# ------------------------------------------------------------------------------------------------

def GetCoordinates(bottomRight):
    while True:
        if keyboard.is_pressed("shift"):
            x, y = pyautogui.position()  # Get current mouse position
            if bottomRight:
                currentBoxCoordinates.append(x-currentBoxCoordinates[0])
                currentBoxCoordinates.append(y-currentBoxCoordinates[1])
            else:
                currentBoxCoordinates.append(x)
                currentBoxCoordinates.append(y)           
            print(f"X={x}, Y={y}")
            break
        
# ------------------------------------------------------------------------------------------------
        
def ReadChips():
    
    global chipsResult
    
    chipsImage = pyautogui.screenshot(region=tuple(currentBoxCoordinates)) # Takes screenshot with Coordinates found from GetCoordinates()
    chipsImage.save("chips.png")

    result = reader.readtext("chips.png")
    chipsResult = result[0][1].replace(",", "").replace(" ","") # The commas in values >1000 often get confused as or spaces
    
    try:
        if "e" in chipsResult:
            index = chipsResult.find("e")  # Find the first occurrence of 'e'
            eAmount = int(chipsResult[index + 1:])  # Get everything after 'e'
            preEAmount = float(chipsResult[:index])  # Get everything before 'e'
            chipsResult = preEAmount * (10**eAmount)
                
        else:
            chipsResult = int(chipsResult.replace(".","")) # The commas in values >1000 often get confused as decimal points
            
    except (ValueError) as e: # Prevents crashing if easyocr cannot find a number
        print(f"\nERROR: Selected text cannot be read as number:\n{e}")
        chipsResult = 0

    os.remove("chips.png") 
 
# ------------------------------------------------------------------------------------------------

comparisonDict = {  
    "Smartphone" : 0.15,
    "Cereal Box" : 0.3,
    "Basketball" : 0.24,
    "Office Chair" : 0.45,
    "1 Meter" : 1,
    "Small Child" : 1.2,
    "Adult Male" : 1.75,
    "Giraffe" : 5.5,
    "Two-Story House" : 8,
    "Statue of Liberty" : 93,
    "Burj Khalifa" : 828,
    "1 Kilometer" : 1000,
    "Mount Everest" : 8849,
    "Width of Lake Ontario" : 193000,
    "Earth Radius" : 6371000,
    "Earth-Moon Distance" : 384400000,
    "Mercury-Sun Distance" : 4.6e10,
    "Distance to Voyager 1" : 2.3e13,
    "Light Year" : 9.46e15,
    "Parsec" : 3.1e18,
    "Milky Way Diameter" : 9.5e20,
    "Local Group Diameter" : 9.5e22,
    "Virgo Supercluster" : 1.0e24,
    "Observable Universe Diameter" : 8.8e26,
    "10,000 x Observable Universe" : 8.8e30,
    "Million x Observable Universe" : 8.8e32,
    "Trillion x Observable Universe" : 8.8e38,
    "Quintillion x Observable Universe" : 8.8e44,
    "Sextillion x Observable Universe" : 8.8e46,
    "Decillion x Observable Universe" : 8.8e52,
    "10^31 x Observable Universe" : 8.8e57,
    "10^36 x Observable Universe" : 8.8e62,
    "10^42 x Observable Universe" : 8.8e68,
    "10^48 x Observable Universe" : 8.8e74,
    "10^54 x Observable Universe" : 8.8e80,
    "10^60 x Observable Universe" : 8.8e86,
    "10^67 x Observable Universe" : 8.8e93,
    "Googol Meters" : 1e100
}

def physicalComparison(pennyDiameter):
    
    currentLargest = ""
    
    for key, value in comparisonDict.items(): # Goes through each value in comparisonDict
        if pennyDiameter > value:
            currentLargest = key # Gets the smallest item pennyDiameter is bigger than
    return currentLargest

# ------------------------------------------------------------------------------------------------

def PennyCalculations(chips):
    
    global pennyVolume, pennyDiameter, pennyMass, sizeComparison

    pennyVolume = round(5.35e-7 * chips,4)
    
    pennyDiameter = round(2*((pennyVolume/((math.pi)*(.16)))**(1/3)),4)

    pennyMass = round(8960 * pennyVolume,4)
    
    sizeComparison = physicalComparison(pennyDiameter)
    
    chips = ScientificFormat(chips)
    pennyVolume = ScientificFormat(pennyVolume)
    pennyDiameter = ScientificFormat(pennyDiameter)
    pennyMass = ScientificFormat(pennyMass)
        
    print(f"\nChips Amount: {chips}")
    print(f"Penny Volume: {pennyVolume}m³")
    print(f"Penny Diameter: {pennyDiameter}m")
    print(f"Penny Mass: {pennyMass}kg")
    print(f"Larger Than: {sizeComparison}")
    
# ------------------------------------------------------------------------------------------------

def SendToOBS():
    
    ws = obsws(host, port, password)
    ws.connect() # Connects to OBS
    
    sources = {
        chipsSource: chipsResult,
        volumeSource: pennyVolume,
        diameterSource: pennyDiameter,
        massSource: pennyMass,
        comparisonSource : sizeComparison,
    }
    
    for sourceName, value in sources.items():
        response = ws.call(requests.GetInputSettings(inputName=sourceName))  # Requests and Stores source Settings
        settings = response.datain["inputSettings"]  # Extracts Input Settings
        
        match sourceName:
            case "VolumeText":
                unit = "m³"
            case "DiameterText":
                unit = "m"
            case "MassText":
                unit = "kg"
            case _:
                unit = ""
        
        settings["text"] = f"{str(value)}{unit}"  # Updates the "text" field
        
        ws.call(requests.SetInputSettings(inputName=sourceName, inputSettings=settings))  # Send updated settings to OBS
    
    ws.disconnect()
    
# ------------------------------------------------------------------------------------------------

    
print("Welcome to the Balatro Chip to Penny Size Calculator.\nPlease press F1 to calibrate the Round Score Box.")

while True:
    if keyboard.is_pressed("F1"):        
        CalibrateBox() # !!COMMENT TO TEST PENNY CALCULATIONS!!
        
        # chipsResult = 1e308 # !!UNCOMMENT TO TEST PENNY CALCULATIONS!!
        # calculationBool = True # !!UNCOMMENT TO TEST PENNY CALCULATIONS!!
        
    elif keyboard.is_pressed("F2") and calculationBool:
        ReadChips() # !!COMMENT TO REST PENNY CALCULATIONS!!
        PennyCalculations(chipsResult)
        SendToOBS()
        
        time.sleep(1) # Prevents Spamming