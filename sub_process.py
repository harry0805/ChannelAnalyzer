import os
import re
import json
import pysrt

from rich.live import Live
from rich.console import Group
from rich.progress import Progress
from rich.status import Status
from rich.console import Console

console = Console(markup=True)


class ConvertCaptions:
    def __init__(self, input_folder: str='./captions', output_folder: str='./processed_captions', lang='en', record_file: str=None):
        self.in_folder = input_folder
        self.out_folder = output_folder
        self.lang = lang
        os.makedirs(output_folder, exist_ok=True)

        record_location = record_file if record_file else os.path.join(input_folder, 'download_record.json')
        with open(record_location, 'r') as f:
            self.record = json.load(f)
        
        self._filter_lang()
    
    def _filter_lang(self):
        self.record = {vid: detils for vid, detils in self.record.items() if self.lang in detils['subtitle_location'].keys()}

    def filter_by_channel(self, channel_id):
        self.record = {vid: detils for vid, detils in self.record.items() if detils['channel'] == channel_id}
    
    @staticmethod
    def remove_brackets(text):
        # Match brackets and their contents, including any trailing whitespace
        return re.sub(r'\[.*?\]\s*', '', text)

    def convert(self, remove_brackets=True):
        file_list = [f['subtitle_location'][self.lang] for f in self.record.values()]

        st = Status('[green]Starting')
        pb = Progress()
        task = pb.add_task('', total=len(file_list))

        with Live(Group(st, pb), refresh_per_second=10, console=console):
            for i, file in enumerate(file_list):
                st.update(f'[green]Processing: [bold blue]{file}')
                pb.update(task_id=task, completed=i+1, description=f'[blue]({i+1}/{len(file_list)})')
                
                # Open and extract all text from the srt file
                subs = pysrt.open(os.path.join(self.in_folder, file))
                text = ' '.join([s.text for s in subs])
                # Remove brackets
                text = self.remove_brackets(text) if remove_brackets else text
                
                output_path = os.path.join(self.out_folder, os.path.splitext(file)[0] + '.txt')
                with open(output_path, 'w') as f:
                    f.write(text)
            st.update(f'[green]Processing: [bold]Done!')


if __name__ == '__main__':
    c = ConvertCaptions(output_folder='./LastDays_captions')
    c.filter_by_channel('UCBqj7_4xib9pKATW4394PmQ')
    c.convert()