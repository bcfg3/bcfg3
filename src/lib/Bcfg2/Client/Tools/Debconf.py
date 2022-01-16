"""Debconf Support for Bcfg2"""

import subprocess
import Bcfg2.Options
import Bcfg2.Client.Tools


class Debconf(Bcfg2.Client.Tools.Tool):
    """Debconf Support for Bcfg2."""
    name = 'Debconf'
    __execs__ = ['/usr/bin/debconf-communicate', '/usr/bin/debconf-show']
    __handles__ = [('Conf', 'debconf')]
    __req__ = {'Conf': ['name']}

    def __init__(self, config):
        Bcfg2.Client.Tools.Tool.__init__(self, config)

        #: This is the referrence to the Popen object of the
        #: running debconf-communicate process. If this is None,
        #: no process is runnning.
        self.debconf = None

    def _start_debconf(self):
        if self.debconf is None:
            self.debconf = subprocess.Popen(
                ['/usr/bin/debconf-communicate'],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def _stop_debconf(self):
        if self.debconf is not None:
            self.debconf.stdin.close()
            self.debconf.stdout.close()
            self.debconf = None

    def _debconf_reply(self, msg):
        if self.debconf is None:
            self._start_debconf()

        self.logger.debug('Debconf: %s' % msg.strip())
        self.debconf.stdin.write(msg)
        line = self.debconf.stdout.readline().rstrip('\n')
        self.logger.debug('< %s' % line)
        reply = line.split(' ', 1)

        result = None
        if len(reply) > 1:
            result = reply[1]
        return (reply[0] == '0', result)

    def debconf_get(self, key):
        (success, value) = self._debconf_reply('GET %s\n' % key)
        if not success:
            return (False, None)

        (_, seen) = self._debconf_reply('FGET %s seen\n' % key)
        return (seen, value)

    def debconf_set(self, key, value):
        (success, _) = self._debconf_reply('SET %s %s\n' % (key, value))
        if success:
            self._debconf_reply('FSET %s seen true\n' % key)

        return success

    def debconf_reset(self, key):
        (success, _) = self._debconf_reply('RESET %s\n' % key)
        return success

    def VerifyConf(self, entry, _modlist):
        """ Verify the given Debconf entry. """
        (_, value) = self.debconf_get(entry.get('name'))
        if value != entry.get('value'):
            return False
        return True

    def InstallConf(self, entry):
        """ Install the given Debconf entry. """
        return self.debconf_set(entry.get('name'), entry.get('value'))

    def Inventory(self, structures=None):
        try:
            result = Bcfg2.Client.Tools.Tool.Inventory(self, structures)
        finally:
            self._stop_debconf()

        return result
    Inventory.__doc__ = Bcfg2.Client.Tools.Tool.Inventory.__doc__

    def Install(self, entries):
        try:
            result = Bcfg2.Client.Tools.Tool.Install(self, entries)
        finally:
            self._stop_debconf()

        return result
    Install.__doc__ = Bcfg2.Client.Tools.Tool.Install.__doc__
    
    def FindExtra(self):
        specified = [entry.get('name')
                     for entry in self.getSupportedEntries()]
        extra = set()
        listowners = self.cmd.run(['/usr/bin/debconf-show', '--listowners'])
        if listowners.success:
            owners = listowners.stdout.splitlines()

            values = self.cmd.run(['/usr/bin/debconf-show'] + owners)
            for line in values.stdout.splitlines():
                if len(line) > 2 and line[0] == '*':
                    (name, value) = line[2:].split(':', 2)
                    if name not in specified:
                        extra.add(name)
        return [Bcfg2.Client.XML.Element('Conf', name=name, type='debconf')
                for name in list(extra)]
    FindExtra.__doc__ = Bcfg2.Client.Tools.Tool.FindExtra.__doc__
