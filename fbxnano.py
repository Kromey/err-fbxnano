from errbot import BotPlugin, botcmd
from errbot.backends.base import RoomNotJoinedError


admincmd = botcmd(admin_only=True)


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
        return {
                'NANO_ROOM': "room@conferenace.example.com",
                'SITE_PATH': "",
               }

    def configure(self, configuration):
        """Allow configuration to be updated incrementally

        Only the part(s) of the config you want changed need to be supplied to
        the !config command. Anything you want left unchanged -- or, if not yet
        set, left at the template value -- can simply be omitted."""
        config = self.get_configuration_template()

        try:
            config.update(self.config)
        except (AttributeError,TypeError):
            # If we're not yet configured, self.config is None; do nothing about it
            pass

        try:
            config.update(configuration)
        except TypeError:
            # We were passed None, or not a valid dictionary; do nothing with it
            pass

        super().configure(config)

    def check_configuration(self, configuration):
        """Check our config, keeping in mind it may be partial.

        We simply merge the configuration with the template, and then do the
        standard check_configuration() on the result."""
        config = self.get_configuration_template()
        config.update(configuration)

        super().check_configuration(config)

    @admincmd
    def check_config(self, msg, args):
        """Check the currently-active configuration.

        Our partial-configuration support means that the standard !config
        command doesn't actually know the full story. This custom command will
        allow us to examine the currently-running configuration instead."""
        yield "My current configuration is:"
        yield self.config

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

    @admincmd
    def deploy_site(self, msg, args):
        """Deploy a new version of the site"""

        if not self.config['SITE_PATH']:
            return "I cannot comply, I have not been configured with a site path yet."

        return "I cannot comply, I have not been coded with that operation yet."

    @admincmd
    def site_version(self, msg, args):
        """Get the current version of the website"""

        if not self.config['SITE_PATH']:
            return "I cannot comply, I have not been configured with a site path yet."

        return "I cannot comply, I have not been coded with that operation yet."

