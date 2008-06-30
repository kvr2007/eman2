#!/usr/bin/env python
#
# Author:  David Woolford 06/02/2008 (woolford@bcm.edu)
# Copyright (c) 2000-2008 Baylor College of Medicine
#
# This software is issued under a joint BSD/GNU license. You may use the
# source code in this file under either license. However, note that the
# complete EMAN2 and SPARX software packages have some GPL dependencies,
# so you are responsible for compliance with the licenses of these packages
# if you opt to use BSD licensing. The warranty disclaimer below holds
# in either instance.
#
# This complete copyright notice must be included in any revised version of the
# source code. Additional authorship citations may be added, but existing
# author citations must be preserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  2111-1307 USA
#
#

from EMAN2 import *
from time import time
from math import ceil
from copy import copy

class EMProjectDB:
	"""
	It's implemented as a singleton
	"""
	outputdir = "Boxerscratch"
	boxersdir = outputdir+"/"
	
	class __impl:
		""" Implementation of the singleton interface """

		def __init__(self):
			self.projectdb = shelve.open('.eman2projectdb','c',-1,True)

		#def __del__(self):
			#print "closing projectdb"
			#self.projectdb.close()
	# storage for the instance reference
		#def getAutoBoxers(self):
			#autoboxers = []
			#for i in self.projectdb.items():
				#if i[0][0:10] == "autoboxer_":
					#ab = self.projectdb[i[0]]
					#swarmAutoBoxer = SwarmAutoBoxer(None)
					#swarmAutoBoxer.become(ab)
					#autoboxers.append(
			
		def close(self):
			self.projectdb.close()
			
		def setKeyEntry(self,key,entry):
			self.projectdb[key]= entry
			self.projectdb.sync()
			
	__instance = None
	
	def __init__(self):
		""" Create singleton instance """
		# Check whether we already have an instance
		if EMProjectDB.__instance is None:
			# Create and remember instance
			EMProjectDB.__instance = EMProjectDB.__impl()
	
	def __getattr__(self, attr):
		""" Delegate access to implementation """
		return getattr(self.__instance.projectdb, attr)

	def __setattr__(self, attr, value):
		""" Delegate access to implementation """
		return setattr(self.__instance, attr, value)
	
	def setKeyEntry(self,key,entry):
		return self.__instance.setKeyEntry(key,entry)
	
class Box:
	CENTERACF = "centeracf"
	#CENTERALIGNINT = "cenlignint"
	CENTEROFMASS = "centerofmass"
	CENTERPROPAGATE = "centerpropagate"
	CENTERMETHODS = [CENTERACF,CENTERPROPAGATE,CENTEROFMASS]
	def become(self,trimbox):
		'''
		This is like a copy constructor
		'''
		self.xcorner = trimbox.xcorner			# the xcorner - bottom left
		self.ycorner = trimbox.ycorner			# the ycorner - bottom left
		self.xsize = trimbox.xsize				# the xsize of the box
		self.ysize = trimbox.ysize				# the ysize of the box
		self.isref = trimbox.isref				# a flag that can be used to tell if the box is being used as a reference
		self.changed = trimbox.changed			# a flag signalling the box has changed and display needs updatin
		self.isanchor = trimbox.isanchor		# a flag signalling the box has changed and display needs updatin
		self.TS = trimbox.TS
		self.imagename = trimbox.imagename
		self.ismanual = trimbox.ismanual
		
		self.moved = trimbox.moved
		self.origxcorner = trimbox.origxcorner
		self.origycorner = trimbox.origycorner
		
	def __init__(self,xcorner=-1,ycorner=-1,xsize=-1,ysize=-1,isref=0,correlationscore=0,imagename=None):
		self.xcorner = xcorner			# the xcorner - bottom left
		self.ycorner = ycorner			# the ycorner - bottom left
		self.xsize = xsize				# the xsize of the box
		self.ysize = ysize				# the ysize of the box
		self.isref = isref				# a flag that can be used to tell if the box is being used as a reference
		self.correlationscore = correlationscore	# the correlation score
		self.ismanual = False			# a flag to store whether or this box was manually added by the user and was not a reference. It's just a plain box
		
		self.optprofile = None			# a correlation worst-case profile, used for selective auto boxing
		self.changed = False			# a flag signalling the box has changed and display needs updating
		self.corx = -1			# stores the x coordinate of the correlation peak
		self.cory = -1			# stores the y coordinate of the correlation peak
		self.shape = None		# stores the shape used by the image2d widget
		self.image = None 		# stores the image itself, an emdata object
		self.r = 0.4			# RGB red
		self.g = 0.9			# RGB green
		self.b = 0.4			# RGB blue
		self.rorig = 0.4			# RGB red
		self.gorig = 0.9			# RGB green
		self.borig = 0.4			# RGB blue
		self.footprint = None	# stores the image footprint as an emdata object
		self.group = None		# stores a group, typically an int
		self.footprintshrink = 1
		self.isanchor = True		# A flag used by AutoBoxer routines that - if set to true the box will not be included in the generation the template) - This is specific to the SwarmPS autoboxer
		self.TS = None
		
		self.isdummy = False # this can be used to avoid parameters updates - i.e. when the user interactively changes parameters forcefully
		self.imagename = imagename
		
		self.moved = False
		self.origxcorner = -1
		self.origycorner = -1
		
	
	def setImageName(self,imagename):
		self.imagename = imagename
		
	def getImageName(self):
		return self.imagename
	
	def move(self,dx,dy):
		if self.moved == False:
			self.origxcorner = self.xcorner
			self.origycorner = self.ycorner
			self.moved = True
		
		self.xcorner += dx
		self.ycorner += dy
		
		if not self.ismanual:
			movedboxes = getKeyEntryIDD(self.imagename,"moved_boxes") # this may potentially be None
			
			if movedboxes == None:
				movedboxes = []
			
			found = False
			for data in movedboxes:
				if data[0] == self.origxcorner and data[1] == self.origycorner:
					data[2] = self.xcorner
					data[3] = self.ycorner
					found = True
					break
					
			if not found:
				movedboxes.append([self.origxcorner,self.origycorner,self.xcorner,self.xcorner])
			
			
			setKeyEntryIDD(self.imagename,"moved_boxes",movedboxes)
		
		self.changed = False
		self.updateBoxImage()

	def updatePositionFromDB(self,movedboxes):
		
		# 0.0064 = 0.08*0.08, then divided by two to make in terms of the radius
		# ... so the proximity limit is 8% of the radius
		sq_size_limit = (self.xsize**2 + self.ysize**2)*0.0032

		for data in movedboxes:
			sq_dif = (data[0] - self.xcorner)**2 + (data[1] - self.ycorner)**2
			if sq_dif < sq_size_limit:
				self.origxcorner = data[0]
				self.origycorner = data[1]
				self.xcorner = data[2]
				self.ycorner = data[3]
				self.changed = True
				self.moved = True
				self.updateBoxImage()
				return 1
		
		return 0
	
	def updateBoxImage(self,norm=True):
		bic = BigImageCache()
		image = bic.getImage(self.imagename)
		#print "getting region",self.xcorner,self.ycorner,self.xsize,self.ysize
		self.image = image.get_clip(Region(self.xcorner,self.ycorner,self.xsize,self.ysize))
		if norm:
			self.image.process_inplace("normalize.edgemean")
		
		# make sure there are no out of date footprints hanging around
		self.footprint = None
		
	def changeBoxSize(self,boxsize):
		'''
			Changes the boxsize if it really is different to that which is currently stored
			Release references to self.image and self.footprint so that they are generated next time
			they are asked for	
		'''
		if boxsize != self.xsize or boxsize != self.ysize:
			self.xcorner -= (boxsize-self.xsize)/2
			self.xsize = boxsize
			self.ycorner -= (boxsize-self.ysize)/2
			self.ysize = boxsize
			
			self.image = None
			self.footprint = None
			
	def getBoxImage(self,norm=True,force=False):
		bic = BigImageCache()
		image = bic.getImage(self.imagename)
		
		if self.image == None or force:
			if image == None:
				print 'error, need to specify the image argument when first calling getBoxImage'
			self.updateBoxImage(norm)
		return self.image
	
	def getSmallBoxImage(self,flattenradius,shrink):
		'''
		gets a shrunken version of the box by asking the database if the shrunken (entire) image
		exists and then clipping out from it
		'''
		image = self.getSmallImage(flattenradius,shrink)
		if image == None:
			return None
		else:
			return image.get_clip(Region(int(self.xcorner/shrink),int(self.ycorner/shrink),int(self.xsize/shrink),int(self.ysize/shrink)))
		
	def getSmallImage(self,flattenradius,shrink):
		
		cfImageCache = CFImageCache()
		return  cfImageCache.getImage(self.imagename, flattenradius,shrink)
		
	def getFLCFImage(self,flattenradius,shrink,template):
		
		cfimage = self.getSmallImage(flattenradius,shrink)
		cache = FLCFImageCache()
		
		return cache.getImage(self.imagename,cfimage,template)

	
	def getFootPrint(self,shrink=1):
		if self.footprint == None or shrink != self.footprintshrink:
			self.footprintshrink = shrink
			if self.image == None:
				print "error, you can not make a footprint if there is no image"
				exit(1)
			if shrink == 1:
				self.footprint = self.image.make_footprint()
			else :
				self.footprint = self.image.process("math.meanshrink",{"n":shrink}).make_footprint()
				
		return self.footprint
			
	def center(self,method,extrasomething,low_res=False):
		'''
		Ask the box to center itself using one of the available methods (as stored in Box.CENTERMETHODS
		extrasomething has to be an AutoBoxer if using CENTEROFMASS or CENTERACF (it's asked for getBestShrink)
		extrasomething has to be the template image and have the same dimensions as the results of getBoxImage if using 
		CENTERPROPOGATE
		The low_res argument has no effect on the CENTERPROPOGATE option
		'''
		if method not in Box.CENTERMETHODS:
			print "error, you called center using an unknown method:",method
			return 0
		
			
		if method == Box.CENTEROFMASS:
			if low_res == True:
				image = self.getSmallBoxImage(self.autoBoxer.getTemplateRadius(),self.autoBoxer.getBestShrink())
				ali = image.calc_center_of_mass()
				dx = -int((ali[0]+0.5-image.get_xsize()/2))*extrasomething.getBestShrink()
				dy = -int((ali[1]+0.5-image.get_ysize()/2))*extrasomething.getBestShrink()
			else:
				image = self.getBoxImage()
				ali = image.calc_center_of_mass()
				dx = -int((ali[0]+0.5-image.get_xsize()/2))
				dy = -int((ali[1]+0.5-image.get_ysize()/2))

		elif method == Box.CENTERACF:
			if low_res == True:
				image = self.getSmallBoxImage(self.autoBoxer.getTemplateRadius(),self.autoBoxer.getBestShrink())
				ccf  = image.calc_ccf(None)
				trans = ccf.calc_max_location_wrap(-1,-1,-1)
				dx = trans[0]/2*extrasomething.getBestShrink()
				dy = trans[1]/2*extrasomething.getBestShrink()
			else:
				image = self.getBoxImage()
				ccf  = image.calc_ccf(None)
				trans = ccf.calc_max_location_wrap(-1,-1,-1)
				dx = trans[0]/2
				dy = trans[1]/2
		
		elif method == Box.CENTERPROPAGATE:
			template = extrasomething
			image =self.getBoxImage()
			ccf  = image.calc_ccf(template)
			#sig = image.calc_fast_sigma_image(None)
			#ccf.div(sig)
			trans = ccf.calc_max_location_wrap(-1,-1,-1)
			dx = trans[0]
			dy = trans[1]
			
		#print "here we are",dx,dy
		
		self.xcorner += dx
		self.ycorner += dy
				
		# have to calculate offsets here
		if low_res == True and not method == Box.CENTERPROPAGATE:
			self.correctResolutionCentering(extrasomething.getBestShrink(),False)
	
		self.updateBoxImage()
		self.changed = True
		
		return 1
		
	def correctResolutionCentering(self,shrink,update=True):
		
		nx = self.getBoxImage().get_xsize()
		smallx = int(nx)/shrink
		ny = self.getBoxImage().get_ysize()
		smally = int(ny)/shrink
			
		difx = int(shrink*int(smallx/2.0+0.5)-int(nx/2.0+0.5))
		dify = int(shrink*int(smally/2.0+0.5)-int(ny/2.0+0.5))
		self.xcorner += difx
		self.ycorner += dify
		
		#print "correction",difx,dify
		
		if update and (difx != 0 or dify != 0):
			self.updateBoxImage()
			self.changed = True
			
	def updateParams(self,autoBoxer,center=False,force=False):
		'''
		Updates internally stored parameters, currently works only for SwarmAutoBoxer, but
		have attempted to lay basic framework if in future we use a different autoBoxer which
		requires its own parameters
		'''
		if self.isdummy:
			return 0
		
		correlation = self.getFLCFImage(autoBoxer.getTemplateRadius(),autoBoxer.getBestShrink(),autoBoxer.getTemplateObject())
		if correlation == None:
			print 'error, can not update the parameters of a Box because the Boxable has no correlation image'
			return 0
		
		if isinstance(autoBoxer,SwarmAutoBoxer):
			shrink = autoBoxer.getBestShrink()
			invshrink = 1/shrink
	
			# the central coordinates of the box in terms of the shrunken correlation image
			x = (self.xcorner+self.xsize/2.0)*invshrink
			y = (self.ycorner+self.ysize/2.0)*invshrink
			
			#the search radius is used in correlation space - it limits the radial distance
			# up to which 'profile' data can be accrued
			# it is currently half the boxsize in terms of the correlation image's dimensions
			searchradius = autoBoxer.getSearchRadius()
		
			peak_location = BoxingTools.find_radial_max(correlation,int(x),int(y),searchradius )
			peak_location2 = BoxingTools.find_radial_max(correlation,peak_location[0],peak_location[1],searchradius )
			if (peak_location != peak_location2):
				# this represents a troubling condition
				# setting box.correlationscore is the flag that other functions can act on in order to exclude
				# this box from consideration
				self.correlationscore = None
				if not force :
					print "Error, peak location unrefined"
					return 0
		
			# store the peak location
			self.corx = peak_location[0]
			self.cory = peak_location[1]
		
			# store the correlation value at the correlation max
			self.correlationscore = correlation.get(self.corx,self.cory)
		
			# store the profile
			self.optprofile = BoxingTools.get_min_delta_profile(correlation,self.corx,self.cory, searchradius )
			# center on the correlation peak
			if (center):
				self.xcorner = self.corx*shrink-self.xsize/2.0
				self.ycorner = self.cory*shrink-self.ysize/2.0
				self.changed = True
			
			return 1
			
		else:
			print 'error, the autoBoxer you are using is not currently known by the Box class'
			return 0
		
