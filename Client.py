#!/usr/bin/python3
# -*- mode:python; conding:utf-8; tab-width:4 -*-

import binascii
import sys
import ice
Ice.loadSlice('downloader.ice')
# pylint: disable=E0401
import Downloader

BLOCK_SIZE = 10240

#TODO:
#Implementar la interfaz ProgressEvent (entender como funciona struct en python).

class ProgressEventI(Downloader.ProgressEvent):	

	def notify(clipData):
		

def receive(transfer, destination_file):

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

class Client(Ice.Application):

	def run(self, argv):
		proxy = self.communicator().stringToProxy(argv[1])
		transfer = Downloader.transferPrx.checkedCast(proxy)

		if not transfer:
			raise RunTimeError('Invalid proxy')

		transfer.addDownloadTask(argv[2])

		return 0

sys.exit(Client().main(sys.argv))
	
	
