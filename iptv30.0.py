import vlc
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import threading
import os
import json

class IPTVPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("NG'ANJO TV Enhanced")
        self.root.geometry("600x800")  # Larger default window size

        self.channels = []
        self.current_channel_index = 0
        self.favorites = set()
        self.config_file = 'iptv_config.json'

        self.instance = vlc.Instance('--no-xlib')
        self.media_player = self.instance.media_player_new()

        # Enhanced caching mechanism
        self.channel_url_cache = {}
        
        # Load saved configuration
        self.load_config()

        self.create_widgets()
        self.setup_key_bindings()

    def create_widgets(self):
        # Playlist Selection Frame
        playlist_frame = tk.Frame(self.root)
        playlist_frame.pack(fill=tk.X, padx=10, pady=5)

        playlist_label = tk.Label(playlist_frame, text="Playlist:")
        playlist_label.pack(side=tk.LEFT)

        self.playlist_entry = tk.Entry(playlist_frame, width=50)
        self.playlist_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        browse_button = tk.Button(playlist_frame, text="Browse", command=self.open_playlist)
        browse_button.pack(side=tk.LEFT)

        # Channel List Frame
        channel_list_frame = tk.Frame(self.root)
        channel_list_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)

        # Search Entry
        search_frame = tk.Frame(self.root)
        search_frame.pack(fill=tk.X, padx=10, pady=5)

        search_label = tk.Label(search_frame, text="Search:")
        search_label.pack(side=tk.LEFT)

        self.search_entry = tk.Entry(search_frame, width=50)
        self.search_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.search_entry.bind('<KeyRelease>', self.filter_channels)

        # Channel Listbox with Scrollbar
        self.channel_listbox = tk.Listbox(channel_list_frame, selectmode=tk.SINGLE, height=20, width=50)
        self.channel_listbox.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        channel_scrollbar = tk.Scrollbar(channel_list_frame, orient=tk.VERTICAL)
        channel_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.channel_listbox.config(yscrollcommand=channel_scrollbar.set)
        channel_scrollbar.config(command=self.channel_listbox.yview)

        # Buttons Frame
        buttons_frame = tk.Frame(self.root)
        buttons_frame.pack(fill=tk.X, padx=10, pady=5)

        play_button = tk.Button(buttons_frame, text="Play", command=self.play_selected_channel)
        play_button.pack(side=tk.LEFT, expand=True)

        next_button = tk.Button(buttons_frame, text="Next", command=self.next_channel)
        next_button.pack(side=tk.LEFT, expand=True)

        prev_button = tk.Button(buttons_frame, text="Previous", command=self.prev_channel)
        prev_button.pack(side=tk.LEFT, expand=True)

        favorite_button = tk.Button(buttons_frame, text="Favorite", command=self.toggle_favorite)
        favorite_button.pack(side=tk.LEFT, expand=True)

        # Status Bar
        self.status_var = tk.StringVar()
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_key_bindings(self):
        # Add keyboard shortcuts
        self.root.bind('<Right>', lambda e: self.next_channel())
        self.root.bind('<Left>', lambda e: self.prev_channel())
        self.root.bind('<space>', lambda e: self.play_selected_channel())
        self.root.bind('<f>', lambda e: self.toggle_favorite())

    def load_config(self):
        # Load saved favorites and last playlist
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.favorites = set(config.get('favorites', []))
                last_playlist = config.get('last_playlist')
                if last_playlist and os.path.exists(last_playlist):
                    self.playlist_entry.insert(0, last_playlist)
                    self.update_channel_list(last_playlist)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def save_config(self):
        # Save favorites and last playlist
        config = {
            'favorites': list(self.favorites),
            'last_playlist': self.playlist_entry.get()
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f)

    def filter_channels(self, event=None):
        # Filter channels based on search term
        search_term = self.search_entry.get().lower()
        self.channel_listbox.delete(0, tk.END)
        
        for channel in self.channels:
            channel_info = channel['info'].replace("#EXTINF:", "").strip().lower()
            if search_term in channel_info:
                display_text = channel_info
                if channel_info in self.favorites:
                    display_text = "★ " + display_text
                self.channel_listbox.insert(tk.END, display_text)

    def toggle_favorite(self):
        # Add/remove channel from favorites
        selected_channel_index = self.channel_listbox.curselection()
        if selected_channel_index:
            index = selected_channel_index[0]
            channel_info = self.channel_listbox.get(index).lstrip('★ ')
            
            if channel_info in self.favorites:
                self.favorites.remove(channel_info)
            else:
                self.favorites.add(channel_info)
            
            self.save_config()
            self.filter_channels()  # Refresh the list to show/hide favorite star

    def open_playlist(self):
        file_path = filedialog.askopenfilename(filetypes=[("M3U files", "*.m3u")])
        if file_path:
            self.playlist_entry.delete(0, tk.END)
            self.playlist_entry.insert(0, file_path)
            self.update_channel_list(file_path)
            self.save_config()

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
                    elif current_channel and line and not line.startswith('#'):
                        current_channel['url'] = line

                if current_channel:
                    self.channels.append(current_channel)

                self.channel_listbox.delete(0, tk.END)
                for channel in self.channels:
                    channel_info = channel['info'].replace("#EXTINF:", "").strip()
                    display_text = channel_info
                    if channel_info in self.favorites:
                        display_text = "★ " + display_text
                    self.channel_listbox.insert(tk.END, display_text)

                self.status_var.set(f"Loaded {len(self.channels)} channels")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load playlist: {str(e)}")
            self.status_var.set("Failed to load playlist")

    def play_selected_channel(self):
        selected_channel_index = self.channel_listbox.curselection()
        if selected_channel_index:
            index = selected_channel_index[0]
            channel_display_text = self.channel_listbox.get(index)
            channel_info = channel_display_text.lstrip('★ ')
            
            # Find the actual channel by info
            selected_channel = next((ch for ch in self.channels if ch['info'].replace("#EXTINF:", "").strip() == channel_info), None)
            
            if selected_channel:
                if not selected_channel.get('url'):
                    threading.Thread(target=self.fetch_and_play_channel, args=(selected_channel,)).start()
                else:
                    self.play_iptv_url(selected_channel['url'])
                
                self.status_var.set(f"Playing: {channel_info}")
            else:
                messagebox.showwarning("Channel Not Found", "Could not find the selected channel.")

    def fetch_and_play_channel(self, selected_channel):
        selected_channel['url'] = self.fetch_selected_channel_url(selected_channel)
        self.play_iptv_url(selected_channel['url'])

    def fetch_selected_channel_url(self, selected_channel):
        channel_info = selected_channel['info']
        
        # Check cache first
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
                    elif current_channel and line and not line.startswith('#'):
                        self.channel_url_cache[channel_info] = line
                        return line
        except Exception as e:
            messagebox.showerror("URL Fetch Error", str(e))
            return None

    def play_iptv_url(self, stream_url):
        if stream_url:
            media = self.instance.media_new(stream_url)
            self.media_player.set_media(media)
            self.media_player.play()
        else:
            messagebox.showwarning("Play Error", "Invalid stream URL")

    def next_channel(self):
        self.current_channel_index = (self.current_channel_index + 1) % len(self.channels)
        self.update_current_channel()

    def prev_channel(self):
        self.current_channel_index = (self.current_channel_index - 1 + len(self.channels)) % len(self.channels)
        self.update_current_channel()

    def update_current_channel(self):
        self.channel_listbox.selection_clear(0, tk.END)
        self.channel_listbox.selection_set(self.current_channel_index)
        self.channel_listbox.see(self.current_channel_index)
        self.play_selected_channel()

    def on_closing(self):
        # Cleanup and save config before closing
        self.media_player.release()
        self.save_config()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    player = IPTVPlayer(root)
    root.protocol("WM_DELETE_WINDOW", player.on_closing)
    root.mainloop()