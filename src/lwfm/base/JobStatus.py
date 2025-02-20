
# Job Status: a record of a state of the job's execution.  The job may go through many states in its lifetime - on the actual
# runtime Site the job status will be expressed in terms of their native status codes.  In lwfm, we desire canonical status
# messages so job chaining is permitted.  Its the role of the Site's Run subsystem to produce these datagrams in their
# canonical form, though we leave room to express the native info too.  There is no firm state transition / state machine for
# job status - while "PENDING" means "submitted to run but not yet running", and "COMPLETE" means "job is done done stick a fork
# in it", in truth the Site is free to emit whateever status code it desires at any moment.  Some status codes might be emitted
# more than once (e.g. "INFO").  We provide a mechanism to track the job's parent-child relationships.


from enum import Enum
import logging
from types import SimpleNamespace

import os


from datetime import datetime
import pickle
import json

from lwfm.base.LwfmBase import LwfmBase, _IdGenerator
from lwfm.base.JobDefn import RepoOp
from lwfm.server.JobStatusSentinelClient import JobStatusSentinelClient


class _JobStatusFields(Enum):
    STATUS        = "status"                         # canonical status
    NATIVE_STATUS = "nativeStatus"                   # the status code for the specific Run implementation
    EMIT_TIME     = "emitTime"
    RECEIVED_TIME = "receivedTime"
    ID            = "id"                             # canonical job id
    NATIVE_ID     = "nativeId"                       # Run implementation native job id
    NAME          = "name"                           # optional human-readable job name
    PARENT_JOB_ID = "parentJobId"                    # immediate predecessor of this job, if any - seminal job has no parent
    ORIGIN_JOB_ID = "originJobId"                    # oldest ancestor - a seminal job is its own originator
    SET_ID        = "setId"                          # optional id of a set if the job is part of a set
    NATIVE_INFO   = "nativeInfo"                     # any additional info the native Run wants to put in the status message
    SITE_NAME     = "siteName"                       # name of the Site which emitted the message
    COMPUTE_TYPE  = "computeType"                    # a named resource on the Site, if any
    GROUP         = "group"                          # a group id that the job belongs to, if any
    USER          = "user"                         # a user id of the user that submitted the job, if any


# The canonical set of status codes.  Run implementations will have their own sets, and they must provide a mapping into these.
class JobStatusValues(Enum):
    UNKNOWN   = "UNKNOWN"
    PENDING   = "PENDING"
    RUNNING   = "RUNNING"
    INFO      = "INFO"
    FINISHING = "FINISHING"
    COMPLETE  = "COMPLETE"           # terminal state
    FAILED    = "FAILED"             # terminal state
    CANCELLED = "CANCELLED"          # terminal state

    def isTerminal(self, stat):
        try:
            if (stat == self.COMPLETE) or (stat == self.FAILED) or (stat == self.CANCELLED):
                return True
            else:
                return False
        except:
            logging.error("Exception thrown determining status value for stat=" + str(stat))
            return False

    def isTerminalSuccess(self, stat):
        if (self.isTerminal(stat) and (stat == self.COMPLETE)):
            return True
        else:
            return False

    def isTerminalFailure(self, stat):
        if (self.isTerminal(stat) and (stat == self.FAILED)):
            return True
        else:
            return False

    def isTerminalCancelled(self, stat):
        if (self.isTerminal(stat) and (stat == self.CANCELLED)):
            return True
        else:
            return False


#************************************************************************************************************************************

