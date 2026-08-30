import os
import json
import base64
import threading
import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform

# Native Android Speech Import
if platform == 'android':
    from jnius import autoclass
    TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
    Locale = autoclass('java.util.Locale')
    PythonActivity = autoclass('org.kivy.android.PythonActivity')

class CruiseAIApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.creator_name = "GOPU.SNEHAL REDDY"
        self.log_file = "cruise_chat_history.txt"
        
        # Token and API Keys list including your provided token
        self.api_keys = [
            "AQ.Ab8RN6Icpk4CZ9dEvNWsArDUm1XoyLdKCnWpFbCrDmqHBiGyhA",
            "YOUR_SECONDARY_AIzaSy_KEY_HERE"
        ]
        self.current_key_index = 0
        self.selected_file_path = None
        self.tts = None

    def on_start(self):
        if platform == 'android':
            try:
                activity = PythonActivity.mActivity
                self.tts = TextToSpeech(activity, None)
                self.tts.setLanguage(Locale.US)
            except Exception as e:
                print(f"Android TTS Init Error: {e}")

    def get_active_key(self):
        return self.api_keys[self.current_key_index].strip()

    def switch_to_next_key(self):
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        print(f"Switched to API Key/Token index: {self.current_key_index}")

    def build(self):
        Window.clearcolor = (0.07, 0.07, 0.08, 1)
        root = BoxLayout(orientation='vertical', padding=12, spacing=10)

        # Chat Display Area
        self.scroll = ScrollView(size_hint=(1, 0.65))
        self.chat_logs = Label(
            text=f"[color=8ab4f8]--- CRUISE AI ---[/color]\nCreator: {self.creator_name}\nStatus: Ready\n" + "-"*35 + "\n",
            size_hint_y=None,
            markup=True,
            color=(0.9, 0.9, 0.9, 1),
            halign='left',
            valign='top'
        )
        self.chat_logs.bind(texture_size=self.chat_logs.setter('size'))
        self.chat_logs.bind(width=lambda instance, value: setattr(instance, 'text_size', (value, None)))
        self.scroll.add_widget(self.chat_logs)
        root.add_widget(self.scroll)

        # Action Buttons Layout
        btn_grid = GridLayout(cols=3, size_hint=(1, 0.15), spacing=6)
        
        btn_spec1 = Button(text="30s Music Spec", background_color=(0.12, 0.25, 0.45, 1), color=(1, 1, 1, 1))
        btn_spec1.bind(on_press=lambda x: self.send_preset("Provide a detailed 30-second music specification format."))
        
        btn_spec2 = Button(text="30s Video+Sound Spec", background_color=(0.3, 0.2, 0.45, 1), color=(1, 1, 1, 1))
        btn_spec2.bind(on_press=lambda x: self.send_preset("Provide a detailed 30-second video and sound specification outline."))
        
        btn_upload = Button(text="Upload Media", background_color=(0.2, 0.35, 0.4, 1), color=(1, 1, 1, 1))
        btn_upload.bind(on_press=self.mock_media_upload)

        btn_save = Button(text="Save Log", background_color=(0.15, 0.3, 0.2, 1), color=(1, 1, 1, 1))
        btn_save.bind(on_press=self.save_log)

        btn_info = Button(text="Creator Info", background_color=(0.2, 0.2, 0.25, 1), color=(1, 1, 1, 1))
        btn_info.bind(on_press=self.show_creator_info)

        btn_grid.add_widget(btn_spec1)
        btn_grid.add_widget(btn_spec2)
        btn_grid.add_widget(btn_upload)
        btn_grid.add_widget(btn_save)
        btn_grid.add_widget(btn_info)
        root.add_widget(btn_grid)

        # Input Row Layout
        input_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), spacing=6)
        self.text_input = TextInput(
            hint_text="Ask Cruise AI or type 'Cruise'...",
            multiline=False,
            background_color=(0.18, 0.19, 0.2, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(0.54, 0.7, 0.97, 1)
        )
        self.text_input.bind(on_text_validate=self.send_message)
        
        btn_send = Button(text="Send", size_hint_x=0.25, background_color=(0.54, 0.7, 0.97, 1), color=(0.07, 0.07, 0.08, 1))
        btn_send.bind(on_press=self.send_message)

        input_layout.add_widget(self.text_input)
        input_layout.add_widget(btn_send)
        root.add_widget(input_layout)

        return root

    def update_chat(self, sender, message):
        if sender == "You":
            color_tag = "[color=c58af9]"
        elif sender == "Cruise AI":
            color_tag = "[color=8ab4f8]"
        else:
            color_tag = "[color=888888]"
            
        self.chat_logs.text += f"\n{color_tag}[b]{sender}:[/b][/color] {message}\n"
        Clock.schedule_once(lambda dt: setattr(self.scroll, 'scroll_y', 0), 0.1)

    def speak(self, text):
        def _speak_thread():
            try:
                clean_text = text.replace("[color=", "").replace("[/color]", "").replace("[b]", "").replace("[/b]", "")
                if platform == 'android' and self.tts:
                    self.tts.speak(clean_text[:250], TextToSpeech.QUEUE_FLUSH, None, None)
            except Exception as e:
                print(f"Native TTS Error: {e}")

        threading.Thread(target=_speak_thread, daemon=True).start()

    def send_preset(self, text):
        self.update_chat("System", f"Building prompt: {text[:20]}...")
        threading.Thread(target=self.get_ai_response, args=(text,), daemon=True).start()

    def send_message(self, instance=None):
        user_text = self.text_input.text.strip()
        if not user_text:
            return
        
        self.update_chat("You", user_text)
        self.text_input.text = ""
        
        file_path = self.selected_file_path
        self.selected_file_path = None
        
        threading.Thread(target=self.get_ai_response, args=(user_text, file_path), daemon=True).start()

    def mock_media_upload(self, instance):
        self.update_chat("System", "Media mode active. Enter your prompt to analyze video or image inputs.")

    def show_creator_info(self, instance):
        info = f"\n--- APPLICATION INFO ---\nCreator: {self.creator_name}\nLocal Log File: {self.log_file}\n" + "-"*25
        self.update_chat("Cruise AI", info)

    def save_log(self, instance):
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(self.chat_logs.text)
            self.update_chat("System", f"Chat history saved to {self.log_file}")
        except Exception as e:
            self.update_chat("System", f"Failed to save log: {str(e)}")

    def get_ai_response(self, user_text, file_path=None):
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
            
            headers = {
                'Content-Type': 'application/json',
                'x-goog-api-key': self.get_active_key()
            }
            
            parts = []
            if file_path and os.path.exists(file_path):
                mime_type = "video/mp4" if file_path.endswith(".mp4") else "image/jpeg"
                with open(file_path, "rb") as f:
                    encoded_string = base64.b64encode(f.read()).decode('utf-8')
                parts.append({
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": encoded_string
                    }
                })

            parts.append({"text": f"You are Cruise AI created by {self.creator_name}. Answer this: {user_text}"})
            payload = {"contents": [{"parts": parts}]}

            response = requests.post(url, headers=headers, json=payload, timeout=60)
            res_json = response.json()
            
            if "error" in res_json:
                self.switch_to_next_key()
                self.get_ai_response(user_text, file_path)
                return

            if "candidates" in res_json:
                reply = res_json["candidates"][0]["content"]["parts"][0]["text"]
            else:
                reply = f"API Error: {res_json.get('error', {}).get('message', 'Unknown response error')}"

            Clock.schedule_once(lambda dt: self.update_chat("Cruise AI", reply))
            self.speak(reply)
        except Exception as e:
            err = str(e)
            Clock.schedule_once(lambda dt: self.update_chat("Error", err))

if __name__ == "__main__":
    CruiseAIApp().run()
                    
