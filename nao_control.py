# -*- coding: utf-8 -*-
# nao_control.py
# Python 2.7

from naoqi import ALProxy
import sys
import time

NAO_IP = "192.168.10.138"
PORT = 9559

AUDIO_DIR = "/home/nao/bangla_audio/"

if len(sys.argv) < 2:
    print("No command received")
    sys.exit(1)

command = sys.argv[1]

posture = ALProxy("ALRobotPosture", NAO_IP, PORT)
motion = ALProxy("ALMotion", NAO_IP, PORT)
player = ALProxy("ALAudioPlayer", NAO_IP, PORT)

motion.wakeUp()


def play_audio(filename):
    audio_path = AUDIO_DIR + filename
    print("Playing:", audio_path)
    player.playFile(audio_path)
    time.sleep(0.3)


# SIT
if command == "confirm_sit":
    play_audio("confirm_sit.mp3")

elif command == "do_sit":
    play_audio("ok_sit.mp3")
    posture.goToPosture("Sit", 0.8)

elif command == "cancel_sit":
    play_audio("cancel.mp3")


# STAND
elif command == "confirm_stand":
    play_audio("confirm_stand.mp3")

elif command == "do_stand":
    play_audio("ok_stand.mp3")
    posture.goToPosture("Stand", 0.8)

elif command == "cancel_stand":
    play_audio("cancel.mp3")


# WALK FORWARD
elif command == "confirm_forward":
    play_audio("confirm_forward.mp3")

elif command == "do_forward":
    play_audio("ok_forward.mp3")
    motion.moveTo(0.3, 0, 0)

elif command == "cancel_forward":
    play_audio("cancel.mp3")

    # GO BACK

elif command == "confirm_back":
    play_audio("confirm_back.mp3")

elif command == "do_back":
    play_audio("ok_back.mp3")
    motion.moveTo(-0.3, 0, 0)

elif command == "cancel_back":
    play_audio("cancel.mp3")


# TURN LEFT
elif command == "confirm_left":
    play_audio("confirm_left.mp3")

elif command == "do_left":
    play_audio("ok_left.mp3")
    motion.moveTo(0, 0, 1.57)

elif command == "cancel_left":
    play_audio("cancel.mp3")


# TURN RIGHT
elif command == "confirm_right":
    play_audio("confirm_right.mp3")

elif command == "do_right":
    play_audio("ok_right.mp3")
    motion.moveTo(0, 0, -1.57)

elif command == "cancel_right":
    play_audio("cancel.mp3")


# STOP
elif command == "confirm_stop":
    play_audio("confirm_stop.mp3")

elif command == "do_stop":
    play_audio("ok_stop.mp3")
    motion.stopMove()


# RIGHT HAND / WAVE
elif command == "confirm_right_hand":
    play_audio("confirm_right_hand.mp3")

elif command == "do_right_hand":
    play_audio("ok_right_hand.mp3")

    motion.setAngles("RShoulderPitch", -0.5, 0.2)
    motion.setAngles("RElbowRoll", 1.2, 0.2)

    for i in range(3):
        motion.setAngles("RWristYaw", 1.0, 0.3)
        time.sleep(0.4)
        motion.setAngles("RWristYaw", -1.0, 0.3)
        time.sleep(0.4)

    posture.goToPosture("Stand", 0.8)

elif command == "cancel_right_hand":
    play_audio("cancel.mp3")


# LEFT HAND / WAVE

elif command == "confirm_left_hand":
    play_audio("confirm_left_hand.mp3")

elif command == "do_left_hand":
    play_audio("ok_left_hand.mp3")

    motion.setAngles("LShoulderPitch", -0.5, 0.2)
    motion.setAngles("LElbowRoll", -1.2, 0.2)

    for i in range(3):
        motion.setAngles("LWristYaw", 1.0, 0.3)
        time.sleep(0.4)
        motion.setAngles("LWristYaw", -1.0, 0.3)
        time.sleep(0.4)

    posture.goToPosture("Stand", 0.8)

elif command == "cancel_left_hand":
    play_audio("cancel.mp3")

    # SALUTE

elif command == "confirm_salute":
    play_audio("confirm_salute.mp3")

elif command == "do_salute":
    play_audio("ok_salute.mp3")

    posture.goToPosture("Stand", 0.8)

    motion.setAngles("RShoulderPitch", -1.49, 0.15)
    motion.setAngles("RShoulderRoll", -0.61, 0.15)
    motion.setAngles("RElbowYaw", -0.31, 0.15)
    motion.setAngles("RElbowRoll", 1.47, 0.15)
    motion.setAngles("RWristYaw", 0.40, 0.15)


    time.sleep(2)

    posture.goToPosture("Stand", 0.8)

elif command == "cancel_salute":
    play_audio("cancel.mp3")



# REST
elif command == "confirm_rest":
    play_audio("confirm_rest.mp3")

elif command == "do_rest":
    play_audio("ok_rest.mp3")
    motion.rest()

elif command == "cancel_rest":
    play_audio("cancel.mp3")


# SIMPLE COMMANDS
elif command == "hello":
    play_audio("hello.mp3")

elif command == "name":
    play_audio("name.mp3")

elif command == "startup":
    play_audio("startup.mp3")

elif command == "unknown":
    play_audio("unknown.mp3")


else:
    play_audio("unknown.mp3")