import pyodbc
from util.logger import Logger

class Database:
    def __init__(self, driver, host, database, owner):
        self.logger = Logger.getLogger(type(self).__name__)
        self.driver = driver
        self.host = host
        self.database = database
        self.owner = owner

    def connect(self):
        try:
            self.conn = pyodbc.connect('Driver={' + self.driver + '};Server=' + self.host + ';Database=' + self.database + ';Trusted_Connection=yes;')
            cursor = self.conn.cursor()
            cursor.execute('SELECT TOP(1) column FROM table_name')
            # see if the cursor returned something
            if cursor:
                return True
            self.logger.error("could not connect to database")
            return False
        except Exception as e:
            self.logger.error("exception on database connection: %s" % e)

    def getCurrentActiveUsers(self):
        try:
            if not hasattr(self,'conn'):
                if self.connect() == False:
                    return
            selectStatement = "SELECT U.GID, U.Name, U.Vorname, U.Email FROM %s.User U INNER JOIN (SELECT * FROM %s.UserActiveSession WHERE DateActive > DateAdd(second,-360, getutcdate())) UAS ON U.appGUID = UAS.appGUID" % (self.owner, self.owner)
            self.logger.debug(selectStatement)
            cursor = self.conn.cursor()
            cursor.execute(selectStatement)
            results = [row for row in cursor.fetchall()]
            return results
        except Exception as e:
            self.conn.close()
            delattr(self,'conn') 
            self.logger.error("could not select in database - %s" % e)
            self.logger.error("Query: %s" % selectStatement)
    
    def getActiveUsersLast90Days(self):
        try:
            if not hasattr(self,'conn'):
                if self.connect() == False:
                    return
            selectStatement = "SELECT U.Name, U.Vorname, U.Email FROM %s.LV_ActiveEmailsLast90Days lastUs LEFT JOIN %s.User U ON lastUs.Email = U.Email" % (self.owner, self.owner)
            self.logger.debug(selectStatement)
            cursor = self.conn.cursor()
            cursor.execute(selectStatement)
            results = [row for row in cursor.fetchall()]
            return results
        except Exception as e:
            self.conn.close()
            delattr(self,'conn') 
            self.logger.error("could not select in database - %s" % e)
            self.logger.error("Query: %s" % selectStatement)

    def getUserCode(self, userGID, userEmail):
        try:
            if not hasattr(self,'conn'):
                if self.connect() == False:
                    return
            selectStatement = "SELECT appGUID FROM %s.User WHERE GID = '%s' OR Email = '%s'" % (self.owner, userGID, userEmail) 
            self.logger.debug(selectStatement)
            cursor = self.conn.cursor()
            cursor.execute(selectStatement)
            return cursor.fetchone()[0]
        except Exception as e:
            self.conn.close()
            delattr(self,'conn') 
            self.logger.error("could not select in database - %s" % e)
            self.logger.error("Query: %s" % selectStatement)
    
    def getUserIDs(self, adresses):
        try:
            if not hasattr(self,'conn'):
                if self.connect() == False:
                    return
            for i in range(len(adresses)):
                if i == 0:
                    inStatement = "'" + adresses[i] + "'"
                else:
                    inStatement += ',' + "'" + adresses[i] + "'"
            selectStatement = "SELECT appGUID FROM %s.User WHERE Email IN (" % (self.owner) + inStatement + ")"
            self.logger.debug(selectStatement)
            cursor = self.conn.cursor()
            cursor.execute(selectStatement)
            results = [row for row in cursor.fetchall()]
            return (results)
        except Exception as e:
            self.conn.close()
            delattr(self,'conn') 
            self.logger.error("could not select in database - %s" % e)
            self.logger.error("Query: %s" % selectStatement)

    def getActiveNotifications(self):
        try:
            if not hasattr(self,'conn'):
                if self.connect() == False:
                    return
            selectStatement = "SELECT COUNT(appGUID) FROM %s.Notifications WHERE Active = 1" % (self.owner)
            self.logger.debug(selectStatement)
            cursor = self.conn.cursor()
            cursor.execute(selectStatement)
            return cursor.fetchone()[0]
        except Exception as e:
            self.conn.close()
            delattr(self,'conn') 
            self.logger.error("could not select in database - %s" % e)
            self.logger.error("Query: %s" % selectStatement)

    def getNotifiedUsers(self):
        try:
            if not hasattr(self,'conn'):
                if self.connect() == False:
                    return
            selectStatement = "SELECT appGUID, DateNew, ShortText, NotifiedUsers FROM %s.Notifications WHERE Active = 1"  % (self.owner)
            self.logger.debug(selectStatement)
            cursor = self.conn.cursor()
            cursor.execute(selectStatement)
            return cursor.fetchone()
        except Exception as e:
            self.conn.close()
            delattr(self,'conn') 
            self.logger.error("could not select in database - %s" % e)
            self.logger.error("Query: %s" % selectStatement)

    def getNotifiedUsersEmails(self, usersIDs):
        try:
            if not hasattr(self,'conn'):
                if self.connect() == False:
                    return
            for i in range(len(usersIDs)):
                if i == 0:
                    inStatement = "'" + usersIDs[i] + "'"
                else:
                    inStatement += ',' + "'" + usersIDs[i] + "'"
            selectStatement = "SELECT Email FROM %s.User WHERE appGUID IN (" % (self.owner) + inStatement + ")"
            self.logger.debug(selectStatement)
            cursor = self.conn.cursor()
            cursor.execute(selectStatement)
            results = [row for row in cursor.fetchall()]
            return (results)
        except Exception as e:
            self.conn.close()
            delattr(self,'conn') 
            self.logger.error("could not select in database - %s" % e)
            self.logger.error("Query: %s" % selectStatement)

    def addNotification(self, user, level, shortText, longText, active, readAccess, writeAccess, notifiedUsers):
        try:
            if not hasattr(self,'conn'):
                if self.connect() == False:
                    return
            insertStatement = "INSERT INTO %s.Notifications(appGUID, DateNew, DateChanged, ReadAccess, UserNew, UserChanged, WriteAccess, Level, ShortText, LongText, Active, NotifiedUsers) VALUES(NEWID(), GETDATE(), GETDATE(), %s, %s, %s, %s, %s, '%s', '%s', %s, '%s')" % (self.owner, readAccess, user, user, writeAccess, level, shortText, longText, active, notifiedUsers)
            cursor = self.conn.cursor()
            cursor.execute(insertStatement)
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.close()
            delattr(self,'conn') 
            self.logger.error("could not insert in database - %s" % e)
            self.logger.error("Query: %s" % insertStatement)

    def uptNotification(self, notifiedUsers):
        try:
            if not hasattr(self,'conn'):
                if self.connect() == False:
                    return
            updateStatement = "UPDATE %s.Notifications SET Active = 0, DateChanged = GETDATE(), NotifiedUsers = '%s' WHERE Active = 1" % (self.owner, notifiedUsers)
            self.logger.debug(updateStatement)
            cursor = self.conn.cursor()
            cursor.execute(updateStatement)
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.close()
            delattr(self,'conn') 
            self.logger.error("could not update in database - %s" % e)
            self.logger.error("Query: %s" % updateStatement) 