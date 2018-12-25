#!/usr/bin/python3
# -*- mode:python; coding:utf-8; tab-width:4 -*-

import binascii
import Ice
Ice.loadSlice('downloader.ice')
# pylint: disable=E0401
import Downloader
import work_queue
from queue import Queue

class TransferI(Downloader.Transfer):
    '''
    Transfer file
    '''
    def __init__(self, local_filename):
        self.file_contents = open(local_filename, 'rb')

    def recv(self, size, current=None):
        '''Send data block to client'''
        return str(
            binascii.b2a_base64(self.file_contents.read(size), newline=False)
        ) #devuelve una representacion imprimible de un objeto, en base64

    def end(self, current=None):
        '''Close transfer and free objects'''
        self.file_contents.close()
        current.adapter.remove(current.id)

#TODO:
#Revisar la implementacion de DownloadScheduler porque faltan muchas cosas

class DownloadSchedulerI(Downloader.DownloadScheduler):

	def __init__(self):
		self.wq = work_queue.WorkQueue()
		self.songList = []
	
	def getSongList(self):
		return self.songList

	def addDownloadTask(self, URL):
		self.songList.append(URL)
		self.wq.add(callback, URL)

	def get(self, song): #Ni idea de que pretende esta funcion
		##

	def cancelTask(URL): #Esto tiene que estar mal pero mas o menos tiene que ser asi como funcione
		AuxJobs = self.wq.queue
		for Job in AuxJobs:
			j = AuxJobs.get()
			if j.url == URL:
				j.cancel()
			else:
				print("The job doesn't exists, no Jobs where removed from the queue")
			
		

#TODO:
#Implementar la funcionalidad principal del servidor 'run()'
#Probar el funcionamiento sin los canales de comunicacion y una vez este funcione implementar el uso de dichos canales y configurar el grid

'''

class Server(Ice.Application):
	
	#def get topic manager
	
	def run(self, args):
		servant = TransferI()

'''
	
	
