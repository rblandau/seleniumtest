#!/usr/bin/python
# python2 not 3

# gohilr.py
# Extract all HILR member biography pages for backup and transfer.  
# RBLandau 20170818

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
 
from    NewTraceFac     import  NTRC,ntrace,ntracef
import  argparse
import  sys
import  re
import  json
import  requests


# ==========================================================
# First, a few routines lifted from Selenium examples in the docs.

# i n i t _ d r i v e r 
@ntrace
def init_driver():
    ''' Allocate a Selenium driver. '''
    driver = webdriver.Firefox()
    driver.wait = WebDriverWait(driver, 15)
    #driver.implicitly_wait(15) 
    return driver


# g o t o 
@ntrace
def goto(driver, url):
    ''' Browse to a URL. '''
    driver.get(url)


# l o o k u p 
@ntrace
def lookup(driver, query):
    ''' Google lookup: enter query string and click search. '''
    try:
        box = driver.wait.until(EC.presence_of_element_located(
            (By.NAME, "q")))
        button = driver.wait.until(EC.element_to_be_clickable(
            (By.NAME, "btnK")))
        box.send_keys(query)
        button.click()
    except TimeoutException:
        print("Box or Button not found in google.com")
 

# ==========================================================
# Routines specific to HILR.

# f n v H i l r L o g i n 
@ntrace
def fnvHilrLogin(driver):
    ''' HILR login '''
    goto(driver, "http://hilr.dce.harvard.edu")
    buttonMemberLogin = driver.wait.until(EC.element_to_be_clickable(
        (By.LINK_TEXT, "Member Login")))
    driver.find_element_by_link_text("Member Login").click()
    # Fill out the login form, username first.
    buttonHarvardKey = driver.wait.until(EC.element_to_be_clickable(
        (By.ID, "HarvardKey")))
    driver.find_element_by_id("HarvardKey").click()
    driver.find_element_by_id("username").click()
    time.sleep(2)
    driver.find_element_by_id("username").send_keys(g.sLoginAcct)
    # Then password.  If there isn't one, ask the user interactively.
    driver.find_element_by_id("password").click()
    if not g.sLoginPw:
        import getpass
        gotpw = getpass.getpass("Enter pw: ")
        print("Got pw, tnx.")
        driver.find_element_by_id("password").send_keys(gotpw)
    else:
        driver.find_element_by_id("password").send_keys(g.sLoginPw)
    time.sleep(2)   # No, I'm not a robot who types too fast.
    driver.find_element_by_id("submitLogin").click()
    # Wait for the two-step authentication, if it is required this time.
    time.sleep(20)
    memberAnchor = driver.wait.until(EC.element_to_be_clickable(
            (By.LINK_TEXT, "Members")))


# f n v H i l r M e m b e r s L i s t A l l 
@ntrace
def fnvHilrMembersListAll(driver):
    ''' Go to Members|ListAll page. '''
    # Think I need to wait for the main page to appear before doing this.
    driver.find_element_by_link_text("Members").click()
    listallAnchor = driver.wait.until(EC.element_to_be_clickable(
            (By.LINK_TEXT, "List All")))
    driver.find_element_by_link_text("List All").click()


# ==========================================================
# C l i P a r s e 
@ntracef("CLI")
def fndCliParse(mysArglist):
    ''' Parse the mandatory and optional positional arguments, and the 
        many options for this run from the command line.  
        Return a dictionary of all of them.    
    '''
    sVersion = "0.0.1"
    cParse = argparse.ArgumentParser(description="Data Extractor "
        "for HILR Member Bio HTML pages", 
        epilog="Defaults for args as follows: "
        "(none), version=%s" % sVersion
        )
    # P O S I T I O N A L  arguments
    #cParse.add_argument('--something', type=, dest='', metavar='', help='')

    cParse.add_argument('sInputFile', type=str
                        , metavar='sINPUTFILE'
                        , help='file of member bio page URLs, one per line'
                        )
    # - - O P T I O N S
    cParse.add_argument("--nskip", type=int
                        , dest='nSkipAhead'
                        , metavar='nSKIPAHEAD'
                        , nargs='?'
                        , help='Number of URLs to skip over at the beginning '
                            'of the run.  Useful for restarting in the middle '
                            'of a long list.'
                        )
    """
    SAMPLE:
    cParse.add_argument("--ncopies", type=str
                        , dest='nCopies'
                        , metavar='nCOPIES'
                        , nargs='?'
                        , help='Number of copies in session.'
                        )
    """
    if mysArglist:          # If there is a specific string, use it.
        (xx) = cParse.parse_args(mysArglist)
    else:                   # If no string, then parse from argv[].
        (xx) = cParse.parse_args()
    return vars(xx)


