from util.database import Database
from util.logger import Logger


class PopUp:
    def __init__(self, config):
        self.logger = Logger.getLogger(type(self).__name__)
        self.db = Database(config["database"]["driver"], config["database"]["host"], config["database"]["database"], config["database"]["owner"])

    def getNotifiedUsersString(self, usersIDs):
        notifiedUsers = ""
        for i in range(len(usersIDs)):
            if i == 0:
                notifiedUsers = str(usersIDs[i])
            else:
                notifiedUsers = notifiedUsers + "," + str(usersIDs[i])
        return notifiedUsers

    def checkActiveNotifications(self):
        return self.db.getActiveNotifications()

    def checkNotifiedUsers(self):
        return self.db.getNotifiedUsers()

    def createNotification(self, userGID, userEmail, level, shortText, longText, active, readAccess, writeAccess, usersIDs):
        user = self.db.getUserCode(userGID, userEmail)
        notifiedUsers = self.getNotifiedUsersString(usersIDs)
        return self.db.addNotification(user, level, shortText, longText, active, readAccess, writeAccess, notifiedUsers)

    def desactivateNotifications(self, usersIDs):
        notifiedUsers = self.getNotifiedUsersString(usersIDs)
        return self.db.uptNotification(notifiedUsers)