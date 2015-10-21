# This is a skeleton for Err plugins, use this to get started quickly.

from errbot import BotPlugin, botcmd
from errbot.backends.base import RoomNotJoinedError


class FbxNano(BotPlugin):
    """An Err plugin for our chat server"""
    min_err_version = '3.0.5' # Optional, but recommended

    def activate(self):
        if not self.config:
            #Don't allow activation until we are configured
            self.log.info('FbxNano is not configured. Forbid activation.')
            return

        super().activate()

    def get_configuration_template(self):
        return {'NANO_ROOM': "room@conferenace.example.com",
               }

    @botcmd
    def invite_me(self, mess, args):
        """Ask the bot to invite you to the group chat"""
        #Get the room object -- we're going to play with it a bit
        room = self.query_room(self.config['NANO_ROOM'])

        #Get the count of occupants in the room
        try:
            occupants = len(room.occupants)
        except RoomNotJoinedError:
            return "I cannot comply. I am not there."

        #The bot is in the room as well, reduce the count
        occupants = occupants - 1

        #Now invite the user
        room.invite(mess.frm.person)

        #And finally, give some character in the response
        if occupants:
            return "The others might enjoy your presence."
        else:
            return "Very well, but you and I could converse just as well here."

