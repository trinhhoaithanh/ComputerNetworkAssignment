from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT
	
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3
	
	# Initiation..
	def __init__(self, master, serveraddr, serverport, rtpport, filename):
		self.master = master
		self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.createWidgets()
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.rtpPort = int(rtpport)
		self.fileName = filename
		self.rtspSeq = 0
		self.sessionId = 0
		self.requestSent = -1
		self.teardownAcked = 0
		self.connectToServer()
		self.frameNbr = 0
		
	# THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI 	
	def createWidgets(self):
		"""Build GUI."""
		# Create Setup button
		self.setup = Button(self.master, width=20, padx=3, pady=3)
		self.setup["text"] = "Setup"
		self.setup["command"] = self.setupMovie
		self.setup.grid(row=1, column=0, padx=2, pady=2)
		
		# Create Play button		
		self.start = Button(self.master, width=20, padx=3, pady=3)
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=1, column=1, padx=2, pady=2)
		
		# Create Pause button			
		self.pause = Button(self.master, width=20, padx=3, pady=3)
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=1, column=2, padx=2, pady=2)
		
		# Create Teardown button
		self.teardown = Button(self.master, width=20, padx=3, pady=3)
		self.teardown["text"] = "Teardown"
		self.teardown["command"] =  self.exitClient
		self.teardown.grid(row=1, column=3, padx=2, pady=2)
		
		# Create a label to display the movie
		self.label = Label(self.master, height=19)
		self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5) 
	
	def setupMovie(self):
		"""Setup button handler."""
		print(123)
	#TODO
	
	def exitClient(self):
		"""Teardown button handler."""
	#TODO

	def pauseMovie(self):
		"""Pause button handler."""
	#TODO
	
	def playMovie(self):
		"""Play button handler."""
	#TODO
	
	def listenRtp(self):		
		"""Listen for RTP packets."""
		#TODO
					
	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
		image_file = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
		file = open(image_file,"wb")
		file.write(data)
		file.close()
		return image_file
	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
		image = Image.open(imageFile)
		photo = ImageTk.PhotoImage(image)
		self.label.configure(image=photo,height=288)
		self.label.image = photo	
	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
		self.rtspSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		try:
			self.rtspSocket.connect((self.serverAddr,self.serverPort))
		except:
			print('Server connection failed')
	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""	
		# Setup request
		if requestCode == self.SETUP and self.state == self.INIT:
			threading.Thread(target=self.recvRtspReply).start()

			#Update RTSP sequence number
			self.rtspSeq+=1

			# Write the RTSP request to be sent 
			request = 'SETUP ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nTransport: RTP/UDP; client_port= ' + str(self.rtpPort)

			# Keep track of the sent request
			self.requestSent = self.SETUP

		# Play request
		elif requestCode == self.PLAY and self.state == self.READY:

			#Update RTSP sequence number
			self.rtspSeq+=1

			# Write the RTSP request to be sent
			request = 'PLAY ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)	
			
			# Keep track of the sent request.
			self.requestSent = self.PLAY
		# Pause request
		elif requestCode == self.PAUSE and self.state == self.PLAYING:
			# Update RTSP sequence number
			self.rtspSeq+=1

			# Write the RTSP request to be sent
			request = 'PAUSE ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)

			# Keep track of the sent request
			self.requestSent = self.PAUSE
		elif requestCode == self.TEARDOWN and self.state == self.INIT:
			# Update RTSP sequence number.
			self.rtspSeq+=1

			# Write the RTSP request to be sent
			request = 'TEARDOWN ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			
			# Keep track of the sent request
			self.requestSent = self.TEARDOWN
		else:
			return
		# Send the RTSP request using rtspSocket
		self.rtspSocket.send(request.encode())
		print(request)
	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		while True: 
			reply = self.rtspSocket.recv(1024)
			if reply:
				self.parseRtspReply(reply)
			
			# Close the RTSP socket upon requesting Teardown
			if self.requestSent == self.TEARDOWN:
				self.rtspSocket.shutdown(socket.SHUT_RDWR)
				self.rtspSocket.close()
				break
	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		#TODO
	
	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		#-------------
		# TO COMPLETE
		#-------------
		# Create a new datagram socket to receive RTP packets from the server
		# self.rtpSocket = ...
		
		# Set the timeout value of the socket to 0.5sec
		# ...
		

	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		#TODO
