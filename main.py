
import pickle
import os.path
import re
import pyttsx3
import speech_recognition as sr
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from email.mime.text import MIMEText
import base64
import pyaudio
import pygame
import threading
import tkinter as tk
from tkinter import BOTTOM, SUNKEN, W, X, Frame, Label, StringVar, ttk
from tkinter import messagebox
import time

# Define the scope of the Gmail API
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']

WAKE = {"start", "new email", "compose","compose message", "write email", "write new email", "to"}
SUBJECT = "subject"
MESSAGE = "message"
SEND = {"send", "send email", "proceed", "yes"}
STOP = {"stop", "goodbye", "bye", "close", "abort", "cancel"}
INBOX = {"inbox", "read", "open inbox", "read email", "unread emails"}

email_pattern = r"[a-zA-z0-9_.+-]+@[a-zA0-z0-9-]+\.[a-zA-z0-9-.]+"

pattern= r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

# Import tkinter
import tkinter as tk

pygame.mixer.init()

# Create the main window
window = tk.Tk()
window.title("Voice Based Email")
window.geometry("500x400")
window.iconbitmap("images/logo.ico")
window.configure(bg="#f8f8f8")

# Define the voice assistant function
def speak(text):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate-20)
    engine.say(text)
    engine.runAndWait()


# Define the speech recognition function
def get_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.pause_threshold = 1
        r.adjust_for_ambient_noise(source, duration=1)
        audio = r.listen(source)
    said = ""
    try:
        said = r.recognize_google(audio,language="en-US")
        print(said)
        match = re.search(email_pattern, said)
        if match:
            print("email:" + match.group())
    except sr.UnknownValueError:
        # messagebox.showinfo("Error", "Sorry, I didn't catch that.")
        pygame.mixer.music.load("sounds/soryididnotget2.wav")
        pygame.mixer.music.play(loops=0)
    except sr.RequestError:
       # messagebox.showinfo("Error", "Sorry, my speech recognition service is down.")
        pygame.mixer.music.load("sounds/spechservicedown2.wav")
        pygame.mixer.music.play(loops=0)
        #speak("Error", "Sorry, my speech recognition service is down.")
    return said.lower()


# Define the Gmail authentication function
def authenticate_gmail():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except Exception as e:
        speak("An error occurred while authenticating Gmail.")
        speak(str(e))
        return None

# Define the function to open a new window for listing inbox emails
def open_inbox_window():
    def fetch_emails():
        # Authenticate Gmail
        service = authenticate_gmail()
        if service is None:
            messagebox.showerror("Error", "Failed to authenticate Gmail.")
            inbox_window.destroy()
            return

        # Get inbox emails
        try:
            results = service.users().messages().list(userId='me', labelIds=['INBOX']).execute()
            messages = results.get('messages', [])
            if messages:
                for message in messages:
                    msg = service.users().messages().get(userId='me', id=message['id']).execute()
                    payload = msg['payload']
                    headers = payload['headers']
                    for header in headers:
                        if header['name'] == 'Subject':
                            subject = header['value']
                        if header['name'] == 'From':
                            sender = header['value']
                    email_listbox.insert(tk.END, f"From: {sender}\nSubject: {subject}\n")
            else:
                email_listbox.insert(tk.END, "No emails in the inbox.")
        except Exception as e:
            pygame.mixer.music.load("sounds/inbox-error.wav")
            pygame.mixer.music.play(loops=0)
            print("error!")
            inbox_window.destroy()
            return

        # Remove the loading text
        loading_label.destroy()

    def read_email_aloud():
        selected_email = email_listbox.get(email_listbox.curselection())
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[1].id)
        rate = engine.getProperty('rate')
        engine.setProperty('rate', rate-20)
        engine.say(selected_email)
        engine.runAndWait()  

    inbox_window = tk.Toplevel(window)
    inbox_window.title("Inbox")
    inbox_window.geometry("400x300")

    # Create a scrollbar
    scrollbar = ttk.Scrollbar(inbox_window)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Create a listbox to display the emails
    email_listbox = tk.Listbox(inbox_window, yscrollcommand=scrollbar.set,  relief="flat",)
    email_listbox.pack(fill=tk.BOTH, expand=True)

    # Create the function to read email aloud
    def read_email_aloud():
        selected_email = email_listbox.get(email_listbox.curselection())
        engine = pyttsx3.init()
        speak(selected_email)
        engine.runAndWait()

    # Create the button to read email aloud
    read_button = tk.Button(inbox_window, text="Read Aloud", command=read_email_aloud)
    read_button.pack()

    # Configure the scrollbar
    scrollbar.config(command=email_listbox.yview)

    # Add a loading text
    loading_label = tk.Label(inbox_window, text="Loading...")
    loading_label.pack()
    #check_mails(service)

    # Start a new thread to fetch emails
    thread = threading.Thread(target=fetch_emails)
    thread.start()
    pygame.mixer.music.load("sounds/inboxenkuan2.wav")
    pygame.mixer.music.play(loops=0)

