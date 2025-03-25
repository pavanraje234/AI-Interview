import os
import json
import together
import speech_recognition as sr
import pyttsx3
from dotenv import load_dotenv
from datetime import datetime
import random
from generate_report import generate_report

# Load API key from .env
load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

if not TOGETHER_API_KEY:
    raise ValueError("TOGETHER_API_KEY is missing. Add it to the .env file.")

client = together.Together(api_key=TOGETHER_API_KEY)

engine = pyttsx3.init()

def set_feminine_voice():
    voices = engine.getProperty("voices")
    for voice in voices:
        if "female" in voice.name.lower() or "zira" in voice.name.lower() or "samantha" in voice.name.lower():
            engine.setProperty("voice", voice.id)
            break
    engine.setProperty("rate", 180)
    engine.setProperty("volume", 1.0)

set_feminine_voice()

if not os.path.exists("logs"):
    os.makedirs("logs")

def speak(text):
    engine.say(text)
    engine.runAndWait()

def listen():
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 2.0
    recognizer.dynamic_energy_threshold = True
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    try:
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Sorry, I couldn't understand.")
        return None
    except sr.RequestError:
        print("Could not request results, check your internet.")
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

def get_user_name():
    speak("Hello! What's your name? Please state your full name only.")
    print("Bot: Hello! What's your name? Please state your full name only.")
    while True:
        name = listen()
        if name:
            speak(f"Nice to meet you, {name}!")
            print(f"Bot: Nice to meet you, {name}!")
            return name.replace(" ", "_")

def load_questions():
    with open("interview_questions.json", "r", encoding="utf-8") as file:
        return json.load(file)

def select_job_role():
    questions = load_questions()
    job_roles = list(questions.keys())
    speak("Please select a job role from the following:")
    print("Bot: Please select a job role from the following:")
    for i, role in enumerate(job_roles, 1):
        speak(f"Option {i}: {role}")
        print(f"Option {i}: {role}")
    while True:
        response = listen()
        for i, role in enumerate(job_roles, 1):
            if response and (str(i) in response or role.lower() in response):
                speak(f"You selected {role}.")
                print(f"Bot: You selected {role}.")
                return role
        speak("Sorry, I didn't catch that. Please say the job title from the options given.")

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

    while question_index < 10:
        question = selected_questions[question_index]
        speak(question)
        print("Bot:", question)
        
        while True:  # Loop until a valid answer is given or next question command is detected
            answer = listen()
            question_index += 1
            if answer:
                if any(phrase in answer.lower() for phrase in ["repeat", "repeat the question", "can you repeat the question"]):
                    speak("Sure, I'll repeat the question.")
                    print("Bot: Sure, I'll repeat the question.")
                    speak(question)
                    print("Bot:", question)
                    continue
                
                log_conversation(question, answer, log_file)
                score = score_answer(question, answer)
                total_score += score
                log_score(score, log_file)
                print(f"Score: {score}/10")
                
                if any(phrase in answer.lower() for phrase in ["next question", "move on to the next question"]):
                    speak("Okay, Moving on to the next question.")
                    print("Okay, Moving on to the next question.")
                    break
                
                follow_up = get_llama_response(f"Candidate answered: {answer}. Ask a relevant follow-up question. Not more than one question.")
                speak(follow_up)
                print("Bot:", follow_up)
                question_index += 1
                
                follow_up_answer = listen()
                if follow_up_answer:
                    log_conversation(question, answer, log_file)
                    score = score_answer(question, answer)
                    total_score += score
                    log_score(score, log_file)
                    print(f"Score: {score}/10")
                break  # Move to next question
                
    
    log_final_score(summary_file, role, total_score, user_name)
    speak("Thank you for your time. The interview is now complete.")
    print("Bot: Thank you for your time. The interview is now complete.")

def log_conversation(question, answer, log_file):
    with open(log_file, "a", encoding="utf-8") as file:
        file.write(f"Q: {question}\nA: {answer}\n")

def log_score(score, log_file):
    with open(log_file, "a", encoding="utf-8") as file:
        file.write(f"Score: {score}/10\n{'-' * 40}\n")

def log_final_score(summary_file, role, total_score, user_name):
    with open(summary_file, "a", encoding="utf-8") as file:
        file.write(f"Candidate Name: {user_name}, Role: {role}, Final Score: {total_score}/100\n")
     # Generate PDF Report
    generate_report(user_name, role, total_score)

def verbal_bot():
    user_name = get_user_name()
    role = select_job_role()
    role_folder = f"logs/{role}"
    os.makedirs(role_folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = f"{role_folder}/{user_name}_{timestamp}.txt"
    summary_file = "logs/final_scores.txt"
    print(f"Logging conversation to: {log_file}\n")
    conduct_interview(role, log_file, summary_file, user_name)


if __name__ == "__main__":
    verbal_bot()