# C G   c l a s s   f o r   g l o b a l   d a t a 
class CG(object):
    ''' Global data.
        Instantiate the class and access the instance's attributes.
    '''
    driver = None
    sInputFile = "bunchofurls.txt"
    sLoginFile = "hilrlogincreds.txt"
    sLoginAcct_default = "landau@ricksoft.com"
    sLoginAcct = None           # From external credentials file.
    sLoginPw = None             # From external credentials file.
    sSubdirForFiles = "./files"
    nSkipAhead = 0              # Nr of URLs to ignore at beginning of list.
    nWaitTimePerPage = 5        # Seconds after getting page.
    nWaitTimeAfterLoad = 2      # For page to be fully formatted.
    lFields = [                 # What fields to retrieve from page.
            "Display name", 
            "Email", 
            "First Name", 
            "Last Name", 
            "Photo", 
            "Phone", 
            "Address", 
            "City State Zip", 
            "Member Since", 
            "Current Status", 
            "Bio Information"
            ]
    dFields = None              # Will be dict to contain all fields and values.
    sOutputFormat = '''
Display name:       {Display name}
Email:              {Email}
First Name:         {First Name}
Last Name:          {Last Name}
Photo:              {Photo}
Phone:              {Phone}
Address:            {Address}
City State Zip:     {City State Zip}
Member Since:       {Member Since}
Current Status:     {Current Status}
Bio Information:    {Bio Information}
'''


# f n v G e t L o g i n C r e d e n t i a l s 
@ntrace
def fnvGetLoginCredentials():
    ''' Read login acct and pw from file, if there is one. 
        May be partial, i.e., acct only and not pw.  Or empty or absent.
    '''
    try:
        with open(g.sLoginFile, 'r') as fh:
            lLines = list(fh)
            lLines.extend(["", ""])     # Protect against empty file.
        g.sLoginAcct = lLines[0].strip() if lLines[0] else g.sLoginAcct_default
        g.sLoginPw = lLines[1].strip() if lLines[1] else None
    except IOError:                     # No file, use defaults.
        g.sLoginAcct = g.sLoginAcct_default
        g.sLoginPw = None
    NTRC.ntrace(0, "proc login creds acct|%s| pw|%s|" 
        % (g.sLoginAcct, '*'*len(g.sLoginPw)))


# ==========================================================
# General Selenium manipulations.

# f n l G e t U R L s T o L i s t 
@ntrace
def fnlGetURLsToList(mysFilename):
    ''' Read file of URLs into list. Filter blanks and comments. '''
    with open(mysFilename, "r") as fhIn:
        lURLs = [sLine for sLine in fhIn 
                if not (re.match("^\s*$", sLine) or re.match("^\s*#", sLine))]
        return lURLs


# f n t G e t A l l U R L s 
@ntrace
def fntGetAllURLs(driver, mylUrls):
    ''' Retrieve pages for all URLs, one at a time. '''
    # Keep track of the last one completed in case we have to restart.
    nGotMany = 0
    sGotLast = None
    for sUrl in mylUrls[int(g.nSkipAhead):]:
        sGotLast = fnlGetOneURL(driver, sUrl)
        nGotMany += 1
        NTRC.ntrace(3, "proc getting url |%s|=|%s|" % (nGotMany, sUrl))
    return (nGotMany, sGotLast)


# f n l G e t O n e U R L 
@ntrace
def fnlGetOneURL(driver, mysUrl):
    ''' Retrieve and save the page for a single URL. '''
    # Get page and wait for it to be fully rendered.
    driver.get(mysUrl)
    memberDatum = driver.wait.until(EC.visibility_of_element_located(
        (By.XPATH, "//table[@class='tool-teaching-staff']")))
    time.sleep(g.nWaitTimeAfterLoad)
    # Extract all field data from page and store in global dict.
    g.dFields = fndGetAllFields(driver)
    # Try to construct a sensible last-name-first name for this person.
    memberDisplayName = g.dFields["Display name"]
    if g.dFields["Last Name"]:
        memberName = ("%s %s" % (g.dFields["Last Name"], 
                g.dFields["First Name"])).replace(" ", "_").replace('"', '_')
    else:
        # Not possible; last name absent.  Use Display name.
        memberName = memberDisplayName
    NTRC.ntrace(3, "proc member|%s|" % (memberName))
    # Add non-field items to the collection of data.
    #sPageBody = driver.find_element_by_xpath("//body").text
    #g.dFields["PageBody"] = sPageBody
    # No good, gets only the text, not the HTML structure.
    # Get the entire ugly HTML, too?  Nah, too long and not informative.
    #sPageSource = driver.page_source
    #g.dFields["PageSource"] = sPageSource
    
    NTRC.ntrace(0, "proc getting |%-30s|    (%s)" % (memberName, memberDisplayName))
    fnsWriteMemberDataFile(driver, memberName)    
    fnsSaveMemberPicture(driver, memberName)
    ### TEMP  Maybe keep harvard.edu from thinking we are a robot.
    time.sleep(g.nWaitTimePerPage)
    return memberName


