from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import UINT8, STRING, BUFFER, UINT16, BOOL
from playground.network.packet.fieldtypes.attributes import Optional

class AutogradeStartTest(PacketType):
    DEFINITION_IDENTIFIER = "20194.exercise6.autogradesubmit"
    DEFINITION_VERSION = "1.0"
    
    FIELDS = [
        ("name", STRING),
        ("team", UINT8),
        ("email", STRING),
        ("port", UINT16)
        ]
        
class AutogradeTestStatus(PacketType):
    DEFINITION_IDENTIFIER = "20194.exercise6.autogradesubmitresponse"
    DEFINITION_VERSION = "1.0"
    
    NOT_STARTED = 0
    PASSED      = 1
    FAILED      = 2
    
    FIELDS = [
        ("test_id", STRING),
        ("submit_status", UINT8),
        ("client_status", UINT8),
        ("server_status", UINT8),
        ("error", STRING({Optional: True}))]
        
class AutogradeResultRequest(PacketType):
    DEFINITION_IDENTIFIER = "20194.exercise6.autograderesult"
    DEFINITION_VERSION = "1.0"
    
    FIELDS = [
        ("test_id", STRING)
    ]
    
class AutogradeResultResponse(PacketType):
    DEFINITION_IDENTIFIER = "20194.exercise6.autograderesultresponse"
    DEFINITION_VERSION = "1.0"
    
    FIELDS = [
        ("test_id", STRING),
        ("passed", BOOL),
    ]
