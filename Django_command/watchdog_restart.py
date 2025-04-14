import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import signal

# Устанавливаем переменную окружения для Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'command_project.settings')

class RestartHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.start_process()

    def start_process(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
        
        self.process = subprocess.Popen([
            "python",
            "manage.py",
            "runserver",
            "0.0.0.0:8000"
        ])

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(('.py', '.html', '.css', '.js')):
            print(f"File changed: {event.src_path}")
            self.start_process()

if __name__ == "__main__":
    path = "."
    event_handler = RestartHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if event_handler.process:
            event_handler.process.terminate()
    observer.join() 