class TrimBox():
	'''
	A trimmed down version of a box
	'''
	def __init__(self,box):
		self.xcorner = box.xcorner			# the xcorner - bottom left
		self.ycorner = box.ycorner			# the ycorner - bottom left
		self.xsize = box.xsize				# the xsize of the box
		self.ysize = box.ysize				# the ysize of the box
		self.isref = box.isref				# a flag that can be used to tell if the box is being used as a reference
		self.changed = box.changed			# a flag signalling the box has changed and display needs updatin
		self.isanchor = box.isanchor		# a flag signalling the box has changed and display needs updatin
		self.TS = box.TS					# a time stamp flag
		self.imagename = box.imagename
		self.moved = box.moved
		self.origxcorner = box.origxcorner
		self.origycorner = box.origycorner
		self.ismanual = box.ismanual

class Cache:
	'''
	Provides a cache of static size (as defined by self.maxsize)
	As the cache grows objects are popped off the end of the self.cache tuple
	
	get the cache via getCache - iterate through it to find your object
	add to the cache via addToCache
	reset the size of the cache using setMaxSize
	'''
	def __init__(self):
		self.maxsize = 10
		self.cache = []

	def setMaxSize(self,size):
		'''
		Will resize the cache if it is current larger than the new maxsize
		'''
		if len(self.cache) > size:
			self.cache = self.cache[0:size]

		self.maxsize = size
		
	def addToCache(self,object):
		'''
		Add 
		'''
		oldcache = self.cache
		self.cache = [object]
		self.cache.extend(oldcache)
		if len(self.cache) > self.maxsize:
			self.cache.pop(self.maxsize)
			if len(self.cache) != self.maxsize:
				print "error, the caching mechanism is not working correctly"
				
	def getCache(self):
		return self.cache

class CFImageCache:
	'''
	A singleton - usef for caching coarsened-flattened images
	'''
	class __impl(Cache):
		""" Implementation of the singleton interface """

		def __init__(self):
			Cache.__init__(self)
			
		def getImage(self,imagename,flattenradius,shrink):
			cfImage = None
			# first see if the object is already stored
			for object in self.getCache():
				if object.getInputImageName() == imagename:
					cfImage = object
					break;
				
				
			if cfImage == None:
				# if we make it here the cfimage is not cached
				#print "had to cache a cf image for",imagename
				cfImage = CoarsenedFlattenedImage(imagename)
				self.addToCache(cfImage)
			#else: print "found a cached cf image for",imagename
				
			
			image = cfImage.getImageCarefully(flattenradius,shrink)
			if image != None:
				return image
			else:
				print "there was an error getting the image in CFImageCache"
				return None
		
		
	# storage for the instance reference	
	__instance = None

	def __init__(self):
		""" Create singleton instance """
		# Check whether we already have an instance
		if CFImageCache.__instance is None:
			# Create and remember instance
			CFImageCache.__instance = CFImageCache.__impl()
	
	def __getattr__(self, attr):
		""" Delegate access to implementation """
		return getattr(self.__instance, attr)

	def __setattr__(self, attr, value):
		""" Delegate access to implementation """
		return setattr(self.__instance, attr, value)

class CoarsenedFlattenedImage:
	def __init__(self,imagename):
		self.smallimage = None		# a small copy of an image which has had its background flattened
		self.imagename = imagename
		self.ouputimagename = EMProjectDB.boxersdir + strip_file_tag(self.imagename)+".cf.hdf"
		
		try:
			# we may have the image already on disk, if so parse it
			# the image on disk is likely up to date but not necessarily so
			self.smallimage = EMData(self.ouputimagename)
			#print "I read the image",self.ouputimagename
		except:
			#print "could not read", self.ouputimagename 
			pass
		
	def getInputImageName(self):
		return self.imagename
		
	def getCreationTS(self):
		return	self.smallimage.get_attr("creation_time_stamp")
	
	def getFlattenRadius(self):
		return self.smallimage.get_attr("flatten_radius")
	
	def getShrinkFactor(self):
		return self.smallimage.get_attr("shrink_factor")
	
	def __updateImage(self,flattenradius,shrink):
		'''
		Updates the image using the function arguments
		If they match current parameters than nothing happens - the correct image is already cached
		'''
		bic = BigImageCache()
		image = bic.getImage(self.imagename)

		self.smallimage = image.process("math.meanshrink",{"n":shrink})
		self.smallimage.process_inplace("filter.flattenbackground",{"radius":flattenradius})
			
		self.smallimage.set_attr("flatten_radius",flattenradius)
		self.smallimage.set_attr("shrink_factor",shrink)
		self.smallimage.set_attr("creation_time_stamp",gm_time_string())
		self.smallimage.write_image(self.ouputimagename)
				
		#else:
			#print "doing nothing to currently stored small image in CoarsenedFlattenedImage"
			
	def getImage(self):
		'''
		Should only be called if you know the stored image is up to date
		'''
		return self.smallimage
	
	
	def getImageCarefully(self,flattenradius,shrink):
		
		if self.smallimage == None or not self.paramsMatch(flattenradius,shrink):
			#print "regenerating cf image"
			self.__updateImage(flattenradius,shrink)
		#else: print "cf image is up to date"
		
		return self.getImage()
	
	def paramsMatch(self,flattenradius,shrink):
		try:
			if flattenradius != self.getFlattenRadius() or shrink != self.getShrinkFactor():
				return False
			else: return True
		except: return False # exception will be thrown if self.smallimage = None


class SigmaImageCache:
	class __impl(Cache):
		""" A cache for storing big images """

		def __init__(self):
			Cache.__init__(self)

	
		def getImage(self,imagename,flattenradius,shrinkfactor,forceupdate=False):
			# this loop takes care of things if the image is cached
			object = None
			for sigmaImage in self.getCache():
				if sigmaImage.getImageName() == imagename:
					object = sigmaImage
					break
				
			
			# if we make it here the image is not cached
			if object == None:
				#print "I am generating a big image in the cache for",imagename
				object = SigmaImage(imagename)
				self.addToCache(object)
			#else: print "I am returning a big image from the cache"
				
			return object.getImageCarefully(flattenradius,shrinkfactor,forceupdate)
			
			
	# storage for the instance reference
	__instance = None

	def __init__(self):
		""" Create singleton instance """
		# Check whether we already have an instance
		if SigmaImageCache.__instance is None:
			# Create and remember instance
			SigmaImageCache.__instance = SigmaImageCache.__impl()
	
	def __getattr__(self, attr):
		""" Delegate access to implementation """
		return getattr(self.__instance, attr)

	def __setattr__(self, attr, value):
		""" Delegate access to implementation """
		return setattr(self.__instance, attr, value)
	
	
class SigmaImage:
	def __init__(self,imagename):
		self.imagename = imagename
		self.image = None
	
	def getImageName(self):
		return self.imagename
	
	def getFlattenRadius(self):
		return self.image.get_attr("flatten_radius")
	
	def getShrinkFactor(self):
		return self.image.get_attr("shrink_factor")
	
	def __updateImage(self,flattenradius,shrinkfactor):
	
		cficache= CFImageCache()
		image = cficache.getImage(self.imagename,flattenradius,shrinkfactor)
		tmp = EMData(flattenradius*2,flattenradius*2)
		tmp.process_inplace("testimage.circlesphere")
		self.image = image.calc_fast_sigma_image(tmp)
		self.image.set_attr("flatten_radius",flattenradius)
		self.image.set_attr("shrink_factor",shrinkfactor)
		
		return self.image
	
	def getImageCarefully(self,flattenradius,shrinkfactor,forceupdate=False):
		
		action = False
		if forceupdate == True: action = True
		elif self.image == None: action = True
		elif flattenradius != self.getFlattenRadius() or shrinkfactor != self.getShrinkFactor(): action = True
		
		if action: self.__updateImage(flattenradius,shrinkfactor)
		
		return self.image

class BinaryCircleImageCache:
	'''
	A cache of white binary circles of a certain radius - used to make erasing fast
	Only ever stores these images in memory
	'''
	class __impl(Cache):
		""" A cache for storing big images """

		def __init__(self):
			Cache.__init__(self)

	
		def getImage(self,circleradius):
			# this loop takes care of things if the image is cached
			object = None
			for circleImage in self.getCache():
				if circleImage.getCircleRadius() == circleradius :
					object = circleImage
					break

			# if we make it here the image is not cached
			if object == None:
				#print "I am generating a big image in the cache for",imagename
				object = BinaryCircleImage(circleradius)
				self.addToCache(object)
			#else: print "I am returning a big image from the cache"
				
			return object.getImage()
			
	# storage for the instance reference
	__instance = None

	def __init__(self):
		""" Create singleton instance """
		# Check whether we already have an instance
		if BinaryCircleImageCache.__instance is None:
			# Create and remember instance
			BinaryCircleImageCache.__instance = BinaryCircleImageCache.__impl()
	
	def __getattr__(self, attr):
		""" Delegate access to implementation """
		return getattr(self.__instance, attr)

	def __setattr__(self, attr, value):
		""" Delegate access to implementation """
		return setattr(self.__instance, attr, value)
		

