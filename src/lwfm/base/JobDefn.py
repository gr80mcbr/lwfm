
# A Job Definition is the abstract representation of a job, the non-instantiated description.
# The JobDefn will be passed to the Site's Run driver which will use the args to instantiate a Job from the defn.

from enum import Enum
import logging
import uuid

from datetime import datetime

from lwfm.base.LwfmBase import LwfmBase


class _JobDefnFields(Enum):
    NAME               = "name"                        # for human convenience
    COMPUTE_TYPE       = "computeType"                 # some sites define addressable compute resources within it
    ENTRY_POINT_PATH   = "entryPointPath"              # defines the top-level "executable" command to pass to the site scheduler
    NOTIFICATION_EMAIL = "notificationEmail"           # some site schedulers permit direct user notification
    # EXTRA_ARGS                                       # site schedulers vary widely - this dict permits arbitrary args

class JobDefn(LwfmBase):

    def __init__(self, args: dict[str, type]=None):
        super(JobDefn, self).__init__(args)

    def setName(self, name: str) -> None:
        LwfmBase._setArg(self, _JobDefnFields.NAME.value, name)

    def getName(self) -> str:
        return LwfmBase._getArg(self, _JobDefnFields.NAME.value)

    def setComputeType(self, name: str) -> None:
        LwfmBase._setArg(self, _JobDefnFields.COMPUTE_TYPE.value, name)

    def getComputeType(self) -> str:
        return LwfmBase._getArg(self, _JobDefnFields.COMPUTE_TYPE.value)

    def setEntryPointPath(self, entryPointPath: [str]) -> None:
        LwfmBase._setArg(self, _JobDefnFields.ENTRY_POINT_PATH.value, entryPointPath)

    def getEntryPointPath(self) -> [str]:
        return LwfmBase._getArg(self, _JobDefnFields.ENTRY_POINT_PATH.value)

    def setNotificationEmail(self, email: str) -> None:
        LwfmBase._setArg(self, _JobDefnFields.NOTIFICATION_EMAIL.value, email)

    def getNotificationEmail(self) -> str:
        return LwfmBase._getArg(self, _JobDefnFields.NOTIFICATION_EMAIL.value)

    def setExtraArgs(self, args: dict[str, type]=None) -> None:
        LwfmBase.setArgs(self, args)

    def getExtraArgs(self) -> dict[str,type]:
        return LwfmBase.getArgs(self)