# Define the function to check unread emails
def check_mails(service):
    try:
        results = service.users().labels().get(userId='me', id='INBOX').execute()
        messages = results.get('messages', [])
        unread = results.get('messagesUnread')
        speak(f"You have {unread} unread messages in your inbox.")
        if messages:
            for message in messages[:10]:
                msg = service.users().messages().get(userId='me', id=message['id']).execute()
                payload = msg['payload']
                headers = payload['headers']
                for header in headers:
                    if header['name'] == 'Subject':
                        subject = header['value']
                    if header['name'] == 'From':
                        sender = header['value']
                speak(f"From {sender}, subject {subject}")
    except Exception as e:
        speak("An error occurred while checking emails.")
        speak(str(e))


# Define the function to create a message
def create_message(sender, to, subject, message_text):
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes())
    raw = raw.decode()
    body = {'raw': raw}
    return body


# Define the function to send a message
def send_message(service, user_id, message):
    try:
        message = service.users().messages().send(userId=user_id, body=message).execute()
       # speak('Your email has been sent.')
        pygame.mixer.music.load("sounds/email-success.wav")
        pygame.mixer.music.play(loops=0)
    except Exception as e:
        pygame.mixer.music.load("sounds/email-sending-error.wav")
        pygame.mixer.music.play(loops=0)


# Define the function to handle the "Compose" button click event
def compose_email():
    to = to_entry.get()
    subject = subject_entry.get()
    message_text = message_text_entry.get("1.0", tk.END).strip()
    message = create_message("me", to, subject, message_text)
    send_message(service, "me", message)


# Define the function to handle the voice input for message field
def get_message():
    #speak("What is the message of the email?")
    pygame.mixer.music.load("sounds/e-message.wav")
    pygame.mixer.music.play(loops=0)
    message = get_audio()
    message_text_entry.delete("1.0", tk.END)
    message_text_entry.insert(tk.END, message)

# Define the function to handle the voice input for subject field
def get_subject():
    #speak("What is the subject of the email?")
    pygame.mixer.music.load("sounds/subject.wav")
    pygame.mixer.music.play(loops=0)
    subject = get_audio()
    subject_entry.delete(0, tk.END)
    subject_entry.insert(tk.END, subject)
    #get_message()

# Define the function to handle the voice input for recipient field
def get_recipient():
    #speak("Who do you want to send the email to?")
    pygame.mixer.music.load("sounds/to-address.wav")
    pygame.mixer.music.play(loops=0)
    recipient = get_audio()
    to_entry.delete(0, tk.END)
    to_entry.insert(tk.END, recipient)
    time.sleep(3)
    #get_subject()


