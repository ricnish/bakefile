#
#  This file is part of Bakefile (http://bakefile.sourceforge.net)
#
#  Copyright (C) 2003,2004 Vaclav Slavik
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License version 2 as
#  published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#  $Id$
#
#  Exceptions classes and errors handling code
#

import xmlparser

_readerContext = []

def pushCtx(desc):
    if isinstance(desc, xmlparser.Element):
        _readerContext.append('at %s' % desc.location())
    else:
        _readerContext.append(desc)

def popCtx():
    _readerContext.pop()

class ErrorBase(Exception):
    def __init__(self, desc):
        self.desc = desc
    def __str__(self):
        s = ''
        for ctx in range(len(_readerContext)-1,-1,-1):
            s += "    %s\n" % _readerContext[ctx]
        return s

class Error(ErrorBase):
    def __init__(self, desc):
        ErrorBase.__init__(self, desc)
    def __str__(self):
        return 'error: %s\n%s' % (self.desc, ErrorBase.__str__(self))

class ReaderError(ErrorBase):
    def __init__(self, el, desc):
        ErrorBase.__init__(self, desc)
        self.element = el
    def __str__(self):
        s = ''
        if self.element != None:
            loc = self.element.location()
            s += "%s: error: %s\n" % (loc, self.desc)
        else:
            s += "error: %s\n" % self.desc
        s += ErrorBase.__str__(self)
        return s