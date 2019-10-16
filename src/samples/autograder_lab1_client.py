import os, asyncio, random
import playground

import autograder_lab1_packets as autograder_packets
from playground.network.packet import PacketType

class DummyProtocol(asyncio.Protocol):
    def __init__(self):
        self.state = "init"
        self.rx_storage = []
        self.connected = asyncio.get_event_loop().create_future()
        self.disconnected = asyncio.get_event_loop().create_future()
        self.rx = asyncio.Event()
        
    def connection_made(self, transport):
        self.connected.set_result(True)
        self.transport = transport
        self.state = "connection_made"
        
    def connection_lost(self, exc):
        self.disconnected.set_result(True)
        if not self.connected.done():
            self.connected.set_exception(Exception("Connection_made never called"))
        self.transport = None
        self.state = "connection_lost"
        
    def data_received(self, data):
        self.rx_storage.append(data)
        self.rx.set()


class Lab1TestProtocol_Server(asyncio.Protocol):
    ID = 0
    def __init__(self):
        self.deserializer = PacketType.Deserializer()
        
    def game_output(self, s):
        output_packet = game_packets.create_game_response(s, self.game.status)
        self.transport.write(output_packet.__serialize__())
        
    def connection_made(self, transport):
        self.transport = transport
        self.state = "await_login"
        
    def bad_payment(self):
        bad_pay_message = game_packets.create_game_response("", "dead")
        self.transport.write(bad_pay_message.__serialize__())
        self.transport.close()
        
    def data_received(self, data):
        try:
            self.data_received_impl(data)
        except Exception as e:
            print("tester server failed because", e)
            # not really. but hopefully closes the connection
            exception_message = game_packets.create_game_response("", "dead")
            self.transport.write(exception_message.__serialize__())
    
    def data_received_impl(self, data):
        self.deserializer.update(data)
        for packet in self.deserializer.nextPackets():
            if self.state == "await_login":
                username = game_packets.process_game_init(packet)
                self.unique_id = "ID_{}".format(Ex8Server.ID)
                Ex8Server.ID += 1
                response = game_packets.create_game_require_pay_packet(self.unique_id, "sample1", 5)
                self.state = "await_pay"
                self.transport.write(response.__serialize__())
            elif self.state == "await_pay":
                receipt, receipt_signature = game_packets.process_game_pay_packet(packet)
                if not bank_client.verify(receipt, receipt_signature):
                    print("server bad payment, bad signature")
                    return self.bad_payment()
                ledger_line = LedgerLineStorage.deserialize(receipt)
                if ledger_line.getTransactionAmount("sample1") != 5:
                    print("server bad payment, bad amount")
                    return self.bad_payment()
                elif ledger_line.memo("sample1") != self.unique_id:
                    print("server bad payment, bad memo")
                    return self.bad_payment()
                self.state = "play"
                self.game = EscapeRoomGame(output=self.game_output)
                self.game.create_game()
                self.game.start()
                for a in self.game.agents:
                    asyncio.ensure_future(a) 
            else:
                command = game_packets.process_game_command(packet)
                if not command: continue
                self.game.command(command)
                if not self.game.status == "playing":
                    self.transport.close()
                
