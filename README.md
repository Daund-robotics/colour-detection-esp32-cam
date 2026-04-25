# ESP32-CAM Color Detection Workstation

A professional computer vision application designed to identify colors using an ESP32-CAM MJPEG stream.

## 🚀 Features
- **Real-time Color Detection**: Identifies Red, Green, Blue, Yellow, and Orange.
- **Modern GUI**: Built with Tkinter for a sleek, dark-themed user experience.
- **Adjustable Scan Zone**: Focus detection only on the center of the frame to avoid noise.
- **Precision Calibration**: Displays real-time HSV values for any pixel under the center crosshair.
- **ESP32-CAM Integration**: Optimized for the provided custom MJPEG streaming firmware.

## 🛠️ Hardware Requirements
- ESP32-CAM (AI-Thinker model recommended)
- Stable WiFi connection

## 📂 Project Structure
- `esp32_color_gui.py`: Main GUI application.
- `color_detection.py`: Simple standalone detection script.
- `requirements.txt`: Python dependencies.
- `ESP32_Code/`: (Backup of the Arduino code provided).

## 📥 Installation
1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 🖥️ Usage
1. Upload the provided Arduino code to your ESP32-CAM.
2. Note the IP address displayed in the Serial Monitor.
3. Update the `URL` in `esp32_color_gui.py` if different.
4. Run the application:
   ```bash
   python esp32_color_gui.py
   ```
5. Click **START STREAM** to begin.

---
Built with ❤️ for Tronix Project.
