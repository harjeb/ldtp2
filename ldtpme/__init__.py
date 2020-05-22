#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu
'''
LDTP Made Easy:
Extend ldtp and make it more easy to manage objects.

The most interesting function here are getTree() and search(),
but it also wrap some existing ldtp functions, fixing some of their bizare behaviours.

objs parameters may be a single object (a string with '::'), or a list of objects [ 'obj1', 'obj2', ... ].

@package ldtp/ldtpme
@author: Jean-Jacques Brucker <jeanjacquesbrucker@gmail.com>

http://ldtp.freedesktop.org

'''

# Stuff for python3/python2 compatibility 
from __future__ import print_function
try:
    unicode
except NameError :
    unicode = str


# required modules
import ldtp
import re
#import time


# Set CurrentObjs to the main root
CurrentObjs=''

# Default deep for search() and getTree()
__DEEP=10
#ACTION_TEMPO=1

def getCurrentObjs():
    ''' Return Currents Objects stored in the global CurrentObjs '''
    return CurrentObjs


def setCurrentObjs(*objects):
    ''' Set the Current Objects (in CurrentObjs), used by other functions when None are specified. '''
    global CurrentObjs

    if len(objects) == 1 and type(objects[0]) in (str, unicode):
        CurrentObjs=objects[0]
        return 1

    r = []
    for o in objects:
        if type(o) in (str, unicode):
            r.append(o)
        elif type(o) is list:
            r += o
        else:
            raise Exception(__name__+' Error: objects should be some strings or some lists of strings')
    CurrentObjs=r
    return len(CurrentObjs)


def __checkObjs(o):
    ''' Internal function to check Objects parameter '''
    if o is None :
        o = CurrentObjs
    if type(o) in (str, unicode) :
        o = [o]
        is_str = 1
    elif type(o) is list :
        is_str = 0
    else :
        raise Exception(__name__+' Error: objs should be a string or a list of strings instead of '+str(type(objs)))
    return o, is_str


def __checkR(tab,rstr):
    ''' Internal function to return str or list depending on Objects parameter '''
    return tab[0] if rstr and len(tab)==1 else tab


def subContext(objs=None):
    ''' Extract the context part of an object string.
        If objs is None, it uses CurrentObjs. '''
    objs, rstr = __checkObjs(objs)
    r = []
    for o in objs:
        s=re.split('::',o)
        if len(s) > 2 :
            r.append( s[0]+'::'+s[1] )
        else:
            r.append(o)
    return __checkR(r,rstr)


def subBaseName(objs=None):
    ''' Extract the base name of an object string.
        If objs is None, it uses CurrentObjs. '''
    objs, rstr = __checkObjs(objs)
    r = []
    for o in objs:
        r.append( re.sub('.*::', '', o) )
    return __checkR(r,rstr)


def subApplication(objs=None):
    ''' Extract the top parent from an object string.
        If objs is None, it uses CurrentObjs. '''
    objs, rstr = __checkObjs(objs)
    r = []
    for o in objs:
        r.append( re.sub('::.*', '', o) )
    return __checkR(r,rstr)


def subParent(objs=None):
    ''' Extract the immediat parent from an object string.
        If objs is None, it uses CurrentObjs. '''
    objs, rstr = __checkObjs(objs)
    r = []
    for o in objs:
        r.append( re.sub('(.*)::.*', r'\1', o) )
    return __checkR(r,rstr)


def getTree(objs=None, deep=__DEEP, deepstart=0 ):
    ''' Return list of all available objects in a custom deep.
        If objs is None, it uses CurrentObjs, else result is stored in CurrentObjs.
        deep is relative to deepstart, and deepstart may be negative.'''
    if objs is None:
        setCurObjs=False
    else:
        global CurrentObjs
        setCurObjs=True
    objs, rstr  = __checkObjs(objs)
    while deepstart < 0 :
        objs=subParent(objs)
        deepstart += 1
    r = []
    if deepstart > 0:
        for o in objs :
            r += list(__yieldTreeObjects(o,deepstart,False))
        objs = r
        r = []
    for o in objs:
        if  deepstart > 0 or o == '' or isExisting(o):
        # if deepstart > 0 or if the object is the root, no need to do the heavier isExisting() check.
            r += list(__yieldTreeObjects(o,deep,True))
    if setCurObjs:
        CurrentObjs = r
    return r