class Lab1AutogradeClient(asyncio.Protocol):
    
    def __init__(self, server_addr, team_number, test_type, mode):
        self.test_type = test_type
        self.mode = mode
        self.server_addr = server_addr
        self.server_port = None
        self.deserializer = PacketType.Deserializer()
        self.my_server_port = random.randint(50000,60000)
        self.server_test_protocol = None
        self.server = None
        self.test_id = None
        self.team_number = team_number
        
    def connection_made(self, transport):
        if self.mode != "submit":
            transport.write(
                autograder_packets.AutogradeResultRequest(
                    test_type=self.test_type,
                    test_id=self.mode).__serialize__())
            self.state = "request_start"
        else:
            transport.write(
                autograder_packets.AutogradeStartTest(
                    team=team_number,
                    test_type=self.test_type,
                    port=self.my_server_port).__serialize__())
            self.state = "test_start"
            
        self.transport = transport
        

    def data_received(self, data):
        try:
            self.data_received_impl(data)
        except Exception as e:
            print("failed autograde because",e)
            self.close_client()
        
    def data_received_impl(self, data):
        print("Got {} bytes of data".format(len(data)))
        self.deserializer.update(data)
        for packet in self.deserializer.nextPackets():
            if isinstance(packet, autograder_packets.AutogradeTestStatus):
                if packet.FAILED in [packet.submit_status, packet.client_status, packet.server_status]:
                    print("Lab1 Autograde test failed because server says", packet.error)
                    self.transport.close()
                    return
                elif self.state == "test_start" and packet.submit_status == packet.NOT_STARTED:
                    print("Lab1 submission process didn't start for some reason.")
                    self.transport.close()
                    return
                elif self.state == "client_test" and packet.client_status == packet.NOT_STARTED:
                    print("Lab1 client test process didn't start for some reason.")
                    self.transport.close()
                    return
                elif self.state == "server_test" and packet.server_status == packet.NOT_STARTED:
                    print("Lab1 server test process didn't start for some reason.")
                    self.transport.close()
                    return

            if self.state == "test_start" and packet.submit_status == packet.PASSED:
                self.server_port = packet.server_port
                self.state = "client_test"
                self.test_id = packet.test_id
                
            elif self.state == "client_test":
                if isinstance(packet, autograder_packets.AutogradeClientCommand):
                    f = asyncio.ensure_future(self.do_client_test(packet.client_command))
                    f.add_done_callback(self.test_complete)
                elif isinstance(packet, autograder_packets.AutogradeTestStatus) and packet.client_status == packet.PASSED:
                    print("Switch to server state")
                    self.state = "server_test"
                else:
                    raise Exception("Unexpected packet for client test. {}".format(packet))
                    
            elif self.state == "server_test":
                if isinstance(packet, autograder_packets.AutogradeServerCommand):
                    print("Server command",packet.server_command)
                    f = asyncio.ensure_future(self.do_server_test(packet.server_command))
                    f.add_done_callback(self.test_complete)
                elif isinstance(packet, autograder_packets.AutogradeTestStatus) and packet.server_status == packet.PASSED:
                    self.state = "done"
                    print("all tests passed for test_id {}".format(self.test_id))
                    asyncio.get_event_loop().stop()
                else:
                    raise Exception("Unexpected packet for client test. {}".format(packet))
                    
            elif self.state == "request_start":
                if packet.passed:
                    print("Test Passed")
                else:
                    print("Test Failed")
                self.close_client()
            else:
                print("unknown state", self.state)
                self.close_client()
                
    def test_complete(self, future):
        if future.exception():
            print("Test failed: {}".format(future.exception()))
            if not self.transport.is_closing():
                self.transport.close()
                
    async def do_client_test(self, client_command):
        print("client test got command {}".format(client_command))
        self.transport.write(autograder_packets.AutogradeCommandAck().__serialize__())
        print("Wrote ack")
        try:
            transport, protocol = await playground.create_connection(
                DummyProtocol,
                host="poop://{}".format(self.server_addr), 
                port=self.server_port)
        except Exception as e:
            raise Exception("Could not connect to server to execute command")
        if client_command == "connect":
            # just disconnect now
            if not transport.is_closing():
                transport.close()
                
    async def do_server_test(self, server_command):
        if self.server == None:
            print("No server. Start poop server")
            try:
                self.server = await playground.create_server(
                    lambda: self.server_test_protocol,
                    port=self.my_server_port,
                    family="poop")
            except Exception as e:
                raise Exception("Could not create server to execute command")
        if server_command == "accept":
            self.server_test_protocol = DummyProtocol()
            self.transport.write(autograder_packets.AutogradeCommandAck().__serialize__())
            await self.server_test_protocol.connected
            if self.server_test_protocol.transport and not self.server_test_protocol.transport.is_closing():
                self.server_test_protocol.transport.close()
                
            
                
    def close_client(self):
        self.transport.close()
        asyncio.get_event_loop().stop()
                
if __name__ == "__main__":
    import sys
    from playground.common.logging import EnablePresetLogging, PRESET_VERBOSE
    EnablePresetLogging(PRESET_VERBOSE)
    
    server_addr, team_number, test_type, mode = sys.argv[1:]
        
    
    loop = asyncio.get_event_loop()
    coro = playground.create_connection(lambda: Lab1AutogradeClient(server_addr, team_number, test_type, mode), host=server_addr, port=19101)
    
    transport, protocol = loop.run_until_complete(coro)
    print("Connected on", transport.get_extra_info("peername"))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    loop.close()

