from gtts import gTTS
import os

audio_files = {
    "confirm_sit.mp3": "তুমি কি আমাকে বসতে বলছো?",
    "ok_sit.mp3": "ঠিক আছে, আমি বসছি।",
    "confirm_stand.mp3": "তুমি কি আমাকে দাঁড়াতে বলছো?",
    "ok_stand.mp3": "ঠিক আছে, আমি দাঁড়াচ্ছি।",
    "cancel.mp3": "ঠিক আছে, আমি করছি না।",
    "repeat.mp3": "আমি বুঝতে পারিনি। আবার বলো।",
    "hello.mp3": "হ্যালো, আমি নাও। তুমি আমাকে বাংলা কমান্ড দিতে পারো।",
    "startup.mp3": "আমি প্রস্তুত। তুমি আমাকে বাংলা কমান্ড দিতে পারো।",
    "unknown.mp3": "আমি বুঝতে পারিনি। দয়া করে আবার বলো।",
    "confirm_forward.mp3": "তুমি কি আমাকে সামনের দিকে যেতে বলছো?",
    "ok_forward.mp3": "ঠিক আছে, আমি সামনের দিকে যাচ্ছি।",       
    "confirm_left.mp3": "তুমি কি আমাকে বাম দিকে যেতে বলছো?",
    "ok_left.mp3": "ঠিক আছে, আমি বাম দিকে যাচ্ছি।",
    "confirm_right.mp3": "তুমি কি আমাকে ডান দিকে যেতে বলছো?",
    "ok_right.mp3": "ঠিক আছে, আমি ডান দিকে যাচ্ছি।",
    "confirm_stop.mp3": "তুমি কি আমাকে থামতে বলছো?",
    "ok_stop.mp3": "ঠিক আছে, আমি থামছি।", 
    "name.mp3": "আমার নাম নাও। তোমার সাথে পরিচিত হয়ে ভালো লাগছে।",
    "confirm_rest.mp3": "তুমি কি আমাকে বিশ্রাম নিতে বলছো?",
    "ok_rest.mp3": "ঠিক আছে, আমি বিশ্রাম নিচ্ছি।",    
    "confirm_left_hand.mp3": "তুমি কি আমাকে বাম হাত নাড়াতে বলছো?",
    "ok_left_hand.mp3": "ঠিক আছে, আমি বাম হাত নাড়াচ্ছি।",
    "confirm_right_hand.mp3": "তুমি কি আমাকে ডান হাত নাড়াতে বলছো?",
    "ok_right_hand.mp3": "ঠিক আছে, আমি ডান হাত নাড়াচ্ছি।",
    "confirm_back.mp3": "তুমি কি আমাকে পিছনে যেতে বলছো?",
"ok_back.mp3": "ঠিক আছে, আমি পিছনে যাচ্ছি।",
"confirm_salute.mp3": "তুমি কি আমাকে স্যালুট দিতে বলছো?",
"ok_salute.mp3": "ঠিক আছে, আমি স্যালুট দিচ্ছি।",


}     

os.makedirs("bangla_audio", exist_ok=True)

for filename, text in audio_files.items():
    path = os.path.join("bangla_audio", filename)

    tts = gTTS(text=text, lang="bn")
    tts.save(path)

    print("Generated:", path)

print("\nAll files generated successfully!")