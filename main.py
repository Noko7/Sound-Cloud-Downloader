import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import shutil
import platform
import re
import sys

YT_DLP_BASE_CMD = [
    "yt-dlp",
    "-x", "--audio-format", "mp3",
    "--embed-metadata",
    "-o", "%(playlist_title)s/%(playlist_index)s - %(title)s.%(ext)s"
]

# CHANGE THIS PATH IF REQUIRED (used as a Windows fallback)
FFMPEG_PATH = r"C:\\ffmpeg\\bin\\ffmpeg.exe"


def check_ffmpeg():
    """Check whether ffmpeg is available on the system.

    Strategy:
    - First check if an `ffmpeg` executable is on PATH (shutil.which).
    - On Windows, if that fails, check the FFMPEG_PATH fallback.
    """
    # Quick check: is ffmpeg on PATH?
    if shutil.which("ffmpeg"):
        return True

    # On Windows, allow a common fallback path
    if platform.system().lower().startswith("win"):
        if os.path.isfile(FFMPEG_PATH):
            return True

    return False


def show_ffmpeg_install_instructions():
    """Show a platform-specific messagebox explaining how to install ffmpeg.

    Uses a transient Tk root so the user sees a native dialog even though the
    main application window isn't created.
    """
    system = platform.system().lower()

    if system.startswith("linux"):
        instructions = (
            "FFmpeg was not found on your system.\n\n"
            "Install on Debian/Ubuntu: sudo apt update && sudo apt install ffmpeg\n"
            "Install on Fedora: sudo dnf install ffmpeg\n"
            "Install on Arch: sudo pacman -S ffmpeg\n\n"
            "Or visit https://ffmpeg.org/download.html for other options."
        )
    elif system.startswith("win"):
        instructions = (
            "FFmpeg was not found on your system.\n\n"
            "Options:\n"
            " - Install via Chocolatey: choco install ffmpeg\n"
            " - Install via winget: winget install ffmpeg\n"
            " - Or download a static build from https://ffmpeg.org/download.html and add it to your PATH.\n\n"
            "If you installed FFmpeg to C:\\ffmpeg, you can set FFMPEG_PATH in this script."
        )
    else:
        instructions = (
            "FFmpeg was not found on your system.\n\n"
            "Please install FFmpeg from https://ffmpeg.org/download.html and ensure the `ffmpeg` executable is on your PATH."
        )

    # Show a dialog without opening the main GUI window
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("FFmpeg not found", instructions)
    root.destroy()

