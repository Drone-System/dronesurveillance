from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PollRequest(_message.Message):
    __slots__ = ("stream_id",)
    STREAM_ID_FIELD_NUMBER: _ClassVar[int]
    stream_id: str
    def __init__(self, stream_id: _Optional[str] = ...) -> None: ...

class PollResponse(_message.Message):
    __slots__ = ("stream_needed",)
    STREAM_NEEDED_FIELD_NUMBER: _ClassVar[int]
    stream_needed: bool
    def __init__(self, stream_needed: bool = ...) -> None: ...

class StreamRequest(_message.Message):
    __slots__ = ("drone_id",)
    DRONE_ID_FIELD_NUMBER: _ClassVar[int]
    drone_id: str
    def __init__(self, drone_id: _Optional[str] = ...) -> None: ...

class ConnectToCloudRequest(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class ConnectToCloudResponse(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class RegisterProducerRequest(_message.Message):
    __slots__ = ("sid", "name")
    SID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    sid: str
    name: str
    def __init__(self, sid: _Optional[str] = ..., name: _Optional[str] = ...) -> None: ...

class RegisterProducerResponse(_message.Message):
    __slots__ = ("stream_id", "viewer_sid")
    STREAM_ID_FIELD_NUMBER: _ClassVar[int]
    VIEWER_SID_FIELD_NUMBER: _ClassVar[int]
    stream_id: str
    viewer_sid: str
    def __init__(self, stream_id: _Optional[str] = ..., viewer_sid: _Optional[str] = ...) -> None: ...

class IceCandidateRequest(_message.Message):
    __slots__ = ("candidate", "sdpMid", "sdp_MLinIndex")
    CANDIDATE_FIELD_NUMBER: _ClassVar[int]
    SDPMID_FIELD_NUMBER: _ClassVar[int]
    SDP_MLININDEX_FIELD_NUMBER: _ClassVar[int]
    candidate: str
    sdpMid: str
    sdp_MLinIndex: int
    def __init__(self, candidate: _Optional[str] = ..., sdpMid: _Optional[str] = ..., sdp_MLinIndex: _Optional[int] = ...) -> None: ...

class IceCandidateResponse(_message.Message):
    __slots__ = ("candidate", "sdpMid", "sdp_MLinIndex")
    CANDIDATE_FIELD_NUMBER: _ClassVar[int]
    SDPMID_FIELD_NUMBER: _ClassVar[int]
    SDP_MLININDEX_FIELD_NUMBER: _ClassVar[int]
    candidate: str
    sdpMid: str
    sdp_MLinIndex: int
    def __init__(self, candidate: _Optional[str] = ..., sdpMid: _Optional[str] = ..., sdp_MLinIndex: _Optional[int] = ...) -> None: ...

class StreamDesc(_message.Message):
    __slots__ = ("type", "sdp")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    SDP_FIELD_NUMBER: _ClassVar[int]
    type: str
    sdp: str
    def __init__(self, type: _Optional[str] = ..., sdp: _Optional[str] = ...) -> None: ...

class StreamOffer(_message.Message):
    __slots__ = ("stream_id", "offer")
    STREAM_ID_FIELD_NUMBER: _ClassVar[int]
    OFFER_FIELD_NUMBER: _ClassVar[int]
    stream_id: str
    offer: StreamDesc
    def __init__(self, stream_id: _Optional[str] = ..., offer: _Optional[_Union[StreamDesc, _Mapping]] = ...) -> None: ...

class StreamAnswer(_message.Message):
    __slots__ = ("stream_id", "answer")
    STREAM_ID_FIELD_NUMBER: _ClassVar[int]
    ANSWER_FIELD_NUMBER: _ClassVar[int]
    stream_id: str
    answer: StreamDesc
    def __init__(self, stream_id: _Optional[str] = ..., answer: _Optional[_Union[StreamDesc, _Mapping]] = ...) -> None: ...

class ConnectRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ConnectResponse(_message.Message):
    __slots__ = ("stream_id",)
    STREAM_ID_FIELD_NUMBER: _ClassVar[int]
    stream_id: str
    def __init__(self, stream_id: _Optional[str] = ...) -> None: ...

class DisconnectRequest(_message.Message):
    __slots__ = ("stream_id",)
    STREAM_ID_FIELD_NUMBER: _ClassVar[int]
    stream_id: str
    def __init__(self, stream_id: _Optional[str] = ...) -> None: ...

class DisconnectResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
