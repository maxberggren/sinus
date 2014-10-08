import StringIO
import socket
import urllib

import socks    # SocksiPy module
import stem.process

from stem.util import term

from stem import Signal
from stem.control import Controller



def query(url):
    """
    Uses urllib to fetch a site using SocksiPy for Tor over the SOCKS_PORT.
    """

    try:
        return urllib.urlopen(url).read()
    except:
        return "Unable to reach %s" % url



def print_bootstrap_lines(line):
    if "Bootstrapped " in line:
        print term.format(line, term.Color.BLUE)


def maxtest(SOCKS_PORT):

    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', SOCKS_PORT)
    socket.socket = socks.socksocket

    print term.format("Starting Tor:\n", term.Attr.BOLD)

    tor_process = stem.process.launch_tor_with_config(
        config = {
            'SocksPort': str(SOCKS_PORT),
        },
        init_msg_handler = print_bootstrap_lines,
    )

    print term.format("\nChecking our endpoint:\n", term.Attr.BOLD)
    print term.format(query("https://www.atagar.com/echo.php"), term.Color.BLUE)



    tor_process.kill()    # stops tor

maxtest(SOCKS_PORT=7001)
maxtest(SOCKS_PORT=7004)