#  f n d G e t A l l F i e l d s 
@ntrace
def fndGetAllFields(driver):
    ''' Extract all field data from page, whether the data is there or not. '''
    dFields = dict()
    for sField in g.lFields:
        try:
            sXpath = ("//table//*[contains(text(),\'%s\')]"
                "/following-sibling::td" 
                % (sField))
            eField = driver.find_element_by_xpath(sXpath)
            sValue = eField.text
        except Exception:   # ignore """NoSuchElementException"""
            NTRC.ntrace(3, "proc err cannot find element|%s|" % (sXpath))
            sValue = ""
        dFields[sField] = sValue
    return dFields


# f n s W r i t e M e m b e r D a t a F i l e 
@ntrace
def fnsWriteMemberDataFile(driver, mysMemberName):
    ''' Extract all useful data from the page and save as JSON. '''
    #sOutput = fnsGentlyFormat(g.sOutputFormat, dFields)
    # BZZZT: Nope, string.format fails on non-ASCII characters.
    #  Escape the funny characters with json lib, and read them back.
    sOutput = json.dumps(g.dFields)
    g.dFields["SafeDict"] = sOutput
    #sFullOutput = fnsGentlyFormat(g.sOutputFormat, dFields)
    #g.dFields["FullOutput"] = sFullOutput
    sOutputFile = fnsPreventDuplicateFilename(mysMemberName, 
                g.sSubdirForFiles, "json")
    sOutput = json.dumps(g.dFields)
    with open(sOutputFile, "w") as fh:
        print >> fh, sOutput
    NTRC.ntrace(3, "proc output file|%s|=|%s|" % (sOutputFile, sOutput))        
    # DONE: Convert dictionary to JSON format.
    # DONE: Get URL of picture file.
    # TODO: Get picture file itself and save separately using member name.
    return sOutputFile


# f n s S a v e M e m b e r P i c t u r e 
@ntrace
def fnsSaveMemberPicture(driver, mysMemberName):
    ''' Find URL of photo, if there is one, and save it. '''
    # Find all the image tag elements:
    try:
        lImageTags = list(driver.find_elements_by_tag_name("img"))
        NTRC.ntrace(3, "proc 3 img elems len|%s| list|%s|" 
            % (len(lImageTags), lImageTags))
    except Exception:
        NTRC.ntrace(0, "proc Error: cannot find any imgs by tag_name|%s|" 
                % ("img"))
        raise
    # Find the src attributes of the img tags.
    lSrcUrls = list()
    for eImageTag in lImageTags:
        try:
            sImgSrc = eImageTag.get_attribute("src")
            NTRC.ntrace(3, "proc 4 img elem|%s| src=|%s|" % (eImageTag, sImgSrc))
        except Exception:
            NTRC.ntrace(1, "proc Error: cannot find img src by get_attribute of|%s|" 
                % (eImageTag))
        lSrcUrls.append(sImgSrc)
    # Which URL contains the picture we want?
    lPhotoUrl = [sUrl for sUrl in lSrcUrls if sUrl.find("icb.template") >= 0]
    # TODO: Get the actual jpg file instead of just the URL.
    #        I seem to be unable to do that in Firefox.  Maybe change to Chrome.
    sOutputFile = ""
    if lPhotoUrl:                   # if there is any picture...
        sSortofName = "%s_photourl" % (mysMemberName)
        sOutputFile = fnsPreventDuplicateFilename(sSortofName, 
                    g.sSubdirForFiles, "txt")
        with open(sOutputFile, 'w') as fh:
            sOutput = json.dumps(lPhotoUrl)
            print >> fh, sOutput

    # Now try to get the actual picture file.
    @ntrace
    def fnoGetReq(url, auth, *otherargs):
        rr = requests.get(url, auth=auth, *otherargs)
        return rr
    if lPhotoUrl:                   # if there is any picture...
        sPhotoUrl = lPhotoUrl[0]
        tAuthCreds = ("", "")
        tAuthCreds = (g.sLoginAcct, g.sLoginPw)
        oReqReturn = fnoGetReq(url=sPhotoUrl, auth=tAuthCreds)
        sPhotoMaybe = oReqReturn.content
        sSortofName = "%s_photo" % (mysMemberName)
        sOutputFile = fnsPreventDuplicateFilename(sSortofName, 
                    g.sSubdirForFiles, "png")
        sOutput = sPhotoMaybe
        with open(sOutputFile, 'w') as fh:
            sOutput = json.dumps(lPhotoUrl)
            print >> fh, sOutput

    return sOutputFile


