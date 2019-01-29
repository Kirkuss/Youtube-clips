#!/usr/bin/python3
# -*- mode:python; conding:utf-8; tab-width:4 -*-

from __future__ import print_function
import sys
import binascii
from work_queue import WorkQueue
import Ice
import IceStorm
Ice.loadSlice('downloader.ice')
# pylint: disable=E0401
import Downloader


class SchedulerFactoryI(Downloader.SchedulerFactory):

    schedulers = {}

    def __init__(self, work_queue, broker):
        self.work_queue = work_queue
        self.broker = broker

    def make(self, name, current=None):
        servant = DownloadSchedulerI(self.work_queue)
        if name in self.schedulers:
            print("That scheduler already exists")
            return Downloader.DownloadSchedulerPrx.checkedCast(
                self.schedulers[name])
        proxy = current.adapter.add(servant, Ice.stringToIdentity(name))
        self.schedulers[name] = proxy
        return Downloader.DownloadSchedulerPrx.checkedCast(proxy)

    def kill(self, name, current=None):
        if name not in self.schedulers:
            raise Downloader.SchedulerNotFound()
        current.adapter.remove(Ice.stringToIdentity(name))
        del self.schedulers[name]

    def availableSchedulers(self, current=None):
        return len(self.schedulers)


class DownloadSchedulerI(Downloader.DownloadScheduler):
    def __init__(self, work_queue):
        self.work_queue = work_queue
        self.songs = {}

    def addDownloadTask_async(self, cb, url, current=None):
        print("New download request received!")
        self.work_queue.add(cb, url)

    def get(self, song, current=None):
        servant = TransferI(song)
        proxy = current.adapter.addWithUUID(servant)
        return Downloader.TransferPrx.checkedCast(proxy)

    def getSongList(self, current=None):
        return self.work_queue.getSongs()


class TransferI(Downloader.Transfer):
    def __init__(self, local_filename):
        self.file_contents = open(local_filename, 'rb')

    def recv(self, size, current=None):
        return str(
            binascii.b2a_base64(
                self.file_contents.read(size),
                newline=False))

    def end(self, current=None):
        self.file_contents.close()
        current.adapter.remove(current.id)


class Server(Ice.Application):
    def get_topic_manager(self):
        key = 'IceStorm.TopicManager.Proxy'
        proxy = self.communicator().propertyToProxy(key)
        if proxy is None:
            return None
        print("using icestorm in: '%s'" % key)
        return IceStorm.TopicManagerPrx.checkedCast(proxy)

    def run(self, args):

        topic_mgr = self.get_topic_manager()
        if not topic_mgr:
            print('invalid proxy')
            return 2

        topic_name = "ProgressTopic"
        try:
            topic = topic_mgr.retrieve(topic_name)
        except IceStorm.NoSuchTopic:
            topic = topic_mgr.create(topic_name)

        publisher = topic.getPublisher()
        progress = Downloader.ProgressEventPrx.uncheckedCast(publisher)

        if progress is None:
            print("Progress topic  not found")

        work_queue = WorkQueue(progress)

        ic = self.communicator()
        adapter = ic.createObjectAdapter("FactoryAdapter")
        servant = SchedulerFactoryI(work_queue, ic)
        proxy = adapter.add(servant, ic.stringToIdentity("Factory1"))

        work_queue.start()

        adapter.activate()
        print(proxy, flush=True)
        self.shutdownOnInterrupt()
        ic.waitForShutdown()

        return 0


if __name__ == '__main__':
    App = Server()
    Exit_status = App.main(sys.argv)
    sys.exit(Exit_status)
