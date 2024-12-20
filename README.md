# SoundCloud Playlist Downloader

A simple GUI application for downloading SoundCloud playlists and profiles. The downloaded files are converted to MP3 format and include embedded metadata. 

![image](https://github.com/user-attachments/assets/5da4de26-7dbb-4540-b172-51a1849d7ad2)

## Features
- Download audio from SoundCloud playlists or profiles.
- Automatically converts downloaded files to MP3 format.
- Embeds metadata into downloaded files.
- Simple and intuitive GUI with progress tracking.

## Prerequisites

Before running the application, ensure the following:

1. **FFmpeg Installed**  
   FFmpeg is required for audio conversion. You can download it from the [official FFmpeg website](https://ffmpeg.org/download.html).

2. **Set FFmpeg Path in the Code**  
   After downloading FFmpeg:
   - Extract the downloaded file.
   - Locate the `bin` directory where `ffmpeg.exe` resides (e.g., `C:\\ffmpeg\\bin\\`).
   - Open the script and update the `FFMPEG_PATH` variable to the exact path of `ffmpeg.exe`:
     ```python
     FFMPEG_PATH = r"C:\\path\\to\\ffmpeg\\bin\\ffmpeg.exe"
     ```

3. **Add FFmpeg to System Path (Optional)**  
   Adding FFmpeg to your system's environment variables allows it to be accessed globally:
   - **Windows**:
     1. Search for "Environment Variables" in the Start menu.
     2. Under System Properties, click on **Environment Variables**.
     3. Select the `Path` variable, click **Edit**, and add the path to FFmpeg's `bin` folder.
   - **Mac/Linux**:
     Add the following line to your shell configuration file (e.g., `.bashrc` or `.zshrc`):
     ```bash
     export PATH="/path/to/ffmpeg/bin:$PATH"
     ```

4. Verify FFmpeg Installation:  
   Open a terminal or command prompt and run:
   ```bash
   ffmpeg -version
   ```

## Installation

### Clone this repository:
    https://github.com/Noko7/SoundCloud-Downloader

### Install the required Python libraries:
  ```bash
      pip install -r requirements.txt
  ```
### Ensure yt-dlp is installed:
``` bash
    pip install yt-dlp
```

### Run the script
  ``` bash
  python main.py
  ```
1. Enter the SoundCloud playlist/profile URLs (comma-separated) in the provided text box.
2. Select a directory where downloaded files will be saved.
3. Click the Download Playlists button to start downloading.
4. Monitor the progress through the progress bar and labels.

### Notes
- Ensure FFmpeg is correctly installed and accessible at the specified path in the script.
- If a URL or FFmpeg error occurs, appropriate error messages will appear.
- The downloaded files are saved in a folder named after the playlist title.
