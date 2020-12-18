### 
### Voice commands for testing the new Unimacro built-in
### 

include "Unimacro.vch";


###########################################################################
#                                                                         #
# Pressing keys/typing/producing characters:                              #
#                                                                         #
###########################################################################

open Explorer window            = WINKEY(e);
push start button               = WINKEY0();

type ASCII character            = A(77);  # M
test unicode delta              = Unimacro("U Delta");
test date                       = DATE();

try shortcut for SendSystemKeys = SSK('x x;y{tab}');


###########################################################################
#                                                                         #
# Waiting:                                                                #
#                                                                         #
###########################################################################

test             wait 1..10 = SetMicrophone(0) WW($1) SetMicrophone(1);
test alternative wait 1..10 = SetMicrophone(0) W1($1) SetMicrophone(1);


Nudge() := MP(2,4,-1,0);  # also test relative mouse motion...

test wait speed =
	Repeat(5, Nudge() W()  )
	Repeat(5, Nudge() SW() )
	Repeat(5, Nudge() LW() );
	
# VW() is tested by travel around the... below


wait for       xterm  = PMP() WWT("xterm alpha") MSG("found xterm!");
wait for upper xterm  = PMP() WWT("xterm Alpha") MSG("found xterm!");

# ???
wait for change = WTC() Beep();



###########################################################################
#                                                                         #
# Mouse commands:                                                         #
#                                                                         #
###########################################################################

<type> := ( absolute         = PMP()    | relative         = PRMP()  |
	    absolute corners = PMP1()   | relative corners = PRMP1() |
	    all              = PALLMP()
	  );

print <type> mouse information = $1;


<area> := (world = 0 | window = 1 | client area = 5 );

travel around the <area> = 
        RM()
        RMP($1, +0.01, +0.01, 0) VW()
        RMP($1, -0.01, +0.01, 0) VW()
        RMP($1, -0.01, -0.01, 0) VW()
        RMP($1, +0.01, -0.01, 0) VW()
        RMP($1, +0.01, +0.01, 0) VW()
	CANCELMOUSE();

travel in the <area> = 
        RM()
        MP($1, 100, 100, 0) VW()
        MP($1, 200, 100, 0) VW()
        MP($1, 200, 200, 0) VW()
        MP($1, 100, 200, 0) VW()
        MP($1, 100, 100, 0) VW()
	CANCELMOUSE();

# ???

test mouse middle = RMP(0,0.5,0.5, left);
test mouse window middle = RMP(5, 0.5, 0.5, left); 
test mouse left top = MP(0, 10, 10, left);
test remember mouse = RM();
another test down = MP(2,0,0,down);
another test up = MP(2,0,0,up);
another test release = MP(2,0,0,release);

test cancel mouse = CANCELMOUSE();
test mouse up = ENDMOUSE();


###########################################################################
#                                                                         #
# Switching between windows/applications:                                 #
#                                                                         #
###########################################################################

mark current window = RW();
marked window       = RTW();

# ???


###########################################################################
#                                                                         #
# Communicating with the user:                                            #
#                                                                         #
###########################################################################

display a message    = MSG('This is a test; can you read it?');
display two messages = MESSAGE(first) MESSAGE(second);

ask a question       = YESNO('is today Friday?') MSG('great!');



###########################################################################
#                                                                         #
# Miscellaneous actions:                                                  #
#                                                                         #
###########################################################################

what version is my Emacs = EMACS(version);


###########################################################################
#                                                                         #
#                                                                         #
#                                                                         #
###########################################################################

run unimacro command = Unimacro(foobar);
bringup explorer = BRINGUP(iexplore);
bringup firefox = BRINGUP(firefox);
test kill window = KW();
test kill document = KW1({ctrl+f4});
test meta action = Unimacro(<<filesave>>);
test line delete = Unimacro("<<selectline>><<linedelete>>"); 

test true = Unimacro("T; this always appears");
test false = Unimacro("F; this never appears");
test print Okay = Unimacro(<<printstart>>) {enter};
test between parens = Unimacro("CLIPSAVE; {ctrl+c}(); CLIPISNOTEMPTY;{left}{ctrl+v}{right}; CLIPRESTORE");
