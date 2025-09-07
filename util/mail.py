import os
import json
import sendgrid
from util.logger import Logger
from util.basedir import BaseDir

class Mail:
    def __init__(self, config):
        self.logger = Logger.getLogger(type(self).__name__)
        self.senderAddress = config["email"]["senderAddress"]
        self.receiverArray = config["email"]["receiverArray"]
        self.bodyPath = BaseDir.get() + '\\config\\' + config["email"]["body"]
        self.contentType = config["email"]["contentType"]

    def sendMail(self, adresses, shortText, longText):
        try:
            sg = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
            data = json.loads(open(self.bodyPath, "r").read())
            # transform longText back in html format
            longText_html = ""
            lines = longText.splitlines()
            for i in range(len(lines)):
                if i == 0:
                    longText_html = '<p>' + lines[i]
                elif (i == (len(lines)-1) and lines[i] == ''):
                    break
                else:
                    longText_html = longText_html + '</p><p>' + lines[i]
            longText_html = longText_html + '</p></p>'
            bcc = []
            for adress in adresses:
                bcc.append({'email':adress})
                data["personalizations"][0]["bcc"] += [{'email':adress}]
            data["personalizations"][0]["to"][0]["email"] = self.receiverArray
            data["from"]["email"] = self.senderAddress
            data["subject"] = shortText
            data["content"][0]["type"] = self.contentType
            data["content"][0]["value"] = longText_html
            try:
                response = sg.client.mail.send.post(request_body=data)
                self.logger.info("send alert email with status\n%s\n%s\n%s" % (response.status_code, response.body, response.headers))
                return True
            except Exception as e:
                self.logger.error("sending mail failed: %s" % str(e))
                return False
        except Exception as e:
            self.logger.error( "sending mail failed: %s" % str(e))
            return False