class BinaryCircleImage:
	def __init__(self,circleradius):
		self.image = EMData(2*circleradius+1,2*circleradius+1)
		self.image.process_inplace("testimage.circlesphere")
		self.image.set_attr("circle_radius",circleradius)
		self.image.write_image(EMProjectDB.boxersdir +"circle"+str(circleradius)+".hdf")

	def getCircleRadius(self):
		return self.image.get_attr("circle_radius")
	
	def getImage(self):
		return self.image

class BigImageCache:
	class __impl(Cache):
		""" A cache for storing big images """

		def __init__(self):
			Cache.__init__(self)
			self.setMaxSize(4)

	
		def getImage(self,imagename):
			# this loop takes care of things if the image is cached
			object = None
			for bigImage in self.getCache():
				if bigImage.getImageName() == imagename:
					object = bigImage
					break
				
			
			# if we make it here the image is not cached
			if object == None:
				#print "I am generating a big image in the cache for",imagename
				object = BigImage(imagename)
				self.addToCache(object)
			#else: print "I am returning a big image from the cache"
				
			return object.getImage()
			
	# storage for the instance reference
	__instance = None

	def __init__(self):
		""" Create singleton instance """
		# Check whether we already have an instance
		if BigImageCache.__instance is None:
			# Create and remember instance
			BigImageCache.__instance = BigImageCache.__impl()
	
	def __getattr__(self, attr):
		""" Delegate access to implementation """
		return getattr(self.__instance, attr)

	def __setattr__(self, attr, value):
		""" Delegate access to implementation """
		return setattr(self.__instance, attr, value)
	
class BigImage:
	def __init__(self,imagename):
		self.imagename = imagename
		self.image = None
	
	def getImageName(self):
		return self.imagename
	
	def getImage(self):
		if self.image == None:
			self.image = EMData(self.imagename)
			self.image.process_inplace("normalize.edgemean") # this seams to be the normal behavior
			
		return self.image

class FLCFImageCache:
	'''
	A singleton - used for caching flcf images
	'''
	class __impl(Cache):
		""" Implementation of the singleton interface """

		def __init__(self):
			Cache.__init__(self)


		def getImage(self,imagename,cfimage,template):
			
			flcfImage = None
			# first see if the object is already stored
			for object in self.getCache():
				if object.getInputImageName() == imagename:
					flcfImage = object
					break;
				
				
			if flcfImage == None:
				# if we make it here the flcfimage is not cached
				#print "generated flcf for",imagename
				flcfImage = FLCFImage(imagename)
				self.addToCache(flcfImage)
			#else: print "found flcf for",imagename
				
			
			image = flcfImage.getImageCarefully(cfimage,template)
			if image != None:
				return image
			else:
				print "there was an error getting the image"
				return None
		
		# storage for the instance reference	
	__instance = None

	def __init__(self):
		""" Create singleton instance """
		# Check whether we already have an instance
		if FLCFImageCache.__instance is None:
			# Create and remember instance
			FLCFImageCache.__instance = FLCFImageCache.__impl()
	
	def __getattr__(self, attr):
		""" Delegate access to implementation """
		return getattr(self.__instance, attr)

	def __setattr__(self, attr, value):
		""" Delegate access to implementation """
		return setattr(self.__instance, attr, value)



class FLCFImage:
	def __init__(self,imagename):
		self.flcfimage = None	# this is the flcf image
		self.imagename=imagename # we must store this it's used externally to determine if the FLCFImage is cached
		self.outputimagename = EMProjectDB.boxersdir + strip_file_tag(imagename)+".flcf.hdf"
		
		
		try: # try to read the image from disk - it may already exist and save us lots of time
			self.flcfimage = EMData(self.outputimagename)
		except:
			# the image doesn't exist, that's okay
			pass
		
	def paramsMatch(self,cfimage,template):
		#print cfimage.get_attr("creation_time_stamp"), self.getCfiTS(),"template",template.getTemplateTS(),self.getTemplateTS()
		try:
			if cfimage.get_attr("creation_time_stamp") != self.getCfiTS() or template.getTemplateTS() != self.getTemplateTS():
				#print "params did not match"
				return False
			else: return True
		except: return False
	
	def getInputImageName(self):
		return self.imagename
	
	def getOutputImageName(self):
		return self.outputimagename
	
	def getTemplateTS(self):
		'''
		get template time stamp
		'''
		return self.flcfimage.get_attr("template_time_stamp")
	def getCfiTS(self):
		'''
		get cfi time stamp
		Cfi = coarsened flattened image
		'''
		return self.flcfimage.get_attr("data_image_time_stamp")
		
	def getImage(self):
		'''
		Returns the currently stored flcfimage
		'''
		return self.flcfimage
	
	def __updateImage(self,cfimage,template):

		sicache = SigmaImageCache()
		sigmaImage = sicache.getImage(self.imagename,cfimage.get_attr("flatten_radius"),cfimage.get_attr("shrink_factor"))
		
		self.flcfimage = cfimage.calc_ccf( template.getTemplate() )
		self.flcfimage.div(sigmaImage)
		self.flcfimage.process_inplace("xform.phaseorigin.tocenter")
		self.flcfimage.set_attr("template_time_stamp",template.getTemplateTS())
		val = cfimage.get_attr("creation_time_stamp")
		self.flcfimage.set_attr("data_image_time_stamp",val)
		self.flcfimage.write_image(self.outputimagename)
		
		
	def getImage(self):
		return self.flcfimage
	
	def getImageCarefully(self,cfimage,template):
		'''
		Checks to see if the arguments are the right types
		Then checks to see if the currently store correlation image is up to date
		If it's not up to date or it doesn't exist then it is (re)generated
		Then it is returned
		'''
		
		if not isinstance(cfimage,EMData):
			print "you can't call genFLCF on the cfimage is not an EMData"
			return None
			
		if not isinstance(template,SwarmTemplate) and not isinstance(template,TrimSwarmTemplate):
			print "you can't call genFLCF on an object that is not a SwarmTemplate"
			return None
		
		action = False
		if self.flcfimage != None:
			if not self.paramsMatch(cfimage,template):
				action = True
		else: action = True
		
		if action:
			#print "generating correlation image"
			self.__updateImage(cfimage,template)
		#else: print "returning cached correlation image"
		return self.getImage()

