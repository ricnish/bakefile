#
#  This file is part of Bakefile (http://www.bakefile.org)
#
#  Copyright (C) 2012 Vaclav Slavik
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to
#  deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#  sell copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
#  IN THE SOFTWARE.
#

"""
Implementation of 'external' target type.
"""

from bkl.api import Extension, Property, TargetType, FileRecognizer
from bkl.vartypes import PathType
from bkl.error import Error, error_context
from bkl.plugins.vsbase import VSProjectBase

import xml.etree.ElementTree


class ExternalBuildHandler(Extension, FileRecognizer):
    """
    Extension type for handler of various external build systems.

    The methods are analogous to corresponding :class:`bkl.api.TargetType`
    methods.
    """

    def get_build_subgraph(self, toolset, target):
        raise NotImplementedError

    def vs_project(self, toolset, target):
        raise NotImplementedError


class ExternalTargetType(TargetType):
    """
    External build system.

    This target type is used to invoke makefiles or project files not
    implemented in Bakefile, for example to build 3rd party libraries.

    Currently, only Visual Studio projects are supported and only when using
    a Visual Studio toolset.
    """
    name = "external"

    properties = [
            Property("file",
                 type=PathType(),
                 inheritable=False,
                 doc="File name of the external makefile or project."),
        ]

    def get_build_subgraph(self, toolset, target):
        return self.get_handler(target).get_build_subgraph(toolset, target)

    def vs_project(self, toolset, target):
        return self.get_handler(target).vs_project(toolset, target)

    def get_handler(self, target):
        with error_context(target["file"]):
            return ExternalBuildHandler.get_for_file(target["file"].as_native_path_for_output(target))


# -----------------------------------------------------------------------
# Support for Visual Studio projects
# -----------------------------------------------------------------------

VS_NAMESPACES = {
    "ms": "http://schemas.microsoft.com/developer/msbuild/2003"
}

class VSExternalProjectBase(VSProjectBase):
    """
    Wrapper around externally-provided project file, base class.
    """
    def __init__(self, target):
        self.projectfile = target["file"]
        self.dependencies = []
        xmldoc = xml.etree.ElementTree.parse(self.projectfile.as_native_path_for_output(target))
        self.xml = xmldoc.getroot()


class VSExternalProject200x(VSExternalProjectBase):
    """
    Wrapper around VS 200{3,5,8} project files.
    """
    @property
    def version(self):
        v = self.xml.get("Version")
        if   v == "7.10": return 2003
        elif v == "8.00": return 2005
        elif v == "9.00": return 2008
        else:
            raise Error("unrecognized version of Visual Studio project %s: Version=\"%s\"",
                        self.projectfile, v)

    @property
    def name(self):
        return self.xml.get("Name")

    @property
    def guid(self):
        return self.xml.get("ProjectGUID")

class VSExternalProject201x(VSExternalProjectBase):
    """
    Wrapper around VS 2010/2011 project files.
    """
    @property
    def version(self):
        v = self.xml.get("ToolsVersion")
        if v == "4.0":
            return 2010
        else:
            raise Error("unrecognized version of Visual Studio project %s: ToolsVersion=\"%s\"",
                        self.projectfile, v)

    @property
    def name(self):
        # TODO-PY26: use "PropertyGroup[@Label='Globals']"
        return self.xml.findtext("ms:PropertyGroup/ms:RootNamespace", namespaces=VS_NAMESPACES)

    @property
    def guid(self):
        # TODO-PY26: use "PropertyGroup[@Label='Globals']"
        return self.xml.findtext("ms:PropertyGroup/ms:ProjectGuid", namespaces=VS_NAMESPACES)


class VisualStudioHandler(ExternalBuildHandler):
    """
    Support for external Visual Studio projects.
    """
    name = "visual-studio"

    extensions = ["vcproj", "vcxproj"]

    def get_build_subgraph(self, toolset, target):
        raise NotImplementedError # FIXME -- invoke msbuild on windows

    def vs_project(self, toolset, target):
        if target["file"].get_extension() == "vcxproj":
            prj_class = VSExternalProject201x
        else:
            prj_class = VSExternalProject200x
        return prj_class(target)