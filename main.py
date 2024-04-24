import os
from os import PathLike
from time import time
import asyncio
from typing import Union

from dotenv import load_dotenv
import openai
import pygame
from pygame import mixer
import elevenlabs
import speech_recognition as sr

from record import speech_to_text

# Load API keys
load_dotenv()
OPENAI_API_KEY = os.getenv("")
from elevenlabs import set_api_key

set_api_key("")

# Initialize APIs
gpt_client = openai.Client(api_key="")
mixer.init()

# Change the context if you want to change Jarvis' personality
context = "You are Rossy, an AI created by brilliant sixth-year computer science students, as a goal for the 2024 science fair. You are resourceful and full of personality. Your answers should be limited to 1 or 2 short sentences."
conversation = {"Conversation": []}
RECORDING_PATH = "audio/recording.wav"

async def transcribe(file_name: Union[Union[str, bytes, PathLike[str], PathLike[bytes]], int]):
    """
    Transcribe audio using SpeechRecognition library.

    Args:
        - file_name: The name of the file to transcribe.

    Returns:
        The transcribed text.
    """
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_name) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data, language="es-ES")
            return text
        except sr.UnknownValueError:
            return "[SR] No se pudo entender el audio"
        except sr.RequestError as e:
            return f"[SR] Error en la solicitud: {e}"

def log(log: str):
    """
    Print and write to status.txt
    """
    print(log)
    with open("status.txt", "w") as f:
        f.write(log)

if __name__== "__main__":
    while True:
        # Record audio
        log("Escuchando...")
        speech_to_text()
        log("Escuchado con exito")

        # Transcribe audio
        current_time = time()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        string_words = loop.run_until_complete(transcribe(RECORDING_PATH))
        with open("conv.txt", "a") as f:
            f.write(f"{string_words}\n")
        transcription_time = time() - current_time
        log(f"Comprendido en {transcription_time:.2f} segundos.")

        # Get response from GPT-3
        current_time = time()
        context += f"\nUsuario: {string_words}\nRossy: "
        response = gpt_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"{context}",
                }
            ],
            model="gpt-3.5-turbo",
        )
        context += response.choices[0].message.content
        gpt_time = time() - current_time
        log(f"Transcribido en {gpt_time:.2f} segundos...")

        # Convert response to audio
        current_time = time()
        audio = elevenlabs.generate(
            text=response.choices[0].message.content, voice="Sarah", model="eleven_multilingual_v2"
        )
        elevenlabs.save(audio, "audio/response.wav")
        audio_time = time() - current_time
        log(f"Generando respuesta en {audio_time:.2f} segundos.")

        # Play response
        log("Hablando...")
        sound = mixer.Sound("audio/response.wav")
        # Add response as a new line to conv.txt
        with open("conv.txt", "a") as f:
            f.write(f"{response.choices[0].message.content}\n")
        sound.play()
        pygame.time.wait(int(sound.get_length() * 1000))
        print(f"\n --- USUARIO: {string_words}\n --- ROSSY: {response.choices[0].message.content}\n")
