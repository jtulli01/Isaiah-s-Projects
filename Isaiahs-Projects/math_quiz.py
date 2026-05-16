# =============================================
#   Isaiah's Math Quiz Game
#   Practice your 4th grade math!
# =============================================

import random  # This lets us pick random numbers

# --- These are the encouraging messages ---
correct_messages = [
    "Great job! You got it right!",
    "Awesome! You're a math superstar!",
    "YES! That's correct!",
    "Wow, nice work Isaiah!",
    "You nailed it!",
]

try_again_messages = [
    "Not quite, but keep going! You've got this!",
    "Almost! Don't give up!",
    "Good try! Keep practicing!",
]

# --- This function makes the quiz problems ---
def ask_question(level):
    """Makes a math problem and returns it with the right answer."""

    # Level 1 = Easy (small numbers, adding and subtracting)
    if level == 1:
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        operation = random.choice(["+", "-"])

    # Level 2 = Medium (bigger numbers, adding, subtracting, multiplying)
    elif level == 2:
        num1 = random.randint(1, 20)
        num2 = random.randint(1, 10)
        operation = random.choice(["+", "-", "x"])

    # Level 3 = Hard (times tables up to 12!)
    else:
        num1 = random.randint(1, 12)
        num2 = random.randint(1, 12)
        operation = "x"

    # Figure out the right answer
    if operation == "+":
        answer = num1 + num2
    elif operation == "-":
        # Make sure we don't get a negative answer (keeping it 4th grade!)
        if num1 < num2:
            num1, num2 = num2, num1  # Swap them around
        answer = num1 - num2
    else:  # multiplication
        answer = num1 * num2

    return num1, num2, operation, answer


# --- This is where the game starts ---
def play_game():
    print("=" * 40)
    print("   Welcome to Isaiah's Math Quiz!")
    print("=" * 40)
    print()
    print("Pick your level:")
    print("  1 = Easy   (adding and subtracting small numbers)")
    print("  2 = Medium (bigger numbers + times tables)")
    print("  3 = Hard   (all times tables up to 12!)")
    print()

    # Ask the player to pick a level
    while True:
        choice = input("Type 1, 2, or 3 and press ENTER: ")
        if choice in ["1", "2", "3"]:
            level = int(choice)
            break
        else:
            print("Hmm, please just type 1, 2, or 3!")

    # How many questions?
    print()
    print("How many questions do you want? (Try 5 or 10!)")
    while True:
        num_questions_str = input("Type a number and press ENTER: ")
        if num_questions_str.isdigit() and int(num_questions_str) > 0:
            num_questions = int(num_questions_str)
            break
        else:
            print("Please type a number like 5 or 10!")

    # --- Start the quiz! ---
    print()
    print(f"Okay! Here come {num_questions} questions. Good luck!")
    print("-" * 40)

    score = 0  # We start with 0 points

    for question_number in range(1, num_questions + 1):
        num1, num2, operation, correct_answer = ask_question(level)

        print(f"\nQuestion {question_number} of {num_questions}:")
        print(f"  What is {num1} {operation} {num2} ?")

        # Get the player's answer
        while True:
            player_answer_str = input("  Your answer: ")
            if player_answer_str.lstrip("-").isdigit():
                player_answer = int(player_answer_str)
                break
            else:
                print("  Please type a number!")

        # Check if the answer is right
        if player_answer == correct_answer:
            score = score + 1  # Add a point!
            print("  " + random.choice(correct_messages))
        else:
            print("  " + random.choice(try_again_messages))
            print(f"  The answer was: {correct_answer}")

    # --- Show the final score ---
    print()
    print("=" * 40)
    print(f"   Quiz Over! Your Score: {score} out of {num_questions}")
    print("=" * 40)

    # Give a message based on how well they did
    percent = score / num_questions * 100  # Calculate percentage

    if percent == 100:
        print("   WOW! PERFECT SCORE! You're AMAZING!")
    elif percent >= 80:
        print("   Great job! You really know your math!")
    elif percent >= 60:
        print("   Nice work! Keep practicing and you'll be a pro!")
    else:
        print("   Good effort! Practice makes perfect. Try again!")

    print()

    # Ask if they want to play again
    play_again = input("Do you want to play again? (yes or no): ").lower()
    if play_again in ["yes", "y", "yeah", "yep"]:
        print()
        play_game()  # Start the game over!
    else:
        print()
        print("Thanks for playing! Keep up the great work, Isaiah!")
        print("See you next time!")


# --- This line starts the game when you run the file ---
play_game()
