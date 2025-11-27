import yt_dlp

def get(video_url, save_path="downloads"):
    try:
        ydl_opts = {'format': 'bestvideo+bestaudio/best', 'outtmpl': f'{save_path}/%(title)s.%(ext)s', 'merge_output_format': 'mp4'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
    except Exception as e:
        pass

cmd = ''

while cmd != 'exit':
    cmd = input()
    print(get(cmd) if cmd.startswith("http") else "")

print("Puszi!")