class Boxable:
	UNERASE = 'Unerase'
	ERASE = 'Erase'
	
	GREAT = '4 - Excellent'
	GOOD = '3'
	AVERAGE = '2 - Average'
	POOR = '1'
	EXCLUDE = '0 - Exclude'
	QUALITY_META_DATA = [EXCLUDE,POOR,AVERAGE,GOOD,GREAT]
	QUALITY_META_DATA_MAP = {}
	QUALITY_META_DATA_MAP[EXCLUDE] = 0
	QUALITY_META_DATA_MAP[POOR] = 1
	QUALITY_META_DATA_MAP[AVERAGE] = 2
	QUALITY_META_DATA_MAP[GOOD] = 3
	QUALITY_META_DATA_MAP[GREAT] =  4
	
	def __init__(self,imagename,parent,autoBoxer=None):
		self.parent = parent		# keep track of the parent in case we ever need it
		self.boxes = []				# a list of boxes
		self.refboxes = []			# a list of boxes
		self.boxsize = -1			#  the boxsize
		self.imagename = imagename
		
		self.fpshrink = -1
		self.exclusionimage = None
		self.template = None
		self.correlation = None
		self.refcache = []
		self.allowcorrelationupdate = False	# a temporary flag that can be used by externally objects, for instance a reference box, which is forcing an update for example
		self.templateTS = -1 # a template time stamp, used to avoid unecessarily regenerating the template in self.autoBox
		self.autoBoxerStateTS = -1 # and autoBoxer time stamp, used to avoid unecessary autoboxing, and to force autoboxing when appropriate
		self.autoBoxerID = -1 # Stores the unique ID of the autoboxer - this is to facilitate having many autoboxers in the project data base
		
		self.autoBoxer = autoBoxer
		self.__frozen = False
		self.__quality = Boxable.QUALITY_META_DATA_MAP[Boxable.AVERAGE] # this makes it the number, not the string
		
		try:
			excimagename = EMProjectDB.boxersdir + strip_file_tag(self.imagename)+".exc.hdf"
			self.exclusionimage = EMData(excimagename)
		except: pass
		
		try: 
			self.getAutoSelectedFromDB(True)
		except: pass # this probably means there is a projectdb but it doesn't store any autoboxing results from this image
		try:
			self.getDBTimeStamps()
		except: pass
		try:
			self.getManualFromDB()	
		except: pass
		try:
			self.getReferencesFromDB()	
		except: pass
		try:
			self.getFrozenFromDB()	
		except: pass
		try:
			self.getQualityFromDB()	
		except: pass
		try:
			self.checkAndStoreImageTagInDB()	
		except: pass
		try:
			if autoBoxer == None:
				self.getAutoBoxerFromDB()
		except: pass
	
	def clearAndCache(self,keepmanual=False):
		self.boxes = []
		
		projectdb = EMProjectDB()
		try:
			data = projectdb[self.getDDKey()]
		except:
			data = {}
		
		data["reference_boxes"] = []
		data["autoboxed"] = []
		
		
		if keepmanual:
			self.getManualFromDB()
		else :
			data["manual_boxes"] = []
	
	
		projectdb.setKeyEntry(self.getDDKey(),data)
	def clearAndReloadImages(self):
		self.boxes = []
		try: 
			self.getAutoSelectedFromDB(True)
		except: pass # this probably means there is a projectdb but it doesn't store any autoboxing results from this image
		try:
			self.getManualFromDB()	
		except: pass
		try:
			self.getReferencesFromDB()	
		except: pass
		
	def cacheExcToDisk(self):
		if self.exclusionimage != None:
			excimagename = EMProjectDB.boxersdir + strip_file_tag(self.imagename)+".exc.hdf"
			self.exclusionimage.write_image(excimagename)

	def center(self,method):
		if method == Box.CENTERACF or method == Box.CENTEROFMASS:
			extrasomething = self.autoBoxer
		elif method == Box.CENTERPROPAGATE:
			extrasomething = self.autoBoxer.getHighResTemplateImage()
		else:
			print "error, the method you specified is unsupported in Boxable:",method
		
		for box in self.boxes:
			if not box.center(method,extrasomething,False):
				print "there was an error boxing"
				return 0
				
		return 1

	def setStamps(self,autoBoxerStateTS,templateTS,autoboxer_unique_id):
		'''
		A convenience function for setting all three important time stamps/ids at once
		
		'''
		self.setAutoBoxerStateTS(autoBoxerStateTS)
		self.setTemplateTS(templateTS)
		self.setAutoBoxerID(autoboxer_unique_id)

	def getAutoBoxerStateTS(self):
		return self.autoBoxerStateTS
	
	def setAutoBoxerStateTS(self,autoBoxerStateTS):
		self.autoBoxerStateTS = autoBoxerStateTS
	
	def getTemplateTS(self):
		return self.templateTS
	
	def setTemplateTS(self,templateTS):
		self.templateTS = templateTS

	def getAutoBoxerID(self):
		return self.autoBoxerID
	
	def setAutoBoxerID(self,autoboxer_unique_id):
		self.autoBoxerID = autoboxer_unique_id
	
	def writeToDB(self):
		'''
		Writes fundamentally important information to the database
		'''
		projectdb = EMProjectDB()
		
		try:
			data = projectdb[self.getDDKey()]
		except:
			data = {}
			
		data["auto_boxer_state_TS"] = self.getAutoBoxerStateTS()
		data["template_TS"] = self.getTemplateTS()
		data["frozen_state"] = self.__frozen
		data["quality"] = self.__quality
		data["auto_boxer_unique_id"] = self.getAutoBoxerID()
		
		projectdb.setKeyEntry(self.getDDKey(),data)
	
	def setKeyEntryToIDD(self,key,object):
		setKeyEntryIDD(self.imagename,key,object)
		
	def getImageName(self):
		return self.imagename
	
	def setAutoBoxer(self,autoBoxer):
		self.autoBoxer = autoBoxer
		
	def getCorrelation(self):
		return self.correlation
	
	def extendBoxes(self,boxes):
		self.boxes.extend(boxes)
		
	def isFrozen(self):
		return self.__frozen
	
	def isInteractive(self):
		return not (self.isFrozen() or self.isExcluded())
	
	def toggleFrozen(self):
		self.__frozen = not self.__frozen
		
	def setFrozen(self,frozen):
		self.__frozen = frozen
	
	
	def getDDKey(self):
		'''
		Get Database Dictionary Key
		'''
		return getIDDKey(self.imagename)
	
	def getAutoBoxerFromDB(self):
		
		projectdb = EMProjectDB()
		data = projectdb[self.getDDKey()]
		self.autoBoxerID = data["auto_boxer_unique_id"]
		trimAutoBoxer = projectdb[self.autoBoxerID]
		self.autoBoxer = SwarmAutoBoxer(self.parent)
		self.autoBoxer.become(trimAutoBoxer)
		
	def setQuality(self,quality):
		if quality not in Boxable.QUALITY_META_DATA:
			print "error",quality,"is not in",Boxable.QUALITY_META_DATA,"can't do anything"
			return
		else:
			self.__quality =  Boxable.QUALITY_META_DATA_MAP[quality]
	
	def isExcluded(self):
		return self.__quality == Boxable.QUALITY_META_DATA_MAP[Boxable.EXCLUDE]
	
	def getQuality(self):
		return self.__quality
		
	def checkAndStoreImageTagInDB(self):
		#print "in cheack and Store image tag in db"
		projectdb = EMProjectDB()
		data = projectdb[self.getDDKey()]
		newimagetag = get_file_tag(self.imagename)
		try:
			oldimagetag = data["image_tag"]
		except:
			#print "stored image tag for first time"
			data["image_tag"] = newimagetag
			projectdb.setKeyEntry(self.getDDKey(),data)
			return
		
		if oldimagetag != newimagetag:
			#print "warning with respect to",self.imagename,"- you are using information in the database that was generated using an image of type",newimagetag,"on an image of type",oldimagetag,". This will potentially cause problems if the images are not equivalent. Suggest renaming the image or boxing it in a separate directory"
			return
		else:
			#print "storing image tag"
			data["image_tag"] = newimagetag
			projectdb.setKeyEntry(self.getDDKey(),data)

		
	def getQualityFromDB(self):
		projectdb = EMProjectDB()
		data = projectdb[self.getDDKey()]
		self.__quality = data["quality"]
		
	def getFrozenFromDB(self):
		projectdb = EMProjectDB()
		data = projectdb[self.getDDKey()]
		self.__frozen = data["frozen_state"]
		
	def getDBTimeStamps(self):
		
		projectdb = EMProjectDB()
		data = projectdb[self.getDDKey()]
		self.autoBoxerStateTS = data["auto_boxer_state_TS"]
		self.templateTS = data["template_TS"] 
		self.autoBoxerID = data["auto_boxer_unique_id"]
	
	def appendStoredAutoBoxes(self,trimboxes):
		'''
		Sometimes this functionality is needed when the currently stored auto-selected
		boxes are not removed prior to the execution of autoboxing - in this case 
		the autoboxes stored in the database need to include what was already stored...
		'''
		for box in self.boxes:
			if not (box.ismanual or box.isref):
				trimboxes.append(TrimBox(box))
	
	def getAutoSelectedFromDB(self,forcereadall=False):	
		
		trimboxes = getKeyEntryIDD(self.imagename,"auto_boxes")
		if trimboxes == None or len(trimboxes) == 0:
			return 0
		
		movedboxes = getKeyEntryIDD(self.imagename,"moved_boxes") # this may potentially be None
		
		for trimbox in trimboxes:
			if trimbox.ismanual or trimbox.isref:
				print "error, the box was manual or it was a reference"
				continue
			if trimbox.changed or forcereadall:
				box = Box()
				
				# had to do conversion stuff so pickle would work
				box.become(trimbox)
				box.setImageName(self.imagename)
				if forcereadall:
					box.changed = True
				if box.isref and not forcereadall:
					continue;
				elif box.isref:
					box.rorig = 0			# RGB red
					box.gorig = 0			# RGB green
					box.borig = 0			# RGB blue
					box.r = 0
					box.g = 0
					box.b = 0
				
				# The box may have a more correct centering
				if movedboxes != None and len(movedboxes) != 0:
					box.updatePositionFromDB(movedboxes)
				self.boxes.append(box)
		
		# Sometimes an exclusion area is added after the autoboxing has occured, in which case
		# autoboxes in the db will be in the excluded area and hence we have to make sure they 
		# are not included
		self.updateExcludedBoxes()	
		
		#print "Added",len(self.boxes)-a," autoboxes"
	
	def getReferencesFromDB(self):
		#debug
		#a = len(self.boxes)
		
		refboxes = getKeyEntryIDD(self.imagename,"reference_boxes")
		if refboxes == None or len(refboxes) == 0:
			return 0
		
		movedboxes = getKeyEntryIDD(self.imagename,"moved_boxes") # movedboxes is potentially None
		
		for trimbox in refboxes:
			box = Box()
			
			# had to do conversion stuff so pickle would work
			box.become(trimbox)
			box.setImageName(self.imagename)
			box.changed = True
			box.rorig = 0			# RGB red
			box.gorig = 0			# RGB green
			box.borig = 0			# RGB blue
			box.r = 0
			box.g = 0
			box.b = 0
			
			# The box may have a more correct centering
			if movedboxes != None and len(movedboxes) != 0:
				box.updatePositionFromDB(movedboxes)
			self.boxes.append(box)

		#print "Added",len(self.boxes)-a," references"
	def getManualFromDB(self):
		#a = len(self.boxes) # debug		
		manualboxes = getKeyEntryIDD(self.imagename,"manual_boxes")
		if manualboxes == None or len(manualboxes) == 0:
			return 0
	
		for trimbox in manualboxes:
			box = Box()
			
			# had to do conversion stuff so pickle would work
			box.become(trimbox)
			box.setImageName(self.imagename)
			box.changed = True
			box.rorig = 1			# RGB red
			box.gorig = 1			# RGB green
			box.borig = 1			# RGB blue
			box.r = 1
			box.g = 1
			box.b = 1
			self.boxes.append(box)
		#print "Added",len(self.boxes)-a," manual boxes"

	def getCoordFileName(self):
		return strip_file_tag(self.imagename)+".box"
		
	def writecoords(self,boxsize=-1,force=False,verbose=True):
		'''
		If boxsize is -1 then the current boxsize is used to write output
		If force is True then the old file with the same name is written over (as opposed to backed up)
		
		'''
		if len(self.boxes) == 0:
			print "no boxes to write, doing nothing. Image name is",self.imagename
		else:
			boxname = self.getCoordFileName()
			if file_exists(boxname):
				if not force:
					f=file(boxname,'r')
					boxname_backup =  strip_file_tag(self.imagename)+str(time()) + ".box.bak"
					print "warning, found box name",boxname,"- am renaming it to", boxname_backup, "- use force to overwrite this behavior"
					fbak=file(boxname_backup,'w')
					fbak.writelines(f.readlines())
					fbak.close()
					f.close()
				else:
					remove_file(boxname)
				
			f=file(boxname,'w')
			
			if verbose: print "writing",self.numBoxes(),"box coordinates to file",boxname
			
			for box in self.boxes:
				if boxsize != -1:
					# FOO - this will not work if the box dimensions are not equal...
					origboxsize = box.xsize
					if origboxsize != box.ysize:
						print "error, uniform box dimensions are not supported"
						return
					box.changeBoxSize(boxsize)
						
				f.write(str(int(box.xcorner))+'\t'+str(int(box.ycorner))+'\t'+str(box.xsize)+'\t'+str(box.ysize)+'\n')
				
				if boxsize != -1:
					box.changeBoxSize(origboxsize)

			f.close()
			
	def getImageFileName(self,imageformat="hdf"):
		return strip_file_tag(self.imagename)+"."+imageformat

	def writeboximages(self,boxsize=-1,force=False,imageformat="hdf",verbose=True):
		'''
		If boxsize is -1 then the current boxsize is used to write output
		If force is True then output is written over (if it already exists) - else an error is printed and nothing happens
		
		'''
		if len(self.boxes) == 0:
			print "no boxes to write, doing nothing. Image name is",self.imagename
		else:
			imagename = self.getImageFileName(imageformat)
			
			if file_exists(imagename):
				if not force:
					print "warning, file already exists - ", imagename, " doing nothing. Use force to override this behavior"
					return
				else:
					remove_file(imagename)
			
			if verbose:	print "writing",self.numBoxes(),"boxed images to", imagename
			
			for box in self.boxes:
				if boxsize != -1:
					# FOO - this will not work if the box dimensions are not equal...
					origboxsize = box.xsize
					if origboxsize != box.ysize:
						print "error, uniform box dimensions are not supported"
						return
					box.changeBoxSize(boxsize)
						
				image = box.getBoxImage()
				
				image.set_attr("original_x_corner",box.xcorner)
				image.set_attr("original_y_corner",box.ycorner)
				image.set_attr("original_x_size",box.xsize)
				image.set_attr("original_y_size",box.ysize)
				
				image.set_attr("originating_imagename",self.getImageName())
				
				image.write_image(imagename,-1)
				
				if boxsize != -1:
					box.changeBoxSize(origboxsize)

	def moveBox(self,box,dx,dy,boxnum):
		if box.ismanual:
			self.moveManualBox(box,dx,dy)
		
		box.move(dx,dy)

	def addbox(self,box):	
		if not isinstance(box,Box):
			print "You can not add a box to this box set if it is not of type Box"
			return;

		box.boxingobj = self
		
		if box.isref:
			box.rorig = 0			# RGB red
			box.gorig = 0			# RGB green
			box.borig = 0			# RGB blue
			box.r = 0
			box.g = 0
			box.b = 0
		else: # box.ismanual = True
			box.rorig = 1			# RGB red
			box.gorig = 1			# RGB green
			box.borig = 1			# RGB blue
			box.r = 1
			box.g = 1
			box.b = 1
			self.cacheManualBox(box)
		
		#print "adding box",box.xcorner,box.ycorner,box.xsize,box.ysize
		self.boxes.append(box)
		self.refboxes.append(box)
	
	def cacheManualBox(self,box):
		print "caching manual boxes"
		manualboxes = getKeyEntryIDD(self.imagename,"manual_boxes")
		
		if manualboxes == None:
			manualboxes = []
		print "there are",len(manualboxes)
		manualboxes.append(TrimBox(box))
		print "there are",len(manualboxes)
		setKeyEntryIDD(self.imagename,"manual_boxes",manualboxes)

	def deleteManualBox(self,box):
		
		manualboxes = getKeyEntryIDD(self.imagename,"manual_boxes")
		
		if manualboxes == None or len(manualboxes) == 0:
			print "error, you can't move a manual box if there are none!"
			return
		
		found = False
		for j,b in enumerate(manualboxes):
			if b.xcorner == box.xcorner and b.ycorner == box.ycorner:
				manualboxes.pop(j)
				setKeyEntryIDD(self.imagename,"manual_boxes",manualboxes)
				found = True
				break
		
		if not found:
			print "error, couldn't find the manual box you tried to delete, nothing happened"
			return
		
	
	def moveManualBox(self,box,dx,dy):
		manualboxes = getKeyEntryIDD(self.imagename,"manual_boxes")
		
		if manualboxes == None or len(manualboxes) == 0:
			print "error, you can't move a manual box if there are none!"
			return
		
		found = False
		for j,b in enumerate(manualboxes):
			if b.xcorner == box.xcorner and b.ycorner == box.ycorner:
				b.xcorner += dx
				b.ycorner += dy
				found = True
				setKeyEntryIDD(self.imagename,"manual_boxes",manualboxes)
				break
		
		if not found:
			print "error, couldn't find the manual box you tried to move, nothing happened"
			return
		
	
	def delbox(self,i):
		tmp = self.boxes.pop(i)
		if tmp.ismanual:
			self.deleteManualBox(tmp)
		#yuck, this is horribly inefficient
		for j,box in enumerate(self.refboxes):
			if box.isref and box.TS == tmp.TS:
				self.refboxes.pop(j)
				return True
			
		return False
	
	def deletenonrefs(self,updatedisplay=True):
		boxestodelete = []
		n = len(self.boxes)
		for m in range(n-1,-1,-1):
			box = self.boxes[m]
			if box.isref == False and box.ismanual == False:
				self.delbox(m)
				boxestodelete.append(m)

		if updatedisplay:
			self.parent.deleteDisplayShapes(boxestodelete)
	
	def addnonrefs(self,boxes):
		'''
		Add boxes that are stored in eman1 format
		box[0] = xnorner, box[1] = ycorner, box[2] = xsize, box[3] = ysize
		'''
		for box in boxes:
			b = Box(box[0],box[1],box[2],box[3])
			b.setImageName(self.imagename)
			b.isref = False
			b.changed = True
			self.boxes.append(b)

	def numBoxes(self):
		return len(self.boxes)
	
	def updateBoxSize(self,boxsize):
		'''
		Updates only the box size and corner coordinates
		Switches the changed flag to True to trigger redisplay (but the calling function
		is responsible for knowing and testing for this)
		'''
		# do nothing if it's the same size as what we already have
		if  boxsize == self.boxsize: return
		
		for box in self.boxes:
			if box.xsize != boxsize:
				box.xcorner -= (boxsize-box.xsize)/2
				box.xsize = boxsize
				box.changed = True
			if box.ysize != boxsize:
				box.ycorner -= (boxsize-box.ysize)/2
				box.ysize = boxsize
				box.changed = True
			
			box.image = None
			box.footprint = None

		self.fprink = -1
		self.flattenimager = -1
		self.boxsize = boxsize
		self.correlation = None
		
	def getfootprintshrink(self):
		if self.fpshrink == -1:
			shrink = 1
			tn = self.boxsize/2
			while ( tn >= 32 ):
				tn /= 2
				shrink *= 2
			self.fpshrink = shrink
		
		return self.fpshrink
		
	def getBestShrink(self):
		'''
		FIXME - there should probably be a more well established framework for doing this
		At the moment it is possible that the self.autBoxer is actually None, which isn't good.	
		'''
		if self.autoBoxer != None:
			return self.autoBoxer.getBestShrink()
		else:
			print 'warning, there is no autoboxer set, am not sure how to shrink, returning 1 as the shrink factor'
			return 1
		
	def updateCorrelation(self,template):
		'''
		A function that will update the correlation image if the correlationupdate flag is set to true
		Useful if a template has been updated somewhere, yet many references originate from this BoxingOject -
		All the references will call this function, but we only need to act the first time it happens
		
		Be warned - whoever opens the gate by setting self.allowcorrelationupdate to True should set it 
		to False once their done with the specialized operation
		
		'''
		if self.allowcorrelationupdate:
			self.templateTS = template.getTemplateTS() # Time Stamp, used for efficiency in autoBox to save an unecessary correlation update
			self.__genCorrelation(template)
			
			# I made a conscientious decision to leave the responsibility of turning this flag off
			# to that of the calling program/function. This uncommented line is left only for documentation purposes
			#self.allowcorrelationupdate = False


	def __genCorrelation(self,template):
		'''
		The force update flag is only meant to be used if the box size has changed - this changes 
		the shrink factor, and also affects the background flattening process.
		'''
		cfimage = self.getSmallImage()
		
		cache = FLCFImageCache()
		self.correlation = cache.getImage(self.imagename,cfimage,template)
		
		return self.correlation
	
	def getCorrelationImage(self):
		return self.correlation
	
	
	def getSmallImage(self):
		cfImageCache = CFImageCache()
		return  cfImageCache.getImage(self.imagename,self.autoBoxer.getTemplateRadius(),self.autoBoxer.getBestShrink())
	
	def updateExcludedBoxes(self, useinternal=True,exclusionimage= None):
		'''
		
		'''
		if useinternal:
			exclusionimage = self.getExclusionImage()

		lostboxes = []
			
		invshrink = 1.0/self.getBestShrink()
		n = len(self.boxes)
		refs = []
		for i in range(n-1,-1,-1):
			box = self.boxes[i]
			x = int((box.xcorner+box.xsize/2.0)*invshrink)
			y = int((box.ycorner+box.ysize/2.0)*invshrink)
			
			if ( exclusionimage.get(x,y) != 0):
				lostboxes.append(i)

				box = self.boxes.pop(i)
				if box.isref: refs.append(box)
	
		return [lostboxes,refs]
	
	def addExclusionParticle(self,box):
		
		xx = box.xcorner+box.xsize/2-1
		yy = box.ycorner+box.ysize/2-1
		
		self.addExclusionArea(None,xx,yy,box.xsize/2)
	
	def addExclusionArea(self,UNUSEDtype,x,y,radius,flag=ERASE):
		'''
		UNUSEDtype was meant to be a flag for adding other exclusion areas like squares
		At the moment only circular exclusion areas can be written
		'''
		xx = int(x/self.getBestShrink())
		yy = int(y/self.getBestShrink())
		
		rr = int(radius/self.getBestShrink())
		bciCache = BinaryCircleImageCache()
		mask = bciCache.getImage(rr)
		
		
		if flag == Boxable.ERASE:
			val = 0.1
		elif flag == Boxable.UNERASE:
			val = 0
		else:
			print "error - unknow flag:",flag,"doing nothing"
			return
		
		BoxingTools.set_region(self.getExclusionImage(),mask,xx,yy,val)
		
	
	def getExclusionImage(self,force=True):
		if self.exclusionimage == None and force:
				
			self.exclusionimage = EMData(self.getSmallImage().get_xsize(),self.getSmallImage().get_ysize())
			self.exclusionimage.to_zero()
		
		return self.exclusionimage
	
	def classify(self):
		
		# accrue all params
		n = self.autoBoxer.optprofileradius+1
		for box in self.boxes:
			# set the force flag true or else the optprofile won't be set when the peak is 'faulty'
			box.updateParams(self.autoBoxer,False,True)
		
		v = []
		for box in self.boxes:
			#b = copy(box.optprofile[0:n])
			b = copy(box.optprofile)
			#for a in b: 
				#a = box[6]-a
			#print b
			v.append(b)
			
		cl = BoxingTools.classify(v,4)
		self.parent.updateboxcolors(cl)
	
	def genRefImages(self):
		tmpimage = "tmpparticles.img"
		self.parent.writeBoxesTo(tmpimage)
		
		self.process = QtCore.QProcess()

		program = QtCore.QString("e2refine2d.py")
		args = QtCore.QStringList()
		args.append("--input="+tmpimage)
		args.append("--ncls=25")
		
		QtCore.QObject.connect(self.process, QtCore.SIGNAL("finished(int)"), self.process_finished)
		QtCore.QObject.connect(self.process, QtCore.SIGNAL("started()"), self.process_start)
		print self.process.start(program,args)

	def process_start(self):
		print "received process start signal"
		
	def boxsel(self,event,lc):
		#print "selected",lc[0]
		for box in self.boxes:
			if box.group == lc[0]:
				box.r = 1
				box.g = 1
				box.b = 1
				box.changed = True
			elif box.r == 1 and box.g == 1 and box.b == 1:
				box.r = box.rorig
				box.g = box.gorig
				box.b = box.borig
				box.changed = True
		self.imagemx2.setSelected(lc[0])
		self.parent.boxDisplayUpdate()
		
	def process_finished(self,int):
		try:
			from emimage import EMImage
		except:
			print "Cannot import EMAN image GUI objects (emimage,etc.)"
			sys.exit(1)
		
		e = EMData().read_images("classes.init.hdf")
		self.imagemx2p = EMImage(e)
		self.imagemx2 = self.imagemx2p.child
		self.imagemx2.setmmode("app")
		QtCore.QObject.connect(self.imagemx2,QtCore.SIGNAL("mousedown"),self.boxsel)
		self.imagemx2p.show()
		
		ef = []
		for image in e:
			image.process_inplace("normalize.edgemean")
			if self.getBestShrink() != 1:
				image = image.process("math.meanshrink",{"n":self.getfootprintshrink()})	
			ef.append(image.make_footprint())
		
		for box in self.boxes:
			best = -1
			group = -1
			for i,g in enumerate(ef): 
				s = box.getFootPrint(self.getfootprintshrink()).cmp("optvariance",g,{"matchfilt":1,"matchamp":1})
				# REMEMBER - cmp returns values that have potentially been negated - a smaller value is better
				if best == -1 or s < best:
					group = i
					best = s
			
			box.group = group
					
		
		#print scores
		
		print "received finish signal"

