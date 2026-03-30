# syt

## What is SYT?!

SYT (Simple Youtube Downloader) is a simple program that runs natively in your terminal and functions as YT-DLP without the Descriptive Lines of Pain!

Disclaimer: This content is intended for educational purposes only.

Have you ever needed to download a YouTube video? If so, you've probably used one of the hundreds of online downloaders, and got jumpscared by 20 separate malware advertisement tabs opening, OR you tried to use `yt-dlp` and gave up after seeing how many arguments you needed to download ONE video.

SYT fixes all your troubles. SYT is fully open-source, 100% free, and so simple that even your grandmother could probably figure out how to use it.

In addition to videos, SYT can extract the audio from videos, download entire **channels** with one link, download YouTube Music tracks, even full **albums** and **playlists**! It also supports all forms of YouTube videos without any extra hassle, including Clips and Lives.

## Requirements

- **Git**
- **Python 3.8+**
- **yt-dlp** — 
`pip install yt-dlp`
- **ffmpeg** — 
Windows: [ffmpeg.org](https://ffmpeg.org/download.html) Mac: `brew install ffmpeg`
Linux: `sudo apt install ffmpeg`

## Installation

**macOS / Linux:**

Step 1: Open your terminal and clone this repository locally:

```bash
git clone http://github.com/newtontriumphant/syt
```

Step 2: In your terminal, change to the folder you just cloned:

```bash
cd syt
```

Step 3: Run the install script:

```bash
chmod +x install.sh && ./install.sh
```

Then restart your terminal (or type `source ~/.zshrc`).

By doing this, you're refreshing the alias that the installer automatically added: a `noglob` alias for zsh so URLs with `?v=` don't break.

After that, you're done! You can go on to Usage!

**Windows:**

After cloning the repository locally, double-click `install.bat` or run it from Command Prompt.

After that, you can proceed to using SYT!

## Usage

After you've followed the above steps, SYT should be ready for use. (Yay!) Here's how to use it:

Open up your Terminal again and just type `syt`.
The interactive SYT main menu should open.

If it doesn't, try fully quitting and reopening your terminal. If that fails, re-run the install script and restart your OS. If nothing else works, feel free to contact @zsharpminor on the Hack Club Slack or ask your LLM of choice!

You can pick between Video + Audio or just Audio, or if you're not sure just paste a link and we'll auto-generate the best option for you.

If you wish to configure other settings (such as resolution, thumbnail inclusion, or audio quality), you can change all 33 yt-dlp settings in the Advanced Options menu of SYT.

If you just want to quickly download something, you can also type `syt [link]` into your terminal and it will immediately start the download.

You can also type `syt -a [link]` to just extract the audio from your linked video.

**Note**: by default, SYT will download videos as 1080p and audio files in the highest available quality. This can be changed in SYT's advanced settings by typing `syt`, hitting enter, and choosing the third option. If you choose to save these as default, they will also apply to the terminal command!

By default, downloads will go into your current Terminal folder, so if your terminal defaults to your `~` (or `home`) folder, that's where your videos will be. If you download playlists or albums, your files will be placed in a new folder inside that directory. For single videos, they'll just be dumped inside the folder.

To change your folder, edit the Advanced Options inside of SYT!

Made with ♡ by zsharpminor, in equivocal hate of the complexity of conventional YouTube downloaders!