#!/usr/bin/env python3
"""Universal video downloader for Windows."""

from __future__ import annotations

import os
import queue
import re
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

import imageio_ffmpeg
import yt_dlp

APP_NAME = "Universal Video Downloader"
DEFAULT_FOLDER = Path.home() / "Downloads" / "Videos"


def ffmpeg_dir() -> str:
    exe = Path(imageio_ffmpeg.get_ffmpeg_exe())
    return str(exe.parent)


def is_url(text: str) -> bool:
    return bool(re.match(r"^https?://", text.strip(), re.I))


class DownloaderApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("760x640")
        self.root.minsize(680, 560)
        self.root.configure(bg="#0f1419")

        self.events: queue.Queue[tuple] = queue.Queue()
        self.busy = False
        self.video_info: dict[str, Any] | None = None
        self.folder = tk.StringVar(value=str(DEFAULT_FOLDER))
        self.url = tk.StringVar()
        self.quality = tk.StringVar(value="best")
        self.audio_only = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="Вставьте ссылку на видео с любого сервиса")
        self.meta = tk.StringVar(value="")
        self.progress = tk.DoubleVar(value=0)

        DEFAULT_FOLDER.mkdir(parents=True, exist_ok=True)
        self._style()
        self._build()
        self.root.after(80, self._poll)

    def _style(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        bg = "#0f1419"
        card = "#1a2330"
        fg = "#e8eef6"
        muted = "#8aa0b8"
        accent = "#3d8bfd"
        style.configure(".", background=bg, foreground=fg, fieldbackground=card)
        style.configure("TFrame", background=bg)
        style.configure("Card.TFrame", background=card)
        style.configure("TLabel", background=bg, foreground=fg, font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=bg, foreground=muted, font=("Segoe UI", 9))
        style.configure("Title.TLabel", background=bg, foreground=fg, font=("Segoe UI Semibold", 18))
        style.configure("Card.TLabel", background=card, foreground=fg, font=("Segoe UI", 10))
        style.configure("TCheckbutton", background=bg, foreground=fg, font=("Segoe UI", 10))
        style.map("TCheckbutton", background=[("active", bg)])
        style.configure("TEntry", fieldbackground=card, foreground=fg, insertcolor=fg)
        style.configure("TCombobox", fieldbackground=card, foreground=fg, background=card)
        style.map("TCombobox", fieldbackground=[("readonly", card)], foreground=[("readonly", fg)])
        style.configure("Accent.TButton", background=accent, foreground="#fff", font=("Segoe UI Semibold", 10), padding=8)
        style.map("Accent.TButton", background=[("active", "#5aa1ff"), ("disabled", "#2a3a4d")])
        style.configure("TButton", background="#243044", foreground=fg, padding=7)
        style.map("TButton", background=[("active", "#31425a")])
        style.configure("Horizontal.TProgressbar", troughcolor="#243044", background=accent, bordercolor=bg)

    def _build(self) -> None:
        pad = {"padx": 22, "pady": 6}
        ttk.Label(self.root, text=APP_NAME, style="Title.TLabel").pack(anchor="w", padx=22, pady=(18, 2))
        ttk.Label(
            self.root,
            text="YouTube, VK, TikTok, Instagram, Twitter/X, Twitch, Vimeo, Rutube и сотни других сайтов",
            style="Muted.TLabel",
        ).pack(anchor="w", padx=22, pady=(0, 10))

        ttk.Label(self.root, text="Ссылка на видео").pack(anchor="w", **pad)
        url_row = ttk.Frame(self.root)
        url_row.pack(fill="x", padx=22)
        entry = ttk.Entry(url_row, textvariable=self.url, font=("Segoe UI", 11))
        entry.pack(side="left", fill="x", expand=True, ipady=6)
        entry.bind("<Return>", lambda _e: self.fetch_info())
        ttk.Button(url_row, text="Вставить", command=self.paste).pack(side="left", padx=(8, 0))
        ttk.Button(url_row, text="Инфо", command=self.fetch_info).pack(side="left", padx=(8, 0))

        ttk.Label(self.root, textvariable=self.meta, style="Muted.TLabel").pack(anchor="w", **pad)

        opts = ttk.Frame(self.root)
        opts.pack(fill="x", padx=22, pady=8)
        ttk.Label(opts, text="Качество").pack(side="left")
        combo = ttk.Combobox(
            opts,
            textvariable=self.quality,
            state="readonly",
            width=28,
            values=(
                "best",
                "bestvideo+bestaudio",
                "1080p",
                "720p",
                "480p",
                "360p",
            ),
        )
        combo.pack(side="left", padx=(8, 18))
        ttk.Checkbutton(opts, text="Только аудио (MP3)", variable=self.audio_only).pack(side="left")

        folder_row = ttk.Frame(self.root)
        folder_row.pack(fill="x", padx=22, pady=6)
        ttk.Label(folder_row, text="Папка").pack(side="left")
        ttk.Entry(folder_row, textvariable=self.folder).pack(side="left", fill="x", expand=True, padx=8, ipady=4)
        ttk.Button(folder_row, text="Обзор…", command=self.pick_folder).pack(side="left")

        btns = ttk.Frame(self.root)
        btns.pack(fill="x", padx=22, pady=10)
        self.dl_btn = ttk.Button(btns, text="Скачать", style="Accent.TButton", command=self.download)
        self.dl_btn.pack(side="left")
        ttk.Button(btns, text="Открыть папку", command=self.open_folder).pack(side="left", padx=8)

        self.bar = ttk.Progressbar(self.root, variable=self.progress, maximum=100)
        self.bar.pack(fill="x", padx=22, pady=(4, 6))
        ttk.Label(self.root, textvariable=self.status, style="Muted.TLabel").pack(anchor="w", padx=22)

        ttk.Label(self.root, text="Журнал").pack(anchor="w", padx=22, pady=(12, 4))
        log_frame = ttk.Frame(self.root)
        log_frame.pack(fill="both", expand=True, padx=22, pady=(0, 18))
        self.log = tk.Text(
            log_frame,
            height=12,
            bg="#1a2330",
            fg="#c9d6e5",
            insertbackground="#c9d6e5",
            relief="flat",
            font=("Consolas", 9),
            wrap="word",
        )
        scroll = ttk.Scrollbar(log_frame, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self._log("Готово. Движок: yt-dlp. Скачивайте только то, на что у вас есть права.")

    def _log(self, text: str) -> None:
        self.log.insert("end", text + "\n")
        self.log.see("end")

    def paste(self) -> None:
        try:
            self.url.set(self.root.clipboard_get().strip())
        except tk.TclError:
            messagebox.showinfo(APP_NAME, "Буфер обмена пуст")

    def pick_folder(self) -> None:
        chosen = filedialog.askdirectory(initialdir=self.folder.get())
        if chosen:
            self.folder.set(chosen)

    def open_folder(self) -> None:
        path = Path(self.folder.get())
        path.mkdir(parents=True, exist_ok=True)
        os.startfile(path)

    def _set_busy(self, value: bool) -> None:
        self.busy = value
        state = "disabled" if value else "normal"
        self.dl_btn.configure(state=state)

    def fetch_info(self) -> None:
        url = self.url.get().strip()
        if not is_url(url):
            messagebox.showwarning(APP_NAME, "Вставьте корректную ссылку (http/https).")
            return
        if self.busy:
            return
        self._set_busy(True)
        self.status.set("Получаю информацию о видео…")
        threading.Thread(target=self._info_worker, args=(url,), daemon=True).start()

    def download(self) -> None:
        url = self.url.get().strip()
        if not is_url(url):
            messagebox.showwarning(APP_NAME, "Вставьте корректную ссылку (http/https).")
            return
        if self.busy:
            return
        out = Path(self.folder.get())
        out.mkdir(parents=True, exist_ok=True)
        self.progress.set(0)
        self._set_busy(True)
        self.status.set("Скачиваю…")
        threading.Thread(target=self._download_worker, args=(url, str(out)), daemon=True).start()

    def _opts_base(self) -> dict[str, Any]:
        return {
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "ffmpeg_location": ffmpeg_dir(),
            "retries": 8,
            "fragment_retries": 8,
            "concurrent_fragment_downloads": 4,
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
                )
            },
        }

    def _format_selector(self) -> str:
        if self.audio_only.get():
            return "bestaudio/best"
        q = self.quality.get()
        mapping = {
            "best": "bv*+ba/b",
            "bestvideo+bestaudio": "bv*+ba/b",
            "1080p": "bv*[height<=1080]+ba/b[height<=1080]/b",
            "720p": "bv*[height<=720]+ba/b[height<=720]/b",
            "480p": "bv*[height<=480]+ba/b[height<=480]/b",
            "360p": "bv*[height<=360]+ba/b[height<=360]/b",
        }
        return mapping.get(q, "bv*+ba/b")

    def _info_worker(self, url: str) -> None:
        try:
            opts = self._opts_base()
            opts["skip_download"] = True
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
            if info is None:
                raise RuntimeError("Сервис не вернул данные")
            self.events.put(("info", info))
        except Exception as exc:  # noqa: BLE001
            self.events.put(("error", f"Не удалось прочитать ссылку: {exc}"))

    def _download_worker(self, url: str, folder: str) -> None:
        def hook(d: dict[str, Any]) -> None:
            status = d.get("status")
            if status == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                done = d.get("downloaded_bytes") or 0
                pct = (done / total * 100) if total else 0
                speed = d.get("speed") or 0
                filename = Path(str(d.get("filename") or "")).name
                self.events.put(("progress", pct, filename, speed))
            elif status == "finished":
                self.events.put(("log", f"Файл получен, обрабатываю: {Path(str(d.get('filename') or '')).name}"))

        try:
            opts = self._opts_base()
            opts.update(
                {
                    "outtmpl": str(Path(folder) / "%(title).200B [%(id)s].%(ext)s"),
                    "format": self._format_selector(),
                    "merge_output_format": "mp4",
                    "progress_hooks": [hook],
                    "ignoreerrors": False,
                    "windowsfilenames": True,
                    "restrictfilenames": False,
                }
            )
            if self.audio_only.get():
                opts["postprocessors"] = [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ]
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            self.events.put(("done", folder))
        except Exception as exc:  # noqa: BLE001
            self.events.put(("error", f"Ошибка загрузки: {exc}"))

    def _poll(self) -> None:
        try:
            while True:
                item = self.events.get_nowait()
                kind = item[0]
                if kind == "info":
                    info = item[1]
                    self.video_info = info
                    title = info.get("title") or "Без названия"
                    extractor = info.get("extractor_key") or info.get("ie_key") or "unknown"
                    duration = info.get("duration")
                    dur = ""
                    if isinstance(duration, (int, float)) and duration:
                        m, s = divmod(int(duration), 60)
                        h, m = divmod(m, 60)
                        dur = f" • {h}:{m:02d}:{s:02d}" if h else f" • {m}:{s:02d}"
                    n = info.get("playlist_count")
                    extra = f" • плейлист: {n} шт." if n else ""
                    self.meta.set(f"{title}{dur} • {extractor}{extra}")
                    self.status.set("Информация получена. Можно скачивать.")
                    self._log(f"Найдено: {title} ({extractor})")
                    self._set_busy(False)
                elif kind == "progress":
                    _, pct, filename, speed = item
                    self.progress.set(min(100, pct))
                    speed_txt = f"{speed / 1024 / 1024:.1f} МБ/с" if speed else "…"
                    self.status.set(f"Скачиваю {filename} — {pct:.1f}% ({speed_txt})")
                elif kind == "log":
                    self._log(item[1])
                elif kind == "done":
                    self.progress.set(100)
                    self.status.set("Готово")
                    self._log(f"Скачивание завершено → {item[1]}")
                    self._set_busy(False)
                    messagebox.showinfo(APP_NAME, "Видео скачано.")
                elif kind == "error":
                    self.status.set("Ошибка")
                    self._log(item[1])
                    self._set_busy(False)
                    messagebox.showerror(APP_NAME, item[1])
        except queue.Empty:
            pass
        self.root.after(80, self._poll)


def main() -> None:
    root = tk.Tk()
    DownloaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