def getIDDKey(imagename):
	return strip_file_tag(imagename)+"_DD"

def setKeyEntryIDD(imagename,key,object):
	'''
	write a key/object pair to the Image Database Dictionary associat
	'''
	dbkey = getIDDKey(imagename)
	
	projectdb = EMProjectDB()
	try:
		data = projectdb[dbkey]
	except:
		data = {}
		
	data[key] = object
	#projectdb[self.getDDKey()] = data
		#projectdb.sync()
	projectdb.setKeyEntry(dbkey,data)


def getKeyEntryIDD(imagename,key):
	dbkey = getIDDKey(imagename)
	
	projectdb = EMProjectDB()
	try:
		data = projectdb[dbkey]
		return data[key] 
	except:
		return None


class AutoBoxer:
	'''
	FIXME - ALL COMMENTS IN THIS CLASS ARE LIABLE TO BE OUTDATED
	Base class design for auto boxers
	'''
	def __init__(self):
		self.version = 1.0

	def getTemplate(self):
		'''This should return a single template which is an EMData object'''
		raise Exception
	
	def name(self):
		'''
		Every autoboxer should return a unique name
		'''
		raise Exception
	
	def addReference(self,box):
		'''
		add a reference box - the box should be in the format of a Box object, see above
		Returns 0 if there is a problem, returns 1 if it's all good
		Adds a reference to a list
		'''
		raise Exception
	
	def removeReference(self,box):
		'''
		Remove a reference box - the box should in the format of a Box object, see above
		Pops a reference from a list
		'''
		raise Exception
	
	def referenceMoved(self,ref):
		'''
		If a reference was moved interactively in the interface this is the function that should be called
		'''
		raise Exception

	def getTemplate(self):
		'''
		Return the template that is being used. Returns None if there is not template
		'''
		raise Exception

	def setBoxSize(self,boxsize):
		'''
		Hard set the boxsize. Note that nothing is done to the reference boxes. It is
		assumed whichever part of the program calls this function also updates the Box objects
		independently (which implicitly affects the boxes stored internally in the AutoBoxer
		class, because it only ever stores programmatic references)
		'''
		raise Exception
	
	def autoBox(self,correlation,boxes=[],exclusion=None):
		'''
		The main autoBox routine. The calling program should pass in its own correlation map (EMData), and optionally
		an exclusion map of ones and zeros (0 means include, non zero means exclude). Also a list of boxes that will
		not be removed prior to the autoBoxing (and hence probably have associated excluded regions in the exlcusion
		image, but this is beside the point), The model of use here is that
		the calling program should get the current template from the AutoBoxer to generate the correlation map. The
		calling program should be able to cache the correlation map, so should be able to detect if there's been
		a template update by asking for the current set of references (getReferences) and cross checking against a list of its own.
		@Returns a list of Boxes
		'''
		raise Exception

