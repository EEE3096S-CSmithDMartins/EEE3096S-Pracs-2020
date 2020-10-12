# Import libraries
import RPi.GPIO as GPIO
import random
import ES2EEPROMUtils
import os
import time

# some global variables that need to change as we run the program
end_of_game = None  # set if the user wins or ends the game
pwm_LED = None  # this will represent the accuracy LED
buzzer = None  # this will represent the buzzer component
current_guess = 0  # the current user guess
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


# Print the game menu
def menu():
    global end_of_game
    global value  # to hold the correct answer
    option = input("Select an option:   H - View High Scores     P - Play Game       Q - Quit\n")
    option = option.upper()
    if option == "H":
        os.system('clear')
        print("HIGH SCORES!!")
        s_count, ss = fetch_scores()
        display_scores(s_count, ss)
    elif option == "P":
        os.system('clear')
        print("Starting a new round!")
        print("Use the buttons on the Pi to make and submit your guess!")
        print("Press and hold the guess button to cancel your game")
        value = generate_number()
        print(value)
        current_guess = 0  # the default guess is 0, for every round
        while not end_of_game:
            pass
        print("You won")
    elif option == "Q":
        print("Come back soon!")
        exit()
    else:
        print("Invalid option. Please select a valid one!")


def display_scores(count, raw_data):
    # print the scores to the screen in the expected format
    print("There are {} scores. Here are the top 3!".format(count))
    # print out the scores in the required format
    pass


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
  
    # Setup PWM channels
    GPIO.setup(LED_accuracy, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(buzzer_pin, GPIO.OUT, initial=GPIO.LOW)
    #endregion
  
    # Setup debouncing and callbacks
    GPIO.add_event_detect(btn_increase, GPIO.FALLING, callback=btn_increase_pressed, bouncetime=200)
    GPIO.add_event_detect(btn_submit, GPIO.FALLING, callback=btn_guess_pressed, bouncetime=200)

    pwm_LED = GPIO.PWM(LED_accuracy, 60)
    pwm_LED.start(50)

    buzzer = GPIO.PWM(buzzer_pin, 1)
    buzzer.start(50)


# Load high scores
def fetch_scores():
    # get however many scores there are
    score_count = None
    # Get the scores
    
    # convert the codes back to ascii
    
    # return back the results
    return score_count, scores


# Save high scores
def save_scores():
    # fetch scores
    # include new score
    # sort
    # update total amount of scores
    # write new scores
    pass


# Generate guess number
def generate_number():
    return random.randint(0, pow(2, 3)-1)


# Increase button pressed
def btn_increase_pressed(channel):
    global current_guess

    print("You pressed the increase button")

    # Increase the value shown on the LEDs
    current_guess += 1  
    if current_guess > 7:
        current_guess = 0  # the guess cannot be higher than 7
    display_on_leds(current_guess)


# Guess button (submit button)
def btn_guess_pressed(channel):
    global end_of_game
    # If they've pressed and held the button, clear up the GPIO and take them back to the menu screen
    # The player does not necessarily have to release the button for it to be considered a long press. long press = press for time >= 2s (2000ms)
    GPIO.remove_event_detect(btn_submit)  # removing other events to avoid conficts

    # when the button is pressed, wait for up to 2000 ms for it to not be pressed
    pin = GPIO.wait_for_edge(channel, GPIO.RISING, timeout=2000)
    if pin is None:  # if the button was not released within the 2s, that is a long press. The player can press it for longer, with no effect
        GPIO.remove_event_detect(btn_submit)  # removing the wait_for_edge event to avoid confilct
        # adding the old event
        GPIO.add_event_detect(btn_submit, GPIO.FALLING, callback=btn_guess_pressed, bouncetime=200)
        print("You long pressed the button on pin", channel)
    else:  # if the button is released withing the 2s, then its just a normal click
        GPIO.remove_event_detect(btn_submit)  # the wait_for_edge event must be removed as soon as it occurs, to avoid bugs
        # adding the old event
        GPIO.add_event_detect(btn_submit, GPIO.FALLING, callback=btn_guess_pressed, bouncetime=200)
        print("You pressed the submit button")

        # Compare the actual value with the user value displayed on the LEDs
        led_duty_cycle = accuracy_leds(current_guess, value)
        if led_duty_cycle == 100:
            end_of_game = True
        # Change the PWM LED
        pwm_LED.ChangeDutyCycle(led_duty_cycle)

        # if it's close enough, adjust the buzzer
        trigger_buzzer()
 


    # if it's an exact guess:
    # - Disable LEDs and Buzzer
    # - tell the user and prompt them for a name
    # - fetch all the scores
    # - add the new score
    # - sort the scores
    # - Store the scores back to the EEPROM, being sure to update the score count


# LED Brightness
def accuracy_leds(guess, answer):
    # Set the brightness of the LED based on how close the guess is to the answer
    # - The % brightness should be directly proportional to the % "closeness"
    # - For example if the answer is 6 and a user guesses 4, the brightness should be at 4/6*100 = 66%
    # - If they guessed 7, the brightness would be at ((8-7)/(8-6)*100 = 50%
    duty_cycle = (8-guess)/(8-answer)*100 if guess > answer else guess/answer*100
    return duty_cycle

# Sound Buzzer
def trigger_buzzer():
    global current_guess, value, buzzer
    # The buzzer operates differently from the LED
    # While we want the brightness of the LED to change(duty cycle), we want the frequency of the buzzer to change
    # The buzzer duty cycle should be left at 50%
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
