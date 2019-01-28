#!/usr/bin/python3
# -*- mode:python; conding:utf-8; tab-width:4 -*-

import binascii
import sys
import time
import Ice
Ice.loadSlice('downloader.ice')
# pylint: disable=E0401
import Downloader

BLOCK_SIZE = 10240

class DownloaderCB(object):
	def response(self, retval):
		print("Callback: Value: {0}".format(retval))
	
	def failure(self, ex):
		print("Ex: {0}".format(ex))


class Client(Ice.Application):
	def sendURL(self, scheduler):		
		url = "http://www.youtube.com/watch?v=LDU_Txk06tM"
		"""url = input("URL to download: ")"""	
		print("enviando")
		downloader = scheduler.make("Scheduler11")
		handler = downloader.begin_addDownloadTask(url)

		while not handler.isSent():
			time.sleep(0.1)

		print("donete")

		return 0

	def run(self, argv):
		proxy = self.communicator().stringToProxy(argv[1])
		print(proxy)
		factory = Downloader.SchedulerFactoryPrx.checkedCast(proxy)
		"""transferCtrl = Downloader.TransferPrx.checkedCast(proxy)"""

		if not factory:
			raise RuntimeError('Invalid proxy')

		downloader_cb = DownloaderCB()

		option = 1
		
		while True:	
			print("--MENU--")
			print("1-Ask for download")
			print("2-Info about download process")
			print("3-Obtain audio files")
			print("4-Obtain list of downloaded files")
			print("Press any number to exit")
			option = int(input("Choose an option from the menu: "))
			if option == 1:
				self.sendURL(factory)
			elif option == 2:
				continue
			elif option == 3:
				transfer = scheduler.get('Noisestorm - Crab Rave [Monstercat Release].mp3')
				self.receive(transfer, 'hola.mp3')
			elif option == 4:
				continue
			else:
				break
	
		return 0


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
		
	
	
