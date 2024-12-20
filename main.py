import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk

YT_DLP_BASE_CMD = [
    "yt-dlp",
    "-x", "--audio-format", "mp3",
    "--embed-metadata",
    "-o", "%(playlist_title)s/%(playlist_index)s - %(title)s.%(ext)s"
]

# CHANGE THIS PATH IF REQUIRED

FFMPEG_PATH = r"C:\\ffmpeg\\bin\\ffmpeg.exe"

def check_ffmpeg():
    """Check if ffmpeg is available in the specified path."""
    return os.path.isfile(FFMPEG_PATH)

def run_download(urls, output_dir, progress_label, progress_bar):
    """Run yt-dlp command for each URL and update progress."""
    if not check_ffmpeg():
        messagebox.showerror("Error", "FFmpeg is not installed. Please install FFmpeg before running this script.")
        return

    total_urls = len(urls)
    for i, url in enumerate(urls, 1):
        cmd = YT_DLP_BASE_CMD + [url.strip()]
        try:
            progress_label.config(text=f"Downloading: {url} ({i}/{total_urls})")
            progress_bar["value"] = ((i - 1) / total_urls) * 100
            progress_bar.update()

            process = subprocess.Popen(cmd, cwd=output_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            for line in process.stdout:
                if "[download]" in line and "%" in line:
                    progress = line.split("%", 1)[0].split()[-1]
                    progress_bar["value"] = ((i - 1) / total_urls + float(progress) / 100 / total_urls) * 100
                    progress_bar.update()

            process.wait()
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, cmd)

        except subprocess.CalledProcessError as e:
            messagebox.showerror("Download Error", f"An error occurred while downloading: {e}")
            return

    progress_label.config(text="All downloads completed successfully!")
    progress_bar["value"] = 100
    progress_bar.update()
    messagebox.showinfo("Success", "All downloads completed successfully!")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SoundCloud Playlist Downloader")
        self.geometry("600x500")
        self.configure(bg="#ffffff")

        # Load and display the logo at the top center
        if os.path.exists("soundcloud-logo.png"):
            logo_img = Image.open("soundcloud-logo.png")
            logo_img = logo_img.resize((150, 150))
            self.logo_tk = ImageTk.PhotoImage(logo_img)
            self.logo_label = tk.Label(self, image=self.logo_tk, bg="#ffffff")
            self.logo_label.pack(pady=10)
        else:
            self.logo_label = tk.Label(self, text="SoundCloud Logo Here", bg="#ffffff", fg="#000000", font=("Arial", 16))
            self.logo_label.pack(pady=20)

        # Instruction label
        instr_label = tk.Label(self, text="Enter SoundCloud playlist/profile URLs (comma-separated):", bg="#ffffff", fg="#333333")
        instr_label.pack(pady=5)

        # Textbox for URLs
        self.url_entry = tk.Text(self, width=60, height=5)
        self.url_entry.pack(pady=5)

        # Button to choose output directory
        self.output_dir = tk.StringVar()
        choose_dir_button = tk.Button(self, text="Choose Download Folder", command=self.choose_directory)
        choose_dir_button.pack(pady=5)

        # Display chosen directory
        self.dir_label = tk.Label(self, text="No directory selected", bg="#ffffff", fg="#555555")
        self.dir_label.pack(pady=5)

        # Download button
        self.download_button = tk.Button(self, text="Download Playlists", bg="green", fg="white", command=self.start_download)
        self.download_button.pack(pady=20)

        # Progress label and bar
        self.progress_label = tk.Label(self, text="", bg="#ffffff", fg="#555555")
        self.progress_label.pack(pady=5)

        self.progress_bar = ttk.Progressbar(self, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.pack(pady=5)

    def choose_directory(self):
        chosen_dir = filedialog.askdirectory()
        if chosen_dir:
            self.output_dir.set(chosen_dir)
            self.dir_label.config(text=chosen_dir)

    def start_download(self):
        urls_text = self.url_entry.get("1.0", tk.END).strip()
        if not urls_text:
            messagebox.showerror("Error", "Please enter at least one URL.")
            return

        if not self.output_dir.get():
            messagebox.showerror("Error", "Please select an output directory.")
            return

        self.download_button.config(bg="red", text="Downloading...")
        urls = [u.strip() for u in urls_text.split(",") if u.strip()]
        if not urls:
            messagebox.showerror("Error", "No valid URLs found.")
            self.download_button.config(bg="green", text="Download Playlists")
            return

        threading.Thread(target=self.run_download_thread, args=(urls,)).start()

    def run_download_thread(self, urls):
        run_download(urls, self.output_dir.get(), self.progress_label, self.progress_bar)
        self.download_button.config(bg="green", text="Download Playlists")

if __name__ == "__main__":
    app = App()
    app.mainloop()
