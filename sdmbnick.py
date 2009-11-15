#!/usr/bin/env python

from google.appengine.ext import db

from waveapi import events
from waveapi import model
from waveapi import robot

import logging
import re

class SdmbUser(db.Model):
    address = db.StringProperty(required=True)
    nick = db.StringProperty(required=True)

    def __str__(self):
        return "SdmbUser{address: %s, nick: %s}" % (self.address, self.nick)


class NotificationsRobot(robot.Robot):
    def __init__(self):
        robot.Robot.__init__(self, "sdmbnicky",
                             version=1,
                             image_url="http://sdmbnicky.appspot.com/favicon.png",
                             profile_url='http://sdmbnicky.appspot.com/')
        self.RegisterListener(self)

    def on_wavelet_participants_changed(self, event, context):
        pass

    def on_blip_submitted(self, event, context):
        """Invoked when a blip is submitted.

        Here we do two things: check for commands, and markup new
        blips."""
        blip = context.GetBlipById(event['blipId'])
        text = blip.GetDocument().GetText()
        if len(text) == 0 or text[0] == "[" or not blip.parentBlipId:
            return
        logging.debug("Matching text: %s" % str(text))
        m = re.match("^My nick is (.*)$", text, re.I)
        if m:
            newnick = m.group(1).strip()
            self.delete_nick(newnick)
            user = SdmbUser(address=blip.creator,
                            nick=newnick)
            logging.debug("Creating new SdmbUser: %s" % str(user));
            user.put()
        nick = self.lookup(blip.creator)
        logging.debug("Looking up: %s" % str(blip.creator))
        if nick:
            logging.debug("Found: %s" % str(nick))
            blip = context.GetBlipById(event['blipId'])
            blip.GetDocument().SetText("[%s]: %s" %
                                       (nick, blip.GetDocument().GetText()))

    def delete_nick(self, nick):
        """Delete the entry with the passed in nick."""

        query = SdmbUser.all()
        query.filter("nick = ", nick)
        results = query.fetch(1)
        if len(results) > 0:
            logging.debug("Deleting entry: %s" % results[0])
            results[0].delete()


    def lookup(self, wave_user):
        """Lookup the nick of the wave user passed in.

        If there is none found, return None."""
        query = SdmbUser.all()
        query.filter("address =", wave_user)
        results = query.fetch(1)
        if len(results) == 0:
            return None
        else:
            return results[0].nick

if __name__ == '__main__':
    NotificationsRobot().Run()
