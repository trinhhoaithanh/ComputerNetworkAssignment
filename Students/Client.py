from tkinter import *
import tkinter.messagebox
from tkinter import messagebox 
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
		if self.state == self.INIT:
			self.sendRtspRequest(self.SETUP)
	#TODO
	
	def exitClient(self):
		"""Teardown button handler."""
		if self.state == self.READY or self.state == self.PLAYING:
			self.sendRtspRequest(self.TEARDOWN)
	#TODO

	def pauseMovie(self):
		"""Pause button handler."""
		if self.state == self.PLAYING:
			self.sendRtspRequest(self.PAUSE)
	#TODO
	
	def playMovie(self):
		"""Play button handler."""
		if self.state == self.READY:
			self.sendRtspRequest(self.PLAY)
	#TODO
	
	def listenRtp(self):		
		"""Listen for RTP packets."""
		while True:
			try:
				data = self.rtpSocket.recv(20480)
				if data:
					rtpPacket = RtpPacket()
					rtpPacket.decode(data)
					frameNum = rtpPacket.seqNum()
					print ("Current frame number: " + str(frameNum))
					# Check for duplicating packet
					if frameNum > self.frameNbr: 
						self.frameNbr = frameNum
						self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
			except:
			# Stop listening in case requesting PAUSE or TEARDOWN
				# Requesting PAUSE
				if not self.run.is_set():
					break
				
				# ACK's value update as TEARDOWN request,
				# Close the RTP socket
				if self.teardownAcked == 1:
					self.rtpSocket.shutdown(socket.SHUT_RDWR)
					self.rtpSocket.close()
					break 
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
		self.label.configure(image = photo, height = 288)
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
		if requestCode == self.SETUP:
			# Create a new thread to receive RTSP reply from Server
			threading.Thread(target=self.recvRtspReply).start()

			# Update RTSP sequence number
			self.rtspSeq+=1

			# Write the RTSP request to be sent 
			request = 'SETUP ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nTransport: RTP/UDP; client_port= ' + str(self.rtpPort)

			# Keep track of the sent request
			self.requestSent = self.SETUP
   
		# Play request
		elif requestCode == self.PLAY:
			# Create a new thread to listen to RTP packet 
			threading.Thread(target=self.listenRtp).start()
   
			# Declare an playEvent as a flag for above thread
			self.run = threading.Event()
   
			# Set state of run (True)
			self.run.set()
   
			# Update RTSP sequence number
			self.rtspSeq+=1

			# Write the RTSP request to be sent
			request = 'PLAY ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)	
			
			# Keep track of the sent request.
			self.requestSent = self.PLAY
		
  		# Pause request
		elif requestCode == self.PAUSE:
			# Update RTSP sequence number
			self.rtspSeq+=1

			# Write the RTSP request to be sent
			request = 'PAUSE ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)

			# Keep track of the sent request
			self.requestSent = self.PAUSE
   
		# Teardown request
		elif requestCode == self.TEARDOWN:
			# Close GUI window
			self.master.destroy()
   
			# Delete the cache image from video
			os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)
   
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
		print('Data sent:\n')
		print(request, '\n')
	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		while True: 
			reply = self.rtspSocket.recv(1024)
			if reply:
				self.parseRtspReply(reply)
			
			# Close the RTSP socket when requesting Teardown
			if self.requestSent == self.TEARDOWN:
				self.rtspSocket.shutdown(socket.SHUT_RDWR)
				self.rtspSocket.close()
				break
	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		lines = data.decode().split('\n')
		seqNum = int(lines[1].split(' ')[1])
		
		# Process only if the server reply's sequence number is the same as the request's
		if seqNum == self.rtspSeq:
			session = int(lines[2].split(' ')[1])
			# New RTSP session ID
			if self.sessionId == 0:
				self.sessionId = session
			
			# Process only if the session ID is the same
			if self.sessionId == session:
				if int(lines[0].split(' ')[1]) == 200: 
					if self.requestSent == self.SETUP:
						# Update RTSP state.
						self.state = self.READY
						
						# Open RTP port.
						self.openRtpPort() 
					elif self.requestSent == self.PLAY:
						self.state = self.PLAYING
					elif self.requestSent == self.PAUSE:
						self.state = self.READY
                        
						# The thread that listening to RTP packet end and is terminated
						self.run.clear()
					elif self.requestSent == self.TEARDOWN:
						self.state = self.INIT
						
						# Flag the teardownAcked to close the socket.
						self.teardownAcked = 1 
		#TODO
	
	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		#-------------
		# TO COMPLETE
		#-------------
		# Create a new datagram socket to receive RTP packets from the server
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		# Set the timeout value of the socket to 0.5sec
		self.rtpSocket.settimeout(0.5)
		try:
			# Bind the RTP socket to the address using the RTP port given by the client user.
			self.state=self.READY
			self.rtpSocket.bind(('',self.rtpPort))
		except:
			messagebox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' %self.rtpPort)
		

	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		self.pauseMovie()
		if messagebox.askokcancel("Quit?", "Are you sure you want to quit?"):
			self.exitClient()
		else: # When the user presses cancel, resume playing.
			self.playMovie()
		#TODO
