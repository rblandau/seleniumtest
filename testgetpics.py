from selenium import webdriver
 
driver = webdriver.Firefox()
driver.get("http://isites.harvard.edu/icb/icb.do?keyword=hilrmembers&panel=icb.pagecontent351604%3ArlistAll%248%3FtemplateId%3D21372&pageid=icb.page175173&pageContentId=icb.pagecontent351604&view=viewBio.do&viewParam_bioUserId=AQR%2Ff05QlFZThAMI%0D%0A&viewParam_templateId=21372#a_icb_pagecontent351604")

elist = driver.find_elements_by_tag_name('img')
for idx in range(len(elist)):
    fname = "pic2%s.png" % (idx)
    with open(fname, 'w') as fh:
        print >> fh, elist[idx].screenshot_as_png


