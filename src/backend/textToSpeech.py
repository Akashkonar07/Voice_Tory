import tkinter as tk
import speech_recognition as sr
import pyaudio
from tkinter import messagebox

def speech_to_text():
    """Convert speech to text and display it in the text entry widget."""
    recognizer = sr.Recognizer()
    
    try:
        with sr.Microphone() as source:
            # Update status to show we're listening
            status_label.config(text="Listening... Speak now", fg="blue")
            root.update()
            
            # Adjust for ambient noise and listen
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
        # Update status to show we're processing
        status_label.config(text="Processing...", fg="orange")
        root.update()
        
        # Recognize speech
        text = recognizer.recognize_google(audio)
        
        # Clear existing text and insert new text
        text_entry.delete("1.0", "end")
        text_entry.insert("end", text)
        
        # Update status to show success
        status_label.config(text="Speech recognized successfully!", fg="green")
        
    except sr.UnknownValueError:
        status_label.config(text="Could not understand audio. Please try again.", fg="red")
    except sr.RequestError as e:
        status_label.config(text=f"Could not request results: {e}", fg="red")
    except sr.WaitTimeoutError:
        status_label.config(text="No speech detected. Please try again.", fg="red")
    except Exception as e:
        status_label.config(text=f"An error occurred: {e}", fg="red")
    
    # Reset status after 3 seconds
    root.after(3000, lambda: status_label.config(text="Ready to listen", fg="black"))

def start_listening():
    """Start the speech-to-text process."""
    speech_to_text()

# GUI setup
root = tk.Tk()
root.title("Speech to Text Converter")
root.geometry("500x400")
root.resizable(False, False)

# Title label
title_label = tk.Label(root, text="Speech to Text Converter", font=("Arial", 16, "bold"))
title_label.pack(pady=10)

# Status label
global status_label
status_label = tk.Label(root, text="Ready to listen", font=("Arial", 10), fg="black")
status_label.pack(pady=5)

# Instructions
instructions_label = tk.Label(root, text="Click the button below and speak into your microphone", font=("Arial", 10))
instructions_label.pack(pady=5)

# Text entry for displaying recognized speech
text_entry_label = tk.Label(root, text="Recognized Speech:", font=("Arial", 10, "bold"))
text_entry_label.pack(pady=(10, 0))

text_entry = tk.Text(root, height=8, width=60, font=("Arial", 10))
text_entry.pack(pady=5)

# Button frame
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

# Listen button
listen_button = tk.Button(button_frame, text="🎤 Start Listening", command=start_listening, 
                        bg="#4CAF50", fg="white", font=("Arial", 12, "bold"),
                        padx=20, pady=10)
listen_button.pack(side=tk.LEFT, padx=5)

# Clear button
clear_button = tk.Button(button_frame, text="Clear Text", command=lambda: text_entry.delete("1.0", "end"),
                        bg="#f44336", fg="white", font=("Arial", 12),
                        padx=20, pady=10)
clear_button.pack(side=tk.LEFT, padx=5)

# Exit button
exit_button = tk.Button(button_frame, text="Exit", command=root.quit,
                       bg="#757575", fg="white", font=("Arial", 12),
                       padx=20, pady=10)
exit_button.pack(side=tk.LEFT, padx=5)

# Footer info
footer_label = tk.Label(root, text="Make sure your microphone is working and internet connection is active", 
                       font=("Arial", 8), fg="gray")
footer_label.pack(pady=10)

root.mainloop()