def voice_command(event=None):
    # Create a recognizer object
    r = sr.Recognizer()
    # Listen to the microphone
    with sr.Microphone() as source:
        #speak("I'm Listening...")
        pygame.mixer.music.load("fx/blip.wav")
        pygame.mixer.music.play(loops=0)
        #r.pause_threshold = 1
        r.adjust_for_ambient_noise(source, duration=1)
        audio = r.listen(source)
    text = ""
    # Try to recognize the speech
    try:
        text = r.recognize_google(audio, language="en-US")
        print("You said:", text)
        # Check if the wake word is in the text
        if any(word in text.lower() for word in WAKE):
            # Print a message
            print("Wake word detected")
            # Get the recipient of the email
            get_recipient()
        # Check if the subject keyword is in the text
        elif SUBJECT in text.lower():
            # Print a message
            print("Subject keyword detected")
            # Get the subject of the email
            get_subject()
        # Check if the message keyword is in the text
        elif MESSAGE in text.lower():
            # Print a message
            print("Message keyword detected")
            # Get the message of the email
            get_message()
        # Check if the send keyword is in the text
        elif any(word in text.lower() for word in SEND):
            # Print a message
            print("Send keyword detected")
            # Send the email
            compose_email()
        # Check if the inbox keyword is in the text
        elif any(word in text.lower() for word in INBOX):
            # Print a message
            print("Inbox keyword detected")
            # Open the inbox window
            open_inbox_window()
        # Check if the stop keyword is in the text
        elif any(word in text.lower() for word in STOP):
            # Print a message
            print("Stop keyword detected")
            # Speak a farewell
            speak("Goodbye")
            # Close the window
            window.destroy()
    except:
        # print("Sorry, I could not understand you")
        pygame.mixer.music.load("fx/error-main.wav")
        pygame.mixer.music.play(loops=0)

pygame.mixer.music.load("sounds/enkuan2.wav")
pygame.mixer.music.play(loops=0)
window.bind("<space>", voice_command)
# Create the Inbox button
inbox_button = tk.Button(window, text="Go to Inbox", command=open_inbox_window, bg="crimson", fg="white", borderwidth="0", cursor="arrow")
inbox_button.grid(row=0, column=0, padx=15, pady=15)
# Create the recipient field
to_label = tk.Label(window, text="To:",bg="#f8f8f8")
to_label.grid(row=1, column=0,)
to_entry = tk.Entry(window, width=50)
to_entry.grid(row=1, column=1,)

# Create the subject field
subject_label = tk.Label(window, text="Subject:",bg="#f8f8f8")
subject_label.grid(row=2, column=0,)
subject_entry = tk.Entry(window, width=50)
subject_entry.grid(row=2, column=1,)

# Create the message field
message_text_label = tk.Label(window, text="Message:",bg="#f8f8f8")
message_text_label.grid(row=3, column=0,)
message_text_entry = tk.Text(window, width=40, height=10)
message_text_entry.grid(row=3, column=1,)



# Create the voice input buttons
recipient_button = tk.Button(window, text="🎙️", command=get_recipient, borderwidth="0", font="Serif",bg="#f8f8f8")
recipient_button.grid(row=1, column=2,padx=5,pady=5)

subject_button = tk.Button(window, text="🎙️", command=get_subject, borderwidth="0", font="Serif", bg="#f8f8f8")
subject_button.grid(row=2, column=2,padx=5,pady=5)

message_button = tk.Button(window, text="🎙️", command=get_message, borderwidth="0", font="Serif",bg="#f8f8f8")
message_button.grid(row=3, column=2,padx=5,pady=5)
# Create the Compose button
compose_button = tk.Button(window, text="Send", command=compose_email, bg="#05f", fg="white", borderwidth="0", font=("Serif", 11), width="7")
compose_button.grid(row=4, column=1,pady=10)

# Authenticate Gmail
service = authenticate_gmail()


# Pack the button
compose_button.grid()


# Start the main event loop
window.after(1000, voice_command)
window.mainloop()