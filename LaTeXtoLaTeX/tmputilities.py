
import re
import component

#################

def strip_brackets(text,lbrack="{",rbrack="}",depth=0):
    """Convert {{text}}} to text}.

    """

    thetext = text
    current_depth = 0

    if not thetext:
        return ""

    while thetext and thetext[0] == lbrack and thetext[-1] == rbrack:
        current_depth += 1
        firstpart,secondpart = first_bracketed_string(thetext,0,lbrack,rbrack)
        firstpart = firstpart[1:-1]
        if not firstpart:
            return secondpart
        elif depth and current_depth >= depth:
            return firstpart
        thetext = firstpart + secondpart

    return thetext

###################

def first_bracketed_string(text, depth=0, lbrack="{", rbrack="}"):
    """If text is of the form {A}B, return {A},B.

    Otherwise, return "",text.

    """

    thetext = text.strip()

    if not thetext:
        print "Error: no text"
        component.error_messages.append("empty string sent to first_bracketed_string()")
        return ""

    previouschar = ""
       # we need to keep track of the previous character becaause \{ does not
       # count as a bracket

    if depth == 0 and thetext[0] != lbrack:
        return "",thetext

    elif depth == 0:
        firstpart = lbrack
        depth = 1
        thetext = thetext[1:]
    else:
        firstpart = ""   # should be some number of brackets?

    while depth > 0 and thetext:
        currentchar = thetext[0]
        if currentchar == lbrack and previouschar != "\\":
            depth += 1
        elif currentchar == rbrack and previouschar != "\\":
            depth -= 1
        firstpart += currentchar
        if previouschar == "\\" and currentchar == "\\":
            previouschar = "\n"
        else:
            previouschar = currentchar

        thetext = thetext[1:]

    if depth == 0:
        return firstpart, thetext
    else:
        print "Error: no matching bracket",lbrack,"in",thetext,"XX"
  #      return "",thetext
        print "returning",firstpart[1:100], "\nPLUS MORE\n"
        return "",firstpart[1:]   # firstpart should be everything
                                  # but take away the bracket that doesn't match


#################

def replacemacro(text,macroname,numargs,replacementtext):
    """Expand a LaTeX macro in text.

    """

    if text == "":
      #  logging.debug("replacing macro %s in an empty string", macroname)
        return ""

    if "\\"+macroname not in text:
        return text

    # there is a tricky situation when a macro is being replaced by nothing.  if it is
    # alone on a line, then you just introduced a paragraph break.  it seems we must
    # treat that as a special case

    
    thetext = text
    global a_macro_changed
    
    a_macro_changed = 1

    while a_macro_changed:   # maybe change to:  while "\\"+macroname in text:

        # first, the special case described above, which we are not really handling right
        if not replacementtext:
            while a_macro_changed:
          #      logging.debug("replacing macro %s by nothing in: %s", macroname, re.sub("\s{2,}","\n",thetext.strip())[:30])
                a_macro_changed = 0
                thetext = re.sub(r"\n\\("+macroname+r")\s*({[^{}]*})\s",
                                 lambda match: replacemac(match,numargs,"\n"),thetext,1,re.DOTALL)
        a_macro_changed = 0

        thetext = re.sub(r"\\("+macroname+r")\**(([0-9]|\b)+.*)",lambda match: replacemac(match,numargs,replacementtext),thetext,1,re.DOTALL)

    return thetext

##############

