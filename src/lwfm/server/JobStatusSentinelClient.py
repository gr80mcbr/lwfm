import pickle
import requests
import logging

class JobStatusSentinelClient:
    # TODO - do the right thing...
    _JSS_URL = "http://127.0.0.1:5000"

    def getUrl(self):
        return self._JSS_URL

    def setEventHandler(self, jobId: str, jobSiteName: str, jobStatus: str,
                        fireDefn: str, targetSiteName: str) -> str:
        payload = {}
        payload["jobId"] = jobId
        payload["jobSiteName"] = jobSiteName
        payload["jobStatus"] = jobStatus
        payload["fireDefn"] = pickle.dumps(fireDefn, 0).decode() # Use protocol 0 so we can easily convert to an ASCII string
        payload["targetSiteName"] = targetSiteName
        response = requests.post(f'{self.getUrl()}/set', payload)
        if response.ok:
            return response.text
        else:
            logging.error(response)
            return None

    def unsetEventHandler(self, handlerId: str) -> bool:
        response = requests.get(f'{self.getUrl()}/unset/{handlerId}')
        if response.ok:
            return True
        else:
            return False

    def unsetAllEventHandlers(self) -> bool:
        response = requests.get(f'{self.getUrl()}/unsetAll')
        if response.ok:
            return True
        else:
            return False

    def listActiveHandlers(self) -> [str]:
        response = requests.get(f'{self.getUrl()}/list')
        if response.ok:
            return eval(response.text)
        else:
            logging.error(response)
            return None

    def emitStatus(self, jobId, jobStatus):
        data = {'jobId' : jobId,
                'jobStatus': jobStatus}
        response = requests.post(f'{self.getUrl()}/emit', data=data)
        if response.ok:
            return None
        else:
            logging.error(response)
            return None

    def getStatus(self, jobId) -> str:
        response = requests.get(f'{self.getUrl()}/status/{jobId}')
        if response.ok:
            return response.text
        else:
            return None


#************************************************************************************************************************************

# test
if __name__ == '__main__':

    # basic client test - assumes the JSS Svc is running and exposing an HTTP API
    jssClient = JobStatusSentinelClient()
    logging.info("*** " + str(jssClient.listActiveHandlers()))
    logging.info("*** " + str(jssClient.unsetAllEventHandlers()))
    handlerId = jssClient.setEventHandler("123", "nersc", "INFO", "{jobDefn}", "nersc")
    logging.info("*** " + handlerId)
    logging.info("*** " + str(jssClient.listActiveHandlers()))
    logging.info("*** " + str(jssClient.unsetEventHandler(handlerId)))
