import cv2
import numpy as np
import tkinter as tk
from tkinter import messagebox, font
from PIL import Image, ImageTk
import threading
import requests

# ============ CONFIGURATION ============
URL = 'http://10.143.133.117/stream' # ESP32-CAM Stream URL

# Disease Mapping: (Lower HSV, Upper HSV, BGR Display Color, Disease Name)
DISEASE_MAP = [
    ([0, 0, 0], [30, 255, 80], (20, 54, 101), "Leaf Spot (Brown/Black)"),
    ([0, 0, 180], [180, 50, 255], (255, 255, 255), "Powdery Mildew (White)"),
    ([10, 150, 100], [25, 255, 255], (0, 165, 255), "Rust (Orange/Yellow)"),
    ([20, 100, 50], [35, 255, 150], (0, 200, 255), "Bacterial Blight (Yellow)"),
    ([15, 50, 50], [25, 150, 200], (50, 100, 150), "Leaf Streak (Yellow/Brown)"),
    ([30, 100, 100], [45, 255, 255], (0, 255, 200), "Mosaic Disease (Yellow-Green)"),
    ([40, 50, 100], [70, 150, 255], (144, 238, 144), "Leaf Curl (Light Green)"),
    ([22, 100, 150], [32, 255, 255], (0, 255, 255), "Nitrogen Deficiency (Yellow)"),
    ([25, 50, 150], [35, 100, 255], (150, 255, 255), "Iron Deficiency (Yellow-Green Veins)")
]

