import subprocess
import os


from errbot import BotPlugin, botcmd
from errbot.backends.base import RoomNotJoinedError


admincmd = botcmd(admin_only=True)


class GitError(Exception):
    pass

class ConfigError(Exception):
    pass


def sitecmd(method):
    """Decorate methods that need to run commands locally in the SITE_PATH

    This decorator handles checking config and properly manipulating the working
    directory to successfully run commands from within SITE_PATH, but without
    affecting other bot operations.
    """
    def wrapper(self, *args, **kwargs):
        if not self.config['SITE_PATH']:
            raise ConfigError("I cannot comply, I have not been configured with a site path yet.")

        oldpath = os.getcwd()
        os.chdir(self.config['SITE_PATH'])

        response = method(self, *args, **kwargs)

        os.chdir(oldpath)

        return response

    return wrapper


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

        cur_version = self._get_site_version()
        new_version = args

        if cur_version == new_version or cur_version == "v{}".format(new_version):
            return "The site is already on version {}".format(cur_version)

        self._fetch_upstream()

        try:
            self._checkout_tag(new_version)
        except GitError:
            # Maybe the user forgot the leading 'v', try again
            try:
                self._checkout_tag("v{}".format(new_version))
            except GitError as e:
                return str(e)

        return "Version {} of the website has been deployed".format(self._get_site_version())

    @admincmd
    def site_version(self, msg, args):
        """Get the current version of the website"""

        return "The website is currently on {}".format(self._get_site_version())

    @admincmd
    def site_tags(self, msg, args):
        """Get the most recent tags available.

        By default, returns only the 5 most recent tags, but you can request a
        different number by supplying the desired count as an argument, such as
        `!site tags 3` to get the 3 most recent tags.
        """

        try:
            tags = self._get_site_tags(int(args))
        except ValueError:
            tags = self._get_site_tags()

        return "The {} most recent tags available are:\n{}".format(len(tags), "\n".join(tags))

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

    @sitecmd
    def _get_site_version(self):
        # git symbolic-ref -q --short HEAD || git describe --tags --exact-match
        try:
            output = subprocess.check_output(['git', 'symbolic-ref', '-q', '--short', 'HEAD'], stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            # Not a regular branch, try looking for a tag
            try:
                #output = check_output(['git', 'describe', '--tags', '--exact-match'], stderr=STDOUT)
                output = subprocess.check_output('git describe --tags --exact-match; exit 0', shell=True, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError:
                # Something else, for now just give up
                raise GitError("I cannot comply, something went wrong: {}".format(output.decode("utf-8")))

        return output.decode("utf-8").strip()

    @sitecmd
    def _get_site_tags(self, count=5):
        try:
            output = subprocess.check_output(['git', 'tag'], stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            raise GitError("I cannot comply, something went wrong: {}".format(output.decode("utf-8")))

        tags = output.decode("utf-8").split()[-1*count:]

        return tags[::-1] # Extended slice notation; reverses the list

    @sitecmd
    def _fetch_upstream(self):
        try:
            subprocess.check_output(['git', 'fetch', '--all'], stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            raise GitError("I cannot comply, something went wrong: {}".format(output.decode("utf-8")))

    @sitecmd
    def _checkout_tag(self, target):
        # First ensure the target tag exists, at least in the last 25 tags
        if target not in self._get_site_tags(25):
            raise GitError("Target does not exist, or is too old: {}".format(target))

        try:
            subprocess.check_output(['git', 'checkout', '--force', target], stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            raise GitError("Something went wrong: {}".format(output.decode("utf-8")))


