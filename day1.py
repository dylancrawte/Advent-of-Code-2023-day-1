total = []
test = []

with open('input.txt', 'r') as file: #opens the file
    for line in file: #for each line in the file
        digits = [char for char in line if char.isdigit()] #iterates through each character, adds any digits to list
        first_digit = digits[0] 
        last_digit = digits[-1]
        number = int(first_digit + last_digit) #concatenates the first and last digit
        total.append(number) #appends to total list
        print(total)
#part 1 completed last week and part 2 to be completed


