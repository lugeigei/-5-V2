import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading
import logging
import cv2
import numpy as np
from main import FaceAccessSystem
from hardware import OV5647Controller
from face_detector import FaceDetector
from face_recognitiona import FaceRecognizer

class ControlPanel:
    def __init__(self, master):
        self.master = master
        master.title("zhineng menjin xitong")
        master.geometry("800x600")
        
        self.system_running = threading.Event() 
        self.last_event = "xitong wei qidong"
        self.preview_update = False
        
        self.system = FaceAccessSystem()
        self.system.disable_native_window = True
        
        self.create_widgets()
        
        self.preview_thread = threading.Thread(target=self.update_preview)
        self.preview_thread.daemon = True
        self.preview_thread.start()
        
        self.system.log_callback = self.add_event_log
        
    def create_widgets(self):
        status_frame = ttk.Frame(self.master)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_label = ttk.Label(
            status_frame,
            text="xitongzhuangtai: daiji",
            font=('helvetica',12))
        self.status_label.pack(side=tk.LEFT)
        
        self.event_label = ttk.Label(
            status_frame,
            text="zuixin shijian:wu",
            font=('helvetica',12))
        self.event_label.pack(side=tk.RIGHT)
        
        self.preview_label = ttk.Label(self.master)
        self.preview_label.pack(pady=10)
        
        control_frame = ttk.Frame(self.master)
        control_frame.pack(pady=10)
        
        self.start_btn = ttk.Button(
            control_frame,
            text="qidong xitong",
            command=self.toggle_system)
        
        self.start_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            control_frame,
            text="shoudong zhuce",
            command=self.show_register_dialog
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame,
            text="chakan rezhi",
            command=self.show_logs
        ).pack(side=tk.LEFT, padx=5)
        
        log_frame = ttk.Frame(self.master)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = tk.Text(
            log_frame,
            height=8,
            state=tk.DISABLED
        )
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
    def toggle_system(self):
        if not self.system_running.is_set():
            self.system_running.set()
            self.start_btn.config(text="tingzhi xitong")
            self.status_label.config(text="xitong zhuangtai: yunxingzhong")
            self.system_thread = threading.Thread(target=self.start_system)
            self.system_thread.start()
        else:
            self.system.shutdown()

    def start_system(self):
        self.system.running = True
        try:
            self.system.run_without_window()
        except Exception as e:
            logging.error(f"xitongyun xingyichang: {str(e)}")
    
    def shutdown_system(self):
        try:
            self.system.running = False
            self.system_running.clear()
            if hasattr(self, 'system_thread') and self.system_thread.is_alive():
                self.system_thread.join(timeout=2)
            
            self.system.hardware.cleanup()
            self.master.after(0, lambda: (
                self.start_btn.config(text="qidong xitong"),
                self.status_label.config(text="xitong zhuangtai: yi tingzhi")))
        except Exception as e:
            logging.error(f"guanbi xingyichang:{str(e)}")
    
    def update_preview(self):
        try:
            while True:
                default_img = np.zeros((480, 640, 3), dtype=np.uint8)
                img = Image.fromarray(default_img)
                imgtk = ImageTk.PhotoImage(image=img)
                
                if self.system.running and hasattr(self.system, 'frame_buffer'):
                    if len(self.system.frame_buffer) > 0:
                        frame = self.system.frame_buffer[-1]
                        #img = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                        #display_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                        resized_frame = cv2.resize(frame, (640, 480))
                        resized_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
                        img = Image.fromarray(resized_frame)
                        imgtk = ImageTk.PhotoImage(image=img)
                self.preview_label.config(image=imgtk)
                self.preview_label.image = imgtk
                self.master.update_idletasks()
        except Exception as e:
            logging.error(f"liulan chuangkou yichang: {str(e)}")
            
                
    def show_register_dialog(self):
        def register_thread():
            try:
                hardware = self.system.hardware
                original_running_state = self.system.running
                self.system.running = False
                
                from register import main
                main(hardware)
                
                self.system.running = original_running_state
                messagebox.showinfo("zhuce wancheng","yonghu zhuce wancheng")
            except Exception as e:
                messagebox.showerror("zhuce shibai",f"cuowu: {str(e)}")
        threading.Thread(target=register_thread, daemon=True).start()
        
        
    def show_logs(self):
        try:
            with open('access.log','r') as f:
                logs = f.read()
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, logs)
            self.log_text.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("cuowu",f"duqu rezhishibai:{str(e)}")
    
    def add_event_log(self, event):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, event + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.event_label.config(text=f"zuixin shijian: {event}")
        
if __name__ == "__main__":
    root = tk.Tk()
    app = ControlPanel(root)
    root.mainloop()
    