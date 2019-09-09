import asyncio

class EchoClient(asyncio.Protocol):
	def __init__(self):
		pass

	def connection_made(self, transport):
		self.transport = transport
		self.transport.write("Hello World".encode())

	def data_received(self, data):
		print(data.decode())

if __name__ == "__main__":
	loop = asyncio.get_event_loop()
	coro = loop.create_connection(EchoClient,'127.0.0.1',8080)
	client = loop.run_until_complete(coro)

	try:
		loop.run_forever()
	except KeyboardInterrupt:
		pass

	client.close()
	loop.run_until_complete(client.close())
	loop.close()
