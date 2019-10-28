import unittest
import random
import asyncio

from playground.network.testing import MockTransportToStorageStream as MockTransport
from playground.asyncio_lib.testing import TestLoopEx
from playground.common.logging import EnablePresetLogging, PRESET_DEBUG

from protocol import *

def pop_packets(storage, deserializer, rx, tx, reorder=False, error_rate=0):
    while storage:
        if reorder:
            next_packet = storage.pop(random.randint(0,len(storage)-1))
        else:
            next_packet = storage.pop(0)
        deserializer.update(next_packet)
    for packet in deserializer.nextPackets():
        if isinstance(packet, AckPacket):
            tx.ack(packet.ack)
        else:
            if error_rate > 0:
                if random.random() < ((error_rate/102400.0)*len(packet.data)):
                    # just drop the packet
                    print("Drop packet")
                    continue
            rx.recv(packet)
            
class ListWriter:
    def __init__(self, l):
        self.l = l
        
    def write(self, data):
        self.l.append(data)
        
class DummyApplication(asyncio.Protocol):
    def __init__(self):
        self._connection_made_called = 0
        self._connecton_lost_called = 0
        self._data = []
        self._transport = None
        
    def connection_made(self, transport):
        self._transport = transport
        self._connection_made_called += 1
        
    def connection_lost(self, reason=None):
        self._connection_lost_called += 1
        
    def data_received(self, data):
        self._data.append(data)
        
    def pop_all_data(self):
        data = b""
        while self._data:
            data += self._data.pop(0)
        return data
        
class TestPoopDataHandling(unittest.TestCase):
    def setUp(self):
        asyncio.set_event_loop(TestLoopEx())
        
        self.dummy_client = DummyApplication()
        self.dummy_server = DummyApplication()
        
        self.client_write_storage = []
        self.server_write_storage = []
        
        self.client_deserializer = PoopPacketType.Deserializer()
        self.server_deserializer = PoopPacketType.Deserializer()
        
        client_transport = MockTransport(ListWriter(self.client_write_storage))
        server_transport = MockTransport(ListWriter(self.server_write_storage))
        
        self.client_tx = PoopTx(client_transport, 1000)
        self.client_rx = PoopRx(self.dummy_client, client_transport, 9000)
        
        self.server_tx = PoopTx(server_transport, 9000)
        self.server_rx = PoopRx(self.dummy_server, server_transport, 1000)
        
    def test_simple_transmission(self):
        msg = b"this is a test"
    
        self.client_tx.send(msg)
        
        self.assertEqual(len(self.client_tx.tx_window), 1)
        
        pop_packets(self.client_write_storage, self.server_deserializer, self.server_rx, self.server_tx)
        # this sends back an ack packet
        pop_packets(self.server_write_storage, self.client_deserializer, self.client_rx, self.client_tx)
        
        self.assertEqual(len(self.client_tx.tx_window), 0)
        
        self.assertEqual(self.dummy_server.pop_all_data(), msg)
        
    def test_large_transmission(self):
        msg = (b"1"*2048)+(b"2"*2048)+(b"3"*2048)+(b"4"*100)
    
        self.client_tx.send(msg)
        
        while self.client_tx.tx_window:
            cur_seq = self.client_tx.tx_window[0].seq
            pop_packets(self.client_write_storage, self.server_deserializer, self.server_rx, self.server_tx, reorder=True, error_rate=3)
            # this sends back an ack packet
            pop_packets(self.server_write_storage, self.client_deserializer, self.client_rx, self.client_tx)
            self.client_tx.resend(cur_seq)
            
        self.assertEqual(len(self.client_tx.tx_window), 0)
        
        self.assertEqual(self.dummy_server.pop_all_data(), msg)
        

class TestPoopHandshake(unittest.TestCase):
    def setUp(self):
        self.client_poop = PoopClientProtocol()
        self.server_poop = PoopServerProtocol()
        
        self.client = DummyApplication()
        self.server = DummyApplication()
        
        self.client_poop.setHigherProtocol(self.client)
        self.server_poop.setHigherProtocol(self.server)
        
        self.client_write_storage = []
        self.server_write_storage = []
        
        self.client_transport = MockTransport(ListWriter(self.client_write_storage))
        self.server_transport = MockTransport(ListWriter(self.server_write_storage))
        
    def tearDown(self):
        pass

    def test_no_error_handshake(self):
        self.server_poop.connection_made(self.server_transport)
        self.client_poop.connection_made(self.client_transport)
        
        self.assertEqual(self.client._connection_made_called, 0)
        self.assertEqual(self.server._connection_made_called, 0)
        
        # there should only be 1 blob of bytes for the SYN
        self.assertEqual(len(self.client_write_storage), 1)
        self.server_poop.data_received(self.client_write_storage.pop())
        
        # server still should not be connected
        self.assertEqual(self.server._connection_made_called, 0)
        
        # there should be 1 blob of bytes from the server for the SYN ACK
        self.assertEqual(len(self.server_write_storage), 1)
        
        self.client_poop.data_received(self.server_write_storage.pop())
        
        # now client should be connected
        self.assertEqual(self.client._connection_made_called, 1)
        
        # there should be 1 blob of bytes for the SYN ACK ACK storage
        self.assertEqual(len(self.client_write_storage), 1)
        self.server_poop.data_received(self.client_write_storage.pop())
        
        # server should be connected
        self.assertEqual(self.server._connection_made_called, 1)
        
    
        
if __name__ == '__main__':
    EnablePresetLogging(PRESET_DEBUG)
    unittest.main()