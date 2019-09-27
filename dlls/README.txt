DNSKeys.dll is without documentation and copyright information.

It can be used for activating the Windows logo key.  In unimacro by doing the action:

WINKEY letter

examples:

WINKEY b goes to the system tray
WINKEY e opens the windows explorer


See the do_WINKEY function  in action.py.

etc.

In NatSpeak macros by calling AdvancedScript:

	DllCall "DNSKeys","WinKey","b"

or possibly DllCall 
	DllCall "DNSKeys","WinKey"
	(this seems NOT TO WORK, Mark, Quintijn, may 2009)

See also http://qh.antenna.nl/spraakherkenning/wisselentussenvensterstaken/vertikaletaakbalkmetmuisklikken.html

Quintijn Hoogenboom, 4 november 2008 (taken from Speechwiki website which is not online any more)
	
	
4/2/2010: the {f1} and {tab} key seem NOT to work with DNSKeys, in spite of earlier messages about this. So ONLY use for one letter parameters like "b", "e" etc.
	
	

    