def getLeaves(objs=None,deep=1):
    ''' Return list of all available objects in the given deep.
        If objs is None, it uses CurrentObjs.
        **deep** is relative to the objects's deep and may be negative'''
    return getTree(objs,deep=0,deepstart=deep)


def __yieldTreeObjects(obj,deep,withparent=True):
    ''' Internal recursive function used by getTree. '''
    if deep < 0 :
        return
    elif deep == 0 :
        if obj :
            yield obj
        return
    elif deep > 0 :
        if obj:
            ol = ldtp.getobjectlist(obj)
            if withparent :
                yield obj
        else:
            ol = ldtp.getapplist()
        for o in ol:
            for r in __yieldTreeObjects(o,deep-1,withparent):
                yield r


def printRoles(objs=None, deep=0, deepstart=0):
    ''' Print role of all available objects in a custom deep.
        If objs is None, it uses CurrentObjs. '''
    for o in getTree(objs,deep,deepstart):
        print("%-80s -> %s" %( o, getRole(o) ) )

def getRole(objs=None):
    ''' Return role of each objects.
        If objs is None, it uses CurrentObjs. '''
    objs, rstr = __checkObjs(objs)
    r = []
    for o in objs:
        s=re.split('::',o)
        if o == '' : # This is the root
            r.append('Root')
        elif len(s) == 2 : # This is a windows
            if o in ldtp.getwindowlist() : # Check if it exist
                r.append('Windows')
            else :
                r.append('')
        elif len(s) == 1 : # This is an application
            if o in ldtp.getapplist() : # Check if it exist
                r.append('Application')
            else :
                r.append('')
        else :
            r.append(ldtp.getobjectrole(subContext(o),o))
    return __checkR(r,rstr)

getRoles = getRole


def printStates(objs=None, deep=0, deepstart=0):
    ''' Print all states of all available objects in a custom deep.
        If objs is None, it uses CurrentObjs. '''
    for o in getTree(objs,deep,deepstart):
        print( "%-80s  -> %s" % (o, str(getStates(o)) ) )

def getStates(objs=None):
    ''' Return states of each objects.
        If objs is None, it uses CurrentObjs. '''
    objs, rstr = __checkObjs(objs)
    r = []
    for o in objs:
        if getRole(o) == 'Windows' :
            r.append(ldtp.getallstates(o))
        else :
            r.append( ldtp.getallstates(subContext(o),o) )
    return __checkR(r,rstr)


def printActions(objs=None, deep=0, deepstart=0):
    ''' Print possible actions for all available objects in a custom deep.
        If objs is None, it uses CurrentObjs. '''
    for o in getTree(objs,deep,deepstart):
        print( "%-80s  -> %s" % (o, str(getActions(o)) ) )

def getActions(objs=None):
    ''' Return possible actions for each objects.
        If objs is None, it uses CurrentObjs. '''
    objs, rstr = __checkObjs(objs)
    r = [ldtp.getactionslist(subContext(o),o) for o in objs]
    return __checkR(r,rstr)


def printProperties(objs=None, deep=0, deepstart=0):
    ''' Print all Properties of all available objects in a custom deep.
        If objs is None, it uses CurrentObjs. '''
    for o in getTree(objs,deep,deepstart):
        print( "%-80s  -> {" % o , end="" )
        for p in ldtp.getobjectpropertieslist(subContext(o),o):
            print( "'"+p+"':'" + ldtp.getobjectproperty(subContext(o),o,p) +"' " , end="")
        print("}")

