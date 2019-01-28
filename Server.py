#!/usr/bin/python3
# -*- mode:python; conding:utf-8; tab-width:4 -*-

import binascii
import Ice
import IceStorm
Ice.loadSlice('downloader.ice')
# pylint: disable=E0401
import Downloader
import sys

from work_queue import *

"""
class SchedulerFactoryI(Downloader.SchedulerFactory):
	def make(self, name, current=None):
		servant = DownloadSchedulerI(work_queue)
		proxy = current.adapter.addWithUUID(servant)
		return Downloader.DownloadSchedulerPrx.checkedCast(proxy)
"""

"""class ProgressEventI(Downloader.ProgressEvent):
	def __init__(self):
		self.clips = {}
		
	def notify(self, ClipData):
		print("notification from {0}".format(ClipData.url))
		self.clips[ClipData.url] = ClipData.status
		print(self.clips)
		sys.stdout.flush()"""

class SchedulerFactoryI(Downloader.SchedulerFactory):

	schedulers = {}
	
	def __init__(self, work_queue, broker, progress):
		self.work_queue = work_queue
		self.broker = broker
		self.progress = progress

	def make(self, name, current=None):
		servant = DownloadSchedulerI(self.work_queue, self.progress)
		if name in self.schedulers:
			print("That scheduler already exists")
			return Downloader.DownloadSchedulerPrx.checkedCast(self.schedulers[name])
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
	def __init__(self, work_queue, progress):
		self.work_queue = work_queue
		self.progress = progress

	def addDownloadTask_async(self, cb, url, current=None):
		self.work_queue.add(cb, url, self.progress)

	def get(self, song, current=None):
		servant = TransferI(song)
		proxy = current.adapter.addWithUUID(servant)
		return Downloader.TransferPrx.checkedCast(proxy)
		
	def cancelTask(self, url, current=None):
		print("{0} recibido".format(url))
		sys.stdout.flush()

class TransferI(Downloader.Transfer):
	def __init__(self, local_filename):
		self.file_contents = open(local_filename, 'rb')

	def recv(self, size, current=None):
		return str(binascii.b2a_base64(self.file_contents.read(size), newline=False))

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

		work_queue = WorkQueue()

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
			print("UY")

		ic = self.communicator()
		properties = ic.getProperties()
		adapter = ic.createObjectAdapter("FactoryAdapter")
		servant = SchedulerFactoryI(work_queue, ic,  progress)
		proxy = adapter.add(servant, ic.stringToIdentity("Factory1"))
		adapter.activate()
		print(proxy, flush=True)
		self.shutdownOnInterrupt()
		ic.waitForShutdown()

		return 0

		"""work_queue = WorkQueue()
		broker = self.communicator()
		servant = SchedulerFactoryI(work_queue, broker)
		transferServant = TransferI("Noisestorm - Crab Rave [Monstercat Release].mp3")
		
		adapter = broker.createObjectAdapter("FactoryAdapter")
		proxy = adapter.add(servant, broker.stringToIdentity("Factory1"))
		
		print(proxy, flush=True)
	
		adapter.activate()
		print("adapter activated")

		work_queue.start()

		self.shutdownOnInterrupt()
		broker.waitForShutdown()

		work_queue.destroy()

		return 0"""

if __name__ == '__main__':
	app = Server()
	exit_status = app.main(sys.argv)
	sys.exit(exit_status)



	


	
	
		
