#!/usr/bin/python3
# -*- mode:python; conding:utf-8; tab-width:4 -*-

import binascii
import sys
import time
import Ice
Ice.loadSlice('downloader.ice')
# pylint: disable=E0401
import Downloader
import IceStorm
import os

BLOCK_SIZE = 10240

"""class DownloaderCB(object):
	def response(self, retval):
		print("Callback: Value: {0}".format(retval))
	
	def failure(self, ex):
		print("Ex: {0}".format(ex))"""
		
class ProgressEventI(Downloader.ProgressEvent):
	
	clips = {}
	
	def notify(self, ClipData, current=None):
		self.clips[ClipData.URL] = ClipData.status
		print("Clip {0} actually in: {1}".format(ClipData.URL, ClipData.status))
		sys.stdout.flush()
		

class Client(Ice.Application):

	songList = []

	def get_topic_manager(self):
		key = "IceStorm.TopicManager.Proxy"
		proxy = self.communicator().propertyToProxy(key)
		if proxy is None:
			print("Error with the IceStorm proxy")
			return None
		print("using IceStorm in '%s'" % key)
		return IceStorm.TopicManagerPrx.checkedCast(proxy)
		
	def conn_IceStorm(self, url):
		topic_mgr = self.get_topic_manager()
		if not topic_mgr:
			print(': invalid proxy')
			return 2
		
		ic = self.communicator()
		servant = ProgressEventI()
		adapter = ic.createObjectAdapter("ProgressAdapter")
		subscriber = adapter.addWithUUID(servant)
		topic_name = "ProgressTopic"
		qos = {}
		try:
			topic = topic_mgr.retrieve(topic_name)
			print("Topic found: {}".format(topic))
		except IceStorm.NoSuchTopic:
			topic = topic_mgr.create(topic_name)
			
		topic.subscribeAndGetPublisher(qos, subscriber)
		print("Showing info about: {} progress".format(url))
		
		adapter.activate()
		
		self.shutdownOnInterrupt()
		ic.waitForShutdown()
		topic.unsubscribe(subscriber)
		return 0

	def sendURL(self, scheduler):		
		url = "http://www.youtube.com/watch?v=LDU_Txk06tM"
		"""url = input("URL to download: ")"""	
		print("enviando")
		downloader = scheduler.make("Scheduler10")
		handler = downloader.begin_addDownloadTask(url)

		while not handler.isSent():
			time.sleep(0.1)

		print("A download request for url: {} was sent to the server!".format(url))

		return 0

	def run(self, argv):
		proxy = self.communicator().stringToProxy(argv[1])
		print(proxy)
		factory = Downloader.SchedulerFactoryPrx.checkedCast(proxy)
		"""transferCtrl = Downloader.TransferPrx.checkedCast(proxy)"""

		if not factory:
			raise RuntimeError('Invalid proxy')

		"""downloader_cb = DownloaderCB()"""

		option = 1
		
		while True:	
			print("\n--MENU--")
			print("1-Ask for download")
			print("2-Info about download process")
			print("3-Obtain audio files")
			print("4-Obtain list of downloaded files")
			print("Press any number to exit\n")
			option = int(input("Choose an option from the menu: "))
			if option == 1:
				self.sendURL(factory)
			elif option == 2:
				self.conn_IceStorm("http://www.youtube.com/watch?v=LDU_Txk06tM")
				continue
			elif option == 3:
				self.askForSong(factory)
			elif option == 4:
				self.printSongList(factory)
				continue
			else:
				break
	
		return 0
		
	def askForSong(self, scheduler):
		print("\nThe list of available songs to transfer is:")
		self.printSongList(scheduler)
		songTT = int(input("Type in the song you want to transfer (indicating number)-->"))
		songTTStr = self.songList[songTT]
		songTTStr = songTTStr[2:]
		fact = scheduler.make("Transfer{}".format(os.getpid))
		target = input("\nType a name for the file-->")
		target = target + ".mp3"
		transfer = fact.get(songTTStr)
		self.receive(transfer, target)
		print("Transfer succesful")
				
	def printSongList(self, scheduler):
		downloader = scheduler.make("SongList")
		self.songList = downloader.getSongList()
		
		print("\nThe list of downloaded songs is as follows:\n")
		
		counter = 0

		for song in self.songList:
			print("{0} - {1}".format(counter,song))
			counter = counter + 1
			
		print("")

	def receive(self, transfer, destination_file): 
		with open(destination_file, 'wb') as file_contents:
			remoteEOF = False
			while not remoteEOF:
				data = transfer.recv(BLOCK_SIZE)
				if len(data) > 1:
					data = data[1:]
				data = binascii.a2b_base64(data)
				remoteEOF = len(data) < BLOCK_SIZE
				if data:
					file_contents.write(data)
			transfer.end()

sys.exit(Client().main(sys.argv))
		
	
	
