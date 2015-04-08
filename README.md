Kurento Media Server Mock
=======================

This project is a simple mock for JSON-RPC 2.0 communication of Kurento Media Server (To know more about Kurento check [this](http://kurento.org/)).

Now only support Python 2 (Tested in python2.7), maybe in the future I will port to python3, but the script [SimpleWebSocketServer.py](https://github.com/opiate/SimpleWebSocketServer) (thanks to [opiate](https://github.com/opiate) for this awesome script!) only work in Python 2 right now.

You can execute it manually:
``` bash
chmod +x kmsmock/kms-mock.py
./kmsmock/kms-mock.py
```

Or install it and execute!
```bash
python2 setup.py install  # Use sudo if you've never done this before and have no idea what this do
kms-mock.py
```

By default the server use the port 8889

Why the version name?
================

Maybe you had seen that the version name is pα-0.0.1-mn (actually the α is an a because pypi don't support unicode :'( )

The name means, literally:  Pre-Alpha-0.0.1-MyNeeds

What says that this is a project that I've built to
