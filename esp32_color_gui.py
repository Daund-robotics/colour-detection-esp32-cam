import cv2
import numpy as np
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import threading
import requests

# ============ CONFIGURATION ============
URL = 'http://10.143.133.117/stream' # ESP32-CAM Stream URL

class ColorDetectionApp:
    def __init__(self, window):
        self.window = window
        self.window.title("Tronix - ESP32 Color Vision Pro")
        self.window.geometry("1100x700")
        self.window.configure(bg="#1e1e1e") # Dark theme

        # State variables
        self.running = False
        self.roi_size = 220
        self.cap = None

        # --- UI Layout ---
        # Sidebar
        self.sidebar = tk.Frame(window, width=250, bg="#2d2d2d", padx=20, pady=20)
        self.sidebar.pack(side="left", fill="y")

        self.title_label = tk.Label(self.sidebar, text="COLOR VISION", font=("Helvetica", 18, "bold"), fg="#00ffcc", bg="#2d2d2d")
        self.title_label.pack(pady=(0, 30))

        # Buttons
        self.btn_start = tk.Button(self.sidebar, text="START STREAM", command=self.toggle_stream, 
                                  bg="#00ffcc", fg="black", font=("Helvetica", 10, "bold"), 
                                  activebackground="#00cca3", relief="flat", height=2, width=20)
        self.btn_start.pack(pady=10)

        # Controls
        tk.Label(self.sidebar, text="Detection Range", bg="#2d2d2d", fg="white", font=("Helvetica", 9)).pack(pady=(20, 5))
        self.slider_roi = tk.Scale(self.sidebar, from_=100, to=400, orient="horizontal", 
                                  bg="#2d2d2d", fg="white", highlightthickness=0, command=self.update_roi)
        self.slider_roi.set(self.roi_size)
        self.slider_roi.pack(fill="x", pady=10)

        # Status Panel
        self.status_frame = tk.Frame(self.sidebar, bg="#3d3d3d", pady=15, padx=10)
        self.status_frame.pack(fill="x", pady=20)
        
        self.lbl_status = tk.Label(self.status_frame, text="Status: Offline", fg="#ff4444", bg="#3d3d3d", font=("Helvetica", 10))
        self.lbl_status.pack()
        
        self.lbl_detected = tk.Label(self.status_frame, text="Detected: None", fg="#ffffff", bg="#3d3d3d", font=("Helvetica", 12, "bold"))
        self.lbl_detected.pack(pady=(10, 0))

        # Main Viewport
        self.main_view = tk.Frame(window, bg="#1e1e1e")
        self.main_view.pack(side="right", fill="both", expand=True)

        self.canvas = tk.Canvas(self.main_view, width=800, height=600, bg="#000000", highlightthickness=0)
        self.canvas.pack(pady=20)

        # Start detection loop
        self.update_frame()

    def update_roi(self, val):
        self.roi_size = int(val)

    def toggle_stream(self):
        if not self.running:
            self.start_stream()
        else:
            self.stop_stream()

    def start_stream(self):
        self.lbl_status.config(text="Status: Connecting...", fg="#ffff00")
        self.window.update()
        
        try:
            # OpenCV handles MJPEG streams via URL
            self.cap = cv2.VideoCapture(URL)
            if not self.cap.isOpened():
                raise Exception("Could not open stream. Check IP.")
            
            self.running = True
            self.btn_start.config(text="STOP STREAM", bg="#ff4444")
            self.lbl_status.config(text="Status: Live", fg="#00ffcc")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect to ESP32-CAM:\n{e}")
            self.lbl_status.config(text="Status: Error", fg="#ff4444")

    def stop_stream(self):
        self.running = False
        if self.cap:
            self.cap.release()
        self.btn_start.config(text="START STREAM", bg="#00ffcc")
        self.lbl_status.config(text="Status: Offline", fg="#ff4444")
        self.lbl_detected.config(text="Detected: None")
        self.canvas.delete("all")

    def update_frame(self):
        if self.running and self.cap:
            ret, frame = self.cap.read()
            if ret:
                # Process the frame
                processed_frame, detected_color = self.process_image(frame)
                
                # Update UI elements
                if detected_color:
                    self.lbl_detected.config(text=f"Detected: {detected_color}")
                else:
                    self.lbl_detected.config(text="Detected: None")

                # Convert to PIL format
                cv2image = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(cv2image)
                # Scale to fit canvas if needed
                img = img.resize((800, 600), Image.Resampling.LANCZOS)
                imgtk = ImageTk.PhotoImage(image=img)
                self.canvas.imgtk = imgtk
                self.canvas.create_image(0, 0, anchor="nw", image=imgtk)
            else:
                self.stop_stream()
                messagebox.showwarning("Connection Lost", "The stream has disconnected.")

        # Schedule next update
        self.window.after(10, self.update_frame)

    def process_image(self, frame):
        h, w, _ = frame.shape
        cx, cy = w // 2, h // 2
        
        # Detection Area
        r = self.roi_size // 2
        x1, y1, x2, y2 = cx - r, cy - r, cx + r, cy + r
        
        # Draw ROI Box
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 1)
        cv2.putText(frame, "Scan Zone", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        colors = {
            "Red": ([0, 120, 70], [10, 255, 255]),
            "Green": ([35, 100, 40], [85, 255, 255]),
            "Blue": ([90, 80, 2], [130, 255, 255]),
            "Yellow": ([20, 100, 100], [35, 255, 255]),
        }
        
        # Extra range for red
        red_mask_extra = cv2.inRange(hsv, np.array([170, 120, 70]), np.array([180, 255, 255]))

        final_detected = None
        
        for name, (lower, upper) in colors.items():
            mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
            if name == "Red":
                mask = cv2.bitwise_or(mask, red_mask_extra)
            
            mask = cv2.dilate(mask, np.ones((5,5), np.uint8))
            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            for cnt in contours:
                if cv2.contourArea(cnt) > 1500:
                    bx, by, bw, bh = cv2.boundingRect(cnt)
                    ob_cx, ob_cy = bx + bw//2, by + bh//2
                    
                    # Check if center is in ROI
                    if x1 < ob_cx < x2 and y1 < ob_cy < y2:
                        final_detected = name
                        # BGR Colors for drawing
                        draw_color = (0, 0, 0)
                        if name == "Red": draw_color = (0, 0, 255)
                        elif name == "Green": draw_color = (0, 255, 0)
                        elif name == "Blue": draw_color = (255, 0, 0)
                        elif name == "Yellow": draw_color = (0, 255, 255)
                        
                        cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), draw_color, 3)
                        cv2.putText(frame, name, (bx, by - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.8, draw_color, 2)

        # Center crosshair color info
        pixel_center = hsv[cy, cx]
        cv2.circle(frame, (cx, cy), 5, (255, 255, 255), -1)
        cv2.putText(frame, f"H:{pixel_center[0]} S:{pixel_center[1]} V:{pixel_center[2]}", 
                    (cx + 15, cy + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        return frame, final_detected

# Start Application
if __name__ == "__main__":
    root = tk.Tk()
    app = ColorDetectionApp(root)
    root.mainloop()
