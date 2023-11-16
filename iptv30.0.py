import vlc
import tkinter as tk
from tkinter import filedialog
import threading

class IPTVPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("NG'ANJO TV")

        self.channels = []
        self.current_channel_index = 0

        self.instance = vlc.Instance('--no-xlib')
        self.media_player = self.instance.media_player_new()

        # Cache for fetched channel URLs
        self.channel_url_cache = {}

        self.create_widgets()

    def create_widgets(self):
        playlist_label = tk.Label(self.root, text="Enter Key:")
        playlist_label.pack()

        self.playlist_entry = tk.Entry(self.root, width=50)
        self.playlist_entry.pack()

        browse_button = tk.Button(self.root, text="Browse", command=self.open_playlist)
        browse_button.pack()

        channel_list_frame = tk.Frame(self.root)
        channel_list_frame.pack()

        self.channel_listbox = tk.Listbox(channel_list_frame, selectmode=tk.SINGLE, height=15, width=30)
        self.channel_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        channel_scrollbar = tk.Scrollbar(channel_list_frame, orient=tk.VERTICAL)
        channel_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.channel_listbox.config(yscrollcommand=channel_scrollbar.set)
        channel_scrollbar.config(command=self.channel_listbox.yview)

        play_channel_button = tk.Button(self.root, text="Play Selected Channel", command=self.play_selected_channel)
        play_channel_button.pack()

        next_button = tk.Button(self.root, text="Next", command=self.next_channel)
        prev_button = tk.Button(self.root, text="Previous", command=self.prev_channel)
        next_button.pack()
        prev_button.pack()

    def open_playlist(self):
        file_path = filedialog.askopenfilename(filetypes=[("M3U files", "*.m3u")])
        if file_path:
            self.playlist_entry.delete(0, tk.END)
            self.playlist_entry.insert(0, file_path)
            self.update_channel_list(file_path)

    def update_channel_list(self, playlist_url):
        self.channels = []
        try:
            with open(playlist_url, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                current_channel = None

                for line in lines:
                    line = line.strip()
                    if line.startswith("#EXTINF:"):
                        if current_channel:
                            self.channels.append(current_channel)
                        current_channel = {'info': line, 'url': ''}
                    elif current_channel:
                        current_channel['url'] = line

                if current_channel:
                    self.channels.append(current_channel)

                self.channel_listbox.delete(0, tk.END)
                for channel in self.channels:
                    channel_info = channel['info'].replace("#EXTINF:", "").strip()
                    self.channel_listbox.insert(tk.END, channel_info)
        except Exception as e:
            self.channel_listbox.delete(0, tk.END)
            self.channel_listbox.insert(tk.END, "Error: " + str(e))

    def fetch_selected_channel_url(self, selected_channel):
        channel_info = selected_channel['info']
        if channel_info in self.channel_url_cache:
            return self.channel_url_cache[channel_info]

        try:
            with open(self.playlist_entry.get(), 'r', encoding='utf-8') as f:
                lines = f.readlines()
                current_channel = None
                for line in lines:
                    line = line.strip()
                    if line.startswith("#EXTINF:") and line == channel_info:
                        current_channel = line
                    elif current_channel:
                        self.channel_url_cache[channel_info] = line  # Cache the URL
                        return line
        except Exception as e:
            return "Error: " + str(e)

    def play_selected_channel(self):
        selected_channel_index = self.channel_listbox.curselection()
        if selected_channel_index:
            index = selected_channel_index[0]
            selected_channel = self.channels[index]
            if not selected_channel.get('url'):
                threading.Thread(target=self.fetch_and_play_channel, args=(selected_channel,)).start()
            else:
                self.play_iptv_url(selected_channel['url'])

    def fetch_and_play_channel(self, selected_channel):
        selected_channel['url'] = self.fetch_selected_channel_url(selected_channel)
        self.play_iptv_url(selected_channel['url'])

    def play_iptv_url(self, stream_url):
        media = self.instance.media_new(stream_url)
        self.media_player.set_media(media)
        self.media_player.play()

    def next_channel(self):
        self.current_channel_index += 1
        if self.current_channel_index >= len(self.channels):
            self.current_channel_index = 0
        self.update_current_channel()

    def prev_channel(self):
        self.current_channel_index -= 1
        if self.current_channel_index < 0:
            self.current_channel_index = len(self.channels) - 1
        self.update_current_channel()

    def update_current_channel(self):
        self.channel_listbox.selection_clear(0, tk.END)
        self.channel_listbox.selection_set(self.current_channel_index)
        self.channel_listbox.see(self.current_channel_index)
        self.play_selected_channel()

if __name__ == "__main__":
    root = tk.Tk()
    player = IPTVPlayer(root)
    root.mainloop()
