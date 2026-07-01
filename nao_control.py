# nao_control.py
# Python 2.7

from naoqi import ALProxy
import sys

NAO_IP = "192.168.10.138"
PORT = 9559

command = sys.argv[1]

tts = ALProxy("ALTextToSpeech", NAO_IP, PORT)
posture = ALProxy("ALRobotPosture", NAO_IP, PORT)
motion = ALProxy("ALMotion", NAO_IP, PORT)

motion.wakeUp()


if command == "sit":
    tts.say("I am sitting")
    posture.goToPosture("Sit", 0.8)

elif command == "stand":
    tts.say("I am standing")
    posture.goToPosture("Stand", 0.8)

elif command == "hello":
    tts.say("Hello. How are you")

elif command == "name":
    tts.say("My name is Nao")

elif command == "walk_forward":
    tts.say("Moving forward")
    motion.moveTo(0.3, 0, 0)

elif command == "turn_left":
    tts.say("Turning left")
    motion.moveTo(0, 0, 1.57)

elif command == "turn_right":
    tts.say("Turning right")
    motion.moveTo(0, 0, -1.57)

elif command == "stop":
    tts.say("Stopping")
    motion.stopMove()

elif command == "right_hand":
    tts.say("Waving right hand")

    motion.setAngles("RShoulderPitch", -0.5, 0.2)
    motion.setAngles("RElbowRoll", 1.2, 0.2)

    for i in range(3):
        motion.setAngles("RWristYaw", 1.0, 0.3)
        motion.setAngles("RWristYaw", -1.0, 0.3)

    posture.goToPosture("Stand", 0.8)

elif command == "rest":
    tts.say("Going to rest")
    motion.rest()

else:
    tts.say("Unknown command")