# f n s P r e v e n t D u p l i c a t e F i l e n a m e 
@ntrace
def fnsPreventDuplicateFilename(mysMemberName, mysPrefixDir, mysTypeSuffix):
    sOutputFile = "%s/%s.%s" % (mysPrefixDir, mysMemberName, mysTypeSuffix)
    try:
        with open(sOutputFile, 'r'):
            sOutputFile = "%s/%s_2.%s" % (mysPrefixDir, mysMemberName, 
                        mysTypeSuffix)
    except IOError:
        pass
    return sOutputFile


# ==========================================================
# General function from long ago.

# f n s G e n t l y F o r m a t 
@ntrace
def fnsGentlyFormat(mysCmd, mydVals):
    '''
    Like string.format() but does not raise exception if the string
     contains a name request for which the dictionary does not have 
     a value.  Leaves unfulfilled name requests in place.  
    Method: construct a dictionary that contains something for every
     name requested in the string.  The value is either a supplied 
     value from the caller or a placeholder for the name request.  
     Then use the now-defanged string.format() method.
    This is way harder than it ought to be, grumble.  
    '''
    # Make a dictionary from the names requested in the string
    #  that just replaces the request '{foo}' with itself.  
    sReNames = '(:?\{([^\}]+)\})+'
    oReNames = re.compile(sReNames)
    lNameTuples = oReNames.findall(mysCmd)
    NTRC.ntracef(3,"FMT","proc gently tuples|%s|" % (lNameTuples))
    lNames = [x[1] for x in lNameTuples]
    dNames = dict(zip(lNames, map(lambda s: "{"+s+"}", lNames)))
    # Pick up any specified values in the global object 
    #  and from CLI args.
    dNames.update(dict(vars(CG)))
    dNames.update(dict(vars(g)))
    # And then add values from the specific instructions.
    dNames.update(mydVals)
    NTRC.ntrace(3,"proc gently dnames|%s|" % (dNames))
    sOut = mysCmd.format(**dNames)
    return sOut


# ==========================================================
# m a i n 
@ntrace
def main():
    # Absorb file of all Member bio page URLs.
    lURLs = fnlGetURLsToList(g.sInputFile)
    # Get external login credentials, if any.
    fnvGetLoginCredentials()
    # Login to HILR.
    fnvHilrLogin(driver)
    # Get all the URLs in the list, saving each one.
    (nLastN, sLastName) = fntGetAllURLs(driver, lURLs)
    print("Done thru #%s = %s." % (nLastN, sLastName))
 

# ==========================================================
# E n t r y   p o i n t 
if __name__ == "__main__":
    # Instantiate global singleton and read CLI params.
    g = CG()
    dCliDict = fndCliParse("")
    dCliDictClean = {k:v for k,v in dCliDict.items() if v is not None}
    g.__dict__.update(dCliDictClean)
    # Start Selenium-driven browser.
    driver = init_driver()
    main()
    #print("Yay!")
    time.sleep(10)
    # If we don't quit, the browser window will remain open.  
    driver.quit()


# Edit history:
# 
# 20170818  RBL Original version.  Managed to get some of the fields.
# 20170819  RBL Get all fields, even those that are absent on the page.
# 20170819  RBL Send output to file in JSON format, because string.format
#                fails on non-ASCII characters.
# 20170820  RBL Aha!  Use JSON to escape the non-ASCII characters, such as
#                typographic quotes (u'2018' and u'2019'), and then
#                format the data using the escaped version.
#                And put the full escaped dictionary, but unfortulately 
#                not the formatted version, back into JSON in the file.
#               Get the URLs of the photos and store them in separate files.
#                But how can I transfer the actual jpg files?
#               Externalize the login credentials to file.
# 20170821  RBL Reduce page wait time for production run.  Hope that 
#                Harvard doesn't look too closely.  
# 20170823  RBL Change filenames to lastname_firstname, and check
#                for and avoid possible duplicates.  One level of protection
#                suffices.
#               Have to reorganize taking data from the page to survive
#                craziness like a person with no Last Name or First Name
#                but only a Display name.  Who set up this mess?  Are there
#                any validity rules on this database?  
#               Also have to escape funny characters in names, e.g., 
#                quotation marks that otherwise mess up filenames.  
#
# 
