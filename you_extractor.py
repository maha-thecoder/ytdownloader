from flask import Flask, render_template, request, redirect, url_for,send_from_directory
import yt_dlp
import os
import subprocess
import tempfile
import re
app = Flask(__name__)

VIDEO_DIR = r"C:\Users\Suraj\Videos"


# used to filter title with unwanted characters
def sanitize_filename(filename):
    # Replace invalid characters with underscores
    filename = re.sub(r'[<>:"/\\|?*@]', '_', filename)  # Replace invalid characters
    filename = filename.replace(" ", "_")  # Replace spaces with underscores
    return filename


# enroute to home
@app.route('/')
def home():
    return render_template('youtube.html')

# enrute to preview
@app.route('/preview', methods=['POST'])
def extract_preview():
    if request.method == 'POST':
        video_url = request.form['link']

        try:
            ydl_opt = {
                'quiet': True,
                'format': 'bestvideo+bestaudio/best',# used to get best video and audio
                'noplaylist': True
            }

            with yt_dlp.YoutubeDL(ydl_opt) as ydl:
                info = ydl.extract_info(video_url, download=False)
                title = info.get('title', None)
                views = info.get('view_count', 0)
                thumbnail = info.get('thumbnail', None)
                likes = info.get('like_count', 0)
                formats = info.get('formats', [])

                target_resolution = [144, 240, 360, 480, 720, 1080, 1440, 2160]

                # Best formats for each resolution
                best_formats = {res: None for res in target_resolution}# it will keep value to none for each key

                for fmt in formats:
                    if 'height' in fmt:
                        height = fmt['height']
                        if height in target_resolution:
                            if best_formats[height] is None or fmt['quality'] > best_formats[height]['quality']: #this is logic used bcoz of it willc heck both the quality taken by system and and quality written by logic
 
                                #  finally the logic select one format and get and set required in object 
                                best_formats[height] = {
                                    'format_id': fmt['format_id'],
                                    'resolution': height,
                                    'ext': fmt.get('ext', 'N/A'),
                                    'quality': fmt.get('quality', 'N/A')
                                }

                # Filter out the formats
                quality_output = [value for value in best_formats.values() if value is not None]

                # Here we will send the available formats and resolutions for selection
                return render_template('youtube.html',
                                       video_title=title,
                                       video_url=video_url,
                                       video_views=views,
                                       video_thumbnail=thumbnail,
                                       video_likes=likes,
                                       video_quality=quality_output)

        except Exception as e:
            return f'an error: {e}'

    
# enrute to download
@app.route('/download', methods=['POST'])
def download_video():
    if request.method == 'POST':
        video_url = request.form['link']
        selected_format = request.form['selected_format']

        if not video_url or not selected_format:
            return "Video URL or format not provided!", 400
        
        try:
            ydl_opt = {
            'quiet': True,
            'format': 'bestvideo+bestaudio/best',
            'noplaylist': True
        }
        
            with yt_dlp.YoutubeDL(ydl_opt) as ydl:
                info = ydl.extract_info(video_url, download=False)
                title = info.get('title', 'video')
                format=info.get('formats',[])

                sanitized_title = sanitize_filename(title) #removing unwanted characters inn title



#getting resolution so that to keep in the end title
                resolution=None
                for fmt in format:
                    if fmt['format_id'] == selected_format:
                        resolutions=fmt.get('height',None)
                        resolution=f'{resolutions}p'
                        break



    
            # tem video and audio file and it directory
                video_file = os.path.join(VIDEO_DIR, f'{sanitized_title}_{resolution}_video.{selected_format}')
                audio_file = os.path.join(VIDEO_DIR, f'{sanitized_title}_{resolution}_audio.mp3')
                output_file = os.path.join(VIDEO_DIR, f'{sanitized_title}_{resolution}.mp4')

        except Exception as e:
            return f"An error occurred while extracting video info: {str(e)}", 500

        try:

            '''
            notes:
            here f stands for format,o stands for output file,i stands for input file,c:v stands for codec:video,
            copy stands no changes to video and send it as a original copy without changes
            '''
            # downloading the video from user input
            subprocess.run(['yt-dlp', '-f', selected_format, '-o', video_file, video_url], check=True)
            print('video downloaded successfull')
            # Download the best audio by using yt-dllp software
            subprocess.run(['yt-dlp', '-f', 'bestaudio', '-o', audio_file, video_url], check=True)
            print('audio is downloaded successfull')
            # Combine video and audio using FFmpeg
            subprocess.run(['ffmpeg', '-i', video_file, '-i', audio_file, '-c:v', 'copy', '-c:a', 'aac', '-strict', 'experimental', output_file], check=True)
            print('merging successfull')

             # Now, delete the temporary video and audio files
            if os.path.exists(video_file):
                os.remove(video_file)
            if os.path.exists(audio_file):
                os.remove(audio_file)
            

            print('all files are removed')

            return send_from_directory(VIDEO_DIR,f'{sanitized_title}_{resolution}.mp4',as_attachment=True)
                                                                

            
            

        
            
        except subprocess.CalledProcessError as e:
            return f"An error occurred: {str(e)}", 500
        
    

    
        
    




if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
