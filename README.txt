python-cctalk
=============

Based on the original package by David Schryer with modifications by James Churchill.
The original code was greatly refactored to be more pythonic and support EMP devices.

This package allows one to send ccTalk messages and decode replies
from a ccTalk device. This code can be easily extended to include any
ccTalk message for use with any device.  Since this package makes use
of hardware that did not have existing free software to control it,
original authors decided to write own package to support this.

This package was created with and includes only free software and is
licensed under GPLv3 or any later version.  A copy of this license 
is found in the file gpl-3.0.txt.

The library uses the excellent python-serial to communicate with ccTalk devices.

Documentation has been stripped out due to efforts needed to keep it up to date.
Check `scripts/` directory for usage examples. Any contributions are welcome.