class PlantDiseaseApp:
    def __init__(self, window):
        self.window = window
        self.window.title("Plant Disease Monitoring System")
        self.window.geometry("1200x800")
        self.window.configure(bg="#0f172a") # Deep Slate Blue

        # State variables
        self.running = False
        self.roi_size = 250
        self.cap = None

        # Custom Fonts
        self.title_font = font.Font(family="Segoe UI", size=18, weight="bold")
        self.label_font = font.Font(family="Segoe UI", size=10)
        self.status_font = font.Font(family="Segoe UI", size=14, weight="bold")

        # --- UI Layout ---
        # Sidebar
        self.sidebar = tk.Frame(window, width=300, bg="#1e293b", padx=25, pady=30)
        self.sidebar.pack(side="left", fill="y")

        self.title_label = tk.Label(self.sidebar, text="PLANT MONITOR", font=self.title_font, fg="#10b981", bg="#1e293b")
        self.title_label.pack(pady=(0, 40))

        # Action Button
        self.btn_start = tk.Button(self.sidebar, text="START MONITORING", command=self.toggle_stream, 
                                  bg="#10b981", fg="white", font=("Segoe UI", 10, "bold"), 
                                  activebackground="#059669", activeforeground="white",
                                  relief="flat", height=2, width=22, cursor="hand2")
        self.btn_start.pack(pady=10)

        # Control Panel
        tk.Label(self.sidebar, text="Detection Sensitivity (ROI)", bg="#1e293b", fg="#94a3b8", font=self.label_font).pack(pady=(30, 5))
        self.slider_roi = tk.Scale(self.sidebar, from_=100, to=500, orient="horizontal", 
                                  bg="#1e293b", fg="white", highlightthickness=0, 
                                  troughcolor="#334155", activebackground="#10b981",
                                  command=self.update_roi)
        self.slider_roi.set(self.roi_size)
        self.slider_roi.pack(fill="x", pady=10)

        # Diagnosis Card
        self.diag_frame = tk.Frame(self.sidebar, bg="#334155", pady=20, padx=15, highlightthickness=1, highlightbackground="#475569")
        self.diag_frame.pack(fill="x", pady=(40, 0))
        
        tk.Label(self.diag_frame, text="DIAGNOSIS RESULT", bg="#334155", fg="#cbd5e1", font=("Segoe UI", 9, "bold")).pack()
        
        self.lbl_status = tk.Label(self.diag_frame, text="System Offline", fg="#ef4444", bg="#334155", font=("Segoe UI", 10))
        self.lbl_status.pack(pady=(5, 10))
        
        self.lbl_disease = tk.Label(self.diag_frame, text="Healthy / None", fg="#10b981", bg="#334155", 
                                    font=self.status_font, wraplength=220, justify="center")
        self.lbl_disease.pack(pady=(10, 0))

        # Main Viewport
        self.main_view = tk.Frame(window, bg="#0f172a")
        self.main_view.pack(side="right", fill="both", expand=True)

        self.canvas_title = tk.Label(self.main_view, text="Live Plant Analysis Feed", bg="#0f172a", fg="#94a3b8", font=("Segoe UI", 10, "italic"))
        self.canvas_title.pack(pady=(20, 0))

        self.canvas = tk.Canvas(self.main_view, width=800, height=600, bg="#000000", highlightthickness=2, highlightbackground="#1e293b")
        self.canvas.pack(pady=20, padx=20)

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
        self.lbl_status.config(text="Connecting...", fg="#eab308")
        self.window.update()
        
        try:
            self.cap = cv2.VideoCapture(URL)
            if not self.cap.isOpened():
                raise Exception("Could not connect to camera. Check IP address.")
            
            self.running = True
            self.btn_start.config(text="STOP MONITORING", bg="#ef4444", activebackground="#dc2626")
            self.lbl_status.config(text="Monitoring Live", fg="#10b981")
        except Exception as e:
            messagebox.showerror("Connection Error", f"{e}")
            self.lbl_status.config(text="System Error", fg="#ef4444")

    def stop_stream(self):
        self.running = False
        if self.cap:
            self.cap.release()
        self.btn_start.config(text="START MONITORING", bg="#10b981", activebackground="#059669")
        self.lbl_status.config(text="System Offline", fg="#ef4444")
        self.lbl_disease.config(text="Healthy / None", fg="#10b981")
        self.canvas.delete("all")

    def update_frame(self):
        if self.running and self.cap:
            ret, frame = self.cap.read()
            if ret:
                # Process the frame
                processed_frame, detected_disease = self.process_image(frame)
                
                # Update UI
                if detected_disease:
                    self.lbl_disease.config(text=detected_disease, fg="#fbbf24") # Warning color
                else:
                    self.lbl_disease.config(text="Healthy / None", fg="#10b981")

                # Convert to PIL format
                cv2image = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(cv2image)
                img = img.resize((800, 600), Image.Resampling.LANCZOS)
                imgtk = ImageTk.PhotoImage(image=img)
                self.canvas.imgtk = imgtk
                self.canvas.create_image(0, 0, anchor="nw", image=imgtk)
            else:
                self.stop_stream()
                messagebox.showwarning("Connection Lost", "Camera stream was interrupted.")

        self.window.after(10, self.update_frame)

    def process_image(self, frame):
        h, w, _ = frame.shape
        cx, cy = w // 2, h // 2
        
        # Detection Area
        r = self.roi_size // 2
        x1, y1, x2, y2 = cx - r, cy - r, cx + r, cy + r
        
        # Draw Scan Zone
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 1)
        cv2.putText(frame, "DISEASE SCAN ZONE", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        final_disease = None
        
        # Iterate through mapped diseases
        for lower, upper, d_color, d_name in DISEASE_MAP:
            mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
            mask = cv2.dilate(mask, np.ones((5,5), np.uint8))
            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            for cnt in contours:
                if cv2.contourArea(cnt) > 1200: # Sensitivity threshold
                    bx, by, bw, bh = cv2.boundingRect(cnt)
                    ob_cx, ob_cy = bx + bw//2, by + bh//2
                    
                    # Detection logic: must be within Scan Zone
                    if x1 < ob_cx < x2 and y1 < ob_cy < y2:
                        final_disease = d_name
                        cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), d_color, 2)
                        cv2.putText(frame, d_name.split('(')[0], (bx, by - 10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, d_color, 2)
                        break # Stop at first significant detection
            if final_disease: break

        # Center Crosshair with HSV data
        pixel_center = hsv[cy, cx]
        cv2.drawMarker(frame, (cx, cy), (0, 255, 0), cv2.MARKER_CROSS, 20, 2)
        cv2.putText(frame, f"HSV: {pixel_center}", (cx + 15, cy + 15), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

        return frame, final_disease

# Start Application
if __name__ == "__main__":
    root = tk.Tk()
    # Apply a modern theme look if possible
    try:
        root.tk.call('tk_setPalette', '#0f172a')
    except:
        pass
    app = PlantDiseaseApp(root)
    root.mainloop()

