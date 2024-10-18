import os
import time
from datetime import timedelta
from multiprocessing import Lock, Process


import whisper
from bs4 import BeautifulSoup
from timeloop import Timeloop
import sys
tl = Timeloop()
estudios_base_path = "C:\\cloud\\Estudios\\"
capturas_base_path = "c:\\capturas\\"

# estudios_base_path = "/mnt/c/inetpub/wwwroot/Estudios/"
# capturas_base_path = "/mnt/c/capturas/"

mutex = Lock()


def transcibir_audio(audio_path):
    print(f"Transcribiendo {audio_path}")
    model = whisper.load_model("base")
    options = whisper.DecodingOptions(language="es")
    result = model.transcribe(audio_path)
    result_encoded = result["text"].encode('utf8').decode(sys.stdout.encoding)
    print(result_encoded)
    return result_encoded


def setup_tray():
    import pystray
    from PIL import Image

    def on_quit():
        icon.stop()

    # Load an image for the tray icon
    image = Image.open("path/to/your/icon.ico")

    # Create a menu for the tray icon
    menu = pystray.Menu(
        pystray.MenuItem("Show Message", lambda: print("Hello from the tray!")),
        pystray.MenuItem("Quit", on_quit),
    )

    # Create the tray icon
    icon = pystray.Icon("SCM", image, "Sistema de Consultas", menu)

    # Run the icon in the system tray
    icon.run()


def get_estudio_wav_path(local_media_capturada):
    wav_files = []
    for media in local_media_capturada:
        if media.MediaTypeID.text == "Audio":
            wav_files.append(media.LocalPath.text)
    return wav_files


def transcribe_path(paciente_id, fecha, wav_filename):
    return (
        estudios_base_path
        + "P_"
        + paciente_id
        + "\\"
        + fecha
        + "\\transcribe\\"
        + wav_filename
        + ".txt"
    )


def is_wav_transcribed(transcription_path):
    print(f"Verificando si {transcription_path} existe")
    return os.path.exists(transcription_path)


def get_file_name_from_path(full_path):
    filename, _=  os.path.splitext(os.path.basename(full_path))
    return filename


def translate_windows_to_linux_path(path):
    return path.replace("\\", "/").replace("C:", "/mnt/c")

def create_subfolders(path):
    if not os.path.exists(path):
        os.makedirs(path)

from datetime import datetime
def trasncribir_wavs(estudio_info_xml):
    soup = BeautifulSoup(estudio_info_xml, "xml")
    wav_files = get_estudio_wav_path(soup.find_all("LocalMediaCapturada"))
    paciente_id = soup.find("Paciente_ID").text
    fecha_estudio_str = soup.find("FechaEstudio").text
    fecha_estudio_datetime = datetime.strptime(fecha_estudio_str.split("T")[0], "%Y-%m-%d")
    formatted_fecha = fecha_estudio_datetime.strftime("%Y%m%d")
    for wav_file in wav_files:
        transcribed_path = transcribe_path(
            paciente_id, formatted_fecha, get_file_name_from_path(wav_file)
        )
        # transcribed_path = translate_windows_to_linux_path(transcribed_path)
        if not is_wav_transcribed(transcribed_path):
            create_subfolders(os.path.dirname(transcribed_path))
            with open(transcribed_path, "w", encoding="utf-8") as f:
                f.write(transcibir_audio(wav_file))


def iterate_subfolders_captura():
    for root, dirs, files in os.walk(capturas_base_path):
        for file in files:
            if file.endswith(".xml"):
                print(f"Procesando {file}")
                with open(os.path.join(root,file), "r") as f:
                    trasncribir_wavs(f.read())


@tl.job(interval=timedelta(minutes=5))
def run_translate():
    print("Running translate")
    with mutex:
        iterate_subfolders_captura()


if __name__ == "__main__":
    # tl.start(block=True)
    run_translate()