class TrimSwarmTemplate:
	'''
	used from writing a template to the database
	'''
	def __init__(self,swarmTemplate):
		self.refboxes = []		# this will eventually be a list of Box objects
		for ref in swarmTemplate.refboxes:
			self.refboxes.append(TrimBox(ref))
		self.template = swarmTemplate.template	# an EMData object that is the template
		self.templateTS = swarmTemplate.templateTS 	# a time stamp that records when the template was generate

class SwarmTemplate:
	def __init__(self,autoBoxer):
		self.refboxes = []		# this will eventually be a list of Box objects
		self.template = None	# an EMData object that is the template
		self.templateTS = -1 	# a time stamp that records when the template was generate
		self.autoBoxer = autoBoxer
	
	def become(self,trimSwarmTemplate):
		if not isinstance(trimSwarmTemplate,TrimSwarmTemplate):
			print "error, can't become anything other than a TrimSwarmTemplate"
			return 0
		else:
			
			self.template = trimSwarmTemplate.template	# an EMData object that is the template
			self.templateTS = trimSwarmTemplate.templateTS 	# a time stamp that records when the template was generate
			self.refboxes = []		# this will eventually be a list of Box objects
			for ref in trimSwarmTemplate.refboxes:
				b = Box()
				b.become(ref)
				self.refboxes.append(b)
			
	def getTemplate(self):
		return self.template
	
	def getImage(self):
		# FIXME - getTemplate should be replaced with this function
		return self.template
	
	def getTemplateTS(self):
		return self.template.get_attr("template_time_stamp")
	
	def getReferences(self):
		#print "asking template for references, there are ",len(self.refboxes)
		return self.refboxes
	
	def appendReference(self,ref):
		if isinstance(ref,Box):
			self.refboxes.append(ref)
		else:
			print "error, can't append that reference, it's not of type Box"
		
	def removeReference(self,box):
		'''
		Returns 1 if the reference was removed
		Returns 0 if it wasn't found
		'''
		if not isinstance(box,Box):
			print "error, can't remove a reference that isn't a box"
			return 0
		
		for j,tmp in enumerate(self.refboxes):
			if box.xcorner == tmp.xcorner and box.ycorner == tmp.ycorner:
				t = self.refboxes.pop(j)
				return 1	
				
		return 0
	
	def genTemplate(self):
		'''
		Returns 0 if there are errors
		Return 1 if not
		'''
		# you can only generate a template if there are references
		if len(self.refboxes) <= 0: 
			print 'error, cant call private function genTemplate when there are no refboxes, this is an internal error'
			return 0
		
		images_copy = []
		for ref in self.refboxes:
			# some references can be excluded from the template generation procedure, this is flagged
			# by the isanchor flag
			if ref.isanchor == False:
				continue
			image = ref.getSmallBoxImage(self.autoBoxer.getTemplateRadius(),self.autoBoxer.getBestShrink())
			image.write_image("refs.hdf",-1)
			images_copy.append(image)
		if len(images_copy) == 0:
			print 'error, you have probably set references that all have the isanchor flag set to false, which exluded them all from the template making process'
			print 'can not proceed without references to create template'
			return 0
			
		ave = images_copy[0].copy()
		
		for i in range(1,len(images_copy)):
			#ta = images_copy[i].align("rotate_translate",ave,{},"dot",{"normalize":1})
			ave.add(images_copy[i])
		
		#ave.write_image("prealigned.hdf")
		ave.mult(1.0/len(images_copy))
		ave.process_inplace("math.radialaverage")
		ave.process_inplace("xform.centeracf")
		ave.process_inplace("mask.sharp",{'outer_radius':ave.get_xsize()/2})
		
		#for image in images_copy:
		#	image.write_image("aligned_refs.img",-1)
		#
		#ave.write_image("aligned_refs.img",-1)
		#
		#black = EMData(image.get_xsize(),image.get_ysize())
		#black.to_zero()
		#black.write_image("aligned_refs.img",-1)
		
		#ave.write_image("ave.hdf")
		shrink = self.autoBoxer.getBestShrink()
		# 4 is a magic number
		for n in range(0,4):
			t = []
			for idx,i in enumerate(images_copy):
				ta = i.align("translational",ave,{},"dot",{"normalize":1})
				#t.append(ta)
				
				# FIXME - make it so that a newly clipped portion of the original image
				# is used as the 'aligned' image, to avoid zeroing effects at the edges
				# The problem with this approach is one of persistence. If the box has no associated
				# boxingobj then it will fail. The box will have no boxing obj using the persistent database 
				# approach of e2boxer
				dx = ta.get_attr("align.dx")
				dy = ta.get_attr("align.dy")
				box = self.refboxes[idx]
				size = ta.get_xsize()
				image = box.getSmallImage(self.autoBoxer.getTemplateRadius(),self.autoBoxer.getBestShrink())
				a = image.get_clip(Region(int(box.xcorner/shrink-dx),int(box.ycorner/shrink-dy),size,size))
				a.process_inplace("normalize.edgemean")
				
				t.append(a)
				
		
			ave = t[0].copy()
			for i in range(1,len(images_copy)):
				ave.add(t[i])
				
			ave.mult(1.0/len(t))
			ave.process_inplace("math.radialaverage")
			ave.process_inplace("xform.centeracf")
			# edge normalize here SL before
			ave.process_inplace("mask.sharp",{'outer_radius':ave.get_xsize()/2})
			# or normalize and no mask
		
		#debug, un-comment to see the aligned refs and the final template
		#for image in t:
		#	image.write_image("aligned_refs.img",-1)
		
		#ave.write_image("aligned_refs.img",-1)
		
		#black = EMData(image.get_xsize(),image.get_ysize())
		#black.to_zero()
		#black.write_image("aligned_refs.img",-1)
		#END uncomment block
		self.template = ave
		
		self.templateTS = gm_time_string()
		self.template.set_attr("template_time_stamp",self.templateTS)
		return 1
	
	

class TrimSwarmAutoBoxer():
	def __init__(self,swarmAutoBoxer):
			
		self.boxsize = swarmAutoBoxer.boxsize
		self.shrink = swarmAutoBoxer.shrink
		self.templatedimmin = swarmAutoBoxer.templatedimmin
		
		self.optthreshold = swarmAutoBoxer.optthreshold
		self.optprofile = copy(swarmAutoBoxer.optprofile)
		self.optprofileradius = swarmAutoBoxer.optprofileradius
		self.selmode = swarmAutoBoxer.selmode
		self.templateTS = swarmAutoBoxer.templateTS
		self.stateTS = swarmAutoBoxer.stateTS
		self.mode = swarmAutoBoxer.mode
		self.refupdate = swarmAutoBoxer.refupdate
		self.regressiveflag = swarmAutoBoxer.regressiveflag
		
		self.template = TrimSwarmTemplate(swarmAutoBoxer.template)
		self.creationTS = swarmAutoBoxer.creationTS
		self.convenienceString = swarmAutoBoxer.convenienceString
	
	def getUniqueStamp(self):
		return "autoboxer_" + self.creationTS
	
	def setConvenienceName(self,string):
		self.convenienceString = string
		#print "set db string",self.getUniqueStamp()
	
	def getConvenienceName(self):
		return self.convenienceString
	
	def setCreationTS(self,TS):
		''' 
		This function is used when creating a fresh copy of this autoboxer and placing it
		in the database in GUIbox
		'''
		#print "setting creationTS",TS
		self.creationTS = TS
		
	def getCreationTS(self):
		return self.creationTS
	
	def getStateTS(self):
		return self.stateTS
	
	def getTemplateTS(self):
		return self.template.getTemplateTS()
	
	def writeToDB(self):
		data = {}
		data["autoboxer"] = self
		data["convenience_name"] = self.getConvenienceName()
		
		projectdb = EMProjectDB()
		projectdb.setKeyEntry(self.getUniqueStamp(),data)
	