class JobContext(LwfmBase):
    """
    The runtime execution context of the job.  It contains the id of the job and references to its parent jobs, if any.
    A Job Status can reference a Job Context, and then augument it with updated job status information.

    Attributes:

    id - the lwfm id of the executing job.  This is distinct from the "native job id" below, which is the id of the job on the
        specific Site.  If the Site is "lwfm local", then one might expect that the id and the native id are the same, else one
        should assume they are not.  lwfm ids are generated as uuids.  Sites can use whatever mechanism they prefer.

    native id - the Site-generated job id

    parent job id - a lwfm generated id, the immediate parent of this job, if any; a seminal job has no parent

    origin job id - the elest parent in the job chain; a seminal job is its own originator

    name - the job can have an optional name for human consumption, else the name is the lwfm job id

    site name - the job is running (or has been submitted to the Site for queuing), therefore the Site name is known

    compute type - if the Site distinguishes compute types, it can be noted here

    """

    def __init__(self, parentContext = None):
        super(JobContext, self).__init__(None)
        self.setId(_IdGenerator.generateId())
        self.setNativeId(self.getId())
        if (parentContext is not None):
            self.setParentJobId(parentContext.getParentJobId())
            self.setOriginJobId(parentContext.getOriginJobId())
        else:
            self.setParentJobId("")                     # a seminal job has no parent
            self.setOriginJobId(self.getId())           # a seminal job is its own originator
        self.setName(self.getId())
        self.setComputeType("")
        self.setSiteName("")

    def setId(self, idValue: str) -> None:
        LwfmBase._setArg(self, _JobStatusFields.ID.value, idValue)

    def getId(self) -> str:
        return LwfmBase._getArg(self, _JobStatusFields.ID.value)

    def setNativeId(self, idValue: str) -> None:
            LwfmBase._setArg(self, _JobStatusFields.NATIVE_ID.value, idValue)

    def getNativeId(self) -> str:
        return LwfmBase._getArg(self, _JobStatusFields.NATIVE_ID.value)

    def setParentJobId(self, idValue: str) -> None:
        LwfmBase._setArg(self, _JobStatusFields.PARENT_JOB_ID.value, idValue)

    def getParentJobId(self) -> str:
        return LwfmBase._getArg(self, _JobStatusFields.PARENT_JOB_ID.value)

    def setOriginJobId(self, idValue: str) -> None:
        LwfmBase._setArg(self, _JobStatusFields.ORIGIN_JOB_ID.value, idValue)

    def getOriginJobId(self) -> str:
        return LwfmBase._getArg(self, _JobStatusFields.ORIGIN_JOB_ID.value)

    def setJobSetId(self, idValue: str) -> None:
        LwfmBase._setArg(self, _JobStatusFields.SET_ID.value, idValue)

    def getJobSetId(self) -> str:
        return LwfmBase._getArg(self, _JobStatusFields.SET_ID.value)    

    # job name
    def setName(self, name: str) -> None:
        LwfmBase._setArg(self, _JobStatusFields.NAME.value, name)

    # job name
    def getName(self) -> str:
        return LwfmBase._getArg(self, _JobStatusFields.NAME.value)

    def setSiteName(self, name: str) -> None:
        LwfmBase._setArg(self, _JobStatusFields.SITE_NAME.value, name)

    def getSiteName(self) -> str:
        return LwfmBase._getArg(self, _JobStatusFields.SITE_NAME.value)

    def setComputeType(self, name: str) -> None:
        LwfmBase._setArg(self, _JobStatusFields.COMPUTE_TYPE.value, name)

    def getComputeType(self) -> str:
        return LwfmBase._getArg(self, _JobStatusFields.COMPUTE_TYPE.value)

    def setGroup(self, name: str) -> None:
        LwfmBase._setArg(self, _JobStatusFields.GROUP.value, name)

    def getGroup(self) -> str:
        return LwfmBase._getArg(self, _JobStatusFields.GROUP.value)

    def setUser(self, name: str) -> None:
        LwfmBase._setArg(self, _JobStatusFields.USER.value, name)

    def getUser(self) -> str:
        return LwfmBase._getArg(self, _JobStatusFields.USER.value)

    def toJSON(self):
        return self.serialize()

    def serialize(self):
        out_bytes = pickle.dumps(self, 0)
        out_str = out_bytes.decode(encoding='ascii')
        return out_str

    @staticmethod
    def deserialize(s: str):
        in_json = json.dumps(s)
        in_obj = pickle.loads(json.loads(in_json).encode(encoding='ascii'))
        return in_obj


