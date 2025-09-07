import logging, os
from datetime import datetime
from util.basedir import BaseDir

FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=FORMAT, level="DEBUG")

class Logger:
    @staticmethod
    def getLogger(name):
        ret = logging.getLogger(name)
        Logger.setFileName(ret)
        return ret

    @staticmethod
    def setFileName(logger):
        path = BaseDir.get() + '\\logs\\'
        # create folder if it not exists
        if not os.path.exists(path):
            os.makedirs(path)

        log_file = str(datetime.now().strftime('%Y_%m_%d')) + '.txt'
        fileh = logging.FileHandler(path + '%s' % log_file, 'a')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fileh.setFormatter(formatter)
        for hdlr in logger.handlers[:]:
            logger.removeHandler(hdlr)
        logger.addHandler(fileh)
