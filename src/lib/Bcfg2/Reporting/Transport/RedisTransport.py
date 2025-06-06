"""
The Redis transport.  Stats are pickled and written to
a redis queue

"""

import time
import signal
import platform
import traceback
import threading
import Bcfg2.Options
from Bcfg2.Reporting.Transport.base import TransportBase, TransportError
from Bcfg2.Compat import cPickle

try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


class RedisMessage(object):
    """An rpc message"""
    def __init__(self, channel, method, args=[], kwargs=dict()):
        self.channel = channel
        self.method = method
        self.args = args
        self.kwargs = kwargs


class RedisTransport(TransportBase):
    """ Redis Transport Class """
    STATS_KEY = 'bcfg2_statistics'
    COMMAND_KEY = 'bcfg2_command'

    options = TransportBase.options + [
        Bcfg2.Options.Option(
            cf=('reporting', 'redis_host'), dest="reporting_redis_host",
            default='127.0.0.1', help='Reporting Redis host'),
        Bcfg2.Options.Option(
            cf=('reporting', 'redis_port'), dest="reporting_redis_port",
            default=6379, type=int, help='Reporting Redis port'),
        Bcfg2.Options.Option(
            cf=('reporting', 'redis_db'), dest="reporting_redis_db",
            default=0, type=int, help='Reporting Redis DB')]

    def __init__(self):
        super(RedisTransport, self).__init__()
        self._commands = None

        self.logger.error("Warning: RedisTransport is experimental")

        if not HAS_REDIS:
            self.logger.error("redis python module is not available")
            raise TransportError

        self._redis = redis.Redis(
            host=Bcfg2.Options.setup.reporting_redis_host,
            port=Bcfg2.Options.setup.reporting_redis_port,
            db=Bcfg2.Options.setup.reporting_redis_db)


    def start_monitor(self, collector):
        """Start the monitor. Eventaully start the command thread"""
        self._commands = threading.Thread(target=self.monitor_thread,
            args=(self._redis, collector))
        self._commands.start()


    def store(self, hostname, metadata, stats):
        """Store the file to disk"""

        try:
            payload = cPickle.dumps(dict(hostname=hostname,
                                         metadata=metadata,
                                         stats=stats))
        except:  # pylint: disable=W0702
            msg = "%s: Failed to build interaction object: %s" % \
                (self.__class__.__name__,
                 traceback.format_exc().splitlines()[-1])
            self.logger.error(msg)
            raise TransportError(msg)

        try:
            self._redis.rpush(RedisTransport.STATS_KEY, payload)
        except redis.RedisError:
            self.logger.error("Failed to store interaction for %s: %s" %
                (hostname, traceback.format_exc().splitlines()[-1]))


    def fetch(self):
        """Fetch the next object"""
        try:
            payload = self._redis.blpop(RedisTransport.STATS_KEY, timeout=5)
            if payload:
                return cPickle.loads(payload[1])
        except redis.RedisError:
            self.logger.error("Failed to fetch an interaction: %s" %
                (traceback.format_exc().splitlines()[-1]))
        except cPickle.UnpicklingError:
            self.logger.error("Failed to unpickle payload: %s" %
                    traceback.format_exc().splitlines()[-1])
            raise TransportError

        return None

    def shutdown(self):
        """Called at program exit"""
        self._redis = None


    def rpc(self, method, *args, **kwargs):
        """
        Send a command to the queue.  Timeout after 10 seconds
        """
        pubsub = self._redis.pubsub()

        channel = "%s%s" % (platform.node(), int(time.time()))
        pubsub.subscribe(channel)
        self._redis.rpush(RedisTransport.COMMAND_KEY,
            cPickle.dumps(RedisMessage(channel, method, args, kwargs)))

        resp = pubsub.listen()
        signal.signal(signal.SIGALRM, self.shutdown)
        signal.alarm(10)
        next(resp) # clear subscribe message
        response = next(resp)
        pubsub.unsubscribe()

        try:
            return cPickle.loads(response['data'])
        except: # pylint: disable=W0702
            msg = "%s: Failed to receive response: %s" % \
                (self.__class__.__name__,
                 traceback.format_exc().splitlines()[-1])
            self.logger.error(msg)
        return None


    def monitor_thread(self, rclient, collector):
        """Watch the COMMAND_KEY queue for rpc commands"""

        self.logger.info("Command thread started")
        while not collector.terminate.isSet():
            try:
                payload = rclient.blpop(RedisTransport.COMMAND_KEY, timeout=5)
                if not payload:
                    continue
                message = cPickle.loads(payload[1])
                if not isinstance(message, RedisMessage):
                    self.logger.error("Message \"%s\" is not a RedisMessage" %
                        message)

                if not message.method in collector.storage.__class__.__rmi__ or\
                    not hasattr(collector.storage, message.method):
                    self.logger.error(
                        "Unknown method %s called on storage engine %s" %
                        (message.method, collector.storage.__class__.__name__))
                    raise TransportError

                try:
                    cls_method = getattr(collector.storage, message.method)
                    response = cls_method(*message.args, **message.kwargs)
                    response = cPickle.dumps(response)
                except:
                    self.logger.error("RPC method %s failed: %s" %
                        (message.method, traceback.format_exc().splitlines()[-1]))
                    raise TransportError
                rclient.publish(message.channel, response)

            except redis.RedisError:
                self.logger.error("Failed to fetch an interaction: %s" %
                    (traceback.format_exc().splitlines()[-1]))
            except cPickle.UnpicklingError:
                self.logger.error("Failed to unpickle payload: %s" %
                    traceback.format_exc().splitlines()[-1])
            except TransportError:
                pass
            except: # pylint: disable=W0702
                self.logger.error("Unhandled exception in command thread: %s" %
                    traceback.format_exc().splitlines()[-1])
        self.logger.info("Command thread shutdown")
