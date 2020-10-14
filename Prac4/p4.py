# Import libraries
import RPi.GPIO as GPIO
import random
import ES2EEPROMUtils
import os
import time  # CHECK IF THIS IS NEEDED BEFORE SUBMITTING

# some global variables that need to change as we run the program
end_of_game = False  # set to True if the user wins or ends the game
game_has_started = False  # this is for the buttons to be irresponsive until the user starts the game
game_won = False  # this will be set to true when the game is won
pwm_LED = None  # this will represent the accuracy LED
buzzer = None  # this will represent the buzzer component
current_guess = 0  # the current user guess
number_of_guesses = 0  # the number of times the user has submitted a guess
value = 0  # this will hold the correct answer

# DEFINE THE PINS USED HERE
LED_value = [31, 13, 15]  # [11, 13, 15]  changing because of broken pin. DON'T FORGET TO REVERT THIS WHEN SUBMITTING
LED_accuracy = 32
btn_submit = 16
btn_increase = 18
buzzer_pin = 33
eeprom = ES2EEPROMUtils.ES2EEPROM()



# Print the game banner
def welcome():
    os.system('clear')
    print("  _   _                 _                  _____ _            __  __ _")
    print("| \ | |               | |                / ____| |          / _|/ _| |")
    print("|  \| |_   _ _ __ ___ | |__   ___ _ __  | (___ | |__  _   _| |_| |_| | ___ ")
    print("| . ` | | | | '_ ` _ \| '_ \ / _ \ '__|  \___ \| '_ \| | | |  _|  _| |/ _ \\")
    print("| |\  | |_| | | | | | | |_) |  __/ |     ____) | | | | |_| | | | | | |  __/")
    print("|_| \_|\__,_|_| |_| |_|_.__/ \___|_|    |_____/|_| |_|\__,_|_| |_| |_|\___|")
    print("")
    print("Guess the number and immortalise your name in the High Score Hall of Fame!")

# Start a round
def start_game():
    global game_has_started, end_of_game, value, game_won, current_guess, number_of_guesses

    os.system('clear')
    print("Starting a new round!")
    print("Use the buttons on the Pi to make and submit your guess!")
    print("Press and hold the guess button to cancel your game")
    # when a new game starts, the game has started, so it is not the end of the game
    game_has_started = True
    end_of_game = False
    game_won = False

    value = generate_number()
    print(value)
    current_guess = 0  # the default guess is 0, for every round
    number_of_guesses = 0



# Print the game menu
def menu():
    global end_of_game, game_has_started
    option = input("Select an option:   H - View High Scores     P - Play Game       Q - Quit\n")
    option = option.upper()
    if option == "H":
        os.system('clear')
        print("HIGH SCORES!!")
        s_count, ss = fetch_scores()
        display_scores(s_count, ss)
    elif option == "P":
        start_game()

        while not end_of_game:
            pass

        # getting ready to start a new game
        game_has_started = False
        end_of_game = False
        
    elif option == "Q":
        print("Come back soon!")
        exit()
    else:
        print("Invalid option. Please select a valid one!")


def display_scores(count, raw_data):
    # print the scores to the screen in the expected format
    print("There are {} scores. Here are the top 3!".format(count[0]))
    # print out the scores in the required format
    # print the top 3 scores
    for x in range(3):
    	#print the position number
    	print(x+1, "-", raw_data[x][0],"took", raw_data[x][1], "guesses")


