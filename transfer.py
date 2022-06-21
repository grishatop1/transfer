import socket
import threading
import queue
import pickle

class Transfer:
	"""Transfer object for transfering data with multiple threads"""
	def __init__(self, sock):
		self.s = sock
		self.pending = queue.Queue()
		self.header = 12
		self.buffer = 1024 * 2
		self.total = 0
		threading.Thread(target=self._dataLoop, daemon=True).start()

	def _appendHeader(self, data):
		data_len = len(data)
		header = str(data_len).encode() + (self.header - len(str(data_len))) * b" "
		return header + data

	def _dataLoop(self):
		while True:
			lock, data = self.pending.get()
			try:
				self.s.send(data)
				if lock:
					lock.put(True)
			except socket.error:
				return

	def send(self, data):
		"""Send data to the socket"""
		h_data = self._appendHeader(data)
		self.pending.put(h_data)

	def sendPickle(self, obj):
		data = pickle.dumps(obj)
		self.send(data)

	def sendNow(self, data):
		"""Sends data not putting it in the queue"""
		try:
			h_data = self._appendHeader(data)
			self.s.send(h_data)
		except socket.error:
			return

	def recv(self):
		"""Returns full data from socket.send
		Use it just in one thread"""
		full = b""
		recv_len = 0
		recv_size = self.header
		header = b""
		new = True
		while True:
			if recv_size == 0:
				break
			try:
				data = self.s.recv(recv_size)
			except socket.error:
				return
			if not data:
				return

			if new:
				header += data
				if len(header) < self.header:
					recv_size = self.header - len(header)
					continue
				try:					
					actual_len = int(header)
				except:
					return
				recv_size = min(actual_len, self.buffer)
				new = False
				continue

			full += data
			recv_len += len(data)
			recv_size = min(actual_len - recv_len, self.buffer)

			self.total = int((recv_len/actual_len)*100)

		self.total = 100
		return full