class SwarmAutoBoxer(AutoBoxer):
	'''
	This is an autoboxer that encapsulates the boxing approach first developed in SwarmPS
	'''
	THRESHOLD = "Threshold"
	SELECTIVE = "Selective"
	MORESELECTIVE = "More Selective"
	DYNAPIX = 1
	ANCHOREDDYNAPIX = 2
	USERDRIVEN = 3
	ANCHOREDUSERDRIVEN = 4
	COMMANDLINE = 5
	def __init__(self,parent):
		AutoBoxer.__init__(self)

		self.template = SwarmTemplate(self)	# an EMData object that is the template
		self.boxsize = -1		# stores the global boxsize, this is the value being used by boxer in the main interface
		self.shrink = -1
		
		# more privately stuff
		self.templatedimmin = 20  # the smallest amount the template can be shrunken to. Will attempt to get as close to as possible. This is an important part of speeding things up.
		self.optthreshold = -1	# the correlation threshold, used to as the basis of finding local maxima
		self.optprofile = []	# the optimum correlation profile used as the basis of auto selection
		self.optprofileradius = -1 # the optimum radius - used to choose which part of the optprofile is used as the basis of selection
		self.selmode = SwarmAutoBoxer.SELECTIVE	# the autobox method - see EMData::BoxingTools for more details
		self.cmpmode = BoxingTools.CmpMode.SWARM_RATIO
		BoxingTools.set_mode(self.cmpmode)
		self.__shrink = -1
		
		self.templateTS = -1 # a template time stamp to 
		self.stateTS = -1 # the time stamp that records when the current template and parameters are completely up to date
		
		
		self.mode = SwarmAutoBoxer.DYNAPIX
		self.refupdate = False # this is a flag used when self.mode is USERDRIVEN
		self.permissablemodes = [SwarmAutoBoxer.DYNAPIX,SwarmAutoBoxer.ANCHOREDDYNAPIX,SwarmAutoBoxer.USERDRIVEN,SwarmAutoBoxer.ANCHOREDUSERDRIVEN,SwarmAutoBoxer.COMMANDLINE]
		self.permissablecmpmodes = [BoxingTools.CmpMode.SWARM_RATIO,BoxingTools.CmpMode.SWARM_DIFFERENCE]  # the permissiable peak profile comparitor modes - for convenience when double
		self.permissableselmodes = [SwarmAutoBoxer.THRESHOLD,SwarmAutoBoxer.SELECTIVE,SwarmAutoBoxer.MORESELECTIVE]  # the permissiable selection modes - for convenience when double checking the calling program is setting the selectionmode explicitly (through setSelectionMode )
		self.regressiveflag = False	# flags a force removal of non references in the Boxable in autoBox
		
		self.dummybox = None
		self.parent = parent
		
		self.creationTS = gm_time_string()
		self.convenienceString = ""
		self.setConvenienceName(self.getCreationTS()) # this string is the string that users will use to name this autoBoxer in the GUIboxCtrl

	def become(self,trimSwarmAutoBoxer):			
		self.boxsize = trimSwarmAutoBoxer.boxsize
		self.shrink = trimSwarmAutoBoxer.shrink
		self.templatedimmin = trimSwarmAutoBoxer.templatedimmin
		
		self.optthreshold = trimSwarmAutoBoxer.optthreshold
		self.optprofile = copy(trimSwarmAutoBoxer.optprofile)
		self.optprofileradius = trimSwarmAutoBoxer.optprofileradius
		self.selmode = trimSwarmAutoBoxer.selmode
		self.templateTS = trimSwarmAutoBoxer.templateTS
		self.stateTS = trimSwarmAutoBoxer.stateTS
		self.creationTS = trimSwarmAutoBoxer.creationTS
		self.mode = trimSwarmAutoBoxer.mode
		self.refupdate = trimSwarmAutoBoxer.refupdate
		self.regressiveflag = trimSwarmAutoBoxer.regressiveflag
		self.convenienceString = trimSwarmAutoBoxer.convenienceString
		self.template = SwarmTemplate(self)
		self.template.become(trimSwarmAutoBoxer.template)
		
		# Things that only the SwarmAutoBoxer (not necessary for the TrimSwarmAutoBoxer to do this in its constructor
		self.__updateRefParams()
		
		
	def setConvenienceName(self,string):
		self.convenienceString = string
		
	def getConvenienceName(self):
		return self.convenienceString
	
	def getBoxable(self):
		return self.parent.getBoxable()
	
	def getStateTS(self):
		return self.stateTS
	
	def getTemplateTS(self):
		return self.template.getTemplateTS()
	
	def getCreationTS(self):
		return self.creationTS
	
	def getTemplate(self):
		return self.template
	
	def setDummyBox(self,box):
		if not box==None and not box.isdummy:
			print "you can never set a dummy box unless the isdummy flag is true"
			return 0
		
		if box != None:
			for i,ref in enumerate(self.getRefBoxes()):
				if ref.isdummy:
					self.removeReference(ref)
				break
			self.addReference(box)
		else:
			if self.dummybox != None:
				self.removeReference(self.dummybox)
			
		self.dummybox = box
	
	def setModeExplicit(self,mode):
		if mode in self.permissablemodes:
			self.mode = mode
		else:
			print "error, that mode:", mode, "was not in the list of permissable modes"
			exit(1)
	def setMode(self,dynapix,anchortemplate):
		if dynapix:
			if anchortemplate: self.mode = SwarmAutoBoxer.ANCHOREDDYNAPIX
			else: self.mode = SwarmAutoBoxer.DYNAPIX
		else:
			if anchortemplate: self.mode = SwarmAutoBoxer.ANCHOREDUSERDRIVEN
			else: self.mode = SwarmAutoBoxer.USERDRIVEN

	def setCmpMode(self,cmpmode):
		if cmpmode in self.permissablecmpmodes:
			if self.cmpmode != cmpmode:
				self.cmpmode = cmpmode
				BoxingTools.set_mode(self.cmpmode)
				if not self.__fullUpdate(): return 0
				self.regressiveflag = True
				if self.mode == SwarmAutoBoxer.DYNAPIX or self.mode == SwarmAutoBoxer.ANCHOREDDYNAPIX:
					self.autoBox(self.getBoxable())
				elif self.mode == SwarmAutoBoxer.COMMANDLINE:
					print "warning, haven't double check SwarmAutoBoxer.COMMANDLINE scenario in setCmpMode"
				return 1
			else:
				print "warning, attempted to set the cmpmode to that which was already stored, no action taken"
				return 0
		else:
			print "the peak profile comparitor mode you specified:", cmpmode,"was not recognized, no action was taken"
			return 0
	def getMode(self):
		return self.mode
	
	def setSelectionMode(self,selmode):
		if selmode in self.permissableselmodes:
			if self.selmode != selmode:
				self.selmode = selmode
				self.__plotUpdate()
				self.stateTS = gm_time_string()
				self.regressiveflag = True
				if self.mode == SwarmAutoBoxer.DYNAPIX or self.mode == SwarmAutoBoxer.ANCHOREDDYNAPIX:
					self.autoBox(self.getBoxable())
				elif self.mode == SwarmAutoBoxer.COMMANDLINE:
					print "warning, haven't double check SwarmAutoBoxer.COMMANDLINE scenario in setSelectionMode"
				return 1
			else:
				print "warning, attempted to set the selmode to that which was already stored, no action taken"
				return 0
		else:
			print "the selection mode you specified:", selmode,"was not recognized, no action was taken"
			return 0

	def name(self):
		return 'swarmautoboxer'

	def addReference(self,box):
		'''
		 add a reference box - the box should be in the format of a Box, see above):
		'''
		if isinstance(box,Box):
			if box.xsize != box.ysize:
				print 'error, support for uneven box dimensions is not currently implemented'
				return 0
		
			# store the boxsize if we don't have one already
			if self.boxsize == -1 and not box.isdummy:
				self.boxsize = box.xsize
			# do a sanity check, this shouldn't happen if the program is managing everything carefully
			elif self.boxsize != box.xsize and not box.isdummy:
				print 'error, the currently stored box size does not match the boxsize of the reference that was just added'
				return 0
			
			self.template.appendReference(box)
			# update the data base
			self.writeSpecificReferencesToDB(self.getBoxable().getImageName())
			
			if self.mode == SwarmAutoBoxer.DYNAPIX:
				if not box.isanchor and not box.isdummy:
					print 'the box flag is internally inconsistent when using pure dynapix'
					return 0
				if not self.__fullUpdate() : return 0
				self.autoBox(self.getBoxable())
			elif self.mode == SwarmAutoBoxer.ANCHOREDDYNAPIX:
				if box.isanchor and not box.isdummy:
					print 'the box flag is internally inconsistent when anchoring'
					return 0
				box.updateParams(self)
				if not self.__accrueOptParams() :
					self.stateTS = gm_time_string()
					print "there is a problem with the references"
					return 0
				self.stateTS = gm_time_string()
				self.autoBox(self.getBoxable())
			elif self.mode == SwarmAutoBoxer.USERDRIVEN:
				self.refupdate = True
				self.stateTS = -1
				self.templateTS = -1
			elif self.mode == SwarmAutoBoxer.ANCHOREDUSERDRIVEN:
				box.updateParams(self)
				if not self.__accrueOptParams() :
					self.stateTS = gm_time_string()
					print "there is a problem with the references"
					return 0
				self.stateTS = gm_time_string()
			else:
				print 'error, unknown mode in SwarmAutoBoxer'
				return 0
		
			return 1
	
			
		else:
			print "error, you cannot add a reference to the AutoBoxer if it is not in the format of a Box object"
			return 0
	
	
	def removeReference(self,boxes):
		'''
		Should potentially be called removeReferences
		This is somewhat of a hack - the function should be called removeReferences because
		it works if the calling function supplies a list of boxes...
		'''
		
		try:
			isanchor = False
			for box in boxes:
				self.template.removeReference(box)
				if box.isanchor: isanchor = True
		except:
			# there is only one box
			box = boxes
			self.template.removeReference(box)
			isanchor = box.isanchor
		
		# update the data base
		self.writeSpecificReferencesToDB(self.getBoxable().getImageName())
			
		if len(self.template.refboxes) == 0:
			self.__reset()
			return 2
			
		if self.mode == SwarmAutoBoxer.DYNAPIX or self.mode == SwarmAutoBoxer.ANCHOREDDYNAPIX:
			if isanchor:
				if not self.__fullUpdate(): return 0
				self.regressiveflag = True
				self.autoBox(self.getBoxable())
			else:
				if not self.__accrueOptParams() :
					self.stateTS = gm_time_string()
					print "there is a problem with the references"
					return 0
				self.stateTS = gm_time_string()
				self.regressiveflag = True
				self.autoBox(self.getBoxable())
			return 1
		elif self.mode == SwarmAutoBoxer.USERDRIVEN or self.mode == SwarmAutoBoxer.ANCHOREDUSERDRIVEN:
			if isanchor:
				self.refupdate = True
				self.stateTS = -1
				self.templateTS = -1
			else:
				box.updateParams(self)
				if not self.__accrueOptParams() :
					self.stateTS = gm_time_string()
					print "there is a problem with the references"
					return 0
				self.stateTS = gm_time_string()
				self.regressiveflag = True
				
			return 1
		
		return 0
	
	def getTemplateRadius(self):
		'''
		Returns what will be or is the template radius
		'''
		return int(self.boxsize/2/self.getBestShrink())
	
	def referenceMoved(self,box):
		'''
		If a reference was moved interactively in the interface this is the function that should be called
		The return value is whether or not autoboxing occured and hence whether or not display should be updated
		A -1 is returned if an error occured
		'''
		if self.mode == SwarmAutoBoxer.DYNAPIX or self.mode == SwarmAutoBoxer.ANCHOREDDYNAPIX:
			if box.isanchor:
				if not self.__fullUpdate() : return 0
				self.regressiveflag = True
				self.autoBox(self.getBoxable())
			else:
				box.updateParams(self)
				if not self.__accrueOptParams() :
					self.stateTS = gm_time_string()
					print "there is a problem with the references"
					return 0
				self.stateTS = gm_time_string()
				self.regressiveflag = True
				self.autoBox(self.getBoxable())
			
			# update the data base
			self.writeSpecificReferencesToDB(self.getBoxable().getImageName())
			return 1
		elif self.mode == SwarmAutoBoxer.USERDRIVEN or self.mode == SwarmAutoBoxer.ANCHOREDUSERDRIVEN:
			if box.isanchor:
				self.refupdate = True
				self.stateTS = -1
				self.templateTS = -1
			else:
				box.updateParams(self)
				if not self.__accrueOptParams() :
					self.stateTS = gm_time_string()
					print "there is a problem with the references"
					return 0
				self.stateTS = gm_time_string()
				self.regressiveflag = True
				
			# update the data base
			self.writeSpecificReferencesToDB(self.getBoxable().getImageName())
			return 0
		else:
			print 'error, unknown mode in SwarmAutoBoxer'
			return -1
		
	def getTemplateObject(self):
		return self.template
		
	def getTemplate(self):
		if self.refupdate:
			if not self.__fullUpdate(): return None
			self.refupdate = False
			
		if self.template == None:
			print 'error, you have either asked for the template without setting a reference, or you have added a reference and not set the refupdate flag'
			return None
		
		return self.template
		
	def getBoxSize(self):
		return self.boxsize
		
	def setBoxSize(self,boxsize):
		if (boxsize < 6 ):
			print 'error, a hard limit of 6 for the box size is currently enforced. Email developers if this is a problem'
			return
		if self.boxsize == boxsize:	return
		
		# FIXME - how should we deal with this?
		# update the data base
		#self.writeSpecificReferencesToDB(self.boxable.getImageName())
		
		self.boxsize = boxsize
		# make sure the shrink value is updated - use the force flag to do it
		self.getBestShrink(True)
		
		if self.mode == SwarmAutoBoxer.DYNAPIX or self.mode == SwarmAutoBoxer.ANCHOREDDYNAPIX:
			# update references
			if not self.__fullUpdate(): 
				print "box size change failed, can't full update"
				return
			self.autoBox(self.getBoxable())
		elif self.mode == SwarmAutoBoxer.USERDRIVEN or self.mode == SwarmAutoBoxer.ANCHOREDUSERDRIVEN :
			self.refupdate = True
			self.stateTS = -1
			self.templateTS = -1
		else:
			print 'error, unknown mode in SwarmAutoBoxer'
	
	def getSearchRadius(self):
		return int(0.75*(self.boxsize)/float(self.getBestShrink()))
	
	def getConstrainingRadius(self):
		return int(0.5*(self.boxsize)/float(self.getBestShrink()))
	
	def getBestShrink(self,force=True):	
		if self.boxsize == -1:
			print "error - the boxsize is currently -1 - I can't figure out the best value to shrink by"	
			return -1
			
		if self.shrink == -1 or force:	
			self.shrink = ceil(float(self.boxsize)/float(self.templatedimmin))	
			
		return self.shrink
		
	def autoBox(self,boxable,updatedisplay=True,force=False):
		# If it's user driven then the user has selected a bunch of references and then hit 'autobox'.
		# In which case we do a complete reference update, which generates the template and the
		# best autoboxing parameters
		
		# this is fine - if a boxable is frozen this is more or less a flag for the autoboxer not
		# to autobox it...
		#print "in autobox"
		if boxable.isExcluded():
			print "Image is excluded, doing nothing"
			return 0
		
		if boxable.isFrozen():
			print "Image is frozen, maintaining current state"
			return 0
		# the projectdb is used at various points in this function
		projectdb = EMProjectDB()
		
		if len(self.getRefBoxes()) == 0:
			boxable.clearAndCache(True)
			# FIXME - debug/double check this functionality
			boxable.setStamps(self.getStateTS(),-1,self.getUniqueStamp())
			boxable.writeToDB()

			self.writeToDB(True)
			
			self.parent.autoBoxerDBChanged()
			#if boxable.getAutoBoxerID() != self.getCreationTS():
				#boxable.setAutoBoxerID(self.getUniqueStamp())
				#self.parent.autoBoxerDBChanged()

			#print 'error, cant get template if there are no references'
			return 1

		# ref update should only be toggled if we are in user driven mode
		if self.refupdate:
			if not self.__fullUpdate(): return 0
			self.refupdate = False

		templateTS = boxable.templateTS
		correlation = boxable.getCorrelationImage()
		if templateTS == -1 or correlation == None or self.template.getTemplateTS() != templateTS:
			if self.template != None:
				boxable.allowcorrelationupdate = True
				boxable.updateCorrelation(self.template)
				boxable.allowcorrelationupdate = False
				
				correlation = boxable.correlation
			else:
				print 'error, cant ask the autoBoxer for its template, it doesnt have one'
				return 0

		autoBoxerStateTS = boxable.autoBoxerStateTS
		# auto boxing will occur if the time stamp of the AutoBoxer is not the
		# same as the time stamp cached by the Boxable. -1 means it's the first time.
		# Auto boxing will also occur if the autoboxer id of the boxable does not match the creation time stamp of this object
		# the creation time stamp of this object is persistent, even it was recovered from the data base
		
		if autoBoxerStateTS == -1 or autoBoxerStateTS != self.stateTS or boxable.getAutoBoxerID() != self.getUniqueStamp() or force:
			
			if self.mode == SwarmAutoBoxer.DYNAPIX or self.mode == SwarmAutoBoxer.USERDRIVEN or self.regressiveflag or self.mode == SwarmAutoBoxer.COMMANDLINE:
				# we must clear all non-refs if we're using dynapix
				boxable.deletenonrefs(updatedisplay)
				self.regressiveflag = False
			
			exclusion = boxable.getExclusionImage().copy()
			self.__paintExcludedBoxAreas(exclusion,boxable.boxes)

			boxes = self.__autoBox(correlation,boxable,exclusion)
			print "autoboxed",len(boxes)

			trimboxes = []
			# if anchoring is on we need to store the auto boxes that were not removed 
			# This is because the boxable didn't remove it's autoboxed particles prior to autoboxing
			# And we need to make the database complete for persistence
			boxable.appendStoredAutoBoxes(trimboxes)
			for box in boxes:
				#if box.ismanual: print "I added a manual box"
				t = TrimBox(box)
				trimboxes.append(t)
			
			boxable.setKeyEntryToIDD("auto_boxes",trimboxes)
			
			boxable.setStamps(self.getStateTS(),self.getTemplateTS(),self.getUniqueStamp())
			boxable.writeToDB()
			
			if self.mode != SwarmAutoBoxer.COMMANDLINE:
				self.writeToDB(True)
		
			# These two lines are a hack because it may not need to happen (redundancy)
			boxable.setAutoBoxerID(self.getUniqueStamp())
			if not (self.mode != SwarmAutoBoxer.COMMANDLINE or self.parent==None):
				self.parent.autoBoxerDBChanged()
				#self.__plotUpdate() # this is inefficent because it may have already happened FIXME
				
			self.writeSpecificReferencesToDB(boxable.getImageName())
			#print "set boxer id",self.getCreationTS()
			
			# finally tell the boxable to read the results from the database
			# the False argument tells the boxable not to re-read those
			# boxes stored by the call to appendStoredAutoBoxes above
			boxable.getAutoSelectedFromDB(False)
				
			return 1

		else: print 'no auto boxing was necessary, up-2-date' # DEBUG
	def getUniqueStamp(self):
		return "autoboxer_"+self.getCreationTS()
	
	def writeToDB(self,writecurrent=False):
		'''
		Writes this object to the DB using its time stamp
		If writecurrent is True then this SwarmAutoBoxer is also written to the DB as the "currentautobxer",
		meaning it is the most recently added autoboxer
		'''
		projectdb = EMProjectDB()
		autoboxerdbstring = self.getUniqueStamp()
		
		trimself = TrimSwarmAutoBoxer(self)
		data = {}	
		data["autoboxer"] = trimself
		data["convenience_name"] = self.getConvenienceName()
		
		projectdb.setKeyEntry(autoboxerdbstring,data)
		
		if writecurrent:
			projectdb.setKeyEntry("currentautoboxer",trimself)
		
	def writeSpecificReferencesToDB(self,imagename):
		'''
		Writes the references originating in the image given by imagename
		to the database.
		
		This is called in autoBox 
		'''
		
		refs = self.template.getReferences()
		refs_to_write = []
		for ref in refs:
			if ref.getImageName() == imagename:
				refs_to_write.append(TrimBox(ref))

		setKeyEntryIDD(imagename,"reference_boxes",refs_to_write)
	
	def __reset(self):
		#self.boxsize = -1
		self.stateTS = -1
		self.templateTS = -1

	def __autoBox(self,correlation,boxable,exclusion=None):
		'''
		Does the autoboxing. Returns a list of Boxes
		'''
		if not isinstance(correlation,EMData):
			print 'error, cannot autobox, the correlation argument is not an EMData object'
			return 0
			
			#print "using opt radius",self.radius, "which has value",tmp,"shrink was",self.shrink
		if self.selmode == SwarmAutoBoxer.THRESHOLD:
			mode = 0
		elif self.selmode == SwarmAutoBoxer.SELECTIVE:
			mode = 1
		elif self.selmode == SwarmAutoBoxer.MORESELECTIVE:
			mode = 2
		
		shrink = self.getBestShrink()
		# Warning, this search radius value should be the same as the one used by the BoxSets that contributed the reference boxes
		# to this AutoBoxer object. There should be one place/function in the code where both parties access this value
		searchradius = self.getSearchRadius()
		soln = BoxingTools.auto_correlation_pick(correlation,self.optthreshold,searchradius,self.optprofile,exclusion,self.optprofileradius,mode)


		template = self.getHighResTemplateImage()

		# This is what should be written to the database
		boxes = []
		
		for b in soln:
			x = b[0]
			y = b[1]
			xx = int(x*shrink)
			yy = int(y*shrink)
			box = Box(xx-self.boxsize/2,yy-self.boxsize/2,self.boxsize,self.boxsize,0)
			box.setImageName(boxable.getImageName())
			box.correlationscore = correlation.get(x,y)
			box.corx = b[0]
			box.cory = b[1]
			box.changed = True
			box.correctResolutionCentering(self.getBestShrink(),False)
			box.center(Box.CENTERPROPAGATE,template,False)
			boxes.append(box)
	
		return boxes
		
	def getHighResTemplateImage(self):
		t = self.getTemplateObject() # this is the template object
		template = t.getTemplate() # this is the image
		template = template.copy()
		newx = self.boxsize
		newy = self.boxsize
		oldx = template.get_xsize()
		oldy = template.get_ysize()
		template.clip_inplace(Region((oldx-newx)/2,(oldy-newy)/2,newx,newy))
		scale = float(newx)/float(oldx)
		template.scale(scale)
		return template
		
	
	def __fullUpdate(self):
		'''
		Forces a template update, then updates all correlation images
		that the references come from, then does a parameters update.
		This is like a completeness function - this needs to happen for internal
		consistency. It is motivated by the thought that if references
		come from many images, then the correlation images of each of the images
		needs to be updated in order for the correlation parameters to be generated
		consistently (from a correlation image generated by a universal template)
		'''
		
		if not self.template.genTemplate():
			print 'error, couldnt generate template'
			return 0
		
		# First tell all references' associated boxing objects to be open to the prospect 
		# if update their correlation images
		
		self.__updateRefParams()

		# parameters should be updated now
		# it's important that the BoxingObjext.updateCorrelation updated the parameters stored in the boxes
		if not self.__accrueOptParams(): return 0
		
		self.stateTS = gm_time_string()

		return 1
	
	def __updateRefParams(self):
		for ref in self.getRefBoxes():
			ref.updateParams(self)
			
	def getRefBoxes(self):
		return self.template.getReferences()
	
	def __accrueOptParams(self):
		'''
		A function for accruing the parameters of the SwarmPSAutoBoxer autoboxing technique
		returns True if optimal parameters were accrued
		return False if not
		'''

		# To determine the threshold from what we've got, iterate through all of the reference
		# boxes and use the lowest correlation score as the correlation threshold
		#print 'current params are, using a total of',len(self.refboxes),'references'
		#print 'threshod:',self.optthreshold
		#print 'profile:',self.optprofile
		#print 'optrad:',self.optprofileradius
		
		if self.dummybox == None:
			found = False
			for i,box in enumerate(self.getRefBoxes()):
				if box.correlationscore == None:
					# this is an error which probably means that the box, as created by the user, has a strong correlation maximum next to it which is disrupting the auto parameters
					# this is mostly an error for dwoolfords attention
					# for the time being just ignoring it  probably suffices
					# FIXME
					print "continuing on faulty"
					continue
				if found == False:
					self.optthreshold = box.correlationscore
					found = True
				else:	
					if box.correlationscore < self.optthreshold: self.optthreshold = box.correlationscore
	
			# catch the circumstance where for some strange reason things just didn't work
			# probably the user has some strange data and the rotational template isn't responding normally. 
			# correlation peaks aren't where the user thinks they are.
			if not found:
				print 'error, there were no parameter data that I could inspect. I cant make the optimal parameters'
				return False
			
			# Iterate through the reference boxes and accrue what you can think of
			# as the worst case scenario, in terms of correlation profiles
			
			
			found = False
			for i,box in enumerate(self.getRefBoxes()):
				if box.correlationscore == None:
					##print "continuing on faulty" - this was already printed above
					continue
				
				#print i,box.optprofile
				if found == False:
					self.optprofile = copy(box.optprofile)
					n = len(self.optprofile)
					found = True
				else:
					profile = box.optprofile
					for j in range(0,n):
						if profile[j] < self.optprofile[j]: self.optprofile[j] = profile[j]
		else:
			self.optprofile = self.dummybox.optprofile
			self.optthreshold = self.dummybox.correlationscore
		
	
		# determine the point in the profile where the drop in correlation score is the greatest, store it in radius
		self.optprofileradius = -1
		tmp = self.optprofile[0]
		for i in range(1,self.getConstrainingRadius()):
			# the tmp > 0 is a
			if self.optprofile[i] > tmp and tmp > 0:
				tmp = self.optprofile[i]
				self.optprofileradius = i
		
		self.__plotUpdate()
		#print 'NOW THEY ARE'
		#print 'threshod:',self.optthreshold
		#print 'profile:',self.optprofile
		#print 'optrad:',self.optprofileradius
		return True
	
	def __plotUpdate(self):
		prof = [] # self.selfmod == SwarmAutoBoxer.THRESHOLD (nothing is the right setting in this case)
		if self.selmode == SwarmAutoBoxer.SELECTIVE:
			prof = [self.optprofileradius]
		elif self.selmode == SwarmAutoBoxer.MORESELECTIVE:
			for i in range(0,self.optprofileradius+1): prof.append(i)
		
		try:
			self.parent.optparamsupdate(self.optthreshold,self.optprofile,prof)
		except: pass
	
	def __paintExcludedBoxAreas(self,exclusionimage,boxes):
	
		searchradius = self.getSearchRadius()

		for box in boxes:
			# xx and yy are the centers of the image, but in real image coordinates
			xx = box.xcorner + box.xsize/2
			yy = box.ycorner + box.ysize/2
			# shrink them to the small correlation image coordinates
			xx /= self.getBestShrink()
			yy /= self.getBestShrink()
			# Set a positive circle into the exclusionimage
			BoxingTools.set_radial_non_zero(exclusionimage,int(xx),int(yy),searchradius)
			