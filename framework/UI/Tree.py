#!/usr/bin/env python

class Node(object):
  def __init__(self, _id, parent=None, level=0, size=1):
    self.id = _id
    if parent is None:
      self.parent = self
    else:
      self.parent = parent
    self.level = level
    self.size = size
    self.children = []

  def addChild(self,_id, level=0, size=1):
    node = Node(_id,self,level,size)
    self.children.append(node)
    return node

  def getNode(self,_id):
    if _id == self.id:
      return self
    else:
      for child in self.children:
        node = child.getNode(_id)
        if node is not None:
          return node
      return None

  def getLeafCount(self, truncationSize=0, truncationLevel=0):
    if len(self.children) == 0:
      return 1

    count = 0
    for child in self.children:
      if child.level >= truncationLevel and child.size >= truncationSize:
        count += child.getLeafCount(truncationSize, truncationLevel)

    if count == 0:
      return 1

    return count

  def maximumChild(self):
    maxChild = None
    for child in self.children:
      if maxChild is None or maxChild.level < child.level:
        maxChild = child

    return maxChild


  def Layout(self,xoffset,width, truncationSize=0, truncationLevel=0):
    ids = [self.id]
    points = [(xoffset+width/2.,self.level)]
    edges = []

    totalCount = self.getLeafCount(truncationSize,truncationLevel)
    if totalCount > 0:

      myOffset = xoffset

      def cmp(a,b):
        if a.level > b.level:
          return -1
        return 1

      children = sorted(self.children, cmp=cmp)
      for child in children:
        if child.level >= truncationLevel and child.size >= truncationSize:
          edges.append((self.id,child.id))

          count = child.getLeafCount()
          myWidth = float(count)/totalCount*width
          (childIds,childPoints,childEdges) = child.Layout(myOffset,myWidth)
          ids.extend(childIds)
          points.extend(childPoints)
          edges.extend(childEdges)
          myOffset += myWidth
    return (ids,points,edges)