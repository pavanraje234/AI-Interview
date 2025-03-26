from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import json
import together
import time
import speech_recognition as sr
import pyttsx3
from dotenv import load_dotenv
from datetime import datetime
import random
from generate_report import generate_report
from posture_eye_analysis import analyze_posture_and_eyes
import threading
from google.cloud import texttospeech
load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

if not TOGETHER_API_KEY:
    raise ValueError("TOGETHER_API_KEY is missing. Add it to the .env file.")

client = together.Together(api_key=TOGETHER_API_KEY)
# Initialize Google Cloud Text-to-Speech client
client = texttospeech.TextToSpeechClient()

def speak(text):
    """Uses Google Cloud Text-to-Speech to convert text into speech and play it."""
    
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE  # Choose FEMALE voice
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )

    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # Save the audio output to a file and play it
    audio_file = "output.wav"
    with open(audio_file, "wb") as out:
        out.write(response.audio_content)

    # Play the generated speech
    os.system(f"aplay {audio_file}")  # For Linux
    # os.system(f"afplay {audio_file}")  # For macOS
    # os.system(f"start {audio_file}")  # For Windows

# Example usage in a new thread
def speak_async(text):
    """Runs the speak function in a new thread to avoid blocking."""
    t = threading.Thread(target=speak, args=(text,))
    t.start()

def listen():
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 2.0
    recognizer.dynamic_energy_threshold = True
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)  # Reduce noise adjustment time
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)  # Added phrase_time_limit
            print("Audio captured. Processing...")
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.WaitTimeoutError:
            speak("Listening timed out. No audio detected.")
            return None
        except sr.UnknownValueError:
            speak("Sorry, I couldn't understand.")
            return None
        except sr.RequestError:
            speak("Could not request results, check your internet.")
            return None


def get_llama_response(prompt):
    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=256
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error: {e}")
        return "Sorry, I couldn't generate a response."

def load_questions():
    with open("interview_questions.json", "r", encoding="utf-8") as file:
        return json.load(file)

# def select_job_role():
#     questions = load_questions()
#     job_roles = list(questions.keys())
#     speak("Please select a job role from the following:")
#     print("Bot: Please select a job role from the following:")
#     for i, role in enumerate(job_roles, 1):
#         speak(f"Option {i}: {role}")
#         print(f"Option {i}: {role}")
#     while True:
#         response = listen()
#         for i, role in enumerate(job_roles, 1):
#             if response and (str(i) in response or role.lower() in response):
#                 speak(f"You selected {role}.")
#                 print(f"Bot: You selected {role}.")
#                 return role
#         speak("Sorry, I didn't catch that. Please say the job title from the options given.")

def score_answer(question, answer):
    if not answer:
        return 0
    prompt = f"Question: {question}\nAnswer: {answer}\nScore the answer from 0 (irrelevant) to 10 (perfectly relevant). Provide only the score as output."
    try:
        score = get_llama_response(prompt)
        return int(score) if score.isdigit() else 0
    except:
        return 0

def conduct_interview(role, log_file, summary_file, user_name):
    questions = load_questions().get(role, [])
    selected_questions = random.sample(questions, min(10, len(questions)))
    total_score = 0
    question_index = 0

    # Analyze posture and eye contact
    # posture_score, eye_score = analyze_posture_and_eyes()
    # print(f"Posture Score: {posture_score}/10, Eye Score: {eye_score}/10")

    while question_index < len(selected_questions):  # Use len(selected_questions) instead of 10
        question = selected_questions[question_index]
        speak(question)
        print(f"Bot: {question} (Question {question_index + 1}/{len(selected_questions)})")
        
        while True:  # Loop until a valid answer is given or next question command is detected
            print("Waiting for your response...")
            answer = listen()
            if answer:
                print(f"Your response: {answer}")
                if any(phrase in answer.lower() for phrase in ["repeat", "repeat the question", "can you repeat the question"]):
                    speak("Sure, I'll repeat the question.")
                    print("Bot: Sure, I'll repeat the question.")
                    speak(question)
                    print(f"Bot: {question} (Question {question_index + 1}/{len(selected_questions)})")
                    continue
                
                log_conversation(question, answer, log_file)
                score = score_answer(question, answer)
                total_score += score
                log_score(score, log_file)
                print(f"Score: {score}/10")
                
                if any(phrase in answer.lower() for phrase in ["next question", "move on to the next question"]):
                    speak("Okay, Moving on to the next question.")
                    print("Bot: Okay, Moving on to the next question.")
                    question_index += 1  # Move to the next question
                    break
                
                follow_up = get_llama_response(f"Candidate answered: {answer}. Ask a relevant follow-up question. Not more than one question.")
                speak(follow_up)
                print(f"Bot: {follow_up} (Follow-up to Question {question_index + 1})")
                
                follow_up_answer = listen()
                if follow_up_answer:
                    print(f"Your follow-up response: {follow_up_answer}")
                    log_conversation(follow_up, follow_up_answer, log_file)
                    score = score_answer(follow_up, follow_up_answer)
                    total_score += score
                    log_score(score, log_file)
                    print(f"Score: {score}/10")
                
                question_index += 1  # Move to the next question after follow-up
                break  # Exit the inner loop to proceed to the next question
            else:
                print("No valid answer detected. Moving to the next question.")
                question_index += 1  # Move to the next question if no answer is detected
                break
    
    # Add posture and eye scores to the total score
    total_score += posture_score + eye_score
    log_final_score(summary_file, role, total_score, user_name, posture_score, eye_score)
    speak("Thank you for your time. The interview is now complete.")
    print("Bot: Thank you for your time. The interview is now complete.")

def log_conversation(question, answer, log_file):
    with open(log_file, "a", encoding="utf-8") as file:
        file.write(f"Q: {question}\nA: {answer}\n")

def log_score(score, log_file):
    with open(log_file, "a", encoding="utf-8") as file:
        file.write(f"Score: {score}/10\n{'-' * 40}\n")

def log_final_score(summary_file, role, total_score, user_name, posture_score, eye_score):
    with open(summary_file, "a", encoding="utf-8") as file:
        file.write(f"Candidate Name: {user_name}, Role: {role}, Final Score: {total_score}/120, Posture Score: {posture_score}/10, Eye Score: {eye_score}/10\n")
    # Generate PDF Report
    generate_report(user_name, role, total_score, posture_score, eye_score)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_interview', methods=['POST'])
def start_interview():
    user_name = request.form['username']
    role = request.form['role']  # Get the job role from the form
    role_folder = f"logs/{role}"
    os.makedirs(role_folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = f"{role_folder}/{user_name}_{timestamp}.txt"
    summary_file = "logs/final_scores.txt"
    print(f"Logging conversation to: {log_file}\n")
    
    # Start the interview in a separate thread
    interview_thread = threading.Thread(target=conduct_interview, args=(role, log_file, summary_file, user_name))
    interview_thread.start()
    
    # Render the interview page
    return render_template('interview.html')

@app.route('/result')
def result():
    return render_template('result.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    app.run(debug=True)
    