def getProperties(objs=None):
    ''' Return all Properties (in a dictionary) for each objects.
        If objs is None, it uses CurrentObjs. '''
    objs, rstr = __checkObjs(objs)
    r = []
    for o in objs:
        dic = {}
        for p in ldtp.getobjectpropertieslist(subContext(o),o):
            dic[p]=ldtp.getobjectproperty(subContext(o),o,p)
        r.append( dic )
    return __checkR(r,rstr)

def search(basename = '.*', from_ = '', role = '.*', state = [], action = [], properties = {}, deep=__DEEP, deepstart=0, flags=0):
    ''' Search from specific objects in the Tree and store result in CurrentObjs.
        *from_* parameter may be an object or a list of objects.
        *basename*, *role* and properties elements are use as regular expressions.
        *state* and *action* may be a string, or a list of string. If a list is given, search for an object containing all items. 
        *flags* parameter are passed to re.search() and may be use for example to do insensitive case search. '''
    global CurrentObjs
    r = []
    for o in getTree(from_,deep,deepstart) :
        if not re.search(basename,subBaseName(o),flags):
            continue
        if not re.search(role,ldtp.getobjectrole(subContext(o),o),flags):
            continue
        if state :
            state, rstr = __checkObjs(state)
            sto = getStates(o)
            found = True
            for st in state :
                if not st in sto :
                    found=False
                    break
            if not found :
                continue
        if action :
            action, rstr = __checkObjs(action)
            aco = getActions(o)
            found = True
            for ac in action :
                if not ac in aco :
                    found=False
                    break
            if not found :
                continue
        if properties :
            pr=getProperties(o)
            found = True
            for key in properties.keys():
                if not ( key in pr.keys() and re.search(properties[key],pr[key],flags) ):
                    found=False
                    break
            if not found :
                continue
        r.append(o)
    CurrentObjs=r
    return r


def action(objs=None,action='click'):
    ''' Do specific action on given object(s).
        If objs is None, it uses CurrentObjs. '''
    objs, rstr = __checkObjs(objs)
    r = []
    for o in objs:
        r.append(ldtp.action(subContext(o),o,action))
    return __checkR(r,rstr)


def click(objs=None):
    ''' Action 'click' on given object(s).
        If objs is None, it uses CurrentObjs. '''
    return action(objs,'click')


def isShowing(objs=None):
    ''' Verify if object(s) are showing (visible for human eyes on screen).
        If objs is None, it uses CurrentObjs. '''
    objs, rstr = __checkObjs(objs)
    r = []
    for o in objs:
        r.append(True if 'showing' in getStates(o) else False)
    return __checkR(r,rstr)


def isExisting(objs=None):
    ''' Verify if the object(s) exist.
        If objs is None, it uses CurrentObjs. '''
    objs, rstr = __checkObjs(objs)
    r = []
    for o in objs:
        role = getRole(o)
        if role == 'Root' or role == 'Windows' or role == 'Application' :
            r.append(True)
        else :
            r.append(ldtp.objectexist(subContext(o),o))
    return __checkR(r,rstr)


def selectTab(objs=None):
    ''' select a "page tab" in a "page tab list".
        If objs is None, it uses CurrentObjs. '''
    objs, rstr = __checkObjs(objs)
    r = []
    for o in objs:
        #if getRole(o) == 'page tab' : #...
        r.append(ldtp.selecttab(subContext(o),subParent(o),o))
    return __checkR(r,rstr)


def imagecapture(window_name = '', out_file = None, x = 0, y = 0, width = -1, height = -1):
    '''
    Captures screenshot of the whole desktop or given window

    @param window_name: Window name to look for, either full name,
    LDTP's name convention, or a Unix glob.
    @type window_name: string
    @param x: x co-ordinate value
    @type x: integer
    @param y: y co-ordinate value
    @type y: integer
    @param width: width co-ordinate value
    @type width: integer
    @param height: height co-ordinate value
    @type height: integer

    @return: screenshot filename
    @rtype: string
    '''
    return ldtp.imagecapture(window_name=window_name,out_file=out_file,x=x,y=y,width=width,height=height)
