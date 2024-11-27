var isIE = (navigator.appName == "Microsoft Internet Explorer");
var isLoaded = 0;
var isNetscape = (navigator.appName == "Netscape");
var prevHeight = 0;
var prevWidth = 0;
function afterLoad() {
//records isLoaded and does onResize()
isLoaded = 1;
onLoadFunctions();
onResize();
}
function bodyHeight(subtract) {
// do at changing size also on load (through onResizeFunctions)
// expecting a div with id "body0" setting at height minus "subtract":
// or a "leftpart" (only IE); with Netscape 15 more
    var height = 0;
    var dh = document.body.clientHeight;
    if (subtract > 0 && dh > subtract) {
    var height = dh - subtract;
    if (isNetscape)
        height += 15;
    }
    else
    var d = null;
    if (isIE)
    var d = document.getElementById("leftpart");
    if (d == null)
    d = document.getElementById("body0");
    if (d == null) {
    alert("no such id: leftpart or body0");
    return;
    }
    d.style.height = height;
}
function changeSize(frameName, Width, Height, minWPadding, minHPadding, scale) {
// do at changing size also on load
// expecting a div with id "frameName":
var dw = parseInt(document.body.clientWidth*scale);
var d = document.getElementById(frameName);
if (d == undefined) {
    alert("no such id: frame");
    return;
}
var p = String(minWPadding);
var q = String(minHPadding);
if (Width > 0 && dw > Width)
   var p = String(Math.max(minWPadding, parseInt((dw-Width)/2)));
var dh = document.body.clientHeight;
if (Height > 0 && dh > Height)
   var q= String(Math.max(minHPadding, parseInt((dh-Height)/2)));
//style_node.appendChild(document.createTextNode(
var selector = "#" + frameName;
var declaration = "padding: " + q + " " + p;
setCssStyleScreenOnly(selector, declaration);
}
function doReload() {
    //reloads if height or width changed more than 10 pixels
var dw = document.body.clientWidth;
var dh = document.body.clientHeight;
var deltax = Math.abs(prevWidth-dw);
var deltay = Math.abs(prevHeight-dh);
if (deltax < 10 && deltay < 10)
    return;
document.location.href = document.location.href;
}
function m(a, b, s, t) {
var mm;mm='<a href="';mm=mm+'mailto';mm+=":"+b;mm+="@"+a;
if(s){mm+="?subj";mm+="ect="+s};mm+='">';
if(t)mm=mm+t;else mm=mm+b+"@"+a;mm+="</a>";w(mm);
}
function onResize() {
    //acts if height or width changed more than 10 pixels
    if (!isLoaded) return;
    var dw = document.body.clientWidth;
    var dh = document.body.clientHeight;
    var deltax = Math.abs(prevWidth-dw);
    var deltay = Math.abs(prevHeight-dh);
    if (deltax < 10 && deltay < 10)
    return;
    prevHeight=dh;
    prevWidth=dw;
    onResizeFunctions();
}
function onResizeReload() {
    //reloads if height or width changed more than 10 pixels
    if (!isLoaded) return;
    var dw = document.body.clientWidth;
    var dh = document.body.clientHeight;
    var deltax = Math.abs(prevWidth-dw);
    var deltay = Math.abs(prevHeight-dh);
    if (deltax < 25 && deltay < 25)
    return;
    document.location.href = document.location.href;
}
function picmenu(Pic, Width, Height, Cl, Link, Text) {
    var L = Pic.length;
    var mw = 0;
    for (var i=0; i<L; i++) {
        mw = Math.max(mw, Width[i]);
    }
    var dw = document.body.clientWidth;
    var nCol = Math.min(parseInt(dw/(mw+10)), L);
    e = '<table class="picmenu" border="0" cellpadding="0" cellspacing="0" width="100%">';
    document.write(e);
    document.write('<tr>');
    var al = "center";
    var im = '';
    var li = '';
    for (var i=0; i<L; i++) {
        if (i%nCol == 0 && i > 0) {
        document.write('</tr><tr><td height="10"><td></tr><tr>');
        }
        if (Pic[i] != "") {
             im = '<img src="'+Pic[i]+'" width="' + Width[i]+
                      '" height="'+Height[i]+'" alt="' + Text[i]+
                     '">';
        }
        else {
            im = Text[i];
        }
        if (Link[i] != "") {
            li = '<a href="'+ Link[i] + '">' + im + '</a>';
        }
        else {
            li = im;
        }
        document.write('<td class="' + Cl[i] + '" align="' +
                        'center' + '">' + li + '</td>');
    }
    document.write('</tr></table>');
}
function setCssStyleScreenOnly(selector, declaration) {
// set style for element screen only. declaration WITHOUT braces!!
// example: see changeSize.
var style_node = document.createElement("style");
style_node.setAttribute("type", "text/css");
style_node.setAttribute("media", "screen");
if (!isIE) { // firefox:
var text = selector + "{" + declaration + "}";
    style_node.appendChild(document.createTextNode(text));
    // append the style node
    document.getElementsByTagName("head")[0].appendChild(style_node);
}
else { //IE
   if (document.styleSheets && document.styleSheets.length > 0) {
         var last_style_node = document.styleSheets[document.styleSheets.length - 1];
         if (typeof(last_style_node.addRule) == "object") last_style_node.addRule(selector, declaration);
        }
}
}
function w(t) {
    // helper function
    document.write(t);
}