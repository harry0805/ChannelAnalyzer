from pytubefix import YouTube, Channel, Playlist
import os
from typing import TypedDict
from datetime import datetime
import json

from rich.live import Live
from rich.console import Group
from rich.progress import Progress
from rich.status import Status
from rich.console import Console


console = Console(markup=True)

class video_detils(TypedDict):
    id: str
    title: str
    channel: str
    publish_date: float
    subtitle_location: dict

class DownloadCaptions:
    def __init__(self, url, mode: str='video', folder: str='captions', lang='en'):
        self.mode = mode
        if mode == 'video':
            v = YouTube(url)
            self.video_list = [v]
            self.name = v.title
        elif mode == 'channel':
            v = Channel(url)
            self.video_list = v.videos
            self.name = v.channel_name
        elif mode == 'playlist':
            v = Playlist(url)
            self.video_list = v.videos
            self.name = v.title
        else:
            raise TypeError('Mode can only be: video, channel or playlist')
        
        if not os.path.exists(folder):
            os.mkdir(folder)
        self.download_folder = folder

        self.lang = lang


    def download(self):
        console.print(f'[green]Starting Download from [bold]{self.mode}[/bold]: [blue]{self.name}')
        video_count = len(self.video_list)
        console.print(f'[blue]{video_count} [green]Total Videos')
        
        st = Status('[green]Starting')
        pb = Progress()
        task = pb.add_task('', total=video_count)
        
        records = {}
        record_file_path = os.path.join(self.download_folder, 'download_record.json')
        if os.path.isfile(record_file_path):
            with open(record_file_path, 'r') as f:
                try:
                    records = json.load(f)
                except json.decoder.JSONDecodeError:
                    console.print('[orange1][bold]WARNING[/bold] Failed to load download record, previous history might be lost')

        with Live(Group(st, pb), refresh_per_second=10, console=console):
            for i, vid in enumerate(self.video_list):
                pb.update(task_id=task, completed=i, description=f'[blue]({i}/{video_count})')
                
                vid_id = vid.video_id
                downloaded_lang = {}

                # Skip the video if an existing download is found
                if vid_id in records.keys():
                    downloaded_lang = records[vid_id]['subtitle_location'].get(self.lang, {})
                    if downloaded_lang:
                        continue
                
                vid_title = vid.title

                st.update(f'[green]Loading: [bold blue]{vid_id} ({vid_title})')
                # Get video captions for the specified language, try the auto generated one if there are none
                captions = vid.captions.get(self.lang, None)
                captions = vid.captions.get('a.' + self.lang, None) if captions is None else captions
                
                # Skip this video if there are no captions for the video
                if captions is None:
                    console.print(f'[yellow][bold]SKIPPING![/bold] [orange1]No [bold]{self.lang}[/bold] captions found for video: {vid_id} ({vid_title})')
                    continue
                
                # Prepare the download record information
                file_name = f"{vid_id}({self.lang}).srt"
                downloaded_lang.update({self.lang: file_name})
                record = video_detils(
                    id=vid_id,
                    title=vid_title,
                    channel=vid.channel_id,
                    publish_date=vid.publish_date.timestamp(),
                    subtitle_location=downloaded_lang
                )
                records.update({vid_id: record})

                if not os.path.isfile(filepath := os.path.join(self.download_folder, file_name)):
                    captions.save_captions(filepath)

                with open(record_file_path, 'w') as f:
                    json.dump(records, f)
                
            st.update(f'[green]Downloading: [bold]Finished!')
            pb.update(task_id=task, completed=i + 1, description=f'[blue]({video_count}/{video_count})')
        console.print('[green]Download complete!')


if __name__ == '__main__':
    # url = 'https://youtube.com/playlist?list=PLo3cFP2tL68PCQE200-ygWdXGi1Y4jXmA'
    # url = 'https://www.youtube.com/@lastdays247'
    url = 'https://www.youtube.com/@MarkRober'
    print('loading...')
    d = DownloadCaptions(url, mode='channel')
    d.download()