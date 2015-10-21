# This is a skeleton for Err plugins, use this to get started quickly.

from errbot import BotPlugin, botcmd


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
        #Invite the user to the NANO_ROOM
        self.query_room(self.config['NANO_ROOM']).invite(mess.frm.person)
        return "You've been invited to the party!"

