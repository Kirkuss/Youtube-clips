#!/usr/bin/python3
# -*- mode:python; conding:utf-8; tab-width:4 -*-

import binascii
import Ice
Ice.loadSlice('downloader.ice')
# pylint: disable=E0401
import Downloader
import sys

from work_queue import *


class DownloadSchedulerI(Downloader.DownloadScheduler):
	def __init__(self, work_queue):
		self.work_queue = work_queue	

	def addDownloadTask_async(self, cb, url, current=None):
		self.work_queue.add(cb, url)

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
	def run(self, args):
		work_queue = WorkQueue()
		broker = self.communicator()
		servant = DownloadSchedulerI(work_queue)
		
		adapter = broker.createObjectAdapter("SchedulerAdapter")
		proxy = adapter.add(servant, broker.stringToIdentity("Scheduler1"))
		
		print(proxy, flush=True)
	
		adapter.activate()
		print("adapter activated")

		work_queue.start()

		self.shutdownOnInterrupt()
		broker.waitForShutdown()

		work_queue.destroy()

		return 0

if __name__ == '__main__':
	app = Server()
	exit_status = app.main(sys.argv)
	sys.exit(exit_status)



	


	
	
		
