import os
import threading
from google import genai
from google.genai import types
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from plyer import tts, filechooser

class CruiseAIApp(App):
    def build(self):
        self.title = "Cruise AI"
        layout = BoxLayout(orientation='vertical', padding=12, spacing=10)
        
        self.creator_name = "GOPU.SNEHAL REDDY"
        self.conversation_history = []
        self.log_file = "cruise_chat_history.txt"
        self.selected_image_path = None
        
        # Hardcoded API Key
        api_key = "AQ.Ab8RN6JgLKuit_qggktnuGXSdc_ufG5_wwpRsGrU9dOl90K4yQ"
        self.client = genai.Client(api_key=api_key)

        # Scrollable Chat Display
        self.scroll = ScrollView(size_hint=(1, 0.65))
        self.chat_label = Label(
            text=f"[color=00FFFF][b]Cruise AI Active[/b][/color] | Created by {self.creator_name}\n\n",
            size_hint_y=None,
            markup=True,
            valign='top',
            halign='left',
            color=(0.9, 0.9, 0.9, 1)
        )
        self.chat_label.bind(texture_size=self.chat_label.setter('size'))
        self.chat_label.bind(width=lambda instance, value: setattr(instance, 'text_size', (value, None)))
        self.scroll.add_widget(self.chat_label)
        layout.add_widget(self.scroll)

        # Button Row 1
        btn_layout1 = BoxLayout(orientation='horizontal', size_hint=(1, 0.08), spacing=5)
        
        mus_btn = Button(text="30s Music Spec", background_color=(0.1, 0.6, 0.6, 1))
        mus_btn.bind(on_press=self.generate_music_prompt)
        btn_layout1.add_widget(mus_btn)

        vid_btn = Button(text="30s Video+Sound Spec", background_color=(0.8, 0.4, 0.1, 1))
        vid_btn.bind(on_press=self.generate_video_prompt)
        btn_layout1.add_widget(vid_btn)

        cam_btn = Button(text="Upload Image", background_color=(0.6, 0.2, 0.7, 1))
        cam_btn.bind(on_press=self.select_image)
        btn_layout1.add_widget(cam_btn)

        layout.add_widget(btn_layout1)

        # Button Row 2
        btn_layout2 = BoxLayout(orientation='horizontal', size_hint=(1, 0.08), spacing=5)

        save_btn = Button(text="Save Log", background_color=(0.2, 0.7, 0.3, 1))
        save_btn.bind(on_press=self.save_history_to_file)
        btn_layout2.add_widget(save_btn)

        hist_btn = Button(text="Creator Info", background_color=(0.4, 0.4, 0.8, 1))
        hist_btn.bind(on_press=self.show_history_creator)
        btn_layout2.add_widget(hist_btn)

        layout.add_widget(btn_layout2)

        # Text Input Row
        input_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.09), spacing=5)
        
        self.text_input = TextInput(
            hint_text="Ask Cruise AI or type 'Cruise'...",
            multiline=False,
            size_hint=(0.75, 1),
            background_color=(0.15, 0.15, 0.2, 1),
            foreground_color=(1, 1, 1, 1)
        )
        self.text_input.bind(on_text_validate=self.process_input)
        input_layout.add_widget(self.text_input)

        send_button = Button(
            text="Send",
            size_hint=(0.25, 1),
            background_color=(0.0, 0.5, 0.9, 1)
        )
        send_button.bind(on_press=self.process_input)
        input_layout.add_widget(send_button)

        layout.add_widget(input_layout)
        return layout

    def speak(self, text):
        try:
            tts.speak(text)
        except Exception:
            pass

    def process_input(self, instance):
        user_text = self.text_input.text.strip()
        if not user_text and not self.selected_image_path:
            return

        self.text_input.text = ""
        
        if "cruise" in user_text.lower():
            self.chat_label.text += "[color=00FF00][Wake Word Detected][/color]\n"

        self.chat_label.text += f"[b]You:[/b] {user_text}\n"
        self.conversation_history.append(f"You: {user_text}")

        img_path = self.selected_image_path
        self.selected_image_path = None

        threading.Thread(target=self.get_ai_response, args=(user_text, img_path)).start()

    def get_ai_response(self, user_text, image_path=None):
        try:
            if image_path and os.path.exists(image_path):
                with open(image_path, "rb") as f:
                    img_bytes = f.read()
                
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[
                        types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                        f"You are Cruise AI by {self.creator_name}. Describe and analyze this image: {user_text}"
                    ]
                )
            else:
                system_prompt = f"You are Cruise AI, created by {self.creator_name}. Answer this: {user_text}"
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=system_prompt
                )
            
            reply = response.text
            Clock.schedule_once(lambda dt: self.update_chat("Cruise AI", reply))
            self.speak(reply[:150])
        except Exception as e:
            err = str(e)
            Clock.schedule_once(lambda dt: self.update_chat("Error", err))

    def generate_music_prompt(self, instance):
        prompt_req = "Generate a full 30-second Music AI prompt structure (bpm, genres, instruments, key shifts, and progression from 0s to 30s)."
        self.chat_label.text += "[b]System:[/b] Building 30s Music Spec...\n"
        threading.Thread(target=self.get_ai_response, args=(prompt_req, None)).start()

    def generate_video_prompt(self, instance):
        prompt_req = "Generate a full 30-second Cinematic Video + Audio prompt spec with detailed timeline breakdowns for seconds 0-10, 10-20, and 20-30."
        self.chat_label.text += "[b]System:[/b] Building 30s Video Spec...\n"
        threading.Thread(target=self.get_ai_response, args=(prompt_req, None)).start()

    def select_image(self, instance):
        try:
            filechooser.open_file(on_selection=self.on_image_selected)
        except Exception as e:
            self.chat_label.text += f"[color=FF0000]File selector error: {e}[/color]\n"

    def on_image_selected(self, selection):
        if selection:
            self.selected_image_path = selection[0]
            self.chat_label.text += f"[color=00FF00]Image Attached: {os.path.basename(self.selected_image_path)}[/color]\n"

    def save_history_to_file(self, instance):
        try:
            with open(self.log_file, "a") as f:
                for line in self.conversation_history:
                    f.write(f"{line}\n")
            self.chat_label.text += f"[color=00FF00]Saved chat history to {self.log_file}[/color]\n"
        except Exception as e:
            self.chat_label.text += f"[color=FF0000]Save failed: {e}[/color]\n"

    def show_history_creator(self, instance):
        info = f"\n--- [b]APPLICATION INFO[/b] ---\n"
        info += f"[b]Creator:[/b] {self.creator_name}\n"
        info += f"[b]Interactions:[/b] {len(self.conversation_history)}\n"
        info += f"[b]Local Log File:[/b] {self.log_file}\n"
        info += "-------------------------\n\n"
        self.chat_label.text += info

    def update_chat(self, sender, text):
        self.chat_label.text += f"[b]{sender}:[/b] {text}\n\n"
        self.conversation_history.append(f"{sender}: {text}")

if __name__ == '__main__':
    CruiseAIApp().run()
    
