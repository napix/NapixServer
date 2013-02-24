import platform
from napixd.managers import Manager

class AvailableOnLinuxOnly(Manager):
    @classmethod
    def detect(self):
        return platform.platform() == 'Linux'
