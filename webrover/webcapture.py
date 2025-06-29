import cv2
import numpy as np
import mss
import threading
import time

drawing = False
ix, iy = -1, -1
capture_box = None
selection_done = False
preview_frame = None

def draw_rectangle(event, x, y, flags, param):
    global ix, iy, drawing, capture_box, preview_frame, selection_done

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y

    elif event == cv2.EVENT_MOUSEMOVE and drawing:
        temp_frame = preview_frame.copy()
        cv2.rectangle(temp_frame, (ix, iy), (x, y), (0, 255, 0), 2)
        cv2.imshow("Select Area", temp_frame)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        ex, ey = x, y
        x1, y1 = min(ix, ex), min(iy, ey)
        x2, y2 = max(ix, ex), max(iy, ey)
        w, h = x2 - x1, y2 - y1

        if w > 0 and h > 0:
            capture_box = {"top": y1, "left": x1, "width": w, "height": h}
            selection_done = True
            print(f"✅ Capture box set: {capture_box}")
        else:
            print("❌ Invalid selection area.")

def select_area():
    global preview_frame
    try:
        with mss.mss() as sct:
            screen = sct.monitors[1]
            img = np.array(sct.grab(screen))
            preview_frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        # Resize preview if too large
        height, width = preview_frame.shape[:2]
        if width > 1920 or height > 1080:
            scale = min(1920/width, 1080/height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            preview_frame = cv2.resize(preview_frame, (new_width, new_height))

        cv2.namedWindow("Select Area", cv2.WINDOW_NORMAL)
        cv2.setMouseCallback("Select Area", draw_rectangle)
        cv2.imshow("Select Area", preview_frame)
        
        print("Press any key after making selection...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        # Give time for window cleanup
        time.sleep(0.5)
        
    except Exception as e:
        print(f"Error in select_area: {e}")
        cv2.destroyAllWindows()

def capture_loop(box):
    try:
        cv2.namedWindow("Captured Area", cv2.WINDOW_NORMAL)
        
        with mss.mss() as sct:
            frame_count = 0
            while True:
                try:
                    img = np.array(sct.grab(box))
                    frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                    
                    # Add frame counter for debugging
                    cv2.putText(frame, f"Frame: {frame_count}", (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    cv2.imshow("Captured Area", frame)
                    frame_count += 1

                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break
                    elif key == ord('s'):
                        filename = f"capture_{int(time.time())}.jpg"
                        cv2.imwrite(filename, frame)
                        print(f"💾 Saved: {filename}")
                        
                except Exception as e:
                    print(f"Error capturing frame: {e}")
                    break

    except Exception as e:
        print(f"Error in capture_loop: {e}")
    finally:
        cv2.destroyAllWindows()

# Alternative: Headless capture function
def headless_capture(box, duration=10):
    """Capture without GUI - useful for debugging"""
    print(f"🎥 Headless capture for {duration} seconds...")
    
    with mss.mss() as sct:
        start_time = time.time()
        frame_count = 0
        
        while time.time() - start_time < duration:
            try:
                img = np.array(sct.grab(box))
                frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                
                # Save every 30th frame
                if frame_count % 30 == 0:
                    filename = f"headless_capture_{frame_count}.jpg"
                    cv2.imwrite(filename, frame)
                    print(f"💾 Saved: {filename}")
                
                frame_count += 1
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                print(f"Error in headless capture: {e}")
                break
    
    print(f"Captured {frame_count} frames")

if __name__ == "__main__":
    # Check OpenCV version and backend
    print(f"OpenCV version: {cv2.__version__}")
    print(f"OpenCV backends: {cv2.getBuildInformation().split('GUI')[1].split('OpenCL')[0]}")
    
    try:
        print("📸 Click and drag to select screen area")
        select_area()

        if capture_box and selection_done:
            print("🎥 Starting capture. Press 'q' to quit, 's' to save frame.")
            
            # Ask user for capture mode
            mode = input("Choose mode: (1) GUI capture, (2) Headless capture [1]: ").strip()
            
            if mode == "2":
                duration = int(input("Duration in seconds [10]: ") or "10")
                headless_capture(capture_box, duration)
            else:
                capture_loop(capture_box)
        else:
            print("⚠️ No area selected. Exiting.")
            
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        cv2.destroyAllWindows()
