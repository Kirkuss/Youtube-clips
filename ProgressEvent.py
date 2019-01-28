#!/usr/bin/python3
# -*- coding: utf-8 -*-

import Ice
import IceStorm
Ice.loadSlice('downloader.ice')
import Downloader
import sys

import enum

"""Status = Enum('PENDING','INPROGRESS','DONE','ERROR')"""
	
class ProgressEventI(Downloader.ProgressEvent):
	
	clips = {}
	
	def notify(self, ClipData):
		print("notification from {0}".format(ClipData.url))	
		self.clips[ClipData.url] = ClipData.status
		print(self.clips)
		sys.stdout.flush()

class Subscriber(Ice.Application):
	def get_topic_manager(self):
		key = "IceStorm.TopicManager.Proxy"
		proxy = self.communicator().propertyToProxy(key)
		if proxy is None:
			print("Fail")
			return None
		print("iceStorm")
		return IceStorm.TopicManagerPrx.checkedCast(proxy)

	def run(self, argv):
		topic_mgr = self.get_topic_manager()
		if not topic_mgr:
			print("Fail topic")
			return 2
		
		ic = self.communicator()
		servant = ProgressEventI()
		adapter = ic.createObjectAdapter("ProgressAdapter")
		subscriber = adapter.addWithUUID(servant)
		topic_name = "ProgressTopic"
		qos = {}
		try:
			topic = topic_mgr.retrieve(topic_name)
		except IceStorm.NoSuchTopic:
			topic = topic_mgr.create(topic_name)

		topic.subscribeAndGetPublisher(qos, subscriber)
		print("Esperando eventos")
		
		adapter.activate()
		self.shutdownOnInterrupt()
		ic.waitForShutdown()
		topic.unsubscribe(subscriber)
		return 0

sys.exit(Subscriber().main(sys.argv))
		