def run_download(urls, output_dir, progress_label, progress_bar, track_label, stop_event=None):
    """Run yt-dlp command for each URL and update progress.

    stop_event: threading.Event used to signal cancellation. If set, the running
    subprocess will be terminated and the function will return early.
    """
    if stop_event is None:
        stop_event = threading.Event()

    try:
        if not check_ffmpeg():
            show_ffmpeg_install_instructions()
            progress_label.config(text="FFmpeg not found. Download aborted.")
            progress_bar["value"] = 0
            try:
                track_label.config(text="Tracks: 0 / ?")
            except Exception:
                pass
            progress_bar.update()
            return

        if not os.path.isdir(output_dir):
            messagebox.showerror("Directory Error", f"Output directory does not exist: {output_dir}")
            progress_label.config(text="Invalid output directory.")
            progress_bar["value"] = 0
            try:
                track_label.config(text="Tracks: 0 / ?")
            except Exception:
                pass
            progress_bar.update()
            return

        total_urls = len(urls)
        for i, url in enumerate(urls, 1):
            if stop_event.is_set():
                progress_label.config(text="Download cancelled.")
                progress_bar["value"] = 0
                try:
                    track_label.config(text="Download cancelled.")
                except Exception:
                    pass
                progress_bar.update()
                return

            cmd = YT_DLP_BASE_CMD + [url.strip()]
            # Show playlist index but not the full URL
            playlist_label = f"Playlist {i}/{total_urls}"
            progress_label.config(text=f"{playlist_label} - Preparing...")
            progress_bar["value"] = ((i - 1) / total_urls) * 100
            progress_bar.update()
            try:
                # current track name for display
                current_track = None
                try:
                    track_label.config(text="Tracks: 0 / ?")
                except Exception:
                    pass

                # Track-level counters for playlist items within this URL
                total_tracks = None
                downloaded_tracks = 0

                process = subprocess.Popen(cmd, cwd=output_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                try:
                    while True:
                        if stop_event.is_set():
                            try:
                                process.terminate()
                            except Exception:
                                pass
                            progress_label.config(text="Download cancelled.")
                            progress_bar["value"] = 0
                            try:
                                track_label.config(text="Download cancelled.")
                            except Exception:
                                pass
                            progress_bar.update()
                            return

                        line = process.stdout.readline()
                        if not line:
                            break
                        
                        # Try to extract total tracks info from playlist/info lines
                        try:
                            if total_tracks is None:
                                # Patterns like 'Playlist ...: Downloading 12 videos' or 'contains 12 entries'
                                m = re.search(r"(?i)(?:contains|downloading)\s+(?P<n>\d+)\s+(?:entries|videos|tracks|items)", line)
                                if m:
                                    total_tracks = int(m.group('n'))
                                    try:
                                        track_label.config(text=f"Tracks: {downloaded_tracks} / {total_tracks} (left: {total_tracks - downloaded_tracks})")
                                    except Exception:
                                        pass
                                else:
                                    # Look for patterns like '1/12' or 'Downloading 1 of 12'
                                    m2 = re.search(r"(?P<idx>\d+)\s*/\s*(?P<total>\d+)", line)
                                    if m2:
                                        total_tracks = int(m2.group('total'))
                                        try:
                                            track_label.config(text=f"Tracks: {downloaded_tracks} / {total_tracks} (left: {total_tracks - downloaded_tracks})")
                                        except Exception:
                                            pass
                        except Exception:
                            pass
                        # Capture the destination line which contains the filename (current song)
                        try:
                            if "Destination:" in line:
                                m_dest = re.search(r"Destination:\s*(?P<path>.+)$", line)
                                if m_dest:
                                    path = m_dest.group('path').strip()
                                    name = os.path.basename(path)
                                    # strip extension
                                    name = re.sub(r"\.[^.]+$", "", name)
                                    current_track = name
                                    # update the visible status to show current track
                                    try:
                                        short_name = (current_track[:120] + '...') if len(current_track) > 120 else current_track
                                        progress_label.config(text=f"{playlist_label}: {short_name}")
                                    except Exception:
                                        pass
                        except Exception:
                            pass

                        # Update per-item progress; detect completed items by seeing 100% download
                        if "[download]" in line and "%" in line:
                            try:
                                progress = line.split("%", 1)[0].split()[-1]
                                progress_val = float(progress)
                                progress_bar["value"] = ((i - 1) / total_urls + progress_val / 100 / total_urls) * 100
                                progress_bar.update()

                                # If we've reached ~100%, count as one downloaded track
                                if progress_val >= 99.9:
                                    downloaded_tracks += 1
                                    try:
                                        if total_tracks:
                                            left = max(total_tracks - downloaded_tracks, 0)
                                            track_label.config(text=f"Tracks: {downloaded_tracks} / {total_tracks} (left: {left})")
                                        else:
                                            track_label.config(text=f"Tracks: {downloaded_tracks} / ? (left: ?)")
                                        # also show the most recently downloaded track name briefly
                                        if current_track:
                                            short_name = (current_track[:120] + '...') if len(current_track) > 120 else current_track
                                            progress_label.config(text=f"{playlist_label}: {short_name} (completed)")
                                    except Exception:
                                        pass
                            except Exception:
                                pass

                    process.wait()
                    if process.returncode != 0:
                        raise subprocess.CalledProcessError(process.returncode, cmd)
                finally:
                    try:
                        if process.stdout:
                            process.stdout.close()
                    except Exception:
                        pass

            except subprocess.CalledProcessError as e:
                if not stop_event.is_set():
                    progress_label.config(text=f"Error downloading: {url}")
                    progress_bar["value"] = 0
                    try:
                        track_label.config(text="Error during download")
                    except Exception:
                        pass
                    progress_bar.update()
                    messagebox.showerror("Download Error", f"An error occurred while downloading: {e}")
                return
            except Exception as e:
                progress_label.config(text=f"Unexpected error: {str(e)}")
                progress_bar["value"] = 0
                try:
                    track_label.config(text="Unexpected error")
                except Exception:
                    pass
                progress_bar.update()
                messagebox.showerror("Unexpected Error", f"An unexpected error occurred: {e}")
                return

        progress_label.config(text="All downloads completed successfully!")
        progress_bar["value"] = 100
        try:
            track_label.config(text="All tracks downloaded")
        except Exception:
            pass
        progress_bar.update()
        messagebox.showinfo("Success", "All downloads completed successfully!")
    except Exception as e:
        progress_label.config(text=f"Fatal error: {str(e)}")
        progress_bar["value"] = 0
        progress_bar.update()
        messagebox.showerror("Fatal Error", f"A fatal error occurred: {e}")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SoundCloud Playlist Downloader")
        # Updated window size per user request
        self.geometry("1200x900")
        self.configure(bg="#ffffff")
        # Load and display the logo at the top center.
        # Prefer a new `logo.png`, fall back to older filenames or an assets folder.
        logo_candidates = ["logo.png", "soundcloud-logo.png", os.path.join("assets", "soundcloud-logo.png")]
        logo_path = next((p for p in logo_candidates if os.path.exists(p)), None)

        if logo_path:
            try:
                logo_img = Image.open(logo_path)
                # Resize while keeping aspect ratio; target max size 140x140
                logo_img.thumbnail((140, 140))
                self.logo_tk = ImageTk.PhotoImage(logo_img)
                self.logo_label = tk.Label(self, image=self.logo_tk, bg="#ffffff")
                self.logo_label.pack(pady=8)
            except Exception:
                # If image loading fails, fall back to text label
                self.logo_label = tk.Label(self, text="SoundCloud Logo Here", bg="#ffffff", fg="#000000", font=("Arial", 14))
                self.logo_label.pack(pady=12)
        else:
            self.logo_label = tk.Label(self, text="SoundCloud Logo Here", bg="#ffffff", fg="#000000", font=("Arial", 14))
            self.logo_label.pack(pady=12)

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

        # Cancel button
        self.cancel_button = tk.Button(self, text="Cancel Download", bg="gray", fg="white", command=self.cancel_download, state="disabled")
        self.cancel_button.pack(pady=5)

        # Progress label and bar
        self.progress_label = tk.Label(self, text="", bg="#ffffff", fg="#555555")
        self.progress_label.pack(pady=5)

        # Track progress label (downloaded / total)
        self.track_progress_label = tk.Label(self, text="Tracks: 0 / ?", bg="#ffffff", fg="#555555")
        self.track_progress_label.pack(pady=2)

        self.progress_bar = ttk.Progressbar(self, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.pack(pady=5)

        # Download thread and stop event
        self.download_thread = None
        self.stop_event = None

        # Handle app close
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def choose_directory(self):
        chosen_dir = filedialog.askdirectory()
        if chosen_dir:
            self.output_dir.set(chosen_dir)
            self.dir_label.config(text=chosen_dir)

    def start_download(self):
        try:
            urls_text = self.url_entry.get("1.0", tk.END).strip()
            if not urls_text:
                self.progress_label.config(text="No URLs entered.")
                self.progress_bar["value"] = 0
                self.progress_bar.update()
                messagebox.showerror("Error", "Please enter at least one URL.")
                return

            if not self.output_dir.get():
                self.progress_label.config(text="No output directory selected.")
                self.progress_bar["value"] = 0
                self.progress_bar.update()
                messagebox.showerror("Error", "Please select an output directory.")
                return

            urls = [u.strip() for u in urls_text.split(",") if u.strip()]
            if not urls:
                self.progress_label.config(text="No valid URLs found.")
                self.progress_bar["value"] = 0
                self.progress_bar.update()
                messagebox.showerror("Error", "No valid URLs found.")
                self.download_button.config(bg="green", text="Download Playlists")
                return

            self.download_button.config(bg="red", text="Downloading...")
            self.cancel_button.config(state="normal")
            # reset track progress label
            try:
                self.track_progress_label.config(text="Tracks: 0 / ?")
            except Exception:
                pass
            self.stop_event = threading.Event()
            self.download_thread = threading.Thread(target=self.run_download_thread, args=(urls, self.stop_event))
            self.download_thread.start()
        except Exception as e:
            self.progress_label.config(text=f"Error: {str(e)}")
            self.progress_bar["value"] = 0
            self.progress_bar.update()
            self.download_button.config(bg="green", text="Download Playlists")
            self.cancel_button.config(state="disabled")
            messagebox.showerror("Error", f"An error occurred: {e}")

    def run_download_thread(self, urls, stop_event):
        try:
            run_download(urls, self.output_dir.get(), self.progress_label, self.progress_bar, self.track_progress_label, stop_event)
        except Exception as e:
            self.progress_label.config(text=f"Thread error: {str(e)}")
            self.progress_bar["value"] = 0
            self.progress_bar.update()
            messagebox.showerror("Thread Error", f"An error occurred in the download thread: {e}")
        finally:
            self.download_button.config(bg="green", text="Download Playlists")
            self.cancel_button.config(state="disabled")
            self.download_thread = None
            self.stop_event = None

    def cancel_download(self):
        if self.stop_event and self.download_thread and self.download_thread.is_alive():
            self.stop_event.set()
            self.progress_label.config(text="Cancelling download...")
            self.cancel_button.config(state="disabled")

    def on_close(self):
        # Handle app close, including kill via UI or terminal
        try:
            if self.stop_event and self.download_thread and self.download_thread.is_alive():
                self.stop_event.set()
                self.progress_label.config(text="Cancelling download before exit...")
                self.cancel_button.config(state="disabled")
                self.download_thread.join(timeout=5)
        except Exception as e:
            try:
                messagebox.showerror("Exit Error", f"Error during shutdown: {e}")
            except Exception:
                pass
        finally:
            self.destroy()

if __name__ == "__main__":
    # Pre-launch check: ensure ffmpeg is installed before creating the main window.
    if not check_ffmpeg():
        show_ffmpeg_install_instructions()
        sys.exit(1)

    app = App()
    app.mainloop()
