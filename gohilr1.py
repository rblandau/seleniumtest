#!/usr/bin/python

# gohilr.py
# Extract all HILR member biography pages for backup and transfer.   

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
 
from    NewTraceFac     import  NTRC,ntrace,ntracef
import  argparse
import  sys


@ntrace
def init_driver():
    ''' Allocate a Selenium driver. '''
    driver = webdriver.Firefox()
    driver.wait = WebDriverWait(driver, 10)
    return driver


@ntrace
def goto(driver, url):
    ''' Browse to a URL. '''
    driver.get(url)


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
 

@ntrace
def fnvHilrLogin(driver):
    ''' HILR login '''
    goto(driver, "http://hilr.dce.harvard.edu")
    buttonMemberLogin = driver.wait.until(EC.element_to_be_clickable(
        (By.LINK_TEXT, "Member Login")))
    driver.find_element_by_link_text("Member Login").click()

    buttonHarvardKey = driver.wait.until(EC.element_to_be_clickable(
        (By.ID, "HarvardKey")))
    driver.find_element_by_id("HarvardKey").click()
    driver.find_element_by_id("username").click()
    driver.find_element_by_id("username").send_keys(g.sLoginAcct)

    driver.find_element_by_id("password").click()
    if not g.sLoginPw:
        import getpass
        gotpw = getpass.getpass("Enter pw: ")
        print("Got pw, tnx.")
        driver.find_element_by_id("password").send_keys(gotpw)
    else:
        driver.find_element_by_id("password").send_keys(g.sLoginPw)
   
    driver.find_element_by_id("submitLogin").click()
    # Wait for the two-step authentication, if it is required this time.
    time.sleep(30)
    memberAnchor = driver.wait.until(EC.element_to_be_clickable(
            (By.LINK_TEXT, "Members")))


@ntrace
def fnvHilrMembersListAll(driver):
    ''' Go to Members|ListAll page. '''
    # Think I need to wait for the main page to appear before doing this.
    driver.find_element_by_link_text("Members").click()
    listallAnchor = driver.wait.until(EC.element_to_be_clickable(
            (By.LINK_TEXT, "List All")))
    driver.find_element_by_link_text("List All").click()
    time.sleep(30)


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
    # None today in this simplified version.  
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
    sLoginAcct = "landau@ricksoft.com"
    sLoginPw = 'z9Justl00k'


@ntrace
def fnlGetURLs(mysFilename):
    ''' Read file of URLs into list. '''
    with open(mysFilename, "r") as fhIn:
        lURLs = list(fhIn)
        return lURLs


@ntrace
def fntGetAllURLs(driver, mylUrls):
    ''' Retrieve pages for all  URLs, one at a time. '''
    nGotMany = 0
    sGotLast = None
    for sUrl in mylUrls:
        sGotLast = fnlGetOneURL(driver, sUrl)
        nGotMany += 1
        NTRC.ntrace(0, "proc getting url |%s|=|%s|" % (nGotMany, sUrl))
    return (nGotMany, sGotLast)


@ntrace
def fnlGetOneURL(driver, mysUrl):
    ''' Retrieve and save the page for a single URL. '''
    driver.get(mysUrl)
    
    memberDatum = driver.wait.until(EC.visibility_of_element_located(
        (By.XPATH, "//table[@class='tool-teaching-staff']")))
# TEMP sneak up on it
    memberNameElement = driver.find_element_by_xpath(
        "//table")                                          # OK
    memberNameElement = driver.find_element_by_xpath(
        "//table/descendant::th")                           # OK
    memberNameElement = driver.find_element_by_xpath(
        "//table//*[contains(text(),'Display name')]")      # OK
    memberNameElement = driver.find_element_by_xpath(
        "//table//*[contains(text(),'Display name')]/following-sibling::td")      
    memberName = memberNameElement.text
    NTRC.ntrace(0, "proc member|%s| from element|%s|" 
        % (memberName, memberNameElement))

    """
    # Hmmm.  Attempts to invoke the File|SaveAs dialog don't seem to work.
    driver.find_element_by_xpath('//body').send_keys("0x13")
    elementAboutFaces = driver.find_element_by_class_name('wrap')
    elementAboutFaces.click()
    elementAboutFaces.send_keys(chr(19))
    """
    
    sPage = driver.find_element_by_xpath("//body").text
    NTRC.ntrace(0, "proc page text /|%s| = |%s|" % (memberName, sPage))

    ### TEMP
    time.sleep(10)
    pass


@ntrace
def main():
    # Absorb file of all Member bio page URLs.
    lURLs = fnlGetURLs(g.sInputFile)
    # Login to HILR.
    fnvHilrLogin(driver)
#    fnvHilrMembersListAll(driver)
    # Get all the URLs in the list, saving each one.
    (nLastN, sLastName) = fntGetAllURLs(driver, lURLs)
    
    print("Done thru #%s = %s." % (nLastN, sLastName))
 
 
if __name__ == "__main__":
    g = CG()
    dCliDict = fndCliParse("")
    dCliDictClean = {k:v for k,v in dCliDict.items() if v is not None}
    g.__dict__.update(dCliDictClean)

    driver = init_driver()
    main()
    print("Yay!")
    time.sleep(10)

    # If we don't quit, the browser window will remain open.  
    driver.quit()