def replacemac(txt,numargs,replacementtext):

    this_macro = txt.group(1)
    text_after = txt.group(2)

    if numargs:
        text_after = text_after.lstrip()

    if text_after.startswith("["):
      #  logging.debug("found square group")
        squaregroup, text_after = first_bracketed_string(text_after,0,"[","]")
        text_after = text_after.lstrip()
        # Currently we ignore the squaregroup.  What should we do with it?

     # first a hack to handle some oddly formed macro calls
    try:
        first_character = text_after[0]
    except IndexError:
        first_character = ""

    if numargs and first_character  not in ["{","\\"] and first_character not in r"0123456789":
     #   logging.debug("found %s but it has no argument %s", this_macro, text_after[:50])
        return text_after

    if first_character in "0123456789":   # wrap it in {} and proceed normally
     #   logging.debug("found that the argument is a number")
        text_after = re.sub("^([0-9])",r"{\1}",text_after,1)
     #   logging.debug("now the text after starts: %s", text_after[:20])
        
    if first_character == r"\\":   # wrap the argument in {} and proceed normally
     #   logging.debug("found that the argument is another macro")
        text_after = re.sub(r"^\\([a-zA-Z]+)",r"{\\\1}",text_after,1)

    global a_macro_changed
    a_macro_changed += 1

    arglis=[""]      # put a throw-away element 0 so that it is less confusing
                     # when we assign to the LaTeX "#N" argmuments

    for ar in range(numargs):
            try:
                theitem, text_after = first_bracketed_string(text_after)
            except ValueError:
        #        logging.error("no text_after in replacemac for argument %s of %s", ar, this_macro)
        #        if ar:
        #            logging.error("arglis so far is %s", arglis)
                theitem = ""
                # below is to fail gracefully when there is an error.
                # need to come up with a better way
            if not theitem:  # probably missing close bracket
        #        logging.error("was scanning argument %s of %s before text_after %s", ar, this_macro, text_after[:20])
        #        logging.error("missing brace?  guess to stop at end of line")
                if "\n" in text_after:
                    theitem, text_after = text_after.split("\n",1)
                else:
                    theitem = ""
            theitem = strip_brackets(theitem)
            theitem = re.sub(r"\\",r"\\\\",theitem)  # This is tricky.  We are using the extracted LaTeX
                                                   # in a substitution, so we should think of it as code.
                                                   # Therefore we need to excape the backslashes.
            arglis.append(theitem)

# confused about which of the next two lines is correct
    macroexpanded = replacementtext
#    macroexpanded = re.sub(r"\\",r"\\\\",replacementtext)

    for arg in range(1,numargs+1):
        mysubstitution = "#"+str(arg)
        macroexpanded = re.sub(mysubstitution,arglis[arg],macroexpanded)
        
    return macroexpanded + text_after


#################

def argument_of_macro(text,mac,argnum=1):
    """Return the argument (without brackets) of the argnum
       argument of the first appearance of the macro \mac
       in text.

    """

    searchstring = r".*?" + r"\\" + mac + r"\b" + r"(.*)"
    # the ? means non-greedy, so it matches the first appearance of \\mac\b

    try:
        text_after = re.match(searchstring,text,re.DOTALL).group(1)
    except AttributeError:
        print "Error: macro " + mac + " not in text"
        return ""

    for _ in range(argnum):
        the_argument, text_after = first_bracketed_string(text_after)

    the_argument = strip_brackets(the_argument)

    return the_argument

#################

def replacein(txt, word_was, word_is, the_first="", the_last="", at_start="", at_end=""):
    """ Replace word_was by word_is in txt.group(0),
        except possibly the fist and last instances.

        User must supply correct number of backslashes.
    """

    text = txt.group(1)
    try:
        start_tag = txt.group(2)
        end_tag = txt.group(3)
    except IndexError:
        start_tag = ""
        end_tag = ""

    # need this so the usual use case is idempotent.
    # but what if we want to only use the at_start and at_end?
    if re.sub(r"\\\\",r"\\",word_was) not in text:
        return text

#    oldword = re.sub(r"\\",r"\\\\",word_was) 
#    newword = re.sub(r"\\",r"\\\\",word_is) 
#    new_first_word = re.sub(r"\\",r"\\\\",the_first) 
#    new_last_word = re.sub(r"\\",r"\\\\",the_last) 
    the_start_tag = re.sub(r"\\",r"\\\\",start_tag)
    the_end_tag = re.sub(r"\\",r"\\\\",end_tag)
    oldword = word_was
    newword = word_is
    new_first_word = the_first
    new_last_word = the_last

    if at_start and start_tag:
        text = re.sub(the_start_tag, the_start_tag + at_start, text, 1)
    if at_end and end_tag:
        text = re.sub(the_end_tag, at_end + the_end_tag, text, 1)
    if new_first_word:
        text = re.sub(r"^(.*?)" + oldword, r"\1" + new_first_word, text, 1, re.DOTALL)
    if new_last_word:
        text = re.sub(oldword + r"(.*?)$", new_last_word + r"\1", text, 1, re.DOTALL)
    text = re.sub(oldword, newword, text)

    return text

#################

def argument_of_macro(text,mac,argnum=1):
    """Return the argument (without brackets) of the argnum
       argument of the first appearance of the macro \mac
       in text.

    """

    searchstring = r".*?" + r"\\" + mac + r"\b" + r"(.*)"
    # the ? means non-greedy, so it matches the first appearance of \\mac\b

    try:
        text_after = re.match(searchstring,text,re.DOTALL).group(1)
    except AttributeError:
        print "Error: macro " + mac + " not in text"
        return ""

    for _ in range(argnum):
        the_argument, text_after = first_bracketed_string(text_after)

    the_argument = strip_brackets(the_argument)

    return the_argument


