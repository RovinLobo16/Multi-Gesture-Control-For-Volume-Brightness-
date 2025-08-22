import cv2
import mediapipe as mp
import numpy as np
import screen_brightness_control as sbc
import math
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import time
import ctypes  

from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))

vol_min, vol_max = volume.GetVolumeRange()[:2]

mpHands = mp.solutions.hands
hands = mpHands.Hands(max_num_hands=1)
mpDraw = mp.solutions.drawing_utils


fingerTips = [4, 8, 12, 16, 20]  


cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

root = tk.Tk()
root.title("Multi-Gesture Brightness & Volume Control")

video_label = tk.Label(root)
video_label.pack()


progress = ttk.Progressbar(root, orient='horizontal', length=300, mode='determinate', maximum=100)
progress.pack(pady=10)


def take_screenshot():
    ret, frame = cap.read()
    if ret:
        cv2.imwrite("screenshot.jpg", frame)

tk.Button(root, text="Take Screenshot", command=take_screenshot).pack(pady=5)


def set_manual_brightness(val):
    val = int(val)
    sbc.set_brightness(val)
    progress['value'] = val

slider = tk.Scale(root, from_=20, to=100, orient=tk.HORIZONTAL, label="Manual Brightness", command=set_manual_brightness)
slider.pack(pady=5)


def fingers_up(lmList):
    up = []
    if lmList[fingerTips[0]][0] > lmList[fingerTips[0] - 1][0]:  
        up.append(1)
    else:
        up.append(0)
    for tip in fingerTips[1:]:
        up.append(1 if lmList[tip][1] < lmList[tip - 2][1] else 0)
    return up


def find_distance(p1, p2):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def update_frame():
    success, img = cap.read()
    if not success:
        return

    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)

    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            lmList = []
            for id, lm in enumerate(handLms.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                lmList.append((cx, cy))

            mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS)

            if lmList:
                fingers = fingers_up(lmList)
                totalFingers = sum(fingers)

                
                if fingers == [0, 1, 1, 0, 0]:
                    x1, y1 = lmList[8]  
                    x2, y2 = lmList[12] 
                    length = find_distance((x1, y1), (x2, y2))
                    vol = np.interp(length, [15, 150], [vol_min, vol_max])
                    volume.SetMasterVolumeLevel(vol, None)
                    cv2.putText(img, "Volume Mode", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                
                elif fingers == [1, 1, 0, 0, 0]:
                    x1, y1 = lmList[4]   
                    x2, y2 = lmList[8]   
                    length = find_distance((x1, y1), (x2, y2))
                    brightness = np.interp(length, [15, 200], [20, 100])
                    sbc.set_brightness(int(brightness))
                    progress['value'] = int(brightness)
                    slider.set(int(brightness))
                    cv2.putText(img, f"Brightness: {int(brightness)}%", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

                
                elif fingers == [1, 1, 1, 1, 1]:
                    sbc.set_brightness(50)
                    progress['value'] = 50
                    slider.set(50)
                    cv2.putText(img, "Reset Brightness", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

                
                elif fingers == [0, 0, 0, 0, 0]:
                    sbc.set_brightness(20)
                    progress['value'] = 20
                    slider.set(20)
                    cv2.putText(img, "Dim Mode", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 100, 255), 2)

    
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img)
    imgtk = ImageTk.PhotoImage(image=img_pil)
    video_label.imgtk = imgtk
    video_label.configure(image=imgtk)
    video_label.after(10, update_frame)

update_frame()
root.mainloop()

cap.release()
cv2.destroyAllWindows()