# Setup Pins
def setup():
    # using the global variables declared earlier
    global pwm_LED
    global buzzer

    # Setup board mode
    GPIO.setmode(GPIO.BOARD)

    #region Setup regular GPIO
    # setting up the LEDs as output
    GPIO.setup(LED_value, GPIO.OUT, initial=GPIO.LOW)

    # setting up pins btn_increase and btn_submit as inputs with a pull-up resistor
    GPIO.setup((btn_increase, btn_submit), GPIO.IN, pull_up_down=GPIO.PUD_UP)
    #endregion

    #region Setup PWM channels
    GPIO.setup(LED_accuracy, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(buzzer_pin, GPIO.OUT, initial=GPIO.LOW)

    # setting the frequencies
    pwm_LED = GPIO.PWM(LED_accuracy, 60)
    buzzer = GPIO.PWM(buzzer_pin, 1)

    # starting them with a duty cycle of 0, so that they're off
    pwm_LED.start(0)
    buzzer.start(0)

    #endregion
  
    # Setup debouncing and callbacks
    GPIO.add_event_detect(btn_increase, GPIO.FALLING, callback=btn_increase_pressed, bouncetime=300)
    GPIO.add_event_detect(btn_submit, GPIO.FALLING, callback=btn_guess_pressed, bouncetime=50)


# Load high scores
def fetch_scores():
    # clear = eeprom.populate_mock_scores
    # clear()
    # get however many scores there are
    read_block = eeprom.read_block
    score_count = read_block(0, 1)
    # Get the scores
    # convert the codes back to ascii
    # return back the results
    scores = []
    for x in range(1, score_count[0] + 1):
    	data = []
    	score = read_block(x, 4)
    	name = chr(score[0]) + chr(score[1]) + chr(score[2])
    	score_val = score[3]
    	data.append(name)
    	data.append(score_val)
    	scores.append(data)
    return score_count, scores

# Save high scores
def save_scores():
    #get use guess
    guess = number_of_guesses
    #get use name
    name = input("Enter your name: ")
    data = []
    for i in name[0:3:1]:
    	data.append(i)
    read_block = eeprom.read_block
    write_block = eeprom.write_block
    #update total amount of scores
    score_count = read_block(0, 1)
    # fetch scores
    scores = []
    for x in range(1, score_count[0] + 1):
    	score = read_block(x, 4)
    	scores.append(score)
    # include new score
    new_score_data = []
    for letter in data:
    	new_score_data.append(ord(letter))
    new_score_data.append(guess)
    scores.append(new_score_data)

    #sort scores
    final_scores = sorted(scores, key=lambda x:x[3])
    for i in range(1, score_count[0] + 1):
    	c = 0
    	write_block(i, final_scores[i-1])
    write_block(0, [score_count[0] + 1])


# Generate guess number
def generate_number():
    return random.randint(0, pow(2, 3)-1)


# Increase button pressed
def btn_increase_pressed(channel):
    global current_guess

    # exit the function if it is the end of the game or the game has not started yet
    if not game_has_started or end_of_game:
        return

    print("You pressed the increase button")

    # Increase the value shown on the LEDs
    current_guess += 1  
    if current_guess > 7:
        current_guess = 0  # the guess cannot be higher than 7
    display_on_leds(current_guess)


# Guess button (submit button)
def btn_guess_pressed(channel):
    global end_of_game, game_won, number_of_guesses
    print("You pressed something: ", end='')
    # exit the function if it is the end of the game or the game has not started yet
    if not game_has_started or end_of_game:
        return
    
    # otherwise, just carry out normally
    
    # If they've pressed and held the button, clear up the GPIO and take them back to the menu screen
    # The player does not necessarily have to release the button for it to be considered a long press. long press = press for time >= 2s (2000ms)
    GPIO.remove_event_detect(btn_submit)  # removing other events to avoid conficts
    press_type = ""
    # when the button is pressed, wait for up to 2000 ms for it to be released (RISING edge)
    pin = GPIO.wait_for_edge(channel, GPIO.RISING, timeout=2000)
    if pin is None:  # if the button was not released within the 2s, that is a long press. The player can press it for longer, with no effect
        press_type = "long"
    else:  # if the button is released withing the 2s, then its just a normal click
        press_type = "click"

    GPIO.remove_event_detect(btn_submit)  # removing the wait_for_edge event to avoid confilct
    # adding the old event
    GPIO.add_event_detect(btn_submit, GPIO.FALLING, callback=btn_guess_pressed, bouncetime=50)

    if press_type == "long":
        print("You long pressed the button on pin")
        end_of_game = True
    
    elif press_type == "click":
        print("You pressed the submit button")
        number_of_guesses += 1
        # Compare the actual value with the user value displayed on the LEDs
        if current_guess == value:
            game_won = True
            end_of_game = True
        else:
            # Change the PWM LED
            accuracy_leds()
            # if it's close enough, adjust the buzzer
            trigger_buzzer()

    # if it's an exact guess:
    if end_of_game: 
        # - Disable LEDs and Buzzer
        pwm_LED.stop()
        GPIO.output(LED_value, 0)
        buzzer.stop()

        if game_won: 
            print("You won")
            # - tell the user and prompt them for a name
            # - fetch all the scores
            # - add the new score
            # - sort the scores
            # - Store the scores back to the EEPROM, being sure to update the score count
            save_scores()

# LED Brightness
def accuracy_leds():
    # Set the brightness of the LED based on how close the guess is to the answer
    # - The % brightness should be directly proportional to the % "closeness"
    # - For example if the answer is 6 and a user guesses 4, the brightness should be at 4/6*100 = 66%
    # - If they guessed 7, the brightness would be at ((8-7)/(8-6)*100 = 50%
    duty_cycle = (8-current_guess)/(8-value)*100 if current_guess > value else current_guess/value*100
    pwm_LED.ChangeDutyCycle(duty_cycle)


# Sound Buzzer
def trigger_buzzer():
    # The buzzer operates differently from the LED
    # While we want the brightness of the LED to change(duty cycle), we want the frequency of the buzzer to change
    # The buzzer duty cycle should be left at 50%
    buzzer.start(50)
    # If the user is off by an absolute value of 3, the buzzer should sound once every second
    error = abs(current_guess - value)
    if error == 3:
        buzzer.ChangeFrequency(1)
    # If the user is off by an absolute value of 2, the buzzer should sound twice every second
    elif error == 2:
        buzzer.ChangeFrequency(2)
    # If the user is off by an absolute value of 1, the buzzer should sound 4 times a second
    elif error == 1:
        buzzer.ChangeFrequency(4)
    # if the user is off by more than 3, the buzzer will be off
    else:
        buzzer.stop()


# A function to display an integer on 3 LEDs
def display_on_leds(integer):
    # converting the integer to binary '0bXYZ'
    binary = list(bin(integer))[2:]  # this will be the array ['X', 'Y', 'Z']
    
    # is will be a problem if the number is less than 4, as they will have less than 3 digits, so that must be fixed
    # region Prepending 0's if necessary
    binary_width = len(binary)
    number_of_leds = len(LED_value)
    if binary_width < number_of_leds:
        for i in range(number_of_leds - binary_width):
            binary.insert(0, 0)  # insert a 0 in the begining of he array
    #endregion

    # converting the array of characters into an array of integers (0 or 1)
    binary = [int(char) for char in binary]  # this will turn binary into [X, Y, Z] instead of ['X', 'Y', 'Z']
    # print(binary)

    # writing the binary number to the LEDs
    GPIO.output(LED_value, binary)  


if __name__ == "__main__":
    try:
        # Call setup function
        setup()
        welcome()
        while True:
            menu()

    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()
