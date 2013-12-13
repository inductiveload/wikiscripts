"""
Script to present the labels of a WD item with taxon rank but not taxon 
name to the user to allow manual selection of the correct one

Released under the MIT license

    Author:     User:Inductiveload
"""

"""
NOTE 2013/12/13: This script uses WikidataQuery, which is a new feature of 
Pywikibot, as yet unmerged. Get this code from:

   https://gerrit.wikimedia.org/r/#/c/99642/
"""

import pywikibot
import pywikibot.data.query as pwq
import json
import re

PROPS = {'parent taxon' : 'P171',
    'taxon rank' : 'P105',
	'taxon name' : 'P225'
	}

class TaxonNamer():
    
    def __init__(self, skipTo):
        self.site = pywikibot.getSite('en')
        self.repo = self.site.data_repository()
        self.skipTo = int(skipTo)
        
    def getItems(self):
        
        q = pwq.Claim(105).AND(pwq.NoClaim(225))
        
        dat = pwq.WikidataQuery(cacheMaxAge=600).query(q)
        
        items = dat['items']
        
        print "Found %d items for query: %s\n" % (len(items), q)
        
        return items
        
    def go(self):
        
        items = self.getItems()
        
        for itemId in items:
            
            if itemId < self.skipTo:
                continue
        
            item = pywikibot.ItemPage(self.repo, 'Q' + str(itemId))
            
            try:
                item.get()
            except pywikibot.exceptions.NoPage:
                continue
                
            
            if item.claims and PROPS['taxon name'] in item.claims:
                taxonName = item.claims[PROPS['taxon name']][0].getTarget()
                print "%d\tThis item has a taxon name: %s" % (itemId, taxonName)
                continue
                
            if (item.claims and PROPS['taxon rank'] in item.claims 
                and not item.claims[PROPS['taxon rank']][0].getTarget()):
                    print("%d\tThis item doesn't take a taxon rank" % (itemId))
                    continue
            
            print itemId
            
            labels = {}
            for lang, lab in item.labels.iteritems():
                
                if lab not in labels:
                    labels[lab] = [lang]
                else:
                    labels[lab].append(lang)
                    
            for lab in labels:
                labStr = ("\03{lightpurple}%s\03{lightpurple}" if "en" in labels[lab] else "%s") % lab
                pywikibot.output("\t%s: %s" % (','.join(labels[lab]), labStr))
                
                
            
            defLang = None
            if "en" in item.labels:
                defLang = "en"
            else: # find one with no unicode - scientific names don't have them
                for l in item.labels:
                    if re.match("^[A-Za-z ]*$", item.labels[l]):
                        defLang = l
                        break;
                
            if defLang:
                default = " [%s: %s]" % (defLang, item.labels[defLang])
            else:
                default = ''
                
            try:
                lang = self.promptForLang(
                        prompt="(x to not use labels, y to skip item)\nUse label of lang ",
                        defaultVal=defLang, defaultPrompt=default, 
                        options=item.labels, abortVal='x', skipVal='y')
            except IOError:
                continue;
                
            name = None
            
            if lang:
                name = item.labels[lang]
                print "Setting from %s label: %s" % (lang, name)
                
            if name:
                self.addTaxonName(item, name)
            else:
                print "No name to add, skipping.."
                
            print "\n"

    def promptForLang(self, prompt, defaultVal, defaultPrompt, abortVal, skipVal, options):
            
        retry = False
        
        while True:
            
            p = prompt + u"%s: " % defaultPrompt
            
            if retry:
                p = (u"Unknown value '%s'. " % value) + p

            value = raw_input(p)
            
            if not value:
                value = defaultVal
                
            if value == skipVal:
                raise IOError
                
            if options and value not in options and value != abortVal:
                retry = True
                continue;
            
            break;
            
        if value == abortVal:
            value = None
            
        return value

    def addTaxonName(self, item, name):
        claim = pywikibot.Claim(self.repo, PROPS["taxon name"])
        
        claim.setTarget(name)
        
        item.addClaim(claim)
        
if __name__ == "__main__":
    
    args = pywikibot.handleArgs()
    
    print args
    newArgs = {}
    
    for a in args:
        if ":" in a and a.startswith('--'):
            b,c = a[2:].split(":")
            newArgs[b] = c
            
    print newArgs
    
    try:
        init = newArgs['skipto']
    except KeyError:
        init = 0
    
    tn = TaxonNamer(init)
    
    tn.go()
    
    

