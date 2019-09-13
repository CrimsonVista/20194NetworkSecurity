import asyncio

class EchoServer(asyncio.Protocol):
	def __init__(self):
		pass

	def connection_made(self, transport):
		self.transport = transport

	def data_received(self, data):
		print(data)
		self.transport.write(data)

if __name__ == "__main__":
	loop = asyncio.get_event_loop()
	coro = loop.create_server(EchoServer,'',8080)
	server = loop.run_until_complete(coro)

	try:
		loop.run_forever()
	except KeyboardInterrupt:
		pass

	server.close()
	loop.run_until_complete(server.wait_close())
	loop.close()
