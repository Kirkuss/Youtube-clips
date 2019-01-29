#!/usr/bin/python3
# -*- mode:python; coding:utf-8; tab-width:4 -*-

'''
Simple task queue implementation
'''

import os.path
from threading import Thread
from queue import Queue

import youtube_dl

import Ice
# pylint: disable=C0413
Ice.loadSlice('downloader.ice')
# pylint: enable=C0413
# pylint: disable=E0401
import Downloader

songs = []


class NullLogger:
    '''
    Logger used to disable youtube-dl output
    '''

    def debug(self, msg):
        '''Ignore debug messages'''

    def warning(self, msg):
        '''Ignore warnings'''

    def error(self, msg):
        '''Ignore errors'''


# Default configuration for youtube-dl
DOWNLOADER_OPTS = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'logger': NullLogger()
}


def _download_mp3_(url, destination='./'):
    '''
    Synchronous download from YouTube
    '''
    options = {}
    task_status = {}

    def progress_hook(status):
        task_status.update(status)
    options.update(DOWNLOADER_OPTS)
    options['progress_hooks'] = [progress_hook]
    options['outtmpl'] = os.path.join(destination, '%(title)s.%(ext)s')
    with youtube_dl.YoutubeDL(options) as ydl:
        ydl.download([url])
    filename = task_status['filename']
    # BUG: filename extension is wrong, it must be mp3
    filename = filename[:filename.rindex('.') + 1]
    songs.append(filename + options['postprocessors'][0]['preferredcodec'])
    return filename + options['postprocessors'][0]['preferredcodec']


class WorkQueue(Thread):
    '''Job Queue to dispatch tasks'''
    QUIT = 'QUIT'
    CANCEL = 'CANCEL'

    def __init__(self, progress):
        super(WorkQueue, self).__init__()
        self.queue = Queue()
        self.progress = progress

    def run(self):
        '''Task dispatcher loop'''
        for job in iter(self.queue.get, self.QUIT):
            status_data = Downloader.ClipData()
            status_data.URL = job.url
            status_data.status = Downloader.Status.INPROGRESS
            self.progress.notify(status_data)
            try:
                job.download()
                status_data = Downloader.ClipData()
                status_data.URL = job.url
                status_data.status = Downloader.Status.DONE
                self.progress.notify(status_data)
                self.queue.task_done()
            except Exception as e:
                status_data = Downloader.ClipData()
                status_data.URL = job.url
                status_data.status = Downloader.Status.ERROR
                self.progress.notify(status_data)

        self.queue.task_done()
        self.queue.put(self.CANCEL)

        for job in iter(self.queue.get, self.CANCEL):
            job.cancel()
            self.queue.task_done()

        self.queue.task_done()

    def add(self, callback, url):
        '''Add new task to queue'''
        status_data = Downloader.ClipData()
        status_data.URL = url
        status_data.status = Downloader.Status.PENDING
        self.queue.put(Job(callback, url))
        self.progress.notify(status_data)

    def destroy(self):
        '''Cancel tasks queue'''
        self.queue.put(self.QUIT)
        self.queue.join()

    def getSongs(self):
        return songs


class Job:
    '''Task: clip to download'''

    def __init__(self, callback, url):
        self.callback = callback
        self.url = url

    def download(self):
        '''Donwload clip'''
        self.callback.ice_response(_download_mp3_(self.url))

    def cancel(self):
        '''Cancel donwload'''
        self.callback.ice_exception(Downloader.SchedulerCancelJob())
