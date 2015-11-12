import subprocess
import os


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

        oldpath = os.getcwd()
        os.chdir(self.config['SITE_PATH'])

        response = self._get_site_version()

        os.chdir(oldpath)

        return response

    @admincmd
    def site_tags(self, msg, args):
        """Get the tags currently available"""

        if not self.config['SITE_PATH']:
            return "I cannot comply, I have not been configured with a site path yet."

        oldpath = os.getcwd()
        os.chdir(self.config['SITE_PATH'])

        response = self._get_site_tags()

        os.chdir(oldpath)

        return response

    @admincmd
    def maintenance_mode(self, msg, args):
        """Maintenance mode for the website.

        With no arguments, this command will simply return the current status of
        the website's maintenance mode. Alternatively, supply "start" or "stop"
        as an argument to start or stop maintenance mode.

        An unrecognized argument will be treated as none at all, and thus return
        the current status."""

        if not self.config['SITE_PATH']:
            return "I cannot comply, I have not been configured with a site path yet."

        cmd = os.path.join(self.config['SITE_PATH'], 'maintenance_mode')

        if args.lower() == 'start':
            subprocess.check_output([cmd, 'start'])
            response = "I have engaged Maintenance Mode"
        elif args.lower() == 'stop':
            subprocess.check_output([cmd, 'stop'])
            response = "I have disengaged Maintenance Mode"
        else:
            response = subprocess.check_output([cmd, 'status']).decode("utf-8")

        return response

    def _get_site_version(self):
        # git symbolic-ref -q --short HEAD || git describe --tags --exact-match
        try:
            output = subprocess.check_output(['git', 'symbolic-ref', '-q', '--short', 'HEAD'], stderr=subprocess.STDOUT)
        except CalledProcessError:
            # Not a regular branch, try looking for a tag
            try:
                #output = check_output(['git', 'describe', '--tags', '--exact-match'], stderr=STDOUT)
                output = subprocess.check_output('git describe --tags --exact-match; exit 0', shell=True, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError:
                # Something else, for now just give up
                return "I cannot comply, something went wrong: {}".format(output)

        return "The website is currently on {}".format(output.decode("utf-8"))

    def _get_site_tags(self):
        try:
            output = subprocess.check_output(['git', 'tag'], stderr=subprocess.STDOUT)
        except CalledProcessError:
            return "I cannot comply, something went wrong: {}".format(output.decode("utf-8"))

        return "The site has these tags available:\n{}".format(output.decode("utf-8"))

