import threading
from AudioTranscriber import AudioTranscriber
import CTKSeperator
from GPTResponder import GPTResponder
import customtkinter as ctk
import AudioRecorder 
import queue
import time
import sys
import TranscriberModels
import subprocess
from docx import Document
import PyPDF2
from PIL import Image, ImageGrab

def write_in_textbox(textbox, text):
    textbox.delete("0.0", "end")
    textbox.insert("0.0", text)

def read_pdf(file_path):
    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page_num in range(len(reader.pages)):
            text += reader.pages[page_num].extract_text()
    return text

def read_docx(file_path):
    doc = Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

def get_job_role():
    job_role = ctk.CTkInputDialog(text="Please enter the job role:", title="Job Role").get_input()
    return job_role

def upload_cv(responder, resume_label):
def upload_cv(responder, resume_label):
    file_path = ctk.filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf"), ("Word files", "*.docx")])
    if file_path:
        print(f"File uploaded: {file_path}")
        resume_label.configure(text=f"Resume: {file_path.split('/')[-1]}")
        resume_label.configure(text=f"Resume: {file_path.split('/')[-1]}")
        if file_path.endswith(".pdf"):
            cv_text = read_pdf(file_path)
        elif file_path.endswith(".docx"):
            cv_text = read_docx(file_path)
        else:
            print("Unsupported file type.")
            return
        
        job_role = get_job_role()
        if job_role:
            cv_text += f"\n\nJob Description: {job_role}"
            cv_text += f"\n\nJob Description: {job_role}"
        
        responder.update_cv(cv_text)
    else:
        resume_label.configure(text="No resume uploaded")
    else:
        resume_label.configure(text="No resume uploaded")

def update_transcript_UI(transcriber, textbox):
    transcript_string = transcriber.get_transcript()
    write_in_textbox(textbox, transcript_string)
    textbox.after(300, update_transcript_UI, transcriber, textbox)

def update_response_UI(responder, textbox, freeze_state):
    if not freeze_state[0] or responder.gen_now:
        response = responder.response

        textbox.configure(state="normal")
        write_in_textbox(textbox, response)
        textbox.configure(state="disabled")

        responder.gen_now = False

    textbox.after(300, update_response_UI, responder, textbox, freeze_state)

def clear_context(transcriber, audio_queue):
    transcriber.clear_transcript_data()
    with audio_queue.mutex:
        audio_queue.queue.clear()

def generate_response(transcriber, responder, custom_instructions_menu, generate_response_button, image_label):
    generate_response_button.configure(text="Generating...")
    _gen_res(transcriber, responder, custom_instructions_menu, image_label)
    generate_response_button.configure(text="Generate Response")

def _gen_res(transcriber, responder, custom_instructions_menu, image_label):
    if hasattr(image_label, 'image'):
        image = image_label.image._light_image
    else:
        image = None

    text = transcriber.get_transcript()
    query = "\n".join(text.split("\n")[::-1])
    custom_instruction = custom_instructions_menu.get()
    response = responder.generate_response_from_transcript(query, custom_instruction, image)
    
    responder.update_response(response)
    responder.gen_now = True

def paste_image(image_label):
    try:
        image = ImageGrab.grabclipboard()
        if isinstance(image, Image.Image):
            image.thumbnail((300, 300))
            photo = ctk.CTkImage(light_image=image, dark_image=image, size=(300, 300))
            image_label.configure(image=photo)
            image_label.image = photo  # Keep a reference to avoid garbage collection
            image_label.configure(text="")
        else:
            image_label.configure(text="No image found in clipboard")
    except Exception as e:
        print(f"Error: {e}")

def clear_image(image_label):
    image_label.configure(image=None, text="No image")
    image_label.image = None

def read_custom_instructions(file_path):
    with open(file_path, "r") as file:
        instructions = [line.strip() for line in file.readlines()]
    return instructions