#************************************************************************************************************************************


class JobStatus(LwfmBase):
    """
    Over the lifetime of the running job, it may emit many status messages.  (Or, more specifically, lwfm might poll the remote
    Site for an updated status of a job it is tracking.)

    The Job Status references the Job Context of the running job, which contains the id of the job and other originating information.

    The Job Status is then augmented with the updated status info.  Like job ids, which come in canonical lwfm and Site-specific
    forms (and we track both), so do job status strings - there's the native job status, and the mapped canonical status.

    Attributes:

    job context - the Job Context for the job, which includes the job id

    status - the current canonical status string

    native status - the current native status string

    emit time - the timestamp when the Site emitted the status - the Site driver will need to populate this value

    received time - the timestamp when lwfm received the Job Status from the Site; this can be used to study latency in
        status receipt (which is by polling)

    native info - the Site may inject Site-specific status information into the Job Status message

    status map - a constant, the mapping of Site-native status strings to canonical status strings; native lwfm local jobs will use
        the literal mapping, and Site drivers will implement Job Status subclasses which provide their own Site-to-canonical
        mapping.

    """

    statusMap:          dict = None                             # maps native status to canonical status
    #statusHistory:      dict = None                             # history of status messages, not copied by copy constructor
    jobContext:         JobContext = None                       # job id tracking info

    def __init__(self, jobContext: JobContext):
        super(JobStatus, self).__init__(None)
        if (jobContext is None):
            self.jobContext = JobContext()
        else:
            self.jobContext = jobContext
        # default map
        self.setStatusMap( {
            "UNKNOWN"   : JobStatusValues.UNKNOWN,
            "PENDING"   : JobStatusValues.PENDING,
            "RUNNING"   : JobStatusValues.RUNNING,
            "INFO"      : JobStatusValues.INFO,
            "FINISHING" : JobStatusValues.FINISHING,
            "COMPLETE"  : JobStatusValues.COMPLETE,
            "FAILED"    : JobStatusValues.FAILED,
            "CANCELLED" : JobStatusValues.CANCELLED
        })
        self.setReceivedTime(datetime.utcnow())
        self.setStatus(JobStatusValues.UNKNOWN)


    def getJobContext(self) -> JobContext:
        return self.jobContext

    def setJobContext(self, jobContext: JobContext) -> None:
        self.jobContext = jobContext

    def setStatus(self, status: JobStatusValues) -> None:
        LwfmBase._setArg(self, _JobStatusFields.STATUS.value, status)

    def getStatus(self) -> JobStatusValues:
        return LwfmBase._getArg(self, _JobStatusFields.STATUS.value)

    def isTerminal(self) -> bool:
        return ( (self.getStatus() == JobStatusValues.COMPLETE) or
                 (self.getStatus() == JobStatusValues.FAILED)   or
                 (self.getStatus() == JobStatusValues.CANCELLED) )

    def getStatusValue(self) -> str:
        return LwfmBase._getArg(self, _JobStatusFields.STATUS.value).value

    def setNativeStatusStr(self, status: str) -> None:
        LwfmBase._setArg(self, _JobStatusFields.NATIVE_STATUS.value, status)
        self.mapNativeStatus()

    def getNativeStatusStr(self) -> str:
        return LwfmBase._getArg(self, _JobStatusFields.NATIVE_STATUS.value)

    def mapNativeStatus(self) -> None:
        try:
            self.setStatus(self.statusMap[self.getNativeStatusStr()])
        except Exception as ex:
            logging.error("Unable to map the native status to canonical: {}".format(ex))
            self.setStatus(JobStatusValues.UNKNOWN)

    def getStatusMap(self) -> dict:
        return self.statusMap

    def setStatusMap(self, statusMap: dict) -> None:
        self.statusMap = statusMap

    def setEmitTime(self, emitTime: datetime) -> None:
        LwfmBase._setArg(self, _JobStatusFields.EMIT_TIME.value, emitTime.timestamp() * 1000)

    def getEmitTime(self) -> datetime:
        try:
            ms = int(LwfmBase._getArg(self, _JobStatusFields.EMIT_TIME.value))
            return datetime.utcfromtimestamp(ms//1000).replace(microsecond=ms%1000*1000)
        except:
            # TODO
            return datetime.now()

    def setReceivedTime(self, receivedTime: datetime) -> None:
        LwfmBase._setArg(self, _JobStatusFields.RECEIVED_TIME.value, receivedTime.timestamp() * 1000)

    def getReceivedTime(self) -> datetime:
        ms = int(LwfmBase._getArg(self, _JobStatusFields.RECEIVED_TIME.value))
        return datetime.utcfromtimestamp(ms//1000).replace(microsecond=ms%1000*1000)

    def setNativeInfo(self, info: str) -> None:
        LwfmBase._setArg(self, _JobStatusFields.NATIVE_INFO.value, info)

    def getNativeInfo(self) -> str:
        return LwfmBase._getArg(self, _JobStatusFields.NATIVE_INFO.value)

#    def setStatusHistory(self, history: dict) -> None:
#        self._statusHistory = history
#
#    def getStatusHistory(self) -> dict:
#        return self._statusHistory

    def serialize(self):
        return pickle.dumps(self, 0)


    # zero out state-sensative fields
    def clear(self):
        zeroTime = 0 if os.name != 'nt' else 24*60*60 # Windows requires an extra day or we get an OS error
        self.setReceivedTime(datetime.fromtimestamp(zeroTime))
        self.setEmitTime(datetime.fromtimestamp(zeroTime))
        self.setNativeInfo("")


    # Send the status message to the lwfm service.
    def emit(self, status: str = None) -> bool:
        if status:
            self.setNativeStatusStr(status)
        self.setEmitTime(datetime.utcnow())
        try:
            jssc = JobStatusSentinelClient()
            jssc.emitStatus(self.getJobContext().getId(), self.getStatus().value, self.serialize())
            self.clear()
            return True
        except Exception as ex:
            logging.error(str(ex))
            return False

    def isTerminal(self) -> bool:
        return self.getStatus().isTerminal(self.getStatus())

    def isTerminalSuccess(self) -> bool:
        return self.getStatus().isTerminalSuccess(self.getStatus())

    def isTerminalFailure(self) -> bool:
        return self.getStatus().isTerminalFailure(self.getStatus())

    def isTerminalCancelled(self) -> bool:
        return self.getStatus().isTerminalCancelled(self.getStatus())


    def toJSON(self):
        return self.serialize()

    def serialize(self):
        out_bytes = pickle.dumps(self, 0)
        out_str = out_bytes.decode(encoding='ascii')
        return out_str

    @staticmethod
    def deserialize(s: str):
        in_json = json.dumps(s)
        in_obj = pickle.loads(json.loads(in_json).encode(encoding='ascii'))
        return in_obj


    @staticmethod
    def makeRepoInfo(verb: RepoOp, success: bool, fromPath: str, toPath: str) -> str:
        return ("[" + verb.value + "," + str(success) + "," + fromPath + "," + toPath + "]")

    def toString(self) -> str:
        s = ("" + str(self.getJobContext().getId()) + "," + str(self.getJobContext().getParentJobId()) + "," +
             str(self.getJobContext().getOriginJobId()) + "," +
             str(self.getJobContext().getNativeId()) + "," +
             str(self.getEmitTime()) + "," + str(self.getStatusValue()) + "," + str(self.getJobContext().getSiteName()))
        if (self.getStatus() == JobStatusValues.INFO):
            s += "," + str(self.getNativeInfo())
        return s


#************************************************************************************************************************************


# test
if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    status = JobStatus()
    statusMap = {
        "NODE_FAIL" : JobStatusValues.FAILED
        }
    status.setStatusMap(statusMap)
    status.setNativeStatusStr("NODE_FAIL")
    status.setEmitTime(datetime.utcnow())

    logging.info(status.serialize())
