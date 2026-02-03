#LAB-1


#2. Use Python as a calculator in IDLE.

print(3.4*12 )
print(3.14 + 2.71 )
print(210 )
print(1+1/2+1/3+1/4+1/5 )
print(5+1 /52 + 1 )
print(10/5/2 )

     
#3. First Program
print("Hello word!")

       
#4. ASCII art: 
print("  o")
print(" /|\\")
print(" / \\")

           
#Do the ASCII art image with print() :
print("*********   ****   ****   *********   *********")
print("*********   ****   ****   *********   *********")
print("***         ****   ****   ***         **     **")
print("***             ***       ***         **     **")
print("*********       ***       ***         **     **")
print("*********       ***       ***         *********")
print("      ***       ***       ***         *********")
print("      ***   ****   ****   ***         ***   ***")
print("*********   ****   ****   *********   ***   ***")
print("*********   ****   ****   *********   ***   ***")

      
#Make an ASCII art of your first name
print("*********   ***         *********   ********   *********   *********")
print("*********   ***         *********   ********   *********   *********")
print("***   ***   ***            ***      ***           ***      **     **")
print("***   ***   ***            ***      ***           ***      **     **")
print("*********   ***            ***      ***           ***      **     **")
print("*********   ***            ***      ***           ***      *********")
print("***   ***   ***            ***      ***           ***      *********")
print("***   ***   ***            ***      ***           ***      ***   ***")
print("***   ***   *********   *********   ********   *********   ***   ***")
print("***   ***   *********   *********   ********   *********   ***   ***")

                    
#5) Expressions:
#Write a Python script that prints out “Xavier’s Xavier’s Xavier’s Xavier’s Xavier’s Xavier’s Xavier’s Xavier’s” 
#Include tab and newline characters to separate the word “Xaviers”.

print("Xavier’s \t Xavier’s\t Xavier’s\n Xavier’s \nXavier’s" )

                    
#Write a script that prints out the divisor and the remainder of the integer division of 123456789 by 98765. You can print out several entities by making them argument to the print function separated by commas. 
numerator = 123456789
divisor = 98765
quotient = numerator // divisor
remainder = numerator % divisor
print("Divisor:", divisor)
print("Quotient:", quotient)
print("Remainder:", remainder)


#6) Types:
#Write programs that convert:
#Centimeters to inches
n=int(input("Enter the length in centimetre: "))
inch=n/2.54
print(n,"cm = ",inch,"inches")

 

#Centimeters to feet
n=int(input("Enter the length in centimetre: "))
feet=n/30.48
print(n,"cm = ",feet,"feet") 

 

#Inches to millimeters
n=int(input("Enter the length in inches: "))
milimetere=n*25.4
print(n,"cm = ",milimetere,"milimetre")

 
 
#Temperatures in Celsius to temperatures in Fahrenheit C = 5/9(°F – 32)
n=float(input("Enter temperature in Celsius: "))
fahrenheit = (n * 9/5) + 32
print(n,"celsius = ",fahrenheit,"fahrenheit")

 

#Fuel consumption of a car from liters per kilometer to miles per gallon 
n = float(input("Enter fuel consumption in liters per km: "))
miles_km = 0.621371
gallons_liter = 0.264172
mpg = 1 / (n* miles_km * gallons_liter)
print(n,"liters per km = ",mpg,"miles per gallons")

 

#Currency conversion:
#USD to EURO
usd = int(input("Enter amount in USD: "))
euro_rate = float(input("Enter conversion rate from USD to EURO: "))
euro = usd * euro_rate
print(usd,"USD = ",euro,"EURO")

 

#USD to INR
usd = int(input("Enter amount in USD: "))
inr_rate = float(input("Enter conversion rate from USD to INR: "))
inr = usd * inr_rate
print(usd,"USD = ",inr,"INR")


