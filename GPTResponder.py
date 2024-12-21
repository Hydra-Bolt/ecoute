import openai
from keys import OPENAI_API_KEY
from prompts import create_prompt, INITIAL_RESPONSE
import time
import base64
from io import BytesIO
from PIL import Image


openai.api_key = OPENAI_API_KEY


class GPTResponder:
    gen_now = False
    freezed = True

    def __init__(self, resume_text=None, custom_instructions_input=None):
        self.response = INITIAL_RESPONSE
        self.response_interval = 2
        self.resume = resume_text
        self.custom_instructions_input = custom_instructions_input

    def image_to_base64(self, image: Image.Image) -> str:
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"

    def generate_response_from_transcript(
        self, transcript, custom_instructions=None, image=None
    ):
        try:
            messages = [
                {
                    "role": "system",
                    "content": create_prompt(
                        transcript, self.resume, custom_instructions
                    ),
                }
            ]
            if image:
                buffered = BytesIO()
                image.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": self.image_to_base64(image)},
                            }
                        ],
                    }
                )

            response = openai.ChatCompletion.create(
                model="gpt-4o-mini", messages=messages, temperature=0.0
            )
        except Exception as e:
            print(e)
            return ""
        full_response = response.choices[0].message.content
        try:
            return full_response
        except:
            return ""

    def respond_to_transcriber(self, transcriber):
        while True:
            if transcriber.transcript_changed_event.is_set() and not self.freezed:
                start_time = time.time()

                transcriber.transcript_changed_event.clear()
                transcript_string = transcriber.get_transcript()
                response = self.generate_response_from_transcript(
                    transcript_string, self.custom_instructions_input.get()
                )

                end_time = time.time()  # Measure end time
                execution_time = (
                    end_time - start_time
                )  # Calculate the time it took to execute the function

                self.update_response(response)

                remaining_time = self.response_interval - execution_time
                if remaining_time > 0:
                    time.sleep(remaining_time)
            else:
                time.sleep(0.3)
    def update_freeze(self, freezed):
        self.freezed = freezed
    def update_response(self, response):
        if response != "":
            self.response = response

    def update_cv(self, resume_text):
        self.resume = resume_text


    def update_response_interval(self, interval):
        self.response_interval = interval
