# Copyright 2017 Battelle Energy Alliance, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Created on Sept 10, 2017

@author: alfoa
"""
from __future__ import division, print_function, unicode_literals, absolute_import
import warnings
warnings.simplefilter('default',DeprecationWarning)
if not 'xrange' in dir(__builtins__):
  xrange = range

import xml.etree.ElementTree as ET
import xml.dom.minidom
import os
import copy
from collections import OrderedDict
#from utils.utils import toBytes, toStrish, compare

class RAVENparser():
  """
    Import the RAVEN input as xml tree, provide methods to add/change entries and print it back
  """
  def __init__(self, inputFile):
    """
      Constructor
      @ In, inputFile, string, input file name
      @ Out, None
    """
    self.printTag  = 'RAVEN_PARSER'
    self.inputFile = inputFile
    if not os.path.exists(inputFile):
      raise IOError(self.printTag+' ERROR: Not found RAVEN input file')
    try:
      tree = ET.parse(file(inputFile,'r'))
    except ET.InputParsingError as e:
      raise IOError(self.printTag+' ERROR: Input Parsing error!\n' +str(e)+'\n')
    self.tree = tree.getroot()
    # do some sanity checks
    sequence = [step.strip() for step in self.tree.find('.//RunInfo/Sequence').text.split(",")]
    # firstly no multiple sublevels of RAVEN can be handled now
    for code in self.tree.findall('.//Models/Code'):
      if 'subType' not in code.attrib:
        raise IOError(self.printTag+' ERROR: Not found subType attribute in <Code> XML blocks!')
      if code.attrib['subType'].strip() == 'RAVEN':
        raise IOError(self.printTag+' ERROR: Only one level of RAVEN runs are allowed (Not a chain of RAVEN runs). Found a <Code> of subType RAVEN!')
    # find steps and check if there are active outstreams (Print)
    foundOutStreams = False
    for step in self.tree.find('.//Steps'):
      if step.attrib['name'] in sequence:
        for role in step:
          if role.tag.strip() == 'Output':
            mainClass, subType = role.attrib['class'].strip(), role.attrib['type'].strip()
            if mainClass == 'OutStreams' and subType == 'Print':
              foundOutStreams = True
              break
    if not foundOutStreams:
      raise IOError(self.printTag+' ERROR: at least one <OutStreams> of type "Print" needs to be inputted in the active Steps!!')
    # Now we grep the paths of all the inputs the SLAVE RAVEN contains in the workind directory.
    self.workingDir = self.tree.find('.//RunInfo/WorkingDir').text.strip()
    # Find the Files
    self.slaveInputFiles = []
    filesNode = self.tree.find('.//Files')
    if filesNode:
      for child in self.tree.find('.//Files'):
        subDirectory = child.attrib['subDirectory'] if 'subDirectory' in child.attrib else None
        if subDirectory:
          self.slaveInputFiles.append(os.path.join(subDirectory,child.text.strip()))
        else:
          self.slaveInputFiles.append(child.text.strip())

    print(self.slaveInputFiles)


  def printInput(self,rootToPrint,outfile=None):
    """
      Method to print out the new input
      @ In, rootToPrint, xml.etree.ElementTree.Element, the Element containing the input that needs to be printed out
      @ In, outfile, string, optional, output file root
      @ Out, None
    """
    xmlObj = xml.dom.minidom.parseString(ET.tostring(rootToPrint))
    inputAsString = xmlObj.toprettyxml()
    inputAsString = "".join([s for s in inputAsString.strip().splitlines(True) if s.strip()])
    if outfile==None:
      outfile =self.inputfile
    IOfile = open(outfile,'wb')
    IOfile.write(inputAsString)
    IOfile.close()
    # get location of input file
    dirName = os.path.dirname(outfile)
    # the dirName is actually in workingDir/StepName/prefix => we need to go back 2 dirs
    dirName = os.path.join(dirName,"../../")

#    # copy SLAVE raven files in case they are needed
#    for slaveInput in self.slaveInputFiles:
#      #fileDirName = os.path.dirname(slaveInput)
#      if os.pathsep in slaveInput:
#        components = slaveInput.split(os.pathsep)
#        # we have a directory to create (if does not exist)
#        for component in components:
#      os.path.join(dirName,slaveInput)
#      shutil.copy(inputFile.getAbsFile(),subSubDirectory)


  def modifyOrAdd(self,modiDictionary={},save=True, allowAdd = False):
    """
      modiDictionary a dict of dictionaries of the required addition or modification
      {"variableToChange":value }
      @ In, modiDictionary, dict, dictionary of variables to modify
            syntax:
            {'Node|SubNode|SubSubNode:value1','Node|SubNode|SubSubNode@attribute:attributeValue|SubSubSubNode':value2
                      'Node|SubNode|SubSubNode@attribute':value3}
             TODO: handle added XML nodes
      @ In, save, bool, optional, True if the original tree needs to be saved
      @ In, allowAdd, bool, optional, True if the nodes that are not found should be added (additional piece of input)
      @ Out, returnElement, xml.etree.ElementTree.Element, the tree that got modified
    """
    if save:
      returnElement = copy.deepcopy(self.tree)            #make a copy if save is requested
    else:
      returnElement = self.tree                           #otherwise return the original modified

    for node, value in modiDictionary.items():
      if "|" not in node:
        raise IOError(self.printTag+' ERROR: the variable '+node.strip()+' does not contain "|" separator and can not be handled!!')
      changeTheNode = True
      allowAddNodes, allowAddNodesPath = [], OrderedDict()
      if "@" in node:
        # there are attributes that are needed to locate the node
        splittedComponents = node.split("|")
        # check the first
        pathNode = './'
        attribName = ''
        for cnt, subNode in enumerate(splittedComponents):
          splittedComp = subNode.split("@")
          component = splittedComp[0]
          attribPath = ""
          attribConstruct = OrderedDict()
          if "@" in subNode:
            # more than an attribute locator
            for attribComp in splittedComp[1:]:
              attribValue = None
              if ":" in attribComp.strip():
                # it is a locator
                attribName  = attribComp.split(":")[0].strip()
                attribValue = attribComp.split(":")[1].strip()

                attribPath +='[@'+attribName+('="'+attribValue+'"]')

              else:
                # it is actually the attribute that needs to be changed
                # check if it is the last component
                if cnt+1 != len(splittedComponents):
                  raise IOError(self.printTag+' ERROR: the variable '+node.strip()+' follows the syntax "Node|SubNode|SubSubNode@attribute"'+
                                              ' but the attribute is not the last component. Please check your input!')
                attribName = attribComp.strip()
                attribPath +='[@'+attribName+']'
              if allowAdd:
                attribConstruct[attribName]  = attribValue
          pathNode += "/" + component.strip()+attribPath
          if allowAdd:
            if len(returnElement.findall(pathNode)) > 0:
              allowAddNodes.append(pathNode)
            else:
              allowAddNodes.append(None)
            #allowAddNodes.append(returnElement.findall(pathNode))
            allowAddNodesPath[component.strip()] = attribConstruct
        if pathNode.endswith("]"):
          changeTheNode = False
        else:
          changeTheNode = True
      else:
        # there are no attributes that are needed to track down the node to change
        pathNode = './/' + node.replace("|","/").strip()
        if allowAdd:
          pathNodeTemp = './/'
          for component in node.replace("|","/").strip():
            pathNodeTemp += component
            if len(returnElement.findall(pathNodeTemp)) > 0:
              allowAddNodes.append(pathNodeTemp)
            else:
              allowAddNodes.append(None)
            #allowAddNodes.append(returnElement.findall(pathNodeTemp))
            allowAddNodesPath[component.strip()] = None
      # look for the node with XPath directives
      foundNodes = returnElement.findall(pathNode)
      if len(foundNodes) > 1:
        raise IOError(self.printTag+' ERROR: multiple nodes have been found corresponding to path -> '+node.strip()+'. Please use the attribute identifier "@" to nail down to a specific node !!')
      if len(foundNodes) == 0 and not allowAdd:
        raise IOError(self.printTag+' ERROR: no node has been found corresponding to path -> '+node.strip()+'. Please check the input!!')
      if len(foundNodes) == 0:
        # this means that the allowAdd is true (=> no error message has been raised)
        indexFirstUnknownNode = allowAddNodes.index(None)
        getFirstElement = returnElement.findall(allowAddNodes[indexFirstUnknownNode-1])[0]
        for i in range(indexFirstUnknownNode,len(allowAddNodes)):
          nodeWithAttributeName = allowAddNodesPath.keys()[i]
          if not allowAddNodesPath[nodeWithAttributeName]:
            subElement =  ET.Element(nodeWithAttributeName)
          else:
            subElement =  ET.Element(nodeWithAttributeName, attrib=allowAddNodesPath[nodeWithAttributeName])
          getFirstElement.append(subElement)
          getFirstElement = subElement
        if changeTheNode:
          subElement.text = str(value).strip()
        else:
          subElement.attrib[attribConstruct.keys()[-1]] = str(value).strip()

      else:
        nodeToChange = foundNodes[0]
        pathNode     = './/'
        if changeTheNode:
          nodeToChange.text = str(value).strip()
        else:
          nodeToChange.attrib[attribName] = str(value).strip()
    if save:
      return returnElement

if __name__ == '__main__':
  parser = RAVENparser("/Users/alfoa/projects/raven_github/raven/tests/framework/test_redundant_inputs.xml")
  modifyDict = {'Distributions|Uniform@name:a_dist|lowerBound':-1,'RunInfo|batchSize':2,'Models|Code@name:py_script@subType:GenericCode|prepend':"Python"}
  lupo = parser.modifyOrAdd(modifyDict,allowAdd=False)
  modifyDict['Distributions|Normal@name:Andrea|mean'] = 22222
  modifyDict['Distributions|Normal@name:Andrea|sigma'] = 2
  parser.printInput(lupo,outfile="lupo1.xml")
  lupo2 = parser.modifyOrAdd(modifyDict,allowAdd=True)
  parser.printInput(lupo2,outfile="lupo2.xml")
