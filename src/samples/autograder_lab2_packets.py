from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import UINT8, STRING, BUFFER, UINT16, BOOL
from playground.network.packet.fieldtypes.attributes import Optional

class AutogradeStartTest(PacketType):
    DEFINITION_IDENTIFIER = "20194.lab1.autogradesubmit"
    DEFINITION_VERSION = "1.0"
    
    TEST_TYPE_MILESTONE1 = "milestone1"
    TEST_TYPE_MILESTONE2 = "milestone2"
    TEST_TYPE_MILESTONE3 = "milestone3"
    
    FIELDS = [
        ("team", UINT8),
        ("port", UINT16),
        ("test_type", STRING)
        ]
        
class AutogradeTestStatus(PacketType):
    DEFINITION_IDENTIFIER = "20194.lab1.autogradesubmitresponse"
    DEFINITION_VERSION = "1.0"
    
    NOT_STARTED = 0
    PASSED      = 1
    FAILED      = 2
    
    FIELDS = [
        ("test_id", STRING),
        ("server_port", UINT16),
        ("submit_status", UINT8),
        ("client_status", UINT8),
        ("server_status", UINT8),
        ("error", STRING({Optional: True}))]
        
class AutogradeServerCommand(PacketType):
    DEFINITION_IDENTIFIER = "20194.lab1.autogradeservercommand"
    DEFINITION_VERSION = "1.0"
    
    FIELDS = [
        ("server_command", STRING)
        ]
        
class AutogradeClientCommand(PacketType):
    DEFINITION_IDENTIFIER = "20194.lab1.autogradeclientcommand"
    DEFINITION_VERSION = "1.0"
    
    FIELDS = [
        ("client_command", STRING)
        ]
        
class AutogradeCommandAck(PacketType):
    DEFINITION_IDENTIFIER = "20194.lab1.autogradecommandack"
    DEFINITION_VERSION = "1.0"
        
class AutogradeResultRequest(PacketType):
    DEFINITION_IDENTIFIER = "20194.lab1.autograderesult"
    DEFINITION_VERSION = "1.0"
    
    TEST_TYPE_MILESTONE1 = "milestone1"
    TEST_TYPE_MILESTONE2 = "milestone2"
    TEST_TYPE_MILESTONE3 = "milestone3"
    
    FIELDS = [
        ("test_id", STRING),
        ("test_type", STRING)
    ]
    
class AutogradeResultResponse(PacketType):
    DEFINITION_IDENTIFIER = "20194.exercise6.autograderesultresponse"
    DEFINITION_VERSION = "1.0"
    
    FIELDS = [
        ("test_id", STRING),
        ("passed", BOOL),
    ]