def create_ui_components(root, custom_instructions):
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    root.title("Ecoute")
    root.configure(bg='#000000')
    root.geometry("1600x800")

    font_size = 20

    main_frame = ctk.CTkFrame(root, corner_radius=10, fg_color='#1a1a1a')
    main_frame.pack(padx=20, pady=20, fill="both", expand=True)

    main_frame.grid_rowconfigure(0, weight=1)
    main_frame.grid_columnconfigure(0, weight=1)
    main_frame.grid_columnconfigure(2, weight=1)
    main_frame.grid_columnconfigure(4, weight=1)

    transcript_frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color='#1a1a1a')
    transcript_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    separator1 = CTKSeperator.CTkWindowSeparator(main_frame, orientation="vertical")
    separator1.grid(row=0, column=1, padx=2, pady=10, sticky="ns")

    response_frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color='#1a1a1a')
    response_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

    separator2 = CTKSeperator.CTkWindowSeparator(main_frame, orientation="vertical")
    separator2.grid(row=0, column=3, padx=2, pady=10, sticky="ns")

    image_frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color='#1a1a1a')
    image_frame.grid(row=0, column=4, padx=10, pady=10, sticky="nsew")

    control_frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color='#1a1a1a')
    control_frame.grid(row=1, column=0, columnspan=5, padx=10, pady=10, sticky="nsew")

    transcript_textbox = ctk.CTkTextbox(transcript_frame, font=("Arial", font_size), text_color='#FFFFFF', wrap="word", fg_color='#1a1a1a')
    transcript_textbox.pack(padx=10, pady=10, fill="both", expand=True)

    response_textbox = ctk.CTkTextbox(response_frame, font=("Arial", font_size), text_color='#FFFFFF', wrap="word", fg_color='#1a1a1a')
    response_textbox.pack(padx=10, pady=10, fill="both", expand=True)

    image_label = ctk.CTkLabel(image_frame, text="No image", font=("Arial", font_size), text_color='#FFFFFF', fg_color='#1a1a1a')
    image_label.pack(padx=10, pady=10, fill="both", expand=True)
    root.bind("<Control-v>", lambda event: paste_image(image_label))

    clear_image_button = ctk.CTkButton(image_frame, text="Clear Image", command=lambda: clear_image(image_label), fg_color='#801414', text_color='#FFFFFF')
    clear_image_button.pack(padx=10, pady=10)

    control_frame.grid_columnconfigure(0, weight=1)
    control_frame.grid_columnconfigure(1, weight=1)
    control_frame.grid_columnconfigure(2, weight=1)

    custom_instructions_menu = ctk.CTkOptionMenu(control_frame, values=custom_instructions, fg_color='#323232', text_color='#FFFFFF', bg_color='#1a1a1a')
    custom_instructions_menu.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

    resume_label = ctk.CTkLabel(control_frame, text="No resume uploaded", font=("Arial", 12), text_color="#FFFFFF")
    resume_label.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

    generate_response_button = ctk.CTkButton(control_frame, text="Generate Response", command=None, fg_color='#801414', text_color='#FFFFFF')
    generate_response_button.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

    upload_cv_button = ctk.CTkButton(control_frame, text="Upload CV", command=None, fg_color='#801414', text_color='#FFFFFF')
    upload_cv_button.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")

    clear_transcript_button = ctk.CTkButton(control_frame, text="Clear Transcript", command=None, fg_color='#801414', text_color='#FFFFFF')
    clear_transcript_button.grid(row=2, column=2, padx=10, pady=10, sticky="nsew")

    return transcript_textbox, response_textbox, clear_transcript_button, upload_cv_button, generate_response_button, custom_instructions_menu, resume_label, image_label

def main():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("ERROR: The ffmpeg library is not installed. Please install ffmpeg and try again.")
        return

    root = ctk.CTk()
    custom_instructions = read_custom_instructions("custom_instructions.txt")
    transcript_textbox, response_textbox, clear_transcript_button, upload_cv_button, generate_response_button, custom_instructions_menu, resume_label, image_label = create_ui_components(root, custom_instructions)

    audio_queue = queue.Queue()

    user_audio_recorder = AudioRecorder.DefaultMicRecorder()
    user_audio_recorder.record_into_queue(audio_queue)

    time.sleep(2)

    speaker_audio_recorder = AudioRecorder.DefaultSpeakerRecorder()
    speaker_audio_recorder.record_into_queue(audio_queue)

    model = TranscriberModels.get_model('--api' in sys.argv)

    transcriber = AudioTranscriber(user_audio_recorder.source, speaker_audio_recorder.source, model)
    transcribe = threading.Thread(target=transcriber.transcribe_audio_queue, args=(audio_queue,))
    transcribe.daemon = True
    transcribe.start()

    responder = GPTResponder(custom_instructions_input=custom_instructions_menu)
    respond = threading.Thread(target=responder.respond_to_transcriber, args=(transcriber,))
    respond.daemon = True
    respond.start()

    print("READY")

    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    freeze_state = [True]  # Responses are frozen from the start

    responder.freezed = freeze_state[0]

    clear_transcript_button.configure(command=lambda: clear_context(transcriber, audio_queue))
    upload_cv_button.configure(command=lambda: upload_cv(responder, resume_label))
    generate_response_button.configure(command=lambda: generate_response(transcriber, responder, custom_instructions_menu, generate_response_button, image_label))

    update_transcript_UI(transcriber, transcript_textbox)
    update_response_UI(responder, response_textbox, freeze_state)

    root.mainloop()

if __name__ == "__main__":
    main()
