# bangla_audio.py
# Python 3 file, used by app.py

CONFIRM_COMMANDS = {
    "sit": "confirm_sit",
    "stand": "confirm_stand",
    "walk_forward": "confirm_forward",
    "go_back": "confirm_back",
    "turn_left": "confirm_left",
    "turn_right": "confirm_right",
    "stop": "confirm_stop",
    "right_hand": "confirm_right_hand",
    "left_hand": "confirm_left_hand",
    "rest": "confirm_rest",
    "salute": "confirm_salute",
}

DO_COMMANDS = {
    "sit": "do_sit",
    "stand": "do_stand",
    "walk_forward": "do_forward",
    "go_back": "do_back",
    "turn_left": "do_left",
    "turn_right": "do_right",
    "stop": "do_stop",
    "right_hand": "do_right_hand",
    "left_hand": "do_left_hand",
    "rest": "do_rest",
    "salute": "do_salute",
}

CANCEL_COMMANDS = {
    "sit": "cancel_sit",
    "stand": "cancel_stand",
    "walk_forward": "cancel_forward",
    "go_back": "cancel_back",
    "turn_left": "cancel_left",
    "turn_right": "cancel_right",
    "right_hand": "cancel_right_hand",
    "left_hand": "cancel_left_hand",
    "rest": "cancel_rest",
    "salute": "cancel_salute",
}


def detect_yes_no(text):
    cleaned = (text or "").lower().strip()

    yes_words = ["হ্যাঁ", "হা", "হ্যা", "জি", "হুম", "yes", "ha", "haa", "hya"]
    no_words = ["না", "নাহ", "no", "na", "naa"]

    for word in yes_words:
        if word in cleaned:
            return "yes"

    for word in no_words:
        if word in cleaned:
            return "no"

    return "unknown"


def needs_confirmation(command):
    return command in CONFIRM_COMMANDS


def get_confirm_command(command):
    return CONFIRM_COMMANDS.get(command, "unknown")


def get_do_command(command):
    return DO_COMMANDS.get(command, "unknown")


def get_cancel_command(command):
    return CANCEL_COMMANDS.get(command, "unknown")