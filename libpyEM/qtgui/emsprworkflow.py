#!/usr/bin/env python
#
# Author: David Woolford 11/10/08 (woolford@bcm.edu)
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston MA 02111-1307 USA
#
#

from emform import EMFormModule,EMParamTable,EMTableFormModule
from emdatastorage import ParamDef
from PyQt4 import QtGui,QtCore
from PyQt4.QtCore import Qt
from EMAN2db import db_check_dict, db_open_dict,db_remove_dict,db_list_dicts,db_close_dict
from EMAN2 import *
import os
import copy
from emapplication import EMProgressDialogModule,get_application
from e2ctf import pspec_and_ctf_fit,GUIctfModule,write_e2ctf_output,get_gui_arg_img_sets
import subprocess
from pyemtbx.boxertools import set_idd_image_entry, TrimBox
import weakref
from e2history import HistoryForm
import time
from emsave import save_data
from emimagemx import EMDataListCache

class EmptyObject:
	'''
	This just because I need an object I can assign attributes to, and object() doesn't seem to work
	'''
	def __init__(self):
		pass
	

class EMFormTask(QtCore.QObject):
	'''
	Something that reflects the common interface for all of the tasks
	'''
	def __init__(self):
		QtCore.QObject.__init__(self)
		self.window_title = "Set me please" # inheriting classes should set this
		self.preferred_size = (480,640) # inheriting classes can change this if they choose

	def run_form(self): 
		self.form = EMFormModule(self.get_params(),get_application())
		self.form.qt_widget.resize(*self.preferred_size)
		self.form.setWindowTitle(self.window_title)
		get_application().show_specific(self.form)
		self.make_form_connections()
	def make_form_connections(self):
		'''
		Make the necesessary form connections
		'''
		QtCore.QObject.connect(self.form,QtCore.SIGNAL("emform_ok"),self.on_form_ok)
		QtCore.QObject.connect(self.form,QtCore.SIGNAL("emform_cancel"),self.on_form_cancel)
		QtCore.QObject.connect(self.form,QtCore.SIGNAL("emform_close"),self.on_form_close)
		
	def get_params(self): raise NotImplementedError
	
	def on_form_ok(self,params):
		self.write_db_entries(params)			
		self.form.closeEvent(None)
		self.form = None
		self.emit(QtCore.SIGNAL("task_idle"))
		
	def on_form_cancel(self):
		self.form.closeEvent(None)
		self.form = None
		self.emit(QtCore.SIGNAL("task_idle"))
	
	def on_form_close(self):
		self.emit(QtCore.SIGNAL("task_idle"))

	def closeEvent(self,event):
		self.form.closeEvent(None)
		#self.emit(QtCore.SIGNAL("task_idle")
		
	def write_db_entries(self,dictionary):
		'''
		Write the dictionary key/entries into the database using self.form_db_name
		Writes all keys except for "blurb" - note the the "blurb" key is mostly used in the context
		of these forms to display helpful information to the user - it doesn't need to be stored in the
		database 
		'''
		raise NotImplementedError
	
class EMErrorMessageDisplay:
	'''
	A step towards a better design
	'''
	def __init__(self): pass
	def run(error_message):
		'''
		error_message is a list of error messages
		'''
		msg = QtGui.QMessageBox()
		msg.setWindowTitle("Almost")
		mes = ""
		for error in error_message:
			mes += error
			
			if len(error) > 0 and error[-1] != '.':
				# correct my own inconsistencies....AWESOME
				mes += '.'
			if error != error_message[-1]: mes += "\n"
		msg.setText(mes)
		msg.exec_()
	
	run = staticmethod(run)
		
class WorkFlowTask(QtCore.QObject):
	def __init__(self):
		QtCore.QObject.__init__(self)
		self.window_title = "Set me please" # inheriting classes should set this
		self.preferred_size = (480,640) # inheriting classes can change this if they choose
		self.form_db_name = None # specify this to make use of automated parameter storage (see write_db_entries(self,...) ) - don't forget the "bdb:"
		self.project_db_entries = ["global.num_cpus","global.apix","global.microscope_voltage","global.microscope_cs","global.memory_available","global.particle_mass"] # used to write entries to a specific db
	
	def run_form(self):
		self.form = EMFormModule(self.get_params(),get_application())
		self.form.qt_widget.resize(*self.preferred_size)
		self.form.setWindowTitle(self.window_title)
		get_application().show_specific(self.form)
		QtCore.QObject.connect(self.form,QtCore.SIGNAL("emform_ok"),self.on_form_ok)
		QtCore.QObject.connect(self.form,QtCore.SIGNAL("emform_cancel"),self.on_form_cancel)
		QtCore.QObject.connect(self.form,QtCore.SIGNAL("emform_close"),self.on_form_close)
		QtCore.QObject.connect(self.form,QtCore.SIGNAL("display_file"),self.on_display_file)
	
	def get_params(self): raise NotImplementedError
	
	def on_display_file(self,filename):
		self.emit(QtCore.SIGNAL("display_file"),filename)	
		
	def on_form_ok(self,params):
		for k,v in params.items():
			self.write_db_entry(k,v)
			
		self.form.closeEvent(None)
		self.form = None
	
		self.emit(QtCore.SIGNAL("task_idle"))
		
	def on_form_cancel(self):
		self.form.closeEvent(None)
		self.form = None

		self.emit(QtCore.SIGNAL("task_idle"))
	
	def on_form_close(self):
		self.emit(QtCore.SIGNAL("task_idle"))

	def closeEvent(self,event):
		self.form.closeEvent(None)
		#self.emit(QtCore.SIGNAL("task_idle")
		
	def write_db_entries(self,dictionary):
		'''
		Write the dictionary key/entries into the database using self.form_db_name
		Writes all keys except for "blurb" - note the the "blurb" key is mostly used in the context
		of these forms to display helpful information to the user - it doesn't need to be stored in the
		database 
		'''
		if self.form_db_name != None: db = db_open_dict(self.form_db_name)
		else: db = None
		
		project_db = db_open_dict("bdb:project")
		for k,v in dictionary.items():
			if k == "blurb": continue
			
			if k in self.project_db_entries: project_db[k] = v
			else:
				if db != None: db[k] = v
		
		#if self.form_db_name != None: db_close_dict(self.form_db_name)
		#db_close_dict("bdb:project")
		
	def get_default_filenames_from_form_db(self,key="filenames"):
		'''
		Opens the self.form_db_name database and retrieves the filenames entry
		Returns None if self.form_db_name is None
		Returns an empty list if the "filenames" entry doesn't exist in the existing database
		'''
		default_selections = None
		if self.form_db_name != None:
			db = db_open_dict(self.form_db_name)
			default_selections = db.get(key,dfl=[])
			#db_close_dict(self.form_db_name)
			
		return default_selections
	
	def write_db_entry(self,key,value):
		'''
		This function is becoming deprecated, used write_db_entries instead
		'''
		db = db_open_dict("bdb:project")
		if len(key) > 5 and key[:6] == "global":
			db[key] = value
		else:
			pass
		
		#db_close_dict("bdb:project")
	def get_wd(self):
		'''
		Get the working directory, originally introduced to provide a centralized mechanism for accessing the working directory,
		specificially for the purpose of spawning processes. Could be used more generally, however.
		'''
		return e2getcwd()

	def spawn_task(self,program,options,string_args,bool_args,additional_args=[],temp_file_name="e2workflow_tmp.txt"):
		'''
		splits the task over the available processors
		example-
		program="e2ctf.py"
		options is an object with the filenames, all string args and all bool_args as attributes 
		string_args=["
		bool_args=["
		additional_args=["--auto_db,--auto_fit"]
		temp_file_name = "etctf_auto_tmp.txt"
		'''
		project_db = db_open_dict("bdb:project")
		ncpu = project_db.get("global.num_cpus",dfl=num_cpus())
		cf = float(len(options.filenames))/float(ncpu) # common factor
		
		files = []
		for n in range(ncpu):
			files.append([])
			
		# distribute the names into bins
		for i,f in enumerate(options.filenames):
			idx = i % ncpu
			files[idx].append(f) 
		
		for n in range(ncpu):
			#print "n"
			filenames = files[n]
			if len(filenames) == 0: continue # maybe there are more CPUS then filenames
								
			args = [e2getinstalldir()+"/bin/"+program]
	
			for name in filenames:
				args.append(name)
			
			for string in string_args:
				args.append("--"+string+"="+str(getattr(options,string)))

			# okay the user can't currently change these, but in future the option might be there
			for string in bool_args:
				# these are all booleans so the following works:
				if getattr(options,string):
					args.append("--"+string)
					
			for arg in additional_args:
				args.append(arg)
#			print "command is ",program
#			for i in args: print i
			
			#print args
			file = open(temp_file_name,"w+")
			if(sys.platform != 'win32'):
				args_adjusted = []
			else:
				args_adjusted = ["pythonw"]
			args_adjusted.extend(args)
			#print args_adjusted
			process = subprocess.Popen(args_adjusted,stdout=file,stderr=subprocess.STDOUT)
			print "started process",process.pid
			self.emit(QtCore.SIGNAL("process_started"),process.pid)
			
		#db_close_dict("bdb:project")
	
	def spawn_single_task(self,program,options,string_args,bool_args,additional_args=[],temp_file_name="e2workflow_tmp.txt"):
		'''
		runs a single job
		example-
		program="e2ctf.py"
		options is an object with the filenames, all string args and all bool_args as attributes 
		string_args=["
		bool_args=["
		additional_args=["--auto_db,--auto_fit"]
		temp_file_name = "etctf_auto_tmp.txt"
		'''
		project_db = db_open_dict("bdb:project")	
								
		#args = [program]
		args = [e2getinstalldir()+"/bin/"+program]
		for name in options.filenames:
			args.append(name)

		for string in string_args:
			args.append("--"+string+"="+str(getattr(options,string)))

		# okay the user can't currently change these, but in future the option might be there
		for string in bool_args:
			# these are all booleans so the following works:
			if getattr(options,string):
				args.append("--"+string)
				
		for arg in additional_args:
			args.append(arg)
		print "command is ",program
		for i in args: print i,
#		print ""
#		
		#print args
		file = open(temp_file_name,"w+")
		if(sys.platform != 'win32'):
			args_adjusted = []
		else:
			args_adjusted = ["pythonw"]
		args_adjusted.extend(args)
		#print args_adjusted
		process = subprocess.Popen(args_adjusted,stdout=file,stderr=subprocess.STDOUT)
		print "started process",process.pid
		self.emit(QtCore.SIGNAL("process_started"),process.pid)
		
		#db_close_dict("bdb:project")
		
	def run_select_files_msg(self):
		'''
		Runs a QMessageBox asking for the user to select files for processing
		'''
		msg = QtGui.QMessageBox()
		msg.setWindowTitle("Almost")
		msg.setText("Please select files for processing")
		msg.exec_()

	def show_error_message(self,error_message):
		'''
		error_message is a list of error messages
		'''
		EMErrorMessageDisplay.run(error_message)
#		msg = QtGui.QMessageBox()
#		msg.setWindowTitle("Almost")
#		mes = ""
#		for error in error_message:
#			mes += error
#			
#			if len(error) > 0 and error[-1] != '.':
#				# correct my own inconsistencies....AWESOME
#				mes += '.'
#			if error != error_message[-1]: mes += "\n"
#		msg.setText(mes)
#		msg.exec_()
		
	def get_latest_r2d_classes(self):
		dirs = get_numbered_directories("r2d_")
		# allright everything left in dirs is "r2d_??" where the ?? is castable to an int, so we should be safe now
		class_files = []
		class_dims = []
		class_ptcls = []
		for dir in dirs:
			classes_db = None
			# check for 00 to 09 but 00 is replaced with "init"
			db_first_part = "bdb:"+dir+"#classes_"
			cont = True
			for i in range(0,10):
				for j in range(0,10):
					if i == 0 and j == 0:
						db_name = db_first_part+"init"
					else:
						db_name = db_first_part+str(i)+str(j)
						
					if db_check_dict(db_name):
						classes_db = db_name
					else:
						if i != 0 or j != 0:
							cont = False
							break
						#else just check for 01 incase the user has specified the --initial arugment
				if not cont:
					break
				
			if classes_db != None:
				class_files.append(classes_db)
				cl_db = db_open_dict(classes_db,ro=True)
				if cl_db.has_key("maxrec"):
					class_ptcls.append(cl_db["maxrec"]+1)
					hdr = cl_db.get_header(0)
					class_dims.append(str(hdr["nx"])+'x'+str(hdr["ny"])+'x'+str(hdr["nz"]))
				else:
					class_ptcls.append("")
					class_dims.append("")
					
				#db_close_dict(classes_db)
					
		return class_files,class_ptcls,class_dims
	
	def check_sym(self,params,options):
		error_message = []
		if params["symname"] in ["c","d","h"]:
			n = params["symnumber"]
			fail = False
			if len(n) == 0: fail = True
			try: int(n)
			except: fail = True
			
			if not fail:
				if int(n) < 1:
					fail = True
					
			if fail:
				error_message.append("The symmetry number must be specified for c,d, and h.")
			else:
				options.sym=params["symname"]+n
		elif len(params["symnumber"]) != 0:
			error_message.append("There is something entered in the symmetry number box but you have not specified c, d or h symmetry.")
		else:
			options.sym = params["symname"]	
			
		return error_message
	
	def get_cmps_list(self):
		return dump_cmps_list().keys()
	
	def get_aligners_list(self):
		return dump_aligners_list().keys()
	
	def get_projectors_list(self):
		return dump_projectors_list().keys()
	
	def get_orientgens_list(self):
		return dump_orientgens_list().keys()
		
	def get_averagers_list(self):
		return dump_averagers_list().keys()
		
#		cmps.append("None") I think this is necessary
		
class HistoryTask(WorkFlowTask,HistoryForm):
	def __init__(self):
		WorkFlowTask.__init__(self)
		# don't need HistoryFrom init
		self.wd = os.getcwd()
		self.window_title = "History"
	
	def run_form(self):	
		self.form = EMFormModule(self.get_history_table(),get_application())
		self.form.qt_widget.resize(*self.preferred_size)
		self.form.setWindowTitle(self.window_title)
		self.form.qt_widget.setWindowIcon(QtGui.QIcon(os.getenv("EMAN2DIR")+"/images/feather.png"))
		get_application().show_specific(self.form)
		QtCore.QObject.connect(self.form,QtCore.SIGNAL("emform_ok"),self.on_form_ok)
		QtCore.QObject.connect(self.form,QtCore.SIGNAL("emform_cancel"),self.on_form_cancel)
		QtCore.QObject.connect(self.form,QtCore.SIGNAL("emform_close"),self.on_form_close)
		
class ChangeDirectoryTask(WorkFlowTask):
	def __init__(self):
		WorkFlowTask.__init__(self)
		self.window_title = "Change project directory"
	
	def run_form(self):	
		
		fsp=QtGui.QFileDialog.getExistingDirectory(None, "Choose a directory")
		fsp = str(fsp)
		if os.path.exists(fsp):
			os.chdir(fsp)
			return fsp
		else: return None
		
	def closeEvent(self,event):
		pass
		#self.form.closeEvent(None)

class TomohunterTask(WorkFlowTask):
	'''
	A class that manages the initialization component of a Tomography workflow
	'''
	
	documentation_string = "This is useful information about this task."

	def __init__(self):
		WorkFlowTask.__init__(self)
		self.window_title = "Tomography input form"
		self.preferred_size = (640,480)
	def get_params(self):
		params = []
		project_db = db_open_dict("bdb:tomography")
		params.append(ParamDef(name="blurb",vartype="text",desc_short="SPR",desc_long="Information regarding this task",property=None,defaultunits=TomohunterTask.documentation_string,choices=None))
		targetimage = ParamDef(name="targetimage",vartype="url",desc_short="target image file name",desc_long="target image file name",property=None,defaultunits=project_db.get("targetimage",dfl=[]),choices=[])
		probeimage = ParamDef(name="probeimage",vartype="url",desc_short="probe image file name",desc_long="probe image file name",property=None,defaultunits=project_db.get("probeimage",dfl=[]),choices=[])
		norm = ParamDef(name="normalization",vartype="int",desc_short="normalization",desc_long="if the normalization needed",property=None,defaultunits=0,choices=[0,1])
		nsoln = ParamDef(name="nsoln",vartype="int",desc_short="#solution",desc_long="number of solution",property=None,defaultunits=1,choices=None)
		thresh = ParamDef(name="thresh",vartype="float",desc_short="threshold",desc_long="threshold",property=None,defaultunits=1.0,choices=None)
		searchx = ParamDef(name="searchx",vartype="int",desc_short="searchx",desc_long="searchx",property=None,defaultunits=0,choices=None)
		searchy = ParamDef(name="searchy",vartype="int",desc_short="searchy",desc_long="searchy",property=None,defaultunits=0,choices=None)
		searchz = ParamDef(name="searchz",vartype="int",desc_short="searchz",desc_long="searchz",property=None,defaultunits=0,choices=None)
		ralt = ParamDef(name="ralt",vartype="float",desc_short="ralt",desc_long="Altitude range",property=None,defaultunits=180.0,choices=None)
		dalt = ParamDef(name="dalt",vartype="float",desc_short="dalt",desc_long="Altitude delta",property=None,defaultunits=10.0,choices=None)
		daz = ParamDef(name="daz",vartype="float",desc_short="daz",desc_long="Azimuth delta",property=None,defaultunits=10.0,choices=None)
		rphi = ParamDef(name="rphi",vartype="float",desc_short="rphi",desc_long="Phi range",property=None,defaultunits=180.0,choices=None)
		dphi = ParamDef(name="dphi",vartype="float",desc_short="dphi",desc_long="Phi delta",property=None,defaultunits=10.0,choices=None)
		params.append([targetimage,probeimage])
		params.append([norm,thresh,nsoln])
		params.append([searchx,searchy,searchz])
		params.append([ralt,dalt,daz,rphi,dphi])
		#db_close_dict("bdb:project")
		return params

	def write_db_entry(self,key,value):
		WorkFlowTask.write_db_entry(self,key,value)
	
	def check_params(self,params):
		error_msg = []
		if len(params["targetimage"]) != 1: error_msg.append("Please choose a single target file to proceed")
		if len(params["probeimage"]) != 1: error_msg.append("Please choose a single probe file to proceed")
		return error_msg
	
	def on_form_ok(self,params):
		print params
		
		error_message = self.check_params(params)
		if len(error_message):
			self.show_error_message(error_message)
			return
		
		self.write_db_entries(params) # will only write filenames
		options = EmptyObject()
		string_args = ["dalt","ralt","dphi","rphi","raz","daz","thresh","nsoln","searchx","searchy","searchz"]
		options.filenames = [params['targetimage'][0], params['probeimage'][0]]
		options.dalt = params['dalt']
		options.ralt = params['ralt']
		options.dphi = params['dphi']
		options.rphi = params['rphi']
		options.raz = params['ralt']
		options.daz = params['dalt']
		options.thresh = params['thresh']
		options.nsoln = params['nsoln']
		options.searchx = params['searchx']
		options.searchy = params['searchy']
		options.searchz = params['searchz']
		bool_args = []
		additional_args = []
		temp_file_name = "e2tomohunter_stdout.txt"
		self.spawn_single_task('e2tomohunter.py',options,string_args,bool_args,additional_args,temp_file_name)
		self.emit(QtCore.SIGNAL("task_idle"))
		self.form.closeEvent(None)
		self.form = None
	
	
class SPRInitTask(WorkFlowTask):
	'''
	A class that manages the initialization component of a Single Particle
	Reconstruction workflow
	'''
	
	# stolen from wikipedia
	Ddocumentation_string = "In physics, in the area of microscopy, single particle reconstruction is a technique in which large numbers of images (10,000 - 1,000,000) of ostensibly identical individual molecules or macromolecular assemblies are combined to produce a 3 dimensional reconstruction. This is a complementary technique to crystallography of biological molecules. As molecules/assembies become larger, it becomes more difficult to prepare high resolution crystals. For single particle reconstruction, the opposite is true. Larger objects actually improve the resolution of the final structure. In single particle reconstruction, the molecules/assemblies in solution are prepared in a thin layer of vitreous (glassy) ice, then imaged on an electron cryomicroscope (see Transmission electron microscopy). Images of individual molecules/assemblies are then selected from the micrograph and then a complex series of algorithms is applied to produce a full volumetric reconstruction of the molecule/assembly. In the 1990s this technique was limited to roughly 2 nm resolution, providing only gross features of the objects being studied. However, recent improvements in both microscope technology as well as available computational capabilities now make 0.5 nm resolution possible."
	documentation_string = "Welcome to the EMAN2 workflow. Use this tool to step through and manage the process of generating single particle reconstructions. Get started by entering what you can of the parameters in this form and then proceed to the next step task in the workflow."
	def __init__(self):
		WorkFlowTask.__init__(self)
		self.window_title = "Project information"
	def get_params(self):
		params = []
		project_db = db_open_dict("bdb:project")
		#params.append(ParamDef(name="global.spr_raw_file_names",vartype="url",desc_short="File Names",desc_long="The raw data from which particles will be extracted and ultimately refined to produce a reconstruction",property=None,defaultunits=db_entry("global.spr_raw_file_names","bdb:project",[]),choices=[]))
		params.append(ParamDef(name="blurb",vartype="text",desc_short="SPR",desc_long="Information regarding this task",property=None,defaultunits=SPRInitTask.documentation_string,choices=None))
		
		papix = ParamDef(name="global.apix",vartype="float",desc_short="A/pix for project",desc_long="The physical distance represented by the pixel spacing",property=None,defaultunits=project_db.get("global.apix",dfl=1.1),choices=None)
		pmass = ParamDef(name="global.particle_mass",vartype="float",desc_short="Particle mass (kda)",desc_long="The mass of the particle in kilodaltons",property=None,defaultunits=project_db.get("global.particle_mass",dfl=800),choices=None)
		
		pvolt = ParamDef(name="global.microscope_voltage",vartype="float",desc_short="Microscope voltage",desc_long="The operating voltage of the microscope in kilo volts",property=None,defaultunits=project_db.get("global.microscope_voltage",dfl=300),choices=None)
		pcs = ParamDef(name="global.microscope_cs",vartype="float",desc_short="Microscope Cs",desc_long="Microscope spherical aberration constant",property=None,defaultunits=project_db.get("global.microscope_cs",dfl=2.0),choices=None)
		pncp = ParamDef(name="global.num_cpus",vartype="int",desc_short="Number of CPUs",desc_long="Number of CPUS available for the project to use",property=None,defaultunits=project_db.get("global.num_cpus",dfl=num_cpus()),choices=None)
		mem = memory_stats()
		pmem = ParamDef(name="global.memory_available",vartype="float",desc_short="Memory usage (%.2f Gb total)" %mem[0],desc_long="The total amount of system memory you want to make available to the project in gigabytes",property=None,defaultunits=project_db.get("global.memory_available",dfl=mem[1]),choices=None)
		params.append(pmass)
		params.append(papix)
		params.append(pvolt)
		params.append(pcs)
		params.append(pncp)
		params.append(pmem)
		#db_close_dict("bdb:project")
		return params

	def write_db_entry(self,key,value):
		WorkFlowTask.write_db_entry(self,key,value)		


class EMRawDataReportTask(WorkFlowTask):	
	documentation_string = "This forms displays the micrograph and/or ccds images that  you currently have associated with this project"
	warning_string = "\n\n\nNOTE: There are no images currenty associated with the project. Please associate or import images"
	def __init__(self):
		WorkFlowTask.__init__(self)
		self.window_title = "Micrographs In Project"
		self.project_files_at_init = None # stores the known project files when the form is created and shown - that way if cancel is hit we can restore the original parameters
		self.project_list = "global.spr_raw_file_names"
		
	def get_image_dimensions(file_name):
		'''
		A static function for getting the dimensions of a file as a string
		'''
		nx,ny,nz = gimme_image_dimensions3D(file_name)
		return "%ix%ix%i" %(nx,ny,nz)
	
	get_image_dimensions = staticmethod(get_image_dimensions)

	def get_raw_data_table(self):
		'''
		Gets an EM2DFileTable - this is type of class that the emform knows how to handle 
		'''
		project_db = db_open_dict("bdb:project")
		project_names = project_db.get(self.project_list,dfl=[])
		self.project_files_at_init = project_names # so if the user hits cancel this can be reset

		from emform import EM2DFileTable,EMFileTable
		table = EM2DFileTable(project_names,desc_short="Raw Data Files",desc_long="")
		context_menu_data = EMRawDataReportTask.ProjectListContextMenu(self.project_list)
		table.add_context_menu_data(context_menu_data)
		table.add_button_data(EMRawDataReportTask.ProjectAddRawDataButton(table,context_menu_data))
	
		#p.append(pdims) # don't think this is really necessary
		return table,len(project_names)
	
	def get_raw_data_table_custom(self):
		'''
		Calls get_raew_data_table and then adds the Dimensions column
		'''
		table,n = self.get_raw_data_table()
		from emform import EMFileTable
		table.add_column_data(EMFileTable.EMColumnData("Dimensions",EMRawDataReportTask.get_image_dimensions,"The dimensions of the file on disk"))
		return table,n
	
	class ProjectAddRawDataButton():
		def __init__(self,table_widget,context_menu_data):
			self.table_widget = weakref.ref(table_widget)
			self.context_menu_data = context_menu_data
			self.name = "Browse To Add"
			
		def function(self,bool):
			self.context_menu_data.context_menu["Add"]([],self.table_widget())
			

	class ProjectListContextMenu:
		def __init__(self,project_list="global.spr_raw_file_names"):
			self.project_list = project_list
			self.validator = AddFilesToProjectValidator(self.project_list)
			self.context_menu = {}
			self.context_menu["Remove"] = EMRawDataReportTask.ProjectListContextMenu.RemoveFilesFromProject(self.project_list)
			self.context_menu["Add"] = EMRawDataReportTask.ProjectListContextMenu.AddFilesToProjectViaContext(self.project_list)
		
		def items(self):
			return self.context_menu.items()
		
		
		class RemoveFilesFromProject:
			def __init__(self,project_list="global.spr_raw_file_names"):
				self.project_list = project_list
			def __call__(self,names,table_widget):
#		def remove_files_from_project(self,names,table_widget):
				if len(names) == 0: return # nothing happened
			
				from emform import get_table_items_in_column
				entries = get_table_items_in_column(table_widget,0)
				text_entries = [table_widget.convert_text(str(i.text())) for i in entries]
				
				project_db = db_open_dict("bdb:project")
				project_names = project_db.get(self.project_list,dfl=[])
				
				full_names = [table_widget.convert_text(name) for name in names]
		
				for name in full_names:
					if name not in project_names:
						EMErrorMessageDisplay.run(["%s is not in the project list" %name])
						return
				
				indices = [ text_entries.index(name) for name in full_names]
				indices.sort()
				indices.reverse()
				for idx in indices:
					table_widget.removeRow(idx)
					project_names.remove(text_entries[idx])
					
				
				project_db[self.project_list] = project_names
				
		class AddFilesToProject:
			def __init__(self,project_list="global.spr_raw_file_names"):
				self.project_list = project_list
				
			def __call__(self,list_of_names,table_widget):
		
		#def add_files_to_project(self,list_of_names,table_widget):	
				project_db = db_open_dict("bdb:project")
				project_names = project_db.get(self.project_list,dfl=[])
				project_name_tags = [get_file_tag(name) for name in project_names]
				
				for name in list_of_names:
					if not file_exists(name):
						EMErrorMessageDisplay.run(["%s does not exists" %name])
						return
				
				for name in list_of_names:
					if get_file_tag(name) in project_name_tags:
						EMErrorMessageDisplay.run(["%s is already in the project" %name])
						return
						
				# if we make it here we're good
				# first add entries to the table
				table_widget.add_entries(list_of_names)
				
				# then add names to the database
				project_names.extend(list_of_names)
				project_db[self.project_list] = project_names
		
		class AddFilesToProjectViaContext:
			def __init__(self,project_list="global.spr_raw_file_names"):
				self.project_list = project_list
				self.validator = AddFilesToProjectValidator(self.project_list)
				
			def __call__(self,list_of_names,table_widget):
			
		#def add_files_from_context_menu(self,list_of_names,table_widget):
				from emselector import EMSelectorModule
				em_qt_widget = EMSelectorModule()
				
				em_qt_widget.widget.set_validator(self.validator)
				files = em_qt_widget.exec_()
				if files != "":
					if isinstance(files,str): files = [files]
					
					from emform import get_table_items_in_column
					entries = get_table_items_in_column(table_widget,0)
					entrie_tags = [get_file_tag(str(i.text())) for i in entries]
					file_tags = [get_file_tag(i) for i in files]
					error_messages = []
					for idx,tag in enumerate(file_tags):
						if tag in entrie_tags:
							error_messages.append("%s is already listed" %files[idx])
					
				
					if len(error_messages) > 0:
						EMErrorMessageDisplay.run(error_messages)
						return
				a = EMRawDataReportTask.ProjectListContextMenu.AddFilesToProject(self.project_list)
				a(files,table_widget)
				#self.add_files_to_project(files,table_widget)
			
	def get_params(self):
		
		project_db = db_open_dict("bdb:project")
		
		params = []
		
		p,n = self.get_raw_data_table_custom()
		
		if n == 0 and False:
			params.append(ParamDef(name="blurb",vartype="text",desc_short="Files",desc_long="",property=None,defaultunits=EMRawDataReportTask.documentation_string+EMRawDataReportTask.warning_string,choices=None))
		else:
			params.append(ParamDef(name="blurb",vartype="text",desc_short="Files",desc_long="",property=None,defaultunits=EMRawDataReportTask.documentation_string,choices=None))
			params.append(p)
			
		return params
	
	def on_form_cancel(self):
		self.recover_original_raw_data_list()
		
		self.form.closeEvent(None)
		self.form = None
		self.emit(QtCore.SIGNAL("task_idle"))
	
	def recover_original_raw_data_list(self):
		'''
		Called if the user hits cancel - if they removed some files or added files the changes
		are not saved unless the user hits ok
		'''
		project_db = db_open_dict("bdb:project")
		project_db["global.spr_raw_file_names"] = self.project_files_at_init
		
	
	def on_form_ok(self,params):
		self.form.closeEvent(None)
		self.form = None
		
class EMTomoRawDataReportTask(EMRawDataReportTask):
	def __init__(self):
		EMRawDataReportTask.__init__(self)
		self.project_list = "global.tomo_raw_file_names"
		
	def get_raw_data_table(self):
		'''
		Gets an EMTomographicFileTable - this is type of class that the emform knows how to handle 
		'''
		project_db = db_open_dict("bdb:project")
		project_names = project_db.get(self.project_list,dfl=[])
		self.project_files_at_init = project_names # so if the user hits cancel this can be reset

		from emform import EMTomographicFileTable,EMFileTable
		table = EMTomographicFileTable(project_names,desc_short="Raw Data Files",desc_long="")
		context_menu_data = EMRawDataReportTask.ProjectListContextMenu(self.project_list)
		table.add_context_menu_data(context_menu_data)
		table.add_button_data(EMRawDataReportTask.ProjectAddRawDataButton(table,context_menu_data))
	
		#p.append(pdims) # don't think this is really necessary
		return table,len(project_names)
		
class AddFilesToProjectValidator():
	def __init__(self,project_list="global.spr_raw_file_names"):
		self.project_list = project_list
	def validate_file_name(self,list_of_names):
		'''
		a validator for the select module
		@exception RuntimeError thrown if list_of_names is not a list
		@return 0 if something went wrong , 1 if it's okay to call save now
		'''
		if not isinstance(list_of_names,list):
			if isinstance(list_of_names,str): list_of_names = [list_of_names]
			else: raise RuntimeError("Files needs to be a list")
		
		project_db = db_open_dict("bdb:project")
		project_names = project_db.get(self.project_list,dfl=[])
		project_name_tags = [get_file_tag(name) for name in project_names]
		
		for name in list_of_names:
			if not file_exists(name):
				EMErrorMessageDisplay.run(["%s does not exists" %name])
				return 0
		
		for name in list_of_names:
			if get_file_tag(name) in project_name_tags:
				EMErrorMessageDisplay.run(["%s is already in the project" %name])
				return 0
			
		return 1

class MicrographCCDImportTask(WorkFlowTask):	
	documentation_string = "Use this tool for importing flat files into the raw_data directory in the project database. Files that you import in this way will be automatically added the list of files in the project."
	
	def __init__(self):
		WorkFlowTask.__init__(self)
		self.window_title = "Import micrographs"
		self.thumb_shrink = -1
	def get_params(self):
		params = []
		project_db = db_open_dict("bdb:project")
		params.append(ParamDef(name="blurb",vartype="text",desc_short="Importing image data",desc_long="",property=None,defaultunits=MicrographCCDImportTask.documentation_string,choices=None))
		params.append(ParamDef(name="import_micrograph_ccd_files",vartype="url",desc_short="File Names",desc_long="The raw data from which particles will be extracted and ultimately refined to produce a reconstruction",property=None,defaultunits=[],choices=[]))
		pinvert = ParamDef(name="invert",vartype="boolean",desc_short="Invert",desc_long="Tick this if you want eman2 to invert your images while importing",property=None,defaultunits=False,choices=None)
		pxray = ParamDef(name="xraypixel",vartype="boolean",desc_short="X-ray pixel",desc_long="Tick this if you want eman2 to automatically filter out X-ray pixels while importing",property=None,defaultunits=False,choices=None)
		pnorm = ParamDef(name="norm.edgemean",vartype="boolean",desc_short="Edge norm",desc_long="Tick this if you want eman2 to automatically normalize your images using the edgmean approach",property=None,defaultunits=True,choices=None)
		pthumbnail = ParamDef(name="thumbs",vartype="boolean",desc_short="Thumbnails",desc_long="Tick this if you want eman2 to automatically generate thumbnails for your images. This will save time at later stages in the project",property=None,defaultunits=True,choices=None)
		
		params.append([pinvert,pxray,pnorm,pthumbnail])
		
		#db_close_dict("bdb:project")
		return params
	
	def on_form_ok(self,params):
		
		error_message = self.check_params(params)
		if len(error_message):
			self.show_error_message(error_message)
			return
 		
		for k,v in params.items():
			if k == "import_micrograph_ccd_files":
				self.do_import(params)
			else:
				self.write_db_entry(k,v)

		self.form.closeEvent(None)
		self.form = None
	
		self.emit(QtCore.SIGNAL("task_idle"))

	def check_params(self,params):
		error_message = []
		filenames = params["import_micrograph_ccd_files"]
		
		if len(filenames) == 0:
			error_message.append("Please specify files to import.")
			return error_message
		
		for name in filenames:
			if len(name) == 0: continue
			if not file_exists(name):
				error_message.append("File %s doesn't exist." %name)
			else:
				try:
					e = EMData()
					e.read_image(name,0,1)
					n = EMUtil.get_image_count(name)
					if n > 1:
						error_message.append("File %s contains more than 1 image." %name)
				except:
					error_message.append("File %s is not a valid EM image." %name)
				
				
			
		no_dir_names = [get_file_tag(name) for name in filenames]
		
		for name in filenames:
			if name.find("bdb:rawdata#") != -1:
				error_message.append("Can't import files that are already in the project raw data directory : %s is invalid" %name)
		
		for name in no_dir_names:
			if no_dir_names.count(name) > 1:
				error_message.append("Can't import files with the same name : %s " %name)

		project_db = db_open_dict("bdb:project")
		current_project_files = project_db.get("global.spr_raw_file_names",dfl=[])
		cpft = [get_file_tag(file) for file in current_project_files]
		
		for name in filenames:
			
			tag = get_file_tag(name)
			if tag in cpft:
				error_message.append("Can't import images have identical tags to those already in the database, the problem is with %s" %name)
				
			
			db_name = "bdb:raw_data#"+tag
			if db_check_dict(db_name):
				error_message.append("There is already a raw_data database entry for %s" %db_name)

		return error_message

	def do_import(self,params):
		filenames = params["import_micrograph_ccd_files"]
		
		project_db = db_open_dict("bdb:project")
#		
		current_project_files = project_db.get("global.spr_raw_file_names",dfl=[])

		# get the number of process operation - the progress dialog reflects image copying and image processing operations
		num_processing_operations = 2 # there is atleast a copy and a disk write
		if params["invert"]: num_processing_operations += 1
		if params["xraypixel"]: num_processing_operations += 1
		if params["thumbs"]:num_processing_operations += 1
		if params["norm.edgemean"]:num_processing_operations += 1
		
		
		# now add the files to db (if they don't already exist
		progress = EMProgressDialogModule(get_application(),"Importing files into database...", "Abort import", 0, len(filenames)*num_processing_operations,None)
		progress.qt_widget.show()
		i = 0
		cancelled = False # if the user cancels the import then we must act
		cancelled_dbs = []
		for name in filenames:
			
			tag = get_file_tag(name)
			db_name = "bdb:raw_data#"+tag

			e = EMData()
			e.read_image(name,0)
			i += 1
			progress.qt_widget.setValue(i)	
			get_application().processEvents()
			e.set_attr("disk_file_name",name)
			
			if params["norm.edgemean"]:
				e.process_inplace("normalize.edgemean")
				i += 1
				progress.qt_widget.setValue(i)
				get_application().processEvents()
			
			if params["invert"]:
				e.mult(-1)
				i += 1
				progress.qt_widget.setValue(i)
				get_application().processEvents()
			
			if params["xraypixel"]:
				e.process_inplace("threshold.clampminmax.nsigma",{"nsigma":4,"tomean":True})
				i += 1
				progress.qt_widget.setValue(i)
				get_application().processEvents()
				
			e.write_image(db_name,0)
			#db_close_dict(db_name)
			cancelled_dbs.append(db_name)
			i += 1
			progress.qt_widget.setValue(i)
			get_application().processEvents()
			current_project_files.append(db_name)
				
			if params["thumbs"]:
				shrink = self.get_thumb_shrink(e.get_xsize(),e.get_ysize())
				thumb = e.process("math.meanshrink",{"n":shrink})
				thumb.process_inplace("normalize.edgemean")
				set_idd_image_entry(db_name,"image_thumb",thumb) # boxer uses the full name
				i += 1
				progress.qt_widget.setValue(i)
				get_application().processEvents()
				
			if progress.qt_widget.wasCanceled():
				cancelled = True
				for data_db in cancelled_dbs: # policy here is to remove only the raw data dbs - the e2boxer thumbnails are tiny and I don't have time...
					db_remove_dict(data_db)
				break
			
			
			
				
		progress.qt_widget.setValue(len(filenames))
		progress.qt_widget.close()
		
		if not cancelled:
			project_db["global.spr_raw_file_names"] = current_project_files
			#db_close_dict("bdb:project")
		
	def get_thumb_shrink(self,nx,ny):
		if self.thumb_shrink == -1:
			shrink = 1
			inx =  nx/2
			iny =  ny/2
			while ( inx >= 128 and iny >= 128):
				inx /= 2
				iny /= 2
				shrink *= 2
		
			self.thumb_shrink=shrink
		
		return self.thumb_shrink
			
	def on_import_cancel(self):
		print "canceled"
		
class ParticleWorkFlowTask(WorkFlowTask):
	'''
	Encapsulates some functionality  common to the particle based work flow tasks
	Such tasks should inherit from this class, not the the WorkFlowTask
	'''
	def __init__(self):
		WorkFlowTask.__init__(self)

	def get_particle_selection_table(self,ptcl_list):
		'''
		
		'''
		from emform import EM2DStackTable,EMFileTable
		table = EM2DStackTable(ptcl_list,desc_short="Particles",desc_long="")
		print ptcl_list
		if len(ptcl_list) != 0:
			a = EMData()
			a.read_image(ptcl_list[0],0,True)
			d = a.get_attr_dict()
			if d.has_key("ctf"):
				self.column_data = ParticleWorkFlowTask.CTFColumns()
				table.add_column_data(EMFileTable.EMColumnData("SNR",self.column_data.get_snr,"The averaged SNR"))
				table.add_column_data(EMFileTable.EMColumnData("Defocus",self.column_data.get_defocus,"The estimated defocus"))
				table.add_column_data(EMFileTable.EMColumnData("B Factor",self.column_data.get_bfactor,"The estimated B factor, note this is ~4x greater than in EMAN1"))
				table.add_column_data(EMFileTable.EMColumnData("Sampling",self.column_data.get_sampling,"The amount of sampling used for generating CTF parameters"))
		else:
			context_menu_data = ParticleWorkFlowTask.DataContextMenu()
			table.add_context_menu_data(context_menu_data)
			table.add_button_data(ParticleWorkFlowTask.AddDataButton(table,context_menu_data))
		#table.insert_column_data(1,EMFileTable.EMColumnData("Particles On Disk",ParticleReportTask.get_num_ptcls,"Particles currently stored on disk that are associated with this image"))
		#table.insert_column_data(2,EMFileTable.EMColumnData("Particle Dims",ParticleReportTask.get_particle_dims,"The dimensions of the particles that are stored on disk"))
	
				
		table.add_column_data(EMFileTable.EMColumnData("Particles On Disk",ParticleReportTask.get_num_ptcls,"Particles currently stored on disk that are associated with this image"))
		table.add_column_data(EMFileTable.EMColumnData("Particle Dims",ParticleReportTask.get_particle_dims,"The dimensions of the particles that are stored on disk"))

		return table, len(ptcl_list)

	class CTFColumns:
		'''
		Basically some functions with a cache - the cache is to avoid
		re-reading stuff from disk multiple times
		'''
		def __init__(self):
			self.ctf_cache = {}
						
#		def __del__(self):
#			print "CTF columns dies"
			
		def get_defocus(self,name):
			if self.ctf_cache.has_key(name):
				return "%.3f" %self.ctf_cache[name].defocus
			
			ctf = self.__get_ctf(name)
			self.ctf_cache[name] = ctf
			return "%.3f" %ctf.defocus
		
		def __get_ctf(self,name):
			a = EMData(name,0,True)
			d = a.get_attr_dict()
			return d["ctf"]
		
		def get_bfactor(self,name):
			if self.ctf_cache.has_key(name):
				return "%.3f" %self.ctf_cache[name].bfactor
			
			ctf = self.__get_ctf(name)
			self.ctf_cache[name] = ctf
			return "%.3f" %ctf.bfactor
			
				
		def get_sampling(self,name):
			if self.ctf_cache.has_key(name):
				ctf = self.ctf_cache[name]
				return str(len(ctf.background))
			
			ctf = self.__get_ctf(name)
			self.ctf_cache[name] = ctf
			return str(len(ctf.background))
				
		def get_snr(self,name):
			if self.ctf_cache.has_key(name):
				snr = 0
				ctf = self.ctf_cache[name]
				try: snr = sum(ctf.snr)/len(ctf.snr)
				except: pass
				return "%.3f" %snr
			
			ctf = self.__get_ctf(name)
			self.ctf_cache[name] = ctf
			snr = 0
			try: snr = sum(ctf.snr)/len(ctf.snr)
			except: pass
			return "%.3f" %snr
	
	class AddDataButton():
		def __init__(self,table_widget,context_menu_data):
			self.table_widget = weakref.ref(table_widget)
			self.context_menu_data = context_menu_data
			self.name = "Browse To Add"
			
		def function(self,bool):
			self.context_menu_data.context_menu["Add"]([],self.table_widget())
			

	class DataContextMenu:
		def __init__(self):
#			self.validator = AddFilesToProjectValidator(self.project_list)
			self.context_menu = {}
			self.context_menu["Remove"] = ParticleWorkFlowTask.RemoveDataFromTable()
			self.context_menu["Add"] = ParticleWorkFlowTask.AddDataToTable()
		
		def items(self):
			return self.context_menu.items()
		
		
	class RemoveDataFromTable:
		def __call__(self,names,table_widget):
			if len(names) == 0: return # nothing happened
		
			from emform import get_table_items_in_column
			entries = get_table_items_in_column(table_widget,0)
			text_entries = [table_widget.convert_text(str(i.text())) for i in entries]

			full_names = [table_widget.convert_text(name) for name in names]
	
			indices = [ text_entries.index(name) for name in full_names]
			indices.sort()
			indices.reverse()
			for idx in indices:
				table_widget.removeRow(idx)
				
	class AddDataToTable:
		def __init__(self):
			pass
#			self.validator = AddFilesToProjectValidator(self.project_list)
			
		def __call__(self,list_of_names,table_widget):
		
	#def add_files_from_context_menu(self,list_of_names,table_widget):
			from emselector import EMSelectorModule
			em_qt_widget = EMSelectorModule()
			
			#em_qt_widget.widget.set_validator(self.validator)
			files = em_qt_widget.exec_()
			
			if files != "":
				if isinstance(files,str): files = [files]
				
				from emform import get_table_items_in_column
				entries = get_table_items_in_column(table_widget,0)
				entrie_tags = [get_file_tag(str(i.text())) for i in entries]
				file_tags = [get_file_tag(i) for i in files]
				error_messages = []
				for idx,tag in enumerate(file_tags):
					if tag in entrie_tags:
						error_messages.append("%s is already listed" %files[idx])
				
			
				if len(error_messages) > 0:
					EMErrorMessageDisplay.run(error_messages)
					return
				
				table_widget.add_entries(files)
	
	def get_initial_models_table_new(self):
		list_name = "global.spr_init_models"
		project_db = db_open_dict("bdb:project")
		init_model_names = project_db.get(list_name,dfl=[])
		self.names_at_init = init_model_names # so if the user hits cancel this can be reset

		from emform import EM3DFileTable,EMFileTable
		table = EM3DFileTable(init_model_names,name="model",desc_short="Initial Models",desc_long="")
		context_menu_data = EMRawDataReportTask.ProjectListContextMenu(list_name)
		table.add_context_menu_data(context_menu_data)
		table.add_button_data(EMRawDataReportTask.ProjectAddRawDataButton(table,context_menu_data))
		table.add_column_data(EMFileTable.EMColumnData("Quality",ParticleWorkFlowTask.get_quality_score,"This the quality score as determined by e2initialmodel.py"))

		table.add_column_data(EMFileTable.EMColumnData("Dimensions",EMRawDataReportTask.get_image_dimensions,"The dimensions of the file on disk"))

		#p.append(pdims) # don't think this is really necessary
		return table,len(init_model_names)
	
	def get_quality_score(image_name):
		'''
		Used by the initial models table to get a quality score
		'''
		a = EMData()
		a.read_image(image_name,0,True)
		d = a.get_attr_dict()
		if d.has_key("quality"): return "%.3f" %(d["quality"])
		else: return "-"
	
	get_quality_score = staticmethod(get_quality_score)

#	def get_initial_models_table(self,key="filenames",title="Current initial models"):
#		'''
#		Get the initial models table, used in the initial models table report widget, and also in the e2refine form
#		'''		
#		self.imt = E2InitialModelsTool())
#		return self.imt.get_initial_models_table_new()
#		db = "bdb:initial_models#"
#		names = []
#		quality = []
#		dims = []
#		mean = [] # just for fun
#		sigma = [] # just for fun
#		max = []
#		min = []
#		for d in db_list_dicts("bdb:initial_models#"):
#			if len(d) != 0 and db_check_dict(db+d):
#				model_db = db_open_dict(db+d,ro=True)
#				if model_db.has_key("maxrec"):
#					hdr = model_db.get_header(0)
#					if hdr["nx"] == hdr["ny"] and hdr["nx"] == hdr["nz"]:
#						names.append(d)
#						
#						dims.append(str(hdr["nx"])+'x'+str(hdr["ny"])+'x'+str(hdr["nz"]))
#						try: mean.append("%4.3f" %hdr["mean"])
#						except: mean.append("")
#						try: sigma.append("%4.3f" %hdr["sigma"])
#						except: sigma.append("")
#						try: max.append("%4.3f" %hdr["maximum"])
#						except: max.append("")
#						try: min.append("%4.3f" %hdr["minimum"])
#						except: min.append("")
#						try: quality.append("%4.3f" %hdr["quality"])
#						except: quality.append("")
#						
#		default_selections = self.get_default_filenames_from_form_db(key)
#		
#		p = EMParamTable(name=key,desc_short=title,desc_long="")
#		pnames = ParamDef(name="Files names",vartype="stringlist",desc_short="Initial model name",desc_long="The name of the initial model in the EMAN2 database",property=None,defaultunits=default_selections,choices=names)
#		pdims = ParamDef(name="dims",vartype="stringlist",desc_short="Dimensions",desc_long="The dimensions of the 3D image",property=None,defaultunits=None,choices=dims)
#		pmax = ParamDef(name="max",vartype="stringlist",desc_short="Maximum",desc_long="The maximum voxel value in this 3D image",property=None,defaultunits=None,choices=max)
#		pmin = ParamDef(name="min",vartype="stringlist",desc_short="Minimum",desc_long="The minimum voxel value in this 3D image",property=None,defaultunits=None,choices=min)
#	
#		pmean = ParamDef(name="mean",vartype="stringlist",desc_short="Mean",desc_long="The mean voxel value of this 3D image",property=None,defaultunits=None,choices=mean)
#		psigma = ParamDef(name="sigma",vartype="stringlist",desc_short="Sigma",desc_long="The standard deviation of the voxel values in this 3D image",property=None,defaultunits=None,choices=sigma)
#		
#		pquality = ParamDef(name="quality",vartype="stringlist",desc_short="Quality",desc_long="A quality metric which is stored in the image header",property=None,defaultunits=None,choices=sigma)
#		
#		
#		p.append(pnames)
#		p.append(pdims)
#		p.append(pquality)
#		p.append(pmax)
#		p.append(pmin)
#		p.append(pmean)
#		p.append(psigma)
#		
#		setattr(p,"convert_text", ptable_convert_4)
#		context_menu_dict = {"Save as":image_db_save_as}
#		#context_menu_dict["Delete"] = image_db_delete
#		setattr(p,"context_menu", context_menu_dict)
#		setattr(p,"icon_type","3d_image")
#		
#		return p,len(names)

# these ptable functions are used by the EMParamTable class for converting entries into absolute file paths, for the purpose of displaying things (like 2D images and plots etc)
def ptable_convert(text):
	return "bdb:particles#"+text+"_ptcls"

def image_generic_delete(text_list,application):
	'''
	A function that will delete all of the files in the argument text list. It does not delete .img/.hed pairs automatically
	'''
	msg = QtGui.QMessageBox()
	msg.setText("Deletion will be permanent. Are you sure you want to delete these files?");
	s = ""
	for text in text_list: s+=text+"\n"
	msg.setInformativeText(s)
	msg.setStandardButtons(QtGui.QMessageBox.Cancel | QtGui.QMessageBox.Ok )
	msg.setDefaultButton(QtGui.QMessageBox.Cancel)
	ret = msg.exec_()
	if ret == QtGui.QMessageBox.Cancel: return
	elif ret == QtGui.QMessageBox.Ok:
		application.setOverrideCursor(Qt.BusyCursor)
 		for text in text_list: remove_file(text,img_couples_too=False)
 		application.setOverrideCursor(Qt.ArrowCursor)

def image_db_delete(text_list,application):
	msg = QtGui.QMessageBox()
	msg.setText("Deletion will be permanent. Are you sure you want to delete these files?");
	s = ""
	for text in text_list: s+=text+"\n"
	msg.setInformativeText(s)
	msg.setStandardButtons(QtGui.QMessageBox.Cancel | QtGui.QMessageBox.Ok )
	msg.setDefaultButton(QtGui.QMessageBox.Cancel)
	ret = msg.exec_()
	if ret == QtGui.QMessageBox.Cancel: return
	elif ret == QtGui.QMessageBox.Ok:
		application.setOverrideCursor(Qt.BusyCursor)
 		for text in text_list: remove_file(text)
 		application.setOverrideCursor(Qt.ArrowCursor)

def image_db_save_as(text_list,application):
	msg = QtGui.QMessageBox()
	msg.setWindowTitle("Woops")
	for text in text_list:
		if not db_check_dict(text):
			msg.setText("The database (%s) does not exist" %text) # this is a disturbing scenario, it should never happen
			msg.exec_()
			continue
		else:
			if EMUtil.get_image_count(text) > 0:
				name = save_data(EMDataListCache(text))
			else:
				name = save_data(EMData(text))
			if name == "": break # a way to cancel 

def ptable_convert_2(text):
	return text

def ptable_convert_3(text):
	return "bdb:particles#"+text

def ptable_convert_4(text):
	return "bdb:initial_models#"+text

class TomoParticleReportTask(WorkFlowTask):
	documentation_string = "This form display the boxed tomographic particles that you currently have associated with the project"
	def __init__(self):
		WorkFlowTask.__init__(self)

	def get_project_particle_table(self):
		project_db = db_open_dict("bdb:project")
		particle_list_name = "global.tpr_ptcls"
		particle_names = project_db.get(particle_list_name,dfl=[])
		self.project_files_at_init = particle_names # so if the user hits cancel this can be reset

		from emform import EM3DFileTable,EMFileTable
		table = EM3DFileTable(particle_names,desc_short="Boxed Tomographic Particles",desc_long="")
		context_menu_data = EMRawDataReportTask.ProjectListContextMenu(particle_list_name)
		table.add_context_menu_data(context_menu_data)
		table.add_button_data(EMRawDataReportTask.ProjectAddRawDataButton(table,context_menu_data))
	#	table.insert_column_data(1,EMFileTable.EMColumnData("Particles On Disk",ParticleReportTask.get_num_ptcls,"Particles currently stored on disk that are associated with this image"))
		table.insert_column_data(2,EMFileTable.EMColumnData("Particle Dims",ParticleReportTask.get_particle_dims,"The dimensions of the particles that are stored on disk"))
		
		return table
	
	def get_params(self):
		params = []
		
	
		table = self.get_project_particle_table()
		
		params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=TomoParticleReportTask.documentation_string,choices=None))
		params.append(table)  
		
		return params

class ParticleReportTask(ParticleWorkFlowTask):
	'''
	
	Reports the current status of the particles in the projec
	'''
	
	documentation_string = "This tool is for displaying the particles that are currently associated with this project. This list is generating by inspecting the contents of the project particles directory."
	warning_string = "\n\n\nNOTE: There are no particles currently associated with the project. You can add particles to the project using e2boxer or by importing them directly - see from the list of options associated with this task." 
	def __init__(self):
		ParticleWorkFlowTask.__init__(self)
		self.window_title = "Project particles"


	def get_project_particle_table(self):
		project_db = db_open_dict("bdb:project")
		particle_list_name = "global.spr_ptcls"
		particle_names = project_db.get(particle_list_name,dfl=[])
		self.project_files_at_init = particle_names # so if the user hits cancel this can be reset

		from emform import EM2DStackTable,EMFileTable
		table = EM2DStackTable(particle_names,desc_short="Raw Data Files",desc_long="")
		context_menu_data = EMRawDataReportTask.ProjectListContextMenu(particle_list_name)
		table.add_context_menu_data(context_menu_data)
		table.add_button_data(EMRawDataReportTask.ProjectAddRawDataButton(table,context_menu_data))
		table.insert_column_data(1,EMFileTable.EMColumnData("Particles On Disk",ParticleReportTask.get_num_ptcls,"Particles currently stored on disk that are associated with this image"))
		table.insert_column_data(2,EMFileTable.EMColumnData("Particle Dims",ParticleReportTask.get_particle_dims,"The dimensions of the particles that are stored on disk"))
		
		return table
	
	def on_form_cancel(self):
		self.recover_original_raw_data_list()
		
		self.form.closeEvent(None)
		self.form = None
		self.emit(QtCore.SIGNAL("task_idle"))
	
	def recover_original_raw_data_list(self):
		'''
		Called if the user hits cancel - if they removed some files or added files the changes
		are not saved unless the user hits ok
		'''
		project_db = db_open_dict("bdb:project")
		project_db["global.spr_ptcls"] = self.project_files_at_init
	
	def get_particle_dims(file_name):
		nx,ny,nz = gimme_image_dimensions3D(file_name)
		return "%ix%ix%i" %(nx,ny,nz)
	
	def get_num_ptcls(file_name):
		return str(EMUtil.get_image_count(file_name))
	
	get_particle_dims = staticmethod(get_particle_dims)
	get_num_ptcls = staticmethod(get_num_ptcls)
	
	def get_params(self):
		params = []
		
	
		table = self.get_project_particle_table()
		
		params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=ParticleReportTask.documentation_string,choices=None))
		params.append(table)  
		
		return params

class E2BoxerTask(ParticleWorkFlowTask):
	'''
	Provides some common functions for the e2boxer tasks
	'''
	def __init__(self):
		ParticleWorkFlowTask.__init__(self)
		self.form_db_name = "bdb:emform.e2boxer"
		self.report_task = None  #will eventually store a EMRawDataReportTask
	
	def get_boxes_in_database(file_name):
		
		db_name = "bdb:e2boxer.cache"		
		box_maps = {}
		nbox = 0
		if db_check_dict(db_name):
			e2boxer_db = db_open_dict(db_name,ro=True)
			for name in e2boxer_db.keys():
				d = e2boxer_db[name]
				if not isinstance(d,dict): continue
				if not d.has_key("e2boxer_image_name"): # this is the test, if something else has this key then we're screwed.
					continue
				name = d["e2boxer_image_name"]
				if name != file_name: continue
				
				for key in ["auto_boxes","manual_boxes","reference_boxes"]:
					if d.has_key(key):
						boxes = d[key]
						if boxes != None: nbox += len(boxes)
		return str(nbox)

	get_boxes_in_database = staticmethod(get_boxes_in_database)
#	get_num_particles_project = staticmethod(get_num_particles_project)
#	get_particle_dims_project = staticmethod(get_particle_dims_project)
	
	class ParticleColumns:
		def __init__(self):
			self.header_cache = {}
			self.translation_cache = {}
						
#		def __del__(self):
#			print "Boxer columns dies"
		
		def get_num_particles_project(self,file_name):
			'''
			Get the particles in the project that are associated with a specific file name
			This is useful for the e2boxer forms, which are used to take raw data files and
			produce boxed output - i.e. if the user wants to know if they've already
			written boxed output for a given raw file
			@param file_name a file name, should be a file that's in global.spr_raw_file_names - this is not checked though
			Note that the only thing that defines the relationship is whether or not the particle's 
			'''
			if self.translation_cache.has_key(file_name):
				name = self.translation_cache[file_name]
				d = self.header_cache[name]
				if d.has_key("ptcl_source_image"):
					if d["ptcl_source_image"] == file_name:
						return str(EMUtil.get_image_count(name))
			
			project_db = db_open_dict("bdb:project")	
			particle_names = project_db.get("global.spr_ptcls",dfl=[])
			for name in particle_names:
				a = EMData()
				a.read_image(name,0,True) # header only
				d = a.get_attr_dict()
				if d.has_key("ptcl_source_image"):
					if d["ptcl_source_image"] == file_name:
						self.header_cache[name] = d
						self.translation_cache[file_name] = name
						return str(EMUtil.get_image_count(name))
					
			return "0"
		
		def get_particle_dims_project(self,file_name):
			'''
			'''
			if self.translation_cache.has_key(file_name):
				name = self.translation_cache[file_name]
				d = self.header_cache[name]
				if d.has_key("ptcl_source_image"):
					if d["ptcl_source_image"] == file_name:
						nx,ny,nz = gimme_image_dimensions3D(name)
						return "%ix%ix%i" %(nx,ny,nz)
			
			project_db = db_open_dict("bdb:project")	
			particle_names = project_db.get("global.spr_ptcls",dfl=[])
			
			for name in particle_names:
				a = EMData()
				a.read_image(name,0,True) # header only
				d = a.get_attr_dict()
				#print d
				if d.has_key("ptcl_source_image"):
					if d["ptcl_source_image"] == file_name:
						nx,ny,nz = gimme_image_dimensions3D(name)
						self.header_cache[name] = d
						self.translation_cache[file_name] = name
						return "%ix%ix%i" %(nx,ny,nz)
			return ""
			
	
	def get_boxer_basic_table(self):
		'''
		
		Returns a table like this:
		
		|| Project image name || Boxes in e2boxer db ||
		
		Returns the table, and the the number of entries (p,n)
		if n is zero there are no entries in the table and the calling function can act appropriately
		'''
		
		self.report_task = EMRawDataReportTask()
		table,n = self.report_task.get_raw_data_table()# now p is a EMParamTable with rows for as many files as there in the project
		from emform import EMFileTable
		table.insert_column_data(0,EMFileTable.EMColumnData("Stored Boxes",E2BoxerTask.get_boxes_in_database,"Boxes currently stored in the EMAN2 database"))
		
		return table, n
	
	def get_project_files_that_have_db_boxes_in_table(self):
		
		self.report_task = EMRawDataReportTask()
		table,n = self.report_task.get_raw_data_table()# now p is a EMParamTable with rows for as many files as there in the project
		from emform import EMFileTable
		table.insert_column_data(0,EMFileTable.EMColumnData("Stored Boxes",E2BoxerTask.get_boxes_in_database,"Boxes currently stored in the EMAN2 database"))
		self.columns_object = E2BoxerTask.ParticleColumns()
		table.insert_column_data(1,EMFileTable.EMColumnData("Particles On Disk",self.columns_object.get_num_particles_project,"Particles currently stored on disk that are associated with this image"))
		table.insert_column_data(2,EMFileTable.EMColumnData("Particle Dims",self.columns_object.get_particle_dims_project,"The dimensions of the particles that are stored on disk"))
		#self.tmp = E2BoxerTask.Tmp()
		return table, n
		

#		
	def __get_e2boxer_data(self,project_names):
		
		db_name = "bdb:e2boxer.cache"		
		box_maps = {}
		if db_check_dict(db_name):
			e2boxer_db = db_open_dict(db_name,ro=True)
			for name in e2boxer_db.keys():
				d = e2boxer_db[name]
				if not isinstance(d,dict): continue
				if not d.has_key("e2boxer_image_name"): # this is the test, if something else has this key then we're screwed.
					continue
				name = d["e2boxer_image_name"]
				if not name in project_names: continue
				dim = ""
				nbox = 0
				for key in ["auto_boxes","manual_boxes","reference_boxes"]:
					if d.has_key(key):
						boxes = d[key]
						if boxes != None:
							nbox += len(boxes)
							if dim == "" and len(boxes) > 0:
								box = boxes[0]
								dim = str(box.xsize) + "x"+str(box.ysize)
				
				if nbox == 0: nbox = "" # just so it appears as nothin in the interface			
				box_maps[name] = [dim,nbox]
		
		nboxes = []
		dimensions = []
		for name in project_names:
			if box_maps.has_key(name):
				dimensions.append(box_maps[name][0])
				nboxes.append(box_maps[name][1])
			else:
				dimensions.append("")
				nboxes.append("")
				
		return nboxes,dimensions
	
	def on_form_cancel(self):
		if self.report_task != None:
			self.report_task.recover_original_raw_data_list()
		self.form.closeEvent(None)
		self.form = None
		self.emit(QtCore.SIGNAL("task_idle"))


class E2BoxerGenericTask(ParticleWorkFlowTask):
	documentation_string = "Fill me in"
	def __init__(self):
		ParticleWorkFlowTask.__init__(self)
		self.window_title = "e2boxer"
		self.preferred_size = (480,200)
		self.form_db_name = "bdb:emform.e2boxer"
		
	def get_params(self):
		params = []		
#		params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=E2CTFGenericTask.documentation_string,choices=None))
		db = db_open_dict(self.form_db_name)
		params.append(ParamDef(name="running_mode",vartype="choice",desc_short="Choose your running mode",desc_long="There are three Boxer related task which are generally run in order",property=None,defaultunits=db.get("running_mode",dfl="Interactive boxing"),choices=["Interactive boxing", "Autoboxing", "Write output"]))
		#db_close_dict(self.form_db_name)
		return params

	def on_form_ok(self,params):
		if params["running_mode"] == "Interactive boxing":
			self.emit(QtCore.SIGNAL("replace_task"),E2BoxerGuiTaskGeneral(),"e2boxer interface launcher")
			self.form.closeEvent(None)
			self.form = None
		elif params["running_mode"] == "Autoboxing":
			self.emit(QtCore.SIGNAL("replace_task"),E2BoxerAutoTaskGeneral(),"e2boxer automated boxing")
			self.form.closeEvent(None)
			self.form = None
		elif params["running_mode"] == "Write output":
			self.emit(QtCore.SIGNAL("replace_task"),E2BoxerOutputTaskGeneral(),"e2boxer write output")
			self.form.closeEvent(None)
			self.form = None	
		else:
			self.form.closeEvent(None)
			self.form = None
			self.emit(QtCore.SIGNAL("task_idle"))
			return
		
		self.write_db_entries(params)
	def write_db_entry(self,key,value):
		pass


class E2BoxerAutoTask(E2BoxerTask):
	'''
	A task for running automated boxing in the project context
	'''
	documentation_string = "Select the images you wish to run autoboxing on and hit OK.\nThis will cause the workflow to spawn processes based on the available CPUs.\nData will be autoboxed using the current autoboxer in the database, which is placed there by e2boxer."
	warning_string = "\n\n\nNOTE: This feature is currently disabled as there is no autoboxing information in the EMAN2 database. You can fix this situation by using e2boxer to interactively box a few images first"
	
	def __init__(self):
		E2BoxerTask.__init__(self)
		self.window_title = "e2boxer autobox"
		self.boxer_module = None # this will actually point to an EMBoxerModule, potentially

	def get_params(self):
		params = []
		
		
		db_name = "bdb:e2boxer.cache"
		fail = False
		if db_check_dict(db_name):
			db = db_open_dict(db_name,ro=True)
			if not db.has_key("current_autoboxer"): fail = True
		else:
			fail = True
			
		if fail:
			params.append(ParamDef(name="blurb",vartype="text",desc_short="Using e2boxer",desc_long="",property=None,defaultunits=E2BoxerAutoTask.documentation_string+E2BoxerAutoTask.warning_string,choices=None))
		else:
			params.append(ParamDef(name="blurb",vartype="text",desc_short="Using e2boxer",desc_long="",property=None,defaultunits=E2BoxerAutoTask.documentation_string,choices=None))
			p,n = self.get_boxer_basic_table()
			params.append(p)
	
		return params
			
	def on_form_ok(self,params): 
		if  params.has_key("filenames") and len(params["filenames"]) == 0:
			self.run_select_files_msg()
			return
	
		else:
			self.write_db_entries(params) # will only write filenames
			options = EmptyObject()
			for k,v in params.items():
				setattr(options,k,v)
			
			string_args = []
			bool_args = []
			additional_args = ["--method=Swarm", "--auto=db"]
			temp_file_name = "e2boxer_autobox_stdout.txt"
			self.spawn_task("e2boxer.py",options,string_args,bool_args,additional_args,temp_file_name)
			self.emit(QtCore.SIGNAL("task_idle"))
			self.form.closeEvent(None)
			self.form = None

class E2BoxerAutoTaskGeneral(E2BoxerAutoTask):
	def __init__(self):
		E2BoxerAutoTask.__init__(self)
		self.window_title = "e2boxer autobox"
		self.boxer_module = None # this will actually point to an EMBoxerModule, potentially

	def get_params(self):
		params = []
		
		
		db_name = "bdb:e2boxer.cache"
		fail = False
		if db_check_dict(db_name):
			db = db_open_dict(db_name,ro=True)
			if not db.has_key("current_autoboxer"): fail = True
		else:
			fail = True
			
		if fail:
			params.append(ParamDef(name="blurb",vartype="text",desc_short="Using e2boxer",desc_long="",property=None,defaultunits=E2BoxerAutoTask.documentation_string+E2BoxerAutoTask.warning_string,choices=None))
		else:
			params.append(ParamDef(name="blurb",vartype="text",desc_short="Using e2boxer",desc_long="",property=None,defaultunits=E2BoxerAutoTask.documentation_string,choices=None))
			params.append(ParamDef(name="filenames",vartype="url",desc_short="File Names",desc_long="The names of the particle files you want to interactively box using e2boxer",property=None,defaultunits=[],choices=[]))
		
		return params
	
class E2TomoBoxerGuiTask(WorkFlowTask):
	documentation_string = "Select the file you want to process and hit okay, this will launch e2tomoboxer"
	
	def __init__(self):
		WorkFlowTask.__init__(self)
		self.tomo_boxer_module = None
	
	def get_tomo_boxer_basic_table(self):
		'''
		
		Returns a table like this:
		
		|| Project image name || Boxes in e2boxer db ||
		
		Returns the table, and the the number of entries (p,n)
		if n is zero there are no entries in the table and the calling function can act appropriately
		'''
		
		self.report_task = EMTomoRawDataReportTask()
		table,n = self.report_task.get_raw_data_table()# now p is a EMParamTable with rows for as many files as there in the project
		from emform import EMFileTable
		table.insert_column_data(0,EMFileTable.EMColumnData("Stored Boxes",E2TomoBoxerGuiTask.get_tomo_boxes_in_database,"Boxes currently stored in the EMAN2 database"))
		
		return table, n

	def get_tomo_boxes_in_database(name):
		return ""
	
	get_tomo_boxes_in_database = staticmethod(get_tomo_boxes_in_database)
	
	def get_params(self):
		params = []
		
		p,n = self.get_tomo_boxer_basic_table() # note n is unused, it's a refactoring residual		
		params.append(ParamDef(name="blurb",vartype="text",desc_short="Interactive use of e2boxer",desc_long="",property=None,defaultunits=E2TomoBoxerGuiTask.documentation_string,choices=None))
		params.append(p)
#		db = db_open_dict(self.form_db_name)
#		params.append(ParamDef(name="interface_boxsize",vartype="int",desc_short="Box size",desc_long="An integer value",property=None,defaultunits=db.get("interface_boxsize",dfl=128),choices=[]))
#		#db_close_dict(self.form_db_name)
		return params
	
	def on_form_ok(self,params):
		
		if not params.has_key("filenames"):
			EMErrorMessageDisplay.run(["Please select files for processing"])
			return
		
		if  params.has_key("filenames") and len(params["filenames"]) == 0:
			EMErrorMessageDisplay.run(["Please select files for processing"])
			return

#		if  params.has_key("interface_boxsize") and params["interface_boxsize"] < 1:
#			self.show_error_message(["Must specify a positive, non zero boxsize."])
#			return
#		else:
		self.write_db_entries(params)
#		options = EmptyObject()
#		for key in params.keys():
#			setattr(options,key,params[key])
#		options.boxsize = params["interface_boxsize"]
#		options.running_mode = "gui"
#		options.method = "Swarm"
		
		from e2tomoboxer import EMTomoBoxerModule
		
		print params["filenames"][0], "is thei file name"
		self.tomo_boxer_module = EMTomoBoxerModule(params["filenames"][0])
		self.emit(QtCore.SIGNAL("gui_running"),"Boxer",self.tomo_boxer_module) # The controlled program should intercept this signal and keep the E2BoxerTask instance in memory, else signals emitted internally in boxer won't work
		
		QtCore.QObject.connect(self.tomo_boxer_module, QtCore.SIGNAL("module_idle"), self.on_boxer_idle)
		QtCore.QObject.connect(self.tomo_boxer_module, QtCore.SIGNAL("module_closed"), self.on_boxer_closed)
		self.form.closeEvent(None)
		print 'saying show guies'
		self.tomo_boxer_module.show_guis()
		self.form = None
			
	def write_db_entires(self,params):
		pass

	def on_boxer_idle(self):pass
	def on_boxer_closed(self):pass

class E2BoxerGuiTask(E2BoxerTask):	
	documentation_string = "Select the images you want to box, enter your boxsize, and hit OK. This will lauch e2boxer and automatically load the selected images for boxing."
	
	warning_string = "\n\n\nNOTE: There are no images currenty associated with the project. Please import or specify which images you want as part of this project in step 1 of the workflow and try again."
	
	def __init__(self):
		E2BoxerTask.__init__(self)
		self.window_title = "e2boxer interface"
		self.boxer_module = None # this will actually point to an EMBoxerModule, potentially

	def get_params(self):
		params = []
		
		p,n = self.get_boxer_basic_table() # note n is unused, it's a refactoring residual		
		params.append(ParamDef(name="blurb",vartype="text",desc_short="Interactive use of e2boxer",desc_long="",property=None,defaultunits=E2BoxerGuiTask.documentation_string,choices=None))
		params.append(p)
		db = db_open_dict(self.form_db_name)
		params.append(ParamDef(name="interface_boxsize",vartype="int",desc_short="Box size",desc_long="An integer value",property=None,defaultunits=db.get("interface_boxsize",dfl=128),choices=[]))
			#db_close_dict(self.form_db_name)
		return params
			
	def on_form_ok(self,params):
		
		if not params.has_key("filenames"): return
		
		if  params.has_key("filenames") and len(params["filenames"]) == 0:
			self.run_select_files_msg()
			return

		if  params.has_key("interface_boxsize") and params["interface_boxsize"] < 1:
			self.show_error_message(["Must specify a positive, non zero boxsize."])
			return
		else:
			self.write_db_entries(params)
			options = EmptyObject()
			for key in params.keys():
				setattr(options,key,params[key])
			options.boxsize = params["interface_boxsize"]
			options.running_mode = "gui"
			options.method = "Swarm"
			
			from e2boxer import EMBoxerModule
			self.boxer_module = EMBoxerModule(get_application(),options)
			self.emit(QtCore.SIGNAL("gui_running"),"Boxer",self.boxer_module) # The controlled program should intercept this signal and keep the E2BoxerTask instance in memory, else signals emitted internally in boxer won't work
			
			QtCore.QObject.connect(self.boxer_module, QtCore.SIGNAL("module_idle"), self.on_boxer_idle)
			QtCore.QObject.connect(self.boxer_module, QtCore.SIGNAL("module_closed"), self.on_boxer_closed)
			self.form.closeEvent(None)
			self.boxer_module.show_guis()
			self.form = None
			
	def on_form_close(self):
		# this is to avoid a task_idle signal, which would be incorrect if e2boxer is running
		if self.boxer_module == None:
			self.emit(QtCore.SIGNAL("task_idle"))
		else: pass
	
	def on_boxer_closed(self): 
		if self.boxer_module != None:
			self.boxer_module = None
			self.emit(QtCore.SIGNAL("gui_exit"))
	
	def on_boxer_idle(self):
		'''
		Presently this means boxer did stuff but never opened any guis, so it's safe just to emit the signal
		'''
		self.boxer_module = None
		self.emit(QtCore.SIGNAL("gui_exit"))

class E2BoxerGuiTaskGeneral(E2BoxerGuiTask):	
	def __init__(self):
		E2BoxerTask.__init__(self)
		self.window_title = "e2boxer interface"
		self.boxer_module = None # this will actually point to an EMBoxerModule, potentially

	def get_params(self):
		params = []
		params.append(ParamDef(name="blurb",vartype="text",desc_short="Using e2boxer",desc_long="",property=None,defaultunits=E2BoxerGuiTask.documentation_string,choices=None))
		params.append(ParamDef(name="filenames",vartype="url",desc_short="File Names",desc_long="The names of the particle files you want to interactively box using e2boxer",property=None,defaultunits=[],choices=[]))
		db = db_open_dict(self.form_db_name)
		params.append(ParamDef(name="interface_boxsize",vartype="int",desc_short="Box size",desc_long="An integer value",property=None,defaultunits=db.get("interface_boxsize",dfl=128),choices=[]))
		#db_close_dict(self.form_db_name)
		return params
	
	
class E2BoxerOutputTask(E2BoxerTask):	
	documentation_string = "Select the images you wish to generate output for, enter the box size and normalization etc, and then hit OK.\nThis will cause the workflow to spawn output writing processes using the available CPUs. Note that the bdb option is the preferred output format, in this mode output particles are written directly to the EMAN project database."
	warning_string = "\n\n\nNOTE: There are no boxes currently stored in the database. To rectify this situation use e2boxer to interactively box your images, or alternatively used autoboxing information stored in the database to autobox your images."
	def __init__(self):
		E2BoxerTask.__init__(self)
		self.window_title = "e2boxer output"
		self.output_formats = ["bdb","hdf"] # disable img from the workflow because in EMAN2 we want to store more metadata in the header
	
#	def __del__(self):
#		print "output task dies"
	
	def get_params(self):
		params = []
		
		p,n = self.get_project_files_that_have_db_boxes_in_table()
		if n == 0 and False:
			params.append(ParamDef(name="blurb",vartype="text",desc_short="Using e2boxer",desc_long="",property=None,defaultunits=E2BoxerOutputTask.documentation_string+E2BoxerOutputTask.warning_string,choices=None))
		else:
			params.append(ParamDef(name="blurb",vartype="text",desc_short="Using e2boxer",desc_long="",property=None,defaultunits=E2BoxerOutputTask.documentation_string,choices=None))
			params.append(p)
			self.add_general_params(params)

		return params
	
	def add_general_params(self,params):
		'''
		Functionality used in several places
		'''
		db = db_open_dict(self.form_db_name)
		pbox = ParamDef(name="output_boxsize",vartype="int",desc_short="Box size",desc_long="An integer value",property=None,defaultunits=db.get("output_boxsize",dfl=128),choices=[])	
		pfo = ParamDef(name="force",vartype="boolean",desc_short="Force overwrite",desc_long="Whether or not to force overwrite files that already exist",property=None,defaultunits=db.get("force",dfl=False),choices=None)
		pwc = ParamDef(name="write_coord_files",vartype="boolean",desc_short="Write box coord files",desc_long="Whether or not box db files should be written",property=None,defaultunits=db.get("write_coord_files",dfl=False),choices=None)
		pwb = ParamDef(name="write_box_images",vartype="boolean",desc_short="Write box image files",desc_long="Whether or not box images should be written",property=None,defaultunits=db.get("write_box_images",dfl=True),choices=None)
		pinv = ParamDef(name="invert_output",vartype="boolean",desc_short="Invert",desc_long="Do you want the pixel intensities in the output inverted?",property=None,defaultunits=db.get("invert_output",dfl=False),choices=None)
		pn =  ParamDef(name="normproc",vartype="string",desc_short="Normalize images",desc_long="How the output box images should be normalized",property=None,defaultunits=db.get("normproc",dfl="normalize.edgemean"),choices=["normalize","normalize.edgemean","none"])
		pop = ParamDef(name="outformat",vartype="string",desc_short="Output image format",desc_long="The format of the output box images",property=None,defaultunits=db.get("outformat",dfl="bdb"),choices=self.output_formats)
		
		#db_close_dict(self.form_db_name)
		pwb.dependents = ["invert_output","normproc","outformat"] # these are things that become disabled when the pwb checkbox is unchecked etc
		
		params.append([pbox,pfo])
		params.append([pwc,pwb,pinv])
		params.append(pn)
		params.append(pop)
		
	
	def check_params(self,params):
		
		error_message = []
		if params["output_boxsize"] < 1: error_message.append("Boxsize must be greater than 0.")
		if not params["write_coord_files"] and not params["write_box_images"]: error_message.append("You must choose at least one of the write_coords/write_box_images options")
	
		return error_message
	
	def on_form_ok(self,params):	
		if  params.has_key("filenames") and len(params["filenames"]) == 0:
			self.run_select_files_msg()
			return
		
		error_message = self.check_params(params)
		if len(error_message) >0: 
			self.show_error_message(error_message)
			return
		
		else:
			self.write_db_entries(params)
			options = EmptyObject()
			for k,v in params.items():
				setattr(options,k,v)	
			options.boxsize = params["output_boxsize"]
			
			options.just_output=True # this is implicit, it has to happen
			
			string_args = ["normproc","outformat","boxsize"]
			bool_args = ["force","write_coord_files","write_box_images","just_output","invert_output"]
			additional_args = ["--method=Swarm", "--auto=db","--dbls=global.spr_ptcls"]
			temp_file_name = "e2boxer_autobox_stdout.txt"
			self.spawn_task("e2boxer.py",options,string_args,bool_args,additional_args,temp_file_name)
			self.emit(QtCore.SIGNAL("task_idle"))
			self.form.closeEvent(None)
			self.form = None

class E2BoxerOutputTaskGeneral(E2BoxerOutputTask):
	documentation_string = "Write me"
	def __init__(self):
		E2BoxerOutputTask.__init__(self)
		self.window_title = "e2boxer output"
		
	def get_params(self):
		params = []
		params.append(ParamDef(name="blurb",vartype="text",desc_short="Using e2boxer",desc_long="",property=None,defaultunits=E2BoxerOutputTaskGeneral.documentation_string,choices=None))
		
		p = self.get_e2boxer_boxes_table(project_check=False)
		params.append(p)
		
		self.add_general_params(params)
	
#		boxer_project_db = db_open_dict("bdb:e2boxer.project")
#		params.append(ParamDef(name="boxsize",vartype="int",desc_short="Box size",desc_long="An integer value",property=None,defaultunits=boxer_project_db.get("interface_boxsize",dfl=128),choices=[]))
		return params
	
	def get_e2boxer_boxes_table(self,project_check=True):
		db_name = "bdb:e2boxer.cache"
		p = EMParamTable(name="filenames",desc_short="Current boxes generated by e2boxer",desc_long="")
		names = []
		nboxes = []
		dimensions = []
		
		if project_check:
			project_db = db_open_dict("bdb:project")	
			project_names = project_db.get("global.spr_raw_file_names",dfl=[])
		
		if db_check_dict(db_name):
			e2boxer_db = db_open_dict(db_name,ro=True)
			for name in e2boxer_db.keys():
				d = e2boxer_db[name]
				if not isinstance(d,dict): continue
				if not d.has_key("e2boxer_image_name"): # this is the test, if something else has this key then we're screwed.
					continue

				name = d["e2boxer_image_name"]
				if project_check:
					if not name in project_names: continue
				names.append(name)
				
				dim = ""
				nbox = 0
				for key in ["auto_boxes","manual_boxes","reference_boxes"]:
					if d.has_key(key):
						boxes = d[key]
						nbox += len(boxes)
						if dim == "" and len(boxes) > 0:
							box = boxes[0]
							dim = str(box.xsize) + "x"+str(box.ysize)
							
							
				nboxes.append(nbox)
				dimensions.append(dim)
			
		pnames = ParamDef(name="Filenames",vartype="stringlist",desc_short="File Names",desc_long="The filenames",property=None,defaultunits=None,choices=names)
		pboxes = ParamDef(name="Num boxes",vartype="intlist",desc_short="Boxes in DB",desc_long="The number of boxes stored for this image in the database",property=None,defaultunits=None,choices=nboxes)
		pdims = ParamDef(name="Dimensions",vartype="stringlist",desc_short="Dimensions",desc_long="The dimensions boxes",property=None,defaultunits=None,choices=dimensions)
		
		p = EMParamTable(name="filenames",desc_short="Choose a subset of these images",desc_long="")
		p.append(pnames)
		p.append(pboxes)
		p.append(pdims)
		return p
	
	
class E2BoxerProgramOutputTask(E2BoxerOutputTask):
	'''
	This task is called from e2boxer itself. Not from the workflow
	'''
	documentation_string = "Use this form for writing output from within the e2boxer interface.\nYou can choose to write image files in a number of formats. The bdb file format is mostly useful if you are using EMAN2. If you plan on using your data with other programs, including EMAN1, you must choose either the hdf or img output formats.\nYou can also choose to write EMAN1 style .box files"
	def __init__(self,application,filenames,target,exclusions=[]):
		E2BoxerOutputTask.__init__(self)
		self.window_title = "E2boxer Output"
		self.filenames = filenames
		self.target = weakref.ref(target)
		self.exclusions = exclusions
		self.output_formats = ["bdb","img","hdf"]
		
	def get_params(self):
		params = []
		params.append(ParamDef(name="blurb",vartype="text",desc_short="E2Boxer output form",desc_long="",property=None,defaultunits=E2BoxerProgramOutputTask.documentation_string,choices=None))
		
		p = EMParamTable(name="filenames",desc_short="Choose a subset of these images",desc_long="")
		pnames = ParamDef(name="Filenames",vartype="stringlist",desc_short="File Names",desc_long="The filenames",property=None,defaultunits=None,choices=self.filenames)
		p.append(pnames)
		setattr(p,"convert_text", ptable_convert_2)
		setattr(p,"icon_type","single_image")
		setattr(p,"exclusions",self.exclusions)
		
		params.append(p)
		
		self.add_general_params(params)
	
#		boxer_project_db = db_open_dict("bdb:e2boxer.project")
#		params.append(ParamDef(name="boxsize",vartype="int",desc_short="Box size",desc_long="An integer value",property=None,defaultunits=boxer_project_db.get("interface_boxsize",dfl=128),choices=[]))
		return params
	
	def on_form_ok(self,params):
		
		if  params.has_key("filenames") and len(params["filenames"]) == 0:
			self.run_select_files_msg()
			return
		
		error_message = self.check_params(params)
		if len(error_message) >0: 
			self.show_error_message(error_message)
			return
		else:
			if params["write_coord_files"]:
				self.target().write_coord_files(params["filenames"],params["output_boxsize"],params["force"])
			if params["write_box_images"]:
				normproc = False
				if params["normproc"] != "none":
					normproc=True
				self.target().write_box_image_files(params["filenames"],params["output_boxsize"],params["force"],params["outformat"],normproc,params["normproc"],params["invert_output"])
				
			self.emit(QtCore.SIGNAL("task_idle"))
			self.form.closeEvent(None)
			self.form = None

class E2CTFWorkFlowTask(ParticleReportTask):
	'''
	Common functionality for E2CTF Work flow taskss
	'''
	def __init__(self):
		ParticleReportTask.__init__(self)
		self.form_db_name = "bdb:emform.e2ctf"
	
	def get_ctf_param_table(self):
		'''
		
		'''
		project_db = db_open_dict("bdb:project",ro=True)
		particle_list_name = "global.spr_ptcls"
		particle_names = project_db.get(particle_list_name,dfl=[])
		
		table = self.get_project_particle_table()
		
		from emform import EMFileTable
		self.column_data = E2CTFWorkFlowTask.CTFColumns()
		table.add_column_data(EMFileTable.EMColumnData("Defocus",self.column_data.get_defocus,"The estimated defocus"))
		table.add_column_data(EMFileTable.EMColumnData("B Factor",self.column_data.get_bfactor,"The estimated B factor, note this is ~4x greater than in EMAN1"))
		table.add_column_data(EMFileTable.EMColumnData("SNR",self.column_data.get_snr,"The averaged SNR"))
		table.add_column_data(EMFileTable.EMColumnData("Sampling",self.column_data.get_sampling,"The amount of sampling used for generating CTF parameters"))
		return table,len(particle_names)
	
	class CTFColumns:
		'''
		Basically some functions with a cache - the cache is to avoid
		re-reading stuff from disk multiple times
		'''
		def __init__(self):
			self.ctf_cache = {}
						
#		def __del__(self):
#			print "CTF columns dies"
			
		def get_defocus(self,name):
			if self.ctf_cache.has_key(name):
				return "%.3f" %self.ctf_cache[name].defocus
			
			if db_check_dict("bdb:e2ctf.parms"):
				ctf_db = db_open_dict("bdb:e2ctf.parms",ro=False)
				try:
					vals = ctf_db[get_file_tag(name)][0]
					ctf = EMAN2Ctf()
					ctf.from_string(vals)
					self.ctf_cache[name] = ctf
					return "%.3f" %ctf.defocus
				except: pass
				
			return ""
		
		def get_bfactor(self,name):
			if self.ctf_cache.has_key(name):
				return "%.3f" %self.ctf_cache[name].bfactor
			if db_check_dict("bdb:e2ctf.parms"):
				ctf_db = db_open_dict("bdb:e2ctf.parms",ro=False)
				try:
					vals = ctf_db[get_file_tag(name)][0]
					ctf = EMAN2Ctf()
					ctf.from_string(vals)
					self.ctf_cache[name] = ctf
					return "%.3f" %ctf.bfactor
				except: pass
				
			return ""
				
		def get_sampling(self,name):
			if self.ctf_cache.has_key(name):
				ctf = self.ctf_cache[name]
				return str(len(ctf.background))
			
			if db_check_dict("bdb:e2ctf.parms"):
				ctf_db = db_open_dict("bdb:e2ctf.parms",ro=False)
				try:
					vals = ctf_db[get_file_tag(name)][0]
					ctf = EMAN2Ctf()
					ctf.from_string(vals)
					self.ctf_cache[name] = ctf
					return str(len(ctf.background))
				except: pass
			
			return ""
				
		def get_snr(self,name):
			if self.ctf_cache.has_key(name):
				snr = 0
				ctf = self.ctf_cache[name]
				try: snr = sum(ctf.snr)/len(ctf.snr)
				except: pass
				return "%.3f" %snr
			
			if db_check_dict("bdb:e2ctf.parms"):
				ctf_db = db_open_dict("bdb:e2ctf.parms",ro=False)
				try:
					vals = ctf_db[get_file_tag(name)][0]
					ctf = EMAN2Ctf()
					ctf.from_string(vals)
					snr = 0
					self.ctf_cache[name] = ctf
					try: snr = sum(ctf.snr)/len(ctf.snr)
					except: pass
					return "%.3f" %snr
				except: pass
			return ""

	def get_full_ctf_table(self,project_names=None,no_particles=False):
		'''
		Gets the ctf param table but also adds information about the wiener and phase flipped
		particles on disk (number, dimensions)
		'''
		table,n = self.get_ctf_param_table()
	
		self.other_column_data = E2CTFWorkFlowTask.MoreCTFColumns()
		from emform import EMFileTable
		table.add_column_data(EMFileTable.EMColumnData("Phase flip",self.other_column_data.get_num_phase_flipped,"The number of phase flipped particles on disk"))
		table.add_column_data(EMFileTable.EMColumnData("Phase flip dims",self.other_column_data.phase_flipped_dim,"The dimensions of the phase flippped particles"))
		table.add_column_data(EMFileTable.EMColumnData("Wiener filt",self.other_column_data.get_num_wein_filt,"The number of Wiener filtered particles on disk"))
		table.add_column_data(EMFileTable.EMColumnData("Wiener filt dims",self.other_column_data.wien_filt_dim,"The dimensions of the Wiener filtered particles"))
		return table, n
		

	
	class MoreCTFColumns:
		'''
		Basically some functions with a cache - the cache is to avoid
		re-reading stuff from disk multiple times
		'''
		def __init__(self):
			db = db_open_dict("bdb:project",ro=True)
			self.db_map = db.get("global.spr_filt_ptcls_map",dfl={})
						
#		def __del__(self):
#			print "CTF columns dies"
		
		def __get_num_filtered(self,name,filt):
			if self.db_map.has_key(name):
				val = self.db_map[name]
				if val.has_key(filt):
					file_name = val[filt]
					return str(EMUtil.get_image_count(file_name))
				
			return ""
		
		def __get_dim_filtered(self,name,filt):
			if self.db_map.has_key(name):
				val = self.db_map[name]
				if val.has_key(filt):
					file_name = val[filt]
					nx,ny,nz = gimme_image_dimensions3D(file_name)
					return "%ix%ix%i" %(nx,ny,nz)

			return ""
		
		def get_num_phase_flipped(self,name):
			return self.__get_num_filtered(name,"Phase flipped")
				
		def phase_flipped_dim(self,name):
			return self.__get_dim_filtered(name,"Phase flipped")
		
		def get_num_wein_filt(self,name):
			return self.__get_num_filtered(name,"Wiener filtered")
				
		def wien_filt_dim(self,name):
			return self.__get_dim_filtered(name,"Wiener filtered")
		
		
				
	def get_names_with_ctf_params(self):
		'''
		opens the e2ctf.parms directory and returns all a list of lists like this:
		[[db_name_key, real_image_name],....]
		eg
		[[neg_001,neg_001.hdf],[ptcls_01,bdb:particles#ptcls_01_ptcls],...] etc
		e2ctf is responsible for making sure the last data entry for each image is the original image name (this was first enforced by d.woolford)
		'''
		if not db_check_dict("bdb:e2ctf.parms"): return None
		parms_db = db_open_dict("bdb:e2ctf.parms",ro=True)
		
		ret = []
		for key,data in parms_db.items():
			if data == None:
				print "error?",key
				continue
			ret.append([key,data[-1]]) # parms[-1] should be the original filename
		#db_close_dict("bdb:e2ctf.parms")
		return ret

class CTFReportTask(E2CTFWorkFlowTask):
	
	documentation_string = "This tool is for displaying the currently determined CTF parameters for the particles associated with the project. It also displays the number of phase flipped and/or wiener filtered images corresponding to each particle set."
	warning_string = "\n\n\nNOTE: There are no particles currently associated with the project. Please go to the \"Particles\" task and import/box particles first."
	def __init__(self):
		E2CTFWorkFlowTask.__init__(self)
		self.window_title = "Particle CTF parameters"

	def get_params(self):
		params = []
		p,n = self.get_full_ctf_table()
		if n == 0:
			params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=CTFReportTask.documentation_string+CTFReportTask.warning_string,choices=None))
		else:
			params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=CTFReportTask.documentation_string,choices=None))
			params.append(p)
		return params

	def write_db_entry(self,key,value):
		pass		

class E2CTFGenericTask(ParticleWorkFlowTask):
	documentation_string = "Fill me in"
	def __init__(self):
		ParticleWorkFlowTask.__init__(self)
		self.window_title = "e2ctf"
		self.preferred_size = (480,200)
		self.form_db_name = "bdb:emform.e2ctf"
		
		
	def get_params(self):
		params = []		
#		params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=E2CTFGenericTask.documentation_string,choices=None))
		db = db_open_dict(self.form_db_name)
		params.append(ParamDef(name="running_mode",vartype="choice",desc_short="Choose your running mode",desc_long="There are three CTF related task which are generally run in order",property=None,defaultunits=db.get("running_mode",dfl="auto params"),choices=["auto params", "interactively fine tune", "write output"]))
		#db_close_dict(self.form_db_name)
		return params

	def on_form_ok(self,params):
		if params["running_mode"] == "auto params":
			self.emit(QtCore.SIGNAL("replace_task"),E2CTFAutoFitTaskGeneral(),"ctf auto fit")
			self.form.closeEvent(None)
			self.form = None
		elif params["running_mode"] == "interactively fine tune":
			self.emit(QtCore.SIGNAL("replace_task"),E2CTFGuiTaskGeneral(),"fine tune ctf")
			self.form.closeEvent(None)
			self.form = None
		elif params["running_mode"] == "write output":
			self.emit(QtCore.SIGNAL("replace_task"),E2CTFOutputTaskGeneral(),"ctf output")
			self.form.closeEvent(None)
			self.form = None	
		else:
			self.form.closeEvent(None)
			self.form = None
			self.emit(QtCore.SIGNAL("task_idle"))
			return
		
		self.write_db_entries(params)
			
class E2CTFAutoFitTask(E2CTFWorkFlowTask):	
	documentation_string = "Select the particles you wish to generate CTF parameters for, enter the appropriate parameters such as microscope voltage etc, and hit OK.\nThis will cause the workflow to spawn processes based on the available CPUs. Once finished the automatically determined CTF parameters will be stored in the EMAN2 database."
	warning_string = "\n\n\nNOTE: There are no particles currently associated with the project. Please go to the \"Particles\" task and import/box particles first."

	def __init__(self):
		E2CTFWorkFlowTask.__init__(self)
		self.window_title = "e2ctf auto fitting"

	def get_params(self):
		params = []
		p,n= self.get_ctf_param_table()
#		if n == 0 and False:
#			params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=E2CTFAutoFitTask.documentation_string+E2CTFAutoFitTask.warning_string,choices=None))
#		else:
		params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=E2CTFAutoFitTask.documentation_string,choices=None))
		params.append(p)
		self.add_general_params(params)

		return params
	
	def add_general_params(self,params):
		project_db = db_open_dict("bdb:project")
		db = db_open_dict(self.form_db_name)
		papix = ParamDef(name="global.apix",vartype="float",desc_short="A/pix for project",desc_long="The physical distance represented by the pixel spacing",property=None,defaultunits=project_db.get("global.apix",dfl=1.1),choices=None)
		pvolt = ParamDef(name="global.microscope_voltage",vartype="float",desc_short="Microscope voltage",desc_long="The operating voltage of the microscope in kilo volts",property=None,defaultunits=project_db.get("global.microscope_voltage",dfl=300),choices=None)
		pcs = ParamDef(name="global.microscope_cs",vartype="float",desc_short="Microscope Cs",desc_long="Microscope spherical aberration constant",property=None,defaultunits=project_db.get("global.microscope_cs",dfl=2.0),choices=None)
		pac = ParamDef(name="ac",vartype="float",desc_short="Amplitude contrast",desc_long="The amplitude contrast constant. It is recommended that this value is identical in all of your images.",property=None,defaultunits=db.get("ac",dfl=10),choices=None)
		pos = ParamDef(name="oversamp",vartype="int",desc_short="Oversampling",desc_long="If greater than 1, oversampling by this amount will be used when images are being phase flipped and Wiener filtered.",property=None,defaultunits=db.get("oversamp",dfl=1),choices=None)
		pncp = ParamDef(name="global.num_cpus",vartype="int",desc_short="Number of CPUs",desc_long="Number of CPUS available for the project to use",property=None,defaultunits=project_db.get("global.num_cpus",dfl=num_cpus()),choices=None)
		pahp = ParamDef(name="autohp",vartype="boolean",desc_short="Auto high pass",desc_long="Automatic high pass filter of the SNR only to remove initial sharp peak, phase-flipped data is not directly affected (default false)",property=None,defaultunits=db.get("autohp",dfl=False),choices=None)
		pns = ParamDef(name="nosmooth",vartype="boolean",desc_short="No smoothing",desc_long="Disable smoothing of the background (running-average of the log with adjustment at the zeroes of the CTF)",property=None,defaultunits=db.get("nosmooth",dfl=False),choices=None)
		#db_close_dict(self.form_db_name)
		
		params.append([papix,pvolt])
		params.append([pcs,pac])
		params.append([pos,pncp])
		params.append([pahp,pns])

		#db_close_dict("bdb:project")
	
	def get_default_ctf_options(self,params):
		'''
		These are the options required to run pspec_and_ctf_fit in e2ctf.py
		'''
		
		error_message = []
		
		if not params.has_key("filenames"): return None # this is fine
		
		if  params.has_key("filenames") and len(params["filenames"]) == 0:
			self.run_select_files_msg()
			return None
		
		filenames = params["filenames"]
		boxsize = None
		db_file_names = []
		for i,name in enumerate(filenames):
			db_name= name
			db_file_names.append(db_name)
			if not file_exists(db_name):
				error_message.append("error, %s does not exist." %name)
				continue
			
			if boxsize == None:
				a = EMData()
				a.read_image(db_name,0,True)
				hdr = a.get_attr_dict()
				boxsize = hdr["nx"] # no consideration is given for non square images
				#db_close_dict(db_name)
			else:
				a = EMData()
				a.read_image(db_name,0,True)
				hdr = a.get_attr_dict()
				#db_close_dict(db_name)
				if boxsize != hdr["nx"]: # no consideration is given for non square images
					error_message.append("Can't run e2ctf on images with different box sizes.")
		
		if boxsize == None or boxsize < 2:
			error_message.append("error, boxsize is less than 2.")
		
		
		if boxsize == None:
			error_message.append("Something went wrong in the form")
			self.show_error_message(error_message)
			return None
		
		options = EmptyObject()
		options.bgmask = boxsize/2
		options.filenames = db_file_names
		error_message.extend(self.append_general_options(options,params))
		
		if len(error_message) > 0:
			self.show_error_message(error_message)
			return None
	
		return options
	
	def append_general_options(self,options,params):
		'''
		This is done in more than one place hence this function
		'''
		
		options.nosmooth = params["nosmooth"]
		options.nonorm = False
		options.autohp = params["autohp"]
		options.invert = False
		options.oversamp = params["oversamp"]
		options.ac = params["ac"]
		options.apix = params["global.apix"]
		options.cs = params["global.microscope_cs"]
		options.voltage = params["global.microscope_voltage"]
		
		
		error_message = []
		if options.oversamp < 1:
			error_message.append("You must specify a value for oversamp that is atleast 1.")
		if options.apix <= 0:
			error_message.append("You must specify a positive non zero value for the apix.")
		if options.voltage <= 0:
			error_message.append("You must specify a positive non zero value for the voltage.")
		
		return error_message
		
	def on_form_ok(self,params):
		
		options = self.get_default_ctf_options(params)
		if options != None:
			self.write_db_entries(params)
			
			string_args = ["bgmask","oversamp","ac","apix","cs","voltage"]
			bool_args = ["nosmooth","nonorm","autohp","invert"]
			additional_args = ["--auto_fit"]
			temp_file_name = "e2ctf_autofit_stdout.txt"
			self.spawn_task("e2ctf.py",options,string_args,bool_args,additional_args,temp_file_name)
			
			self.form.closeEvent(None)
			self.emit(QtCore.SIGNAL("task_idle"))
			
		else:
			return
		
	def on_form_close(self):
		# this is to avoid a task_idle signal, which would be incorrect if e2boxer is running
		self.emit(QtCore.SIGNAL("task_idle"))
			
class E2CTFAutoFitTaskGeneral(E2CTFAutoFitTask):
	'''
	This one has a generic url browser to get the input file names as opposed to the more rigid project based one
	'''
	documentation_string = "Use this tool to use e2ctf to generate ctf parameters for the particles located anywhere on disk. Use the browse buttons to locate the files on disk, enter the fitting parameters such as microscope voltage and angstrom per pixel, and hit OK. \nThis will cause the workflow to spawn processes based on the available CPUs. Once finished the automatically determined CTF parameters will be stored in the EMAN2 database."
	
	def __init__(self):
		E2CTFAutoFitTask.__init__(self)
		self.window_title = "e2ctf auto fitting"
		self.file_check = True
	def get_params(self):
		params = []		
		params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=E2CTFAutoFitTask.documentation_string,choices=None))
		
		params.append(ParamDef(name="filenames",vartype="url",desc_short="File Names",desc_long="The names of the particle files you want to generate automated ctf parameters for",property=None,defaultunits=[],choices=[]))
		
		self.add_general_params(params)

		return params
	
	def get_default_ctf_options(self,params):
		'''
		These are the options required to run pspec_and_ctf_fit in e2ctf.py
		'''
		
		if not params.has_key("filenames"): return None # this is fine
		
		if  params.has_key("filenames") and len(params["filenames"]) == 0:
			return None # this is fine
		
		
		filenames = params["filenames"]
		fine,message = check_files_are_em_images(filenames)
		
		if not fine:
			print message
			return None
		
		boxsize = None
		db_file_names = []
		for i,name in enumerate(filenames):
			a = EMData()
			a.read_image(name,0,True)
			if boxsize == None:
				boxsize = a.get_attr("nx") # no consideration is given for non square images
			elif boxsize != a.get_attr("nx"): # no consideration is given for non square images
					print "error, can't run e2ctf on images with different box sizes." # Specifically, I can not deduce the bgmask option for the group"
					return None
		
		if boxsize == None or boxsize < 2:
			print "error, boxsize is less than 2"
			return None
		
		options = EmptyObject()
		options.bgmask = boxsize/2
		options.filenames = filenames
		self.append_general_options(options,params)
		return options

class E2CTFOutputTask(E2CTFWorkFlowTask):	
	documentation_string = "Select the particle data for which you wish to generate phase flipped and/or Wiener filtered output and hit OK.\nThis will cause the workflow to spawn processes based on the available CPUs that write the output into a predefined location in the EMAN2 database.\nNote that the Wiener filtered output images are also phase flipped."
	warning_string = "\n\n\nNOTE: There are no particles associated with the project and/or there are no previously generated CTF parameters for these particles. To establish project particles go to the \"Particles\" task. To generate CTF parameters go to the \"Automated fitting - e2ctf\" task" 
	def __init__(self):
		E2CTFWorkFlowTask.__init__(self)
		self.window_title = "e2ctf output"

	def get_params(self):
		params = []		

		p,n = self.get_full_ctf_table()
		db = db_open_dict(self.form_db_name)
		params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=E2CTFOutputTask.documentation_string,choices=None))
		params.append(p)
		pos = ParamDef(name="oversamp",vartype="int",desc_short="Oversampling",desc_long="If greater than 1, oversampling by this amount will be used when images are being phase flipped and Wiener filtered.",property=None,defaultunits=db.get("oversamp",dfl=1),choices=None)
		pwiener = ParamDef(name="wiener",vartype="boolean",desc_short="Wiener",desc_long="Wiener filter your particle images using parameters in the database. Phase flipping will also occur",property=None,defaultunits=db.get("wiener",dfl=False),choices=None)
		pphase = ParamDef(name="phaseflip",vartype="boolean",desc_short="Phase flip",desc_long="Phase flip your particle images using parameters in the database",property=None,defaultunits=db.get("phaseflip",dfl=False),choices=None)
		params.append(pos)
		params.append([pphase,pwiener])
			#db_close_dict(self.form_db_name)
		
		return params

	def get_default_ctf_options(self,params):
		'''
		These are the options required to run pspec_and_ctf_fit in e2ctf.py, works in e2workflow
		'''
		
		error_message = []
		if  not params.has_key("filenames") or (params.has_key("filenames") and len(params["filenames"]) == 0):
			error_message.append("Please select files to process")
			return None
		
		
		options = EmptyObject()
	
		filenames = params["filenames"]
#
		db_file_names = []
		for i,name in enumerate(filenames):
			db_name=name
			db_file_names.append(db_name)
			if not file_exists(db_name):
				print "error, particle entry doesn't exist for",name,"aborting."
				return None
			
		options.filenames = db_file_names
		options.wiener = params["wiener"]
		options.phaseflip = params["phaseflip"]
		options.oversamp = params["oversamp"]
		if not options.wiener and not options.phaseflip:
			error_message.append("Please choose at atleast one of the phaseflip or Wiener options.")
			
		if options.oversamp < 1:
			error_message.append("The oversampling factor must be atleast 1")
			
		if len(error_message) > 0:
			self.show_error_message(error_message)
			return None
#		
		return options
	
	def on_form_ok(self,params):

		options = self.get_default_ctf_options(params)
		if options != None and len(options.filenames) > 0 and (options.wiener or options.phaseflip):
			self.write_db_entries(params)
			string_args = []
			bool_args = ["wiener","phaseflip"]
			additional_args = ["--dbds="+"global.spr_filt_ptcls_map"]
			temp_file_name = "e2ctf_output_stdout.txt"
			self.spawn_task("e2ctf.py",options,string_args,bool_args,additional_args,temp_file_name)
			

			self.form.closeEvent(None)
			self.emit(QtCore.SIGNAL("task_idle"))
		else:
			return
	
	def on_ctf_closed(self):
		self.emit(QtCore.SIGNAL("gui_exit")) #
		
	def on_form_close(self):
		# this is to avoid a task_idle signal, which would be incorrect if e2boxer is running
		self.emit(QtCore.SIGNAL("task_idle"))

class E2CTFOutputTaskGeneral(E2CTFOutputTask):
	''' This one uses the names in the e2ctf.parms to generate it's table of options, not the particles in the particles directory
	'''
	warning_string = "\n\n\nNOTE: There are no CTF parameters currently stored for any images in the local database. You can change this by running automated fitting with e2ctf."
	
	def __init__(self):
		E2CTFOutputTask.__init__(self)
		self.window_title = "e2ctf output"

	def get_params(self):
		params = []
		names = self.get_names_with_ctf_params()
		n = [l[0] for l in names]
		p,num = self.get_ctf_param_table()
		
		if num == 0:
			params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=E2CTFOutputTask.documentation_string+E2CTFOutputTaskGeneral.warning_string,choices=None))
		else:
			params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=E2CTFOutputTask.documentation_string,choices=None))
			params.append(p)
			pwiener = ParamDef(name="wiener",vartype="boolean",desc_short="Wiener",desc_long="Wiener filter your particle images using parameters in the database. Phase flipping will also occur",property=None,defaultunits=False,choices=None)
			pphase = ParamDef(name="phaseflip",vartype="boolean",desc_short="Phase flip",desc_long="Phase flip your particle images using parameters in the database",property=None,defaultunits=False,choices=None)
		
			params.append([pphase,pwiener])
			
		return params
	
	def get_ctf_options(self,params):
		'''
		This is a way to get the ctf optiosn if one is using the "alternate" path, which means just in the context of general use of e2ctf (not the workflow)
		'''
		options = EmptyObject()
		
		if  params.has_key("filenames") and len(params["filenames"]) == 0:
			return None # this is fine, for example, there were no files to work

		selected_filenames = params["filenames"]
		
		filenames = []
		names = self.get_names_with_ctf_params()
		for name in names:
			if name[0] in selected_filenames:
				filenames.append(name[1])
		options.filenames = filenames

		options.wiener = params["wiener"]
		options.phaseflip = params["phaseflip"]
#		
		return options

	def on_form_ok(self,params):
		for k,v in params.items():
			self.write_db_entry(k,v)

		options = self.get_ctf_options(params)
		if options != None and len(options.filenames) > 0 and (options.wiener or options.phaseflip):
			
			string_args = []
			bool_args = ["wiener","phaseflip"]
			additional_args = []
			temp_file_name = "e2ctf_output_stdout.txt"
			self.spawn_task("e2ctf.py",options,string_args,bool_args,additional_args,temp_file_name)
			

			self.form.closeEvent(None)
			self.emit(QtCore.SIGNAL("task_idle"))
		else:
			self.form.closeEvent(None)
			self.emit(QtCore.SIGNAL("task_idle"))
	
class E2CTFGuiTask(E2CTFWorkFlowTask):	
	documentation_string = "Select the particle data you wish to evaluate/tweak in the e2ctf interactive interface and hit OK. This will launch e2ctf and the selected images will automatically be loaded for viewing. Once inside the e2ctf interface you can save your tweaked parameters to the database using the Save button."
	warning_string = "\n\n\nNOTE: There are no particles associated with the project and/or there are no previously generated CTF parameters for these particles. To establish project particles go to the \"Particles\" task. To generate CTF parameters go to the \"Automated fitting - e2ctf\" task" 
	def __init__(self):
		E2CTFWorkFlowTask.__init__(self)
		self.window_title = "e2ctf interface"
		self.gui = None # will eventually be a e2ctf gui

	def get_params(self):

#		ptcl_names = self.get_particle_db_names(strip_ptcls=False) # particles in the project directory
#		if ptcl_names != None and len(ptcl_names) != 0: 
		p,n = self.get_ctf_param_table()
#		else:
#			n = 0
		params = []		
		if n == 0:
			params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=E2CTFGuiTask.documentation_string+E2CTFGuiTask.warning_string,choices=None))
		else:
			params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=E2CTFGuiTask.documentation_string,choices=None))
		  	params.append(p)
		return params
	
	def get_default_ctf_options(self,params):
		'''
		These are the options required to run pspec_and_ctf_fit in e2ctf.py
		'''
		
		if  params.has_key("filenames") and len(params["filenames"]) == 0:
			self.run_select_files_msg()
			return None

		options = EmptyObject()
		filenames = params["filenames"]
#
		db_file_names = []
		for i,name in enumerate(filenames):
			db_name=name
			db_file_names.append(db_name)
			if not file_exists(db_name):
				print "No project particles entry exists for",name,"aborting."
				return None
		options.filenames = db_file_names
#		
		return options

	
	def on_form_ok(self,params):
		for k,v in params.items():
			self.write_db_entry(k,v)

		options = self.get_default_ctf_options(params)
		if options != None and len(options.filenames) > 0:
			
			img_sets = get_gui_arg_img_sets(options.filenames)
		
			
			self.gui=GUIctfModule(get_application(),img_sets)
			self.emit(QtCore.SIGNAL("gui_running"), "CTF", self.gui) # so the desktop can prepare some space!
			self.form.closeEvent(None)
			QtCore.QObject.connect(self.gui,QtCore.SIGNAL("module_closed"), self.on_ctf_closed)
			self.gui.show_guis()
		else:
			return
	
	def on_ctf_closed(self):
		if self.gui != None:
			self.gui = None
			self.emit(QtCore.SIGNAL("gui_exit")) #
		
	def on_form_close(self):
		# this is to avoid a task_idle signal, which would be incorrect if e2boxer is running
		if self.gui == None:
			self.emit(QtCore.SIGNAL("task_idle"))
		else: pass
		
class E2CTFGuiTaskGeneral(E2CTFGuiTask):
	''' This one uses the names in the e2ctf.parms to generate it's table of options, not the particles in the particles directory
	'''
	warning_string = "\n\n\nNOTE: There are there are no previously generated CTF parameters. Please run automated fitting using e2ctf first." 
	
	documentation_string = "Write me"
	def __init__(self):
		E2CTFGuiTask.__init__(self)

	def get_params(self):
		params = []		
		
		names = self.get_names_with_ctf_params()
		n = [l[0] for l in names]
		p,num = self.get_ctf_param_table()
		
		if num == 0:
			params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=E2CTFGuiTask.documentation_string+E2CTFGuiTaskGeneral.warning_string,choices=None))
		else:
			params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=E2CTFGuiTaskGeneral.documentation_string,choices=None))
			params.append(p)
		return params
	
	def get_default_ctf_options(self,params):
		'''
		These are the options required to run pspec_and_ctf_fit in e2ctf.py
		'''
	
		if  params.has_key("filenames") and len(params["filenames"]) == 0:
			self.run_select_files_msg()
			return None # this is fine
		
		
		options = EmptyObject()

		selected_filenames = params["filenames"]
		
		filenames = []
		names = self.get_names_with_ctf_params()
		for name in names:
			if name[0] in selected_filenames:
				filenames.append(name[1])
		options.filenames = filenames
#		
		return options


class E2Refine2DReportTask(ParticleWorkFlowTask):
	documentation_string = "This form displays the current sets of reference free class averages that have been generated by 2D refinement processess."
	warning_string = "\n\n\nNote: There are no reference free class averages currently associated with the project. Try running e2refine2d in the options below."
	
	def __init__(self):
		ParticleWorkFlowTask.__init__(self)
		self.window_title = "Refine 2D class averages "
		
		
	def get_params(self):
		params = []		
		
		self.rfcat = E2RefFreeClassAveTool()
		p,n = self.rfcat.get_reference_free_class_averages_table()

		params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=E2Refine2DReportTask.documentation_string,choices=None))
		params.append(p)
		return params
	
	def on_form_cancel(self):
		self.rfcat.recover_original_raw_data_list()
		
		self.form.closeEvent(None)
		self.form = None
		self.emit(QtCore.SIGNAL("task_idle"))


class EMClassificationTools(ParticleWorkFlowTask):
	'''
	Encapsulation of common functionality.
	Specifically - e2classaverage and e2simmx pages - both of which are used by e2refine and e2refine2d
	'''
	def __init__(self):
		ParticleWorkFlowTask.__init__(self)
		
	def get_simmx_page(self):
		
		params = []
		params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=E2RefineParticlesTask.simmx_documentation,choices=None))

		db = db_open_dict(self.form_db_name)
		pshrink = ParamDef(name="shrink",vartype="int",desc_short="Shrink",desc_long="The the downsampling rate used to shrink the data at various stages in refinement, for speed purposes",property=None,defaultunits=db.get("shrink",dfl=4),choices=[])
		
		
		params.append(pshrink)
		params.extend(self.get_cls_simmx_params(parameter_prefix="sim"))
		
		#db_close_dict(self.form_db_name)
		return ["Simmx",params]
	

	def get_classaverage_page(self,include_sep=True):
		params = []
		params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=E2RefineParticlesTask.class_documentation,choices=None))

		db = db_open_dict(self.form_db_name)
		
		psep = ParamDef(name="sep",vartype="int",desc_short="Class separation",desc_long="The number of classes a particle can contribute towards",property=None,defaultunits=db.get("sep",dfl=1),choices=[])
		piter = ParamDef(name="classiter",vartype="int",desc_short="Averaging iterations",desc_long="The number of class averaging iterations",property=None,defaultunits=db.get("classiter",dfl=2),choices=[])
		
		averagers = self.get_averagers_list()
		averagers.sort()
		paverager =  ParamDef("classaverager",vartype="string",desc_short="Averager",desc_long="The method used for generating class averages",property=None,defaultunits=db.get("classaverager",dfl="mean"),choices=averagers)
		
		pkeep = ParamDef(name="classkeep",vartype="float",desc_short="keep",desc_long="The fraction of particles to keep in each class average. If sigma based is checked this value is interpreted in standard deviations from the mean instead",property=None,defaultunits=db.get("classkeep",dfl=0.8),choices=[])
		pkeepsig = ParamDef(name="classkeepsig",vartype="boolean",desc_short="Sigma based",desc_long="If checked the keep value is interpreted in standard deviations from the mean instead of basic ratio",property=None,defaultunits=db.get("classkeepsig",dfl=True),choices=[])
		
		pnormproc =  ParamDef("classnormproc",vartype="string",desc_short="Normalization processor",desc_long="The normalization method applied to the class averages",property=None,defaultunits=db.get("classnormproc",dfl="normalize.edgemean"),choices=["normalize","normalize.edgemean","None"])
		
		#db_close_dict(self.form_db_name)
		
		if include_sep: 
			params.append([piter,psep])
			params.append([pkeep,pkeepsig])
		else: # this happens in the eotest
			# I made the next row longer because it seemed like there was room
			params.append([piter,pkeep,pkeepsig])
		params.append([paverager,pnormproc])
		params.extend(self.get_cls_simmx_params(parameter_prefix="class"))

		return ["Class averaging",params]
	
	def get_cls_simmx_params(self,parameter_prefix=""):
		params = []
		aligners = self.get_aligners_list()
		cmps = self.get_cmps_list()
		
		aligners.sort()
		cmps.sort()
		
		db = db_open_dict(self.form_db_name)
		
		palign =  ParamDef(name=parameter_prefix+"align",vartype="string",desc_short="Aligner",desc_long="The aligner being used",property=None,defaultunits=db.get(parameter_prefix+"align",dfl="rotate_translate_flip"),choices=aligners)
		palignargs =  ParamDef(name=parameter_prefix+"alignargs",vartype="string",desc_short="params",desc_long="Parameters for the aligner, see \"e2help.py aligners\"",property=None,defaultunits=db.get(parameter_prefix+"alignargs",dfl=""),choices=[])
		
		paligncmp =  ParamDef(name=parameter_prefix+"aligncmp",vartype="string",desc_short="Align comparator",desc_long="The comparator being used",property=None,defaultunits=db.get(parameter_prefix+"aligncmp",dfl="phase"),choices=cmps)
		paligncmpargs =  ParamDef(name=parameter_prefix+"aligncmpargs",vartype="string",desc_short="params",desc_long="Parameters for this comparator, see \"e2help.py cmps\"",property=None,defaultunits=db.get(parameter_prefix+"aligncmpargs",dfl=""),choices=[])	
		
		
		pralign =  ParamDef(name=parameter_prefix+"ralign",vartype="string",desc_short="Refine aligner",desc_long="The refine aligner being used",property=None,defaultunits=db.get(parameter_prefix+"ralign",dfl="None"),choices=["None","refine"])
		pralignargs =  ParamDef(name=parameter_prefix+"ralignargs",vartype="string",desc_short="params",desc_long="Parameters for this aligner, see \"e2help.py aligners\"",property=None,defaultunits=db.get(parameter_prefix+"ralignargs",dfl=""),choices=[])
		
		praligncmp =  ParamDef(name=parameter_prefix+"raligncmp",vartype="string",desc_short="Refine align comparator",desc_long="The comparator being used for refine alignment",property=None,defaultunits=db.get(parameter_prefix+"raligncmp",dfl="phase"),choices=cmps)
		praligncmpargs =  ParamDef(name=parameter_prefix+"raligncmpargs",vartype="string",desc_short="params",desc_long="Parameters for thos comparator, see \"e2help.py cmps\"",property=None,defaultunits=db.get(parameter_prefix+"raligncmpargs",dfl=""),choices=[])	
		
		pcmp  =  ParamDef(name=parameter_prefix+"cmp",vartype="string",desc_short="Main comparator",desc_long="The comparator to determine the final quality metric",defaultunits=db.get(parameter_prefix+"cmp",dfl="phase"),choices=cmps)
		pcmpargs =  ParamDef(name=parameter_prefix+"cmpargs",vartype="string",desc_short="params",desc_long="Parameters for the this comparator, see \"e2help.py cmps\"",property=None,defaultunits=db.get(parameter_prefix+"cmpargs",dfl=""),choices=[])	
	
		#db_close_dict(self.form_db_name)

		params.append([pcmp,pcmpargs])
		params.append([palign,palignargs])
		params.append([paligncmp,paligncmpargs])
		params.append([pralign,pralignargs])
		params.append([praligncmp,praligncmpargs])
		
		return params
	
	def check_aligners_and_cmps(self,params,options,parameter_prefix="class",page="Class averaging"):
		
		error_message = []
		vals = []
		
		vals.append(["align","alignargs"])
		vals.append(["ralign","ralignargs"])
		vals.append(["aligncmp","aligncmpargs"])
		vals.append(["raligncmp","raligncmpargs"])
		vals.append(["cmp","cmpargs"])
		
		
		for v in vals:
			v[0] = parameter_prefix + v[0]
			v[1] = parameter_prefix + v[1]
		
		for v in vals:
			setattr(options,v[0],params[v[0]])
			setattr(options,v[1],params[v[1]])
		
		for v in vals:
			if getattr(options,v[0]) == "None": setattr(options,v[0],None)
			elif len(getattr(options,v[1])) != 0: setattr(options,v[0],getattr(options,v[0])+":"+getattr(options,v[1]))
		
		
		for i,v in enumerate(vals):
			arg = getattr(options,v[0])
			if arg != None:
				if i > 1: # its a cmp, yes a hack but I have no time
					if not check_eman2_type(arg,Cmps,"Cmp",False): error_message.append("There is problem with the " +v[0]+ " comparator argument in the "+page+" page.")
				else:
					if not check_eman2_type(arg,Aligners,"Aligner",False): error_message.append("There is problem with the " +v[0]+ " aligner argument in the "+page+" page.")
  	
  		return error_message
  	
  	def add_classaverage_args(self,options,string_args,bool_args,additional_args,include_sep=True):
		
		optionals = ["classcmp","classalign","classaligncmp","classralign","classraligncmp"]
		for opt in optionals:
			if getattr(options,opt) != None: string_args.append(opt)
			
		string_args.extend(["classiter","classkeep","classnormproc","classaverager"])
		if include_sep: string_args.append("sep")
		bool_args.append("classkeepsig")
	
	def check_classaverage_page(self,params,options):
		error_message = []
		
		if params.has_key("sep") and params["sep"] <= 0: # sometimes this key is absent (from the e2eotest form)
			error_message.append("The separation argument in the Class average page must be atleast 1")
		
		if params["classiter"] < 0:
			error_message.append("The number of class averaging iterations must be atleast 0")
		
		if params["classkeepsig"] == False:
			if params["classkeep"] < 0 or params["classkeep"] > 1:
				error_message.append("The keep parameter in the Class average page must be between 0 and 1. This does not hold if the \'Sigma based\' option is selected.")
				
		error_message.extend(self.check_aligners_and_cmps(params,options,"class", "Class average"))
		
		if len(error_message) > 0: return error_message # calling program should act and discontinue
		
		if params.has_key("sep"): options.sep = params["sep"] # sometimes this key is absent (from the e2eotest form)
		options.classkeep = params["classkeep"]
		options.classkeepsig = params["classkeepsig"]
		options.classnormproc = params["classnormproc"]
		options.classiter = params["classiter"]
		
		options.classaverager = params["classaverager"] # at the moment there are no extra averager parameter, but if that changes then the parameteres would have to be checked
		
		return error_message

	
	def add_simmx_args(self,options,string_args,bool_args,additional_args,include_shrink=True):
		
		optionals = ["simcmp","simalign","simaligncmp","simralign","simraligncmp"]
		for opt in optionals:
			if getattr(options,opt) != None: string_args.append(opt)
		
		if include_shrink and options.shrink > 1: string_args.append("shrink") # e2simmx doesn't like it if shrink is 1
	
	
	def check_simmx_page(self,params,options):
		error_message = []
		if params["shrink"] <= 0:
			error_message.append("The shrink argument in the simmx page must be atleast 1")
			
		options.shrink=params["shrink"]
		
		error_message.extend(self.check_aligners_and_cmps(params,options,"sim","Simmx"))
		
		return error_message

class E2Refine2DTask(EMClassificationTools):
	'''
	Common e2refine2D functionality
	'''
	documentation_string = "This form is a way for the user to supply arguments to and execute e2refine2d.py"
	def __init__(self):
		EMClassificationTools.__init__(self)
		self.window_title = "Run e2refine2d"
		self.form_db_name = "bdb:emform.e2refine2d"
		self.workflow_setting = True # you can turn this off if you don't want results stored workflow list of reference free class averages
		
	def get_general_params(self):
		db = db_open_dict(self.form_db_name)
		
		params = []		
		piter = ParamDef(name="iter",vartype="int",desc_short="Refinement iterations",desc_long="The number of times the e2refine2d svd-based class averaging procedure is iterated",property=None,defaultunits=db.get("iter",dfl=5),choices=[])
		pnaliref = ParamDef(name="naliref",vartype="int",desc_short="# alignment references",desc_long="The number of alignment references to use when determining particle orientations",property=None,defaultunits=db.get("naliref",dfl=8),choices=[])
		pnbasisfp = ParamDef(name="nbasisfp",vartype="int",desc_short="# basis fp",desc_long="The number of MSA basis vectors to use when classifying",property=None,defaultunits=db.get("nbasisfp",dfl=5),choices=[])
		pncls = ParamDef(name="ncls",vartype="int",desc_short="# classes",desc_long="The number of classes to produce",property=None,defaultunits=db.get("ncls",dfl=32),choices=[])

		pnp = ParamDef(name="normproj",vartype="boolean",desc_short="Normalize projection vectors",desc_long="Normalizes each projected vector into the MSA subspace",property=None,defaultunits=db.get("normproj",dfl=False),choices=None)
		
		project_db = db_open_dict("bdb:project")
		pncp = ParamDef(name="global.num_cpus",vartype="int",desc_short="Number of CPUs",desc_long="Number of CPUS available for e2refine2d to use",property=None,defaultunits=project_db.get("global.num_cpus",dfl=num_cpus()),choices=None)
		pinitclasses =  ParamDef(name="initial",vartype="string",desc_short="Initial class averages",desc_long="A file (full path) containing starting class averages. If note specificed will generate starting class averages automatically.",property=None,defaultunits=db.get("initial",dfl=""),choices=[])	
		
		#db_close_dict(self.form_db_name)
		#db_close_dict("bdb:project")
		
		params.append([pncls,pnp])
		params.append(piter)
		params.append([pnaliref,pnbasisfp])
		params.append([pncp,pinitclasses])
		
		return params

	def check_main_page(self,params,options):
		error_message = []
		interested_in = ["initial","iter","naliref","nbasisfp","ncls","filenames","normproj"] #including filenames could be a hack
		for val in interested_in:
			setattr(options,val,params[val])
		
		#options.parallel = params["global.num_cpus"]
		if options.initial == "" or str(options.initial) == "None" or str(options.initial) == "none":
			options.initial = None
			
		if options.initial != None and len(options.initial) > 0:
	 		if not file_exists(options.initial):
	 			error_message.append("The initial class averages file you specified (%s) does not exist." %(options.initial))
	 		
	 	if options.iter < 0: error_message.append("The number of e2refine2d iterations must be atleast 0.")
		if options.naliref < 1:	error_message.append("The number alignment references must be atleast 1.")
	  	if options.nbasisfp < 1: error_message.append("The number of MSA basis vectors must be atleast 1.")
	  	if options.ncls < 2: error_message.append("The number of classes must be atleast 2.")
	  	#if options.parallel < 1: error_message.append("The number CPUs availables must be atleast 1.")
  		
  		if len(error_message) != 0:
 			return error_message
	 	
	 	# if we make it here we are almost definitely good to go, the only thing that can fail is the e2bdb or e2proc2d commands
	 	options.path = numbered_path("r2d",True)
	 	if options.filenames[0][:4] == "bdb:": 
	 		bdb_success, bdb_cmd = self.make_v_stack(options)
		 	if bdb_success:
		 		if options.shrink > 1:
		 			cmd = "e2proc2d.py"
		 			cmd += " bdb:"+options.path+"#all"
		 			options.input =  "bdb:"+options.path+"#all"+str(options.shrink)
		 			cmd += " "+options.input
		 			cmd += " --process=math.meanshrink:n="+str(options.shrink)
		 			
		 			get_application().setOverrideCursor(Qt.BusyCursor)
		 			success = (os.system(cmd) in (0,12))
		 			get_application().setOverrideCursor(Qt.ArrowCursor)
		 			
		 			if not success:
		 				return ["e2proc2d.py shrinking command failed. This command was\n" + cmd +"\nTry again please. If the failure occurs a second time please contact developers."]

		 		else: options.input =  "bdb:"+options.path+"#all"
		 		
		 		options.filenames = [] # this is so spawn_task doesn't supply args to e2refine2d.py
		 		return [] # THIS IS IT, THE POINT OF SUCCESS - returning this means e2refine2d.py is good to go using the given parameters
		 	else:
		 		return ["e2bdb.py command failed. The command was\n" + bdb_cmd +"\nTry again please. If the failure occurs a second time please contact developers"]
		else:
			return self.process_specified_files(options,params)
  		
  		return error_message
  	
  	def add_main_args(self,options,string_args,bool_args,additional_args,):
  		string_args.extend( ["iter","naliref","nbasisfp","path","input","ncls"] ) # May 2009, took "parallel" out
		bool_args.append("normproj")
		optionals = ["initial"]
		for opt in optionals:
			if getattr(options,opt) != None: string_args.append(opt)
			
		

	def get_cmd_line_options(self,params):
		mesbox = QtGui.QMessageBox()
		mesbox.setWindowTitle("Almost but not quite")
		
		options = EmptyObject()
		for k,v in params.items():
			setattr(options,k,v)
		
		if options.initial == "" or str(options.initial) == "None" or str(options.initial) == "none":
			options.initial = None
		
		vals = []
		vals.append(["simcmp","simcmpargs"])
		vals.append(["simalign","simalignargs"])
		vals.append(["simralign","simralignargs"])
		vals.append(["simaligncmp","simaligncmpargs"])
		vals.append(["simraligncmp","simraligncmpargs"])
		
		for v in vals:
			if getattr(options,v[0]) == "None": setattr(options,v[0],None)
			elif len(getattr(options,v[1])) != 0: setattr(options,v[0],getattr(options,v[0])+":"+getattr(options,v[1]))
		
		error_message = []
		if len(options.filenames) == 0: # this is the specialized part - the workflow creates starting data sets from a list of filenames
			error_message.append("Please choose the file(s) that you want to use as as input data for e2refine2d.")

		
		from e2refine2d import check_e2refin2d_args
#		options.parallel = params["global.num_cpus"]
		error_message.extend(check_e2refin2d_args(options))
		
 		if len(error_message) != 0:
 			self.show_error_message(error_message)
	 		return None
	 	
	 	# if we make it here we are almost definitely good to go, the only thing that can fail is the e2bdb or e2proc2d commands
	 	options.path = numbered_path("r2d",True)
	 	if options.filenames[0][:4] == "bdb:": 
	 		bdb_success, bdb_cmd = self.make_v_stack(options)
		 	if bdb_success:
		 		if options.shrink > 1:
		 			cmd = "e2proc2d.py"
		 			cmd += " bdb:"+options.path+"#all"
		 			options.input =  "bdb:"+options.path+"#all"+str(options.shrink)
		 			cmd += " "+options.input
		 			cmd += " --process=math.meanshrink:n="+str(options.shrink)
		 			
		 			get_application().setOverrideCursor(Qt.BusyCursor)
		 			success = (os.system(cmd) in (0,12))
		 			get_application().setOverrideCursor(Qt.ArrowCursor)
		 			
		 			if not success:
		 				mesbox.setText("e2proc2d.py shrinking command failed. This command was\n" + cmd +"\nTry again please. If the failure occurs a second time please contact developers.")
		 			   	mesbox.exec_()
		 				return None
		 		else: options.input =  "bdb:"+options.path+"#all"
		 		
		 		options.filenames = [] # this is so spawn_task doesn't supply args to e2refine2d.py
		 		return options # THIS IS IT, THE POINT OF SUCCESS - returning this means e2refine2d.py is good to go using the given parameters
		 	else:
		 		mesbox.setText("e2bdb.py command failed. The command was\n" + bdb_cmd +"\nTry again please. If the failure occurs a second time please contact developers")
		 		mesbox.exec_()
		 		return None
		else:
			return self.process_specified_files(options,params)
		 	
	 		  
	def make_v_stack(self,options):
	 	
	 	cmd = "e2bdb.py"

	 	for name in options.filenames:
	 		cmd += " "+name
	 	
	 	cmd += " --makevstack=bdb:"+options.path+"#all"
	 	
	 	get_application().setOverrideCursor(Qt.BusyCursor)
	 	success = os.system(cmd)
		print "mvs ",success
		success = (success in (0,12))
	 	get_application().setOverrideCursor(Qt.ArrowCursor)
	 	return success,cmd

	def process_specified_files(self,options,params):
		error_message = []
		if not params.has_key("filenames") or len(params["filenames"]) == 0:
			return ["Please specify files to process"]
#			error_message.append("Please specify files to process")
#			self.show_error_message(error_message)
#			return None
		
		rx = -1
		a = EMData()
		for file in params["filenames"]:
			if not file_exists(file): error_message.append("%s does not exist" %s)
			else:
				try:
					nx,ny,nz = gimme_image_dimensions3D(file)
				except:
					error_message.append("%s is not a valid EM image" %file)
					continue
				
				
				if nz > 1:
					error_message.append("%s is 3D, refine2d works on 2D images only" &file)
					break
				else:
					if nx != ny:
						error_message.append("%s contains images that are not square. Refine2d requires square images" %file)
						break
					if rx == -1:
						rx = nx
					elif nx != rx:
						error_message.append("The dimensions of the image files you specified are not uniform")
						break
						
		if rx == -1:
			error_message.append("Couldn't determine image dimensions")
		
		if len(error_message) != 0:
			return error_message
			#self.show_error_message(error_message)
			#return None
		
		# if we make it here we are good to go
		options.input = None
		options.filenames = [] # important - makes the spawn_process task work
		if len(params["filenames"]) > 1 or options.shrink > 1:
			progress = EMProgressDialogModule(get_application(),"Processing files...", "Abort import", 0, len(params["filenames"]),None)
			progress.qt_widget.show()
		
			for i,file in enumerate(params["filenames"]):
				cmd = "e2proc2d.py"
				cmd += " %s" %file # the input name
				
				if options.shrink > 1: out_name = "bdb:"+options.path+"#all"+str(options.shrink)
				else: out_name = "bdb:"+options.path+"#all"
				
				if options.input == None: options.input = out_name
	 			
	 			cmd += " %s" %out_name # the output name
	 			
	 			if options.shrink > 1: 
	 				cmd += " --process=math.meanshrink:n="+str(options.shrink)
	 			
	 			get_application().setOverrideCursor(Qt.BusyCursor)
	 			success = (os.system(cmd) in (0,12))
	 			get_application().setOverrideCursor(Qt.ArrowCursor)
	 			if not success:
	 				return ["Command %s failed" %cmd]
	 			
	 			
	 			progress.qt_widget.setValue(i+1)
	 			get_application().processEvents()
	 			if progress.qt_widget.wasCanceled():
	 				db_remove_dict(options.input)
	 				progress.qt_widget.close()
	 				return ["Processing was cancelled"]
	 			
	 		try: db_close_dict(out_name)
	 		except:
	 			print "db close dict failed",out_name
	 			
	 		progress.qt_widget.close()
	 		
	 	else:
	 		options.input = params["filenames"][0]
	 	
	 	return []

class EMParticleOptions:
	''' 
	e2refine2d and e2refine, from with the worklfow setting, both want to know the same 
	thing, basically, what are the available particles (including filtered options)
	'''
#	def __init__(self, form_db_name ="bdb:emform.e2refine2d"):
#		self.particles_map = {} # used to cache data in get_params
#		self.particles_name_map = {} # used to recall which selection was taken
#		self.form_db_name = form_db_name
		
	def get_particle_options(self):
		particles_map = {} # used to cache data in get_params
		particles_name_map = {} # used to recall which selection was taken
		
		db = db_open_dict("bdb:project")
		n = 0
		if db.has_key("global.spr_ptcls"):
			ptcls = db["global.spr_ptcls"]
			for name in ptcls:
				n += EMUtil.get_image_count(name)
				
			particles_map["Particles"] = ptcls
				
		# now build up the list of filtered things
		filter_opts = {} # key is the filter type, value is the number of images with this filter type
		if db.has_key("global.spr_filt_ptcls_map"):
			for name,d in db["global.spr_filt_ptcls_map"].items():
				for filt,ptcl_name in d.items():
					if filter_opts.has_key(filt):
						filter_opts[filt] += EMUtil.get_image_count(ptcl_name)
						particles_map[filt].append(ptcl_name)
					else:
						filter_opts[filt] = EMUtil.get_image_count(ptcl_name)
						particles_map[filt] = [ptcl_name]
		
		choices = []
		if n != 0:
			ptcl_name = "Particles ("+str(n)+")"
			choices.append(ptcl_name)
			particles_name_map[ptcl_name] = "Particles"
		for filt,num in filter_opts.items():
			name = filt+" ("+str(num)+")"
			choices.append( name )
			particles_name_map[name] = filt
			
		return particles_map, particles_name_map,choices
		
 		 	
class E2Refine2DChooseDataTask(ParticleWorkFlowTask):
	documentation_string = "Choose the data you wish to use for use for running e2refine2d from the list of options below and hit OK. This will pop up a second form asking you to fill in more details.\n\nNote that usually you should have 4 options to choose from below. If you are not seeing all 4 options it means you should go back in the work flow, import particles, and generate phase flipped and Wiener filtered output." 
	def __init__(self):
		ParticleWorkFlowTask.__init__(self)
		self.window_title = "e2refine2d - getting starting"
		self.preferred_size = (480,300)
		self.form_db_name ="bdb:emform.e2refine2d"
	
	def get_params(self):
		ptcl_opts = EMParticleOptions()
		self.particles_map, self.particles_name_map,choices = ptcl_opts.get_particle_options()
		choices.append("Specify")
			
		params = []		
			
		
		#if as_string:
		#params.append(ParamDef(name="particle_set_choice",vartype="string",desc_long="Choose the particle data set you wish to use to generate a starting data for e2refine2d",desc_short=title,property=None,defaultunits=db.get("particle_set_choice",dfl=""),choices=choices))
		db = db_open_dict(self.form_db_name)
		params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=E2Refine2DChooseDataTask.documentation_string,choices=None))
		params.append(ParamDef(name="particle_set_choice",vartype="choice",desc_long="Choose the particle data set you wish to use to generate a starting data for e2refine2d",desc_short="Choose data",property=None,defaultunits=db.get("particle_set_choice",dfl=""),choices=choices))
		return params

	def on_form_ok(self,params):

		choice = params["particle_set_choice"]
		
		if choice == "Specify":
			self.emit(QtCore.SIGNAL("replace_task"),E2Refine2DWithGenericTask(),"e2refine2d arguments")
		else:
			self.emit(QtCore.SIGNAL("replace_task"),E2Refine2DRunTask(self.particles_map[self.particles_name_map[choice]]),"e2refine2d arguments")
		self.form.closeEvent(None)
		self.form = None
		
		self.write_db_entries(params)
		
class E2RefFreeClassAveTool():
	
	def get_reference_free_class_averages_table(self):
	
		project_db = db_open_dict("bdb:project")
		list_name = "global.spr_ref_free_class_aves"
		names = project_db.get(list_name,dfl=[])
		self.project_files_at_init = names # so if the user hits cancel this can be reset

		from emform import EM2DStackTable,EMFileTable
		table = EM2DStackTable(names,desc_short="Class Averages",desc_long="")
		context_menu_data = EMRawDataReportTask.ProjectListContextMenu(list_name)
		table.add_context_menu_data(context_menu_data)
		table.add_button_data(EMRawDataReportTask.ProjectAddRawDataButton(table,context_menu_data))
		table.insert_column_data(1,EMFileTable.EMColumnData("Particles On Disk",ParticleReportTask.get_num_ptcls,"Particles currently stored on disk that are associated with this image"))
		table.insert_column_data(2,EMFileTable.EMColumnData("Particle Dims",ParticleReportTask.get_particle_dims,"The dimensions of the particles that are stored on disk"))
		
		return table, len(names)
	
	def recover_original_raw_data_list(self):
		'''
		Called if the user hits cancel - if they removed some files or added files the changes
		are not saved unless the user hits ok
		'''
		project_db = db_open_dict("bdb:project")
		project_db["global.spr_ref_free_class_aves"] = self.project_files_at_init
		

class E2Refine2DRunTask(E2Refine2DTask):
	documentation_string = "Choose which files you want to be part of the input data set, enter the appropriate e2refine2d input parameters, and hit OK. This will cause the workflow to spawn e2refine2d in a separate process. Output data will automatically be stored in the EMAN2 database."
	warning_string = "\n\nThere are no files" 
	def __init__(self,particles):
		E2Refine2DTask.__init__(self)
		self.window_title = "run e2refine2d"
		self.end_tag = "_ptcls"
		self.particles = particles
		
	
	def run_form(self):
		self.form = EMTableFormModule(self.get_params(),get_application())
		self.form.qt_widget.resize(*self.preferred_size)
		self.form.setWindowTitle(self.window_title)
		get_application().show_specific(self.form)
		QtCore.QObject.connect(self.form,QtCore.SIGNAL("emform_ok"),self.on_form_ok)
		QtCore.QObject.connect(self.form,QtCore.SIGNAL("emform_cancel"),self.on_form_cancel)
		QtCore.QObject.connect(self.form,QtCore.SIGNAL("emform_close"),self.on_form_close)
		QtCore.QObject.connect(self.form,QtCore.SIGNAL("display_file"),self.on_display_file)
		
	def get_params(self):
	 	params = []
		
		params.append(self.get_main_params())
		params.append(self.get_simmx_page())
		params.append(self.get_classaverage_page(include_sep=False))
		
		return params
	
	def get_main_params(self):
		params = []
		
#		if self.end_tag != "generic":
#			p,n = self.get_particle_selection_table(tag=self.end_tag)
#		else:
#			p = ParamDef(name="filenames",vartype="url",desc_short="Input file name(s)",desc_long="The names of the particle files you want to use as in the input data for e2refine2d.py",property=None,defaultunits=[],choices=[])
#			n = 1 # just to fool the next bit, that's all
#			
	   	p,n = self.get_particle_selection_table(self.particles)
#		if n == 0:
#			params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=E2Refine2DRunTask.documentation_string+E2Refine2DRunTask.warning_string,choices=None))
#		else:
		params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=E2Refine2DRunTask.documentation_string,choices=None))
		params.append(p)
			
		other_params = self.get_general_params()
		
		params.extend(other_params)
		return ["General",params]

	def on_form_ok(self,params):
		self.write_db_entries(params) # I wrote the entries here so that the filenames entry is not altered, allowing the form parameters to be correctly memorized. This breaks a general pattern I am following. It probably doesn't matter at all.
		
#		if self.end_tag != "generic":
#			names = ["bdb:particles#"+name for name in params["filenames"]]
#			params["filenames"] = names 
			
		options = EmptyObject()
		for checker in [self.check_classaverage_page,self.check_simmx_page,self.check_main_page]: # check main page needs the shrink parameter to be checked first
			error_message = checker(params,options)
			if len(error_message) > 0 :
				self.show_error_message(error_message)
#				self.display_errors(error_message)
				return
		# w'oh if we make it here a lot of checking has occured. Now get the args in order to spawn_single_task
		string_args = []
		bool_args = []
		additional_args = []
		
		for get_args in [self.add_main_args,self.add_simmx_args,self.add_classaverage_args]:
			if get_args == self.add_classaverage_args:
				error = get_args(options,string_args,bool_args,additional_args,include_sep=False)
			elif get_args == self.add_simmx_args:
				error = get_args(options,string_args,bool_args,additional_args,include_shrink=False)
			else:
				error = get_args(options,string_args,bool_args,additional_args)
		  	#error = get_args(options,string_args,bool_args,additional_args)
		
			if error != None: # not too fast, something still could have gone wrong
				#self.display_errors([error])
				self.show_error_message([error])
				return
		print "launching"
		if self.workflow_setting: 
			additional_args = ["--dbls=global.spr_ref_free_class_aves"]
		else: 
			additional_args = []
		temp_file_name = "e2refine2d_stdout.txt"
		self.spawn_single_task("e2refine2d.py",options,string_args,bool_args,additional_args,temp_file_name)
		self.emit(QtCore.SIGNAL("task_idle"))
		self.form.closeEvent(None)
		self.form = None

class E2Refine2DWithGenericTask(E2Refine2DRunTask):
	def __init__(self,workflow_setting=True):
		E2Refine2DRunTask.__init__(self,[])
		self.end_tag = "generic"
		self.workflow_setting = workflow_setting
			
							
class E2InitialModelsTool:
	
	def get_initial_models_table(self):
		list_name = "global.spr_init_models"
		project_db = db_open_dict("bdb:project")
		init_model_names = project_db.get(list_name,dfl=[])
		self.project_files_at_init = init_model_names # so if the user hits cancel this can be reset

		from emform import EM3DFileTable,EMFileTable
		table = EM3DFileTable(init_model_names,name="model",desc_short="Initial Models",desc_long="")
		context_menu_data = EMRawDataReportTask.ProjectListContextMenu(list_name)
		table.add_context_menu_data(context_menu_data)
		table.add_button_data(EMRawDataReportTask.ProjectAddRawDataButton(table,context_menu_data))
		table.add_column_data(EMFileTable.EMColumnData("Quality",E2InitialModelsTool.get_quality_score,"This the quality score as determined by e2initialmodel.py"))

		table.add_column_data(EMFileTable.EMColumnData("Dimensions",EMRawDataReportTask.get_image_dimensions,"The dimensions of the file on disk"))

		#p.append(pdims) # don't think this is really necessary
		return table,len(init_model_names)
	
	def get_quality_score(image_name):
		'''
		Used by the initial models table to get a quality score
		'''
		a = EMData()
		a.read_image(image_name,0,True)
		d = a.get_attr_dict()
		if d.has_key("quality"): return "%.3f" %(d["quality"])
		else: return "-"
	
	get_quality_score = staticmethod(get_quality_score)
	
	def recover_original_raw_data_list(self):
		'''
		Called if the user hits cancel - if they removed some files or added files the changes
		are not saved unless the user hits ok
		'''
		project_db = db_open_dict("bdb:project")
		project_db["global.spr_init_models"] = self.project_files_at_init
	
class InitialModelReportTask(ParticleWorkFlowTask):
	documentation_string = "This form displays the initial models currently associated with the project. You can associate initial models with the project using e2makeinitialmodel or by importing them directly, see the options below."
	warning_string = "\n\n\nNOTE: There are no initial models currently associated with the project."
	def __init__(self):
		ParticleWorkFlowTask.__init__(self)
		self.window_title = "Project Initial Models"
		self.imf = None # will eventually become an E2IntialModelsTool
	
	def get_params(self):
		params = []
		
		self.imt = E2InitialModelsTool()
		p,n = self.imt.get_initial_models_table()
		
#		if n == 0:
#			params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=InitialModelReportTask.documentation_string+InitialModelReportTask.warning_string,choices=None))
#		else:
		params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=InitialModelReportTask.documentation_string,choices=None))
		params.append(p)
		return params

	def on_form_cancel(self):
		self.imt.recover_original_raw_data_list()
		
		self.form.closeEvent(None)
		self.form = None
		self.emit(QtCore.SIGNAL("task_idle"))
		

class E2InitialModel(ParticleWorkFlowTask):
	documentation_string = "Make an initial model with e2initialmodel."
	warning_string = "\n\n\nNOTE: there are no reference free classes in the project. Go back a step and try running e2refine2d" 
	def __init__(self):
		ParticleWorkFlowTask.__init__(self)
		self.window_title = "run e2makeinitialmodel"
		self.form_db_name = "bdb:emform.e2initialmodel"
		
	def get_params(self):
		params = []
		
		self.rfcat = E2RefFreeClassAveTool()
		p,n = self.rfcat.get_reference_free_class_averages_table()

		params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=E2InitialModel.documentation_string,choices=None))
		
		db = db_open_dict(self.form_db_name)
		piter = ParamDef(name="iter",vartype="int",desc_short="Iterations",desc_long="The number of times each 3D is iteratively refined",property=None,defaultunits=db.get("iter",dfl=4),choices=[])
		ptries = ParamDef(name="tries",vartype="int",desc_short="Tries",desc_long="The number of 3D models to generate",property=None,defaultunits=db.get("tries",dfl=10),choices=[])
		syms = ["icos","oct","tet","c","d","h"]
		psym =  ParamDef(name="symname",vartype="string",desc_short="Symmetry",desc_long="Symmetry to be imposed during refinement",property=None,defaultunits=db.get("symname",dfl="c"),choices=syms)
		psymnum = ParamDef(name="symnumber",vartype="string",desc_short="Symmetry number",desc_long="In C,D and H symmetry, this is the symmetry number",property=None,defaultunits=db.get("symnumber",dfl=""),choices=None)
		#db_close_dict(self.form_db_name)
		orientgens = self.get_orientgens_list()
		porientgens =  ParamDef(name="orientgen",vartype="string",desc_short="Orientation generator",desc_long="The method of orientation generation",property=None,defaultunits=db.get("orientgen",dfl="eman"),choices=orientgens)

		p.enable_multiple_selection = False
		params.append(p)
		params.append([piter,ptries,porientgens])
		params.append([psym,psymnum])
	
		return params
	
	def on_form_ok(self,params):
		
		error_message = []
		
		if not params.has_key("filenames"):
			# THERE ARE no classes to choose from and the user has hit ok
			self.emit(QtCore.SIGNAL("task_idle"))
			self.form.closeEvent(None)
			self.form = None
			return
		
		error_message = []
		if len(params["filenames"]) != 1: error_message.append("Please choose a single file to proceed")
		
		if params["iter"] < 0: error_message.append("Please specify an iter value of atleast 0")
		if params["tries"] < 1: error_message.append("Please specify a number of tries that is atleast 1")
		
		
		# copied from e2refine
		
		options = EmptyObject()
		
		error_message.extend(self.check_sym(params,options))
		options.orientgen = params["orientgen"]
		
		if len(error_message) > 0:
			self.show_error_message(error_message)
			return	
		else:
			# obviously if we make it here the parameters are sensible so we can store them (and later use them again for the user's convenience)
			self.write_db_entries(params)
			
			options.input = params["filenames"][0]
			options.iter = params["iter"]
			options.tries = params["tries"]
			options.filenames = []
			#options.sym - taken care of by check_sum
			string_args = ["iter","input","tries","sym","orientgen"]
			bool_args = []
			additional_args = ["--dbls=global.spr_init_models"]
			temp_file_name = "e2initialmodel_stdout.txt"
			self.spawn_single_task("e2initialmodel.py",options,string_args,bool_args,additional_args,temp_file_name)
			self.emit(QtCore.SIGNAL("task_idle"))
			self.form.closeEvent(None)
			self.form = None
	def on_form_cancel(self):
		self.rfcat.recover_original_raw_data_list()
		
		self.form.closeEvent(None)
		self.form = None
		self.emit(QtCore.SIGNAL("task_idle"))
#class ImportInitialModels(ParticleWorkFlowTask):
#	documentation_string = "Import initial models into the EMAN2 database. Browse for the images you wish to import or type them directly into the entry form. If you tick force overwrite initial models in the EMAN2 database with the same name will automatically be over written."
#	
#	def __init__(self):
#		ParticleWorkFlowTask.__init__(self)
#		self.window_title = "Import initial models"
#		self.form_db_name = "bdb:emform.e2initialmodel"
#		
#	def get_params(self):
#		params = []
#		
#		db = db_open_dict(self.form_db_name)
#		params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=ImportInitialModels.documentation_string,choices=None))
#		params.append(ParamDef(name="filenames",vartype="url",desc_short="Import models",desc_long="A list of 3D images that you wish to import into the EMAN2 database scheme.",property=None,defaultunits=[],choices=[]))
#		pfo = ParamDef(name="force",vartype="boolean",desc_short="Force overwrite",desc_long="Whether or not to force overwrite files that already exist",property=None,defaultunits=db.get("force",dfl=False),choices=None)
#		params.append(pfo)
#		
#		#db_close_dict(self.form_db_name)
#		
#		return params
#	
#	def on_form_ok(self,params):
#		error_message = []
#		
#		
#		mesbox = QtGui.QMessageBox()
#		mesbox.setWindowTitle("Almost but not quite")
#		if params.has_key("filenames") and len(params["filenames"])==0:
#			mesbox.setText("Please provide at least one filename to proceed")
#	 		mesbox.exec_()
#	 		return
#	 	
#	 	
#	 	for name in params["filenames"]:
#	 		if not file_exists(name):
#	 			error_message.append("The file "+name+" does not exist")
#	 		else:
#	 			e = EMData()
#	 			e.read_image(name,0,True)
#	 			if e.get_xsize() != e.get_ysize() or e.get_xsize() != e.get_zsize():
#	 				error_message.append("The file "+name+" is not cubic")
#	 				
#	 	if params["force"] == False:	
#		 	for file in params["filenames"]:
#		 		output_name = "bdb:initial_models#"+get_file_tag(file)
#				if file_exists(output_name):
#					error_message.append("An entry exists in the initial_models database with the same name as this file "+file+", please rename your file or choose force over write")
#		 	
#	 			
#	 	if len(error_message) > 0:
#	 		self.show_error_message(error_message)
#	 		return
#	 	
#	 	# if we make it here we're all good, 
#	 	self.write_db_entries(params) # so store the parameters for recollection later
#	 	num_processing_operations = 2 # one read and one write
#	 	progress = EMProgressDialogModule(get_application(),"Importing files into database...", "Abort import", 0, len(params["filenames"])*num_processing_operations,None)
#		progress.qt_widget.show()
#		
#		i = 0
#		for file in params["filenames"]:
#			e = EMData()
#			e.read_image(file,0)
#			i +=1
#			progress.qt_widget.setValue(i)
#			output_name = "bdb:initial_models#"+get_file_tag(file)
#			e.write_image(output_name,0)
#			#db_close_dict(output_name)
#			i +=1
#			progress.qt_widget.setValue(i)
#		
#		progress.qt_widget.close()
#		
#	 	self.emit(QtCore.SIGNAL("task_idle"))
#		self.form.closeEvent(None)
#		self.form = None
#	 			


class RefinementReportTask(ParticleWorkFlowTask):
	documentation_string = "This form displays the models produced at the end of each refinement."
	warning_string = "\n\n\nNOTE: There are no results available."
	def __init__(self):
		ParticleWorkFlowTask.__init__(self)
		self.window_title = "Refinement results"
	
	def get_params(self):
		params = []
		
		p,n = self.get_last_refinement_models_table()
		
		if n == 0:
			params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=RefinementReportTask.documentation_string+RefinementReportTask.warning_string,choices=None))
		else:
			params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=RefinementReportTask.documentation_string,choices=None))
			params.append(p)
		return params
	
	
	def get_last_refinement_models_table(self):
		'''
		Looks for bdb:r2d_??#classes_?? and the bdb:r2d_??#classes_init file, finds the most recent one, then fills in the number of particles in
		in the class average file and also its dimensions.
		'''
		dirs = get_numbered_directories("refine_")
#		dirs, files = get_files_and_directories(e2getcwd())
##		for root, dirs, files in os.walk(os.getcwd()):
##			break
#		
#		dirs.sort()
#		for i in range(len(dirs)-1,-1,-1):
#			if len(dirs[i]) != 9:
#				dirs.pop(i)
#			elif dirs[i][:7] != "refine_":
#				dirs.pop(i)
#			else:
#				try: int(dirs[i][7:])
#				except: dirs.pop(i)
		# allright everything left in dirs is "refine_??" where the ?? is castable to an int, so we should be safe now
		threed_files = []
		threed_dims = []
		threed_mean = []
		threed_sigma = []
		threed_max = []
		threed_min = []
		for dir in dirs:
			threed_db = None
			# check for 00 to 09 but 00 is replaced with "init"
			db_first_part = "bdb:"+dir+"#threed_"
			cont = True
			for i in range(0,10):
				for j in range(0,10):
					db_name = db_first_part+str(i)+str(j)
					if db_check_dict(db_name):
						threed_db = db_name
					else:
						if i != 0 or j != 0:
							cont = False
							break
						#else just check for 01 incase the user has specified the --initial arugment
				if not cont:
					break
				
			if threed_db != None:
				threed_files.append(threed_db)
				th_db = db_open_dict(threed_db,ro=True)
				dims = ""
				mean = ""
				sigma = ""
				max = ""
				min = ""
				try:
					hdr = th_db.get_header(0)
					dims = str(hdr["nx"])+'x'+str(hdr["ny"])+'x'+str(hdr["nz"])
					mean = "%4.3f" %hdr["mean"]
					sigma = "%4.3f" %hdr["sigma"]
					min = "%4.3f" %hdr["minimum"]
					max = "%4.3f" %hdr["maximum"]
				except: pass
				
				
				#db_close_dict(threed_db)
				threed_dims.append(dims)
				threed_mean.append(mean)
				threed_sigma.append(sigma)
				threed_max.append(max)
				threed_min.append(min)
		if len(threed_files) > 0:
			
			p = EMParamTable(name="filenames",desc_short="Most current 3D reconstructions",desc_long="")
			pnames = ParamDef(name="Files names",vartype="intlist",desc_short="3D image file",desc_long="The location of 3D reconstructions",property=None,defaultunits=None,choices=threed_files)
			pmean = ParamDef(name="Mean",vartype="stringlist",desc_short="Mean",desc_long="The mean voxel value",property=None,defaultunits=None,choices=threed_mean)
			psigma = ParamDef(name="Standard deviation",vartype="stringlist",desc_short="Standard deviation",desc_long="The standard deviation of the voxel values",property=None,defaultunits=None,choices=threed_sigma)
			pdims = ParamDef(name="Dimensions",vartype="stringlist",desc_short="Dimensions",desc_long="The dimensions of the 3D images",property=None,defaultunits=None,choices=threed_dims)
			pmax = ParamDef(name="min",vartype="stringlist",desc_short="Minimum",desc_long="The maximum voxel value",property=None,defaultunits=None,choices=threed_max)
			pmin = ParamDef(name="max",vartype="stringlist",desc_short="Maximum",desc_long="The minimum voxel value",property=None,defaultunits=None,choices=threed_min)
			
			p.append(pnames)
			p.append(pdims)
			p.append(pmean)
			p.append(psigma)
			p.append(pmax)
			p.append(pmin)
			
			
			setattr(p,"convert_text", ptable_convert_2)
			context_menu_dict = {"Save as":image_db_save_as}
			#context_menu_dict["Delete"] = image_db_delete
			setattr(p,"context_menu", context_menu_dict)
			setattr(p,"icon_type","3d_image")
			
			return p,len(threed_files)
		else:
			return None,0
			
class E2Make3DTools:
	'''
	e2eotest and e2refine tasks both need the functionality embodied here
	'''
	def __init__(self):pass
	
	def add_make3d_args(self,options,string_args,bool_args,additional_args):
		
		string_args.extend(["m3diter","m3dkeep","recon"])
		bool_args.append("m3dkeepsig")
		if hasattr(options,"m3dpreprocess"): string_args.append("m3dpreprocess")
		if hasattr(options,"pad"): string_args.append("pad")

	def check_make3d_page(self,params,options):
		error_message = []
		
		if params["m3diter"] < 0:
			error_message.append("The number of make3d iterations must be atleast 0")
		
		if params["m3dkeepsig"] == False:
			if params["m3dkeep"] < 0 or params["m3dkeep"] > 1:
				error_message.append("The keep parameter in the Make3D page must be between 0 and 1. This does not hold if the \'Sigma based\' option is selected.")
		
		if len(error_message) > 0 : return error_message # calling program should discontinue
		
		
		
		if len(params["pad"]) > 0:
			try: int(params["pad"])
			except: error_message.append("The value you entered for padding is nonsensical")
			pad = int(params["pad"])
			if params["filenames"] > 0:
#				try:
					if self.end_tag != "generic":
						nx,ny = gimme_image_dimensions2D("bdb:particles#"+params["filenames"][0])
					else:
						nx,ny = gimme_image_dimensions2D(params["filenames"][0])
					if nx >= pad or ny >= pad:
						error_message.append("You must specify a value for padding that is larger than the image dimensions - the image dimensions are %i x %i and your pad value is %i" %(nx,ny,pad))				
					else:
						options.pad = int(params["pad"])
#				except:
#					error_message.append("Can't get the dimensions of the first image???")
			else:
				pass # the user not entering filenames is an error, so after they've correct that we'll with the issues here
		
		options.m3diter = params["m3diter"]
		options.m3dkeep = params["m3dkeep"]
		options.m3dkeepsig = params["m3dkeepsig"]
		
		options.recon = params["recon"]
		
		if params["m3dpreprocess"] != "None":
			options.m3dpreprocess = params["m3dpreprocess"]

			
		return error_message

	def get_make3d_page(self):
		
		db = db_open_dict(self.form_db_name)
		pkeep = ParamDef(name="m3dkeep",vartype="float",desc_short="keep",desc_long="The fraction of particles to keep in each class average. If sigma based is checked this value is interpreted in standard deviations from the mean instead",property=None,defaultunits=db.get("m3dkeep",dfl=0.8),choices=[])
		pkeepsig = ParamDef(name="m3dkeepsig",vartype="boolean",desc_short="Sigma based",desc_long="If checked the keep value is interpreted in standard deviations from the mean instead of basic ratio",property=None,defaultunits=db.get("m3dkeepsig",dfl=True),choices=[])
		
		piter = ParamDef(name="m3diter",vartype="int",desc_short="Reconstruction iterations",desc_long="The number of times the reconstruction algorithm is iterated",property=None,defaultunits=db.get("m3diter",dfl=3),choices=[])
	
		pnormproc =  ParamDef("m3dpreprocess",vartype="string",desc_short="Normalization processor",desc_long="The normalization method applied to the class averages",property=None,defaultunits=db.get("m3dpreprocess",dfl="normalize.edgemean"),choices=["normalize","normalize.edgemean","None"])
		
		precon = ParamDef("recon",vartype="string",desc_short="Reconstruction technique",desc_long="The method used to perform 3D reconstruction",property=None,defaultunits=db.get("recon",dfl="fourier"),choices=["fourier","back_projection"])
		ppad = ParamDef("pad",vartype="string",desc_short="Pad to",desc_long="The amount to which you want to pad the 3D volume when Fourier inversion is being used. At least 25% is recommended", defaultunits=db.get("pad",dfl=""),choices=[])
		params = []
		
		#db_close_dict(self.form_db_name)
		
		params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=E2RefineParticlesTask.make3d_documentation,choices=None))

		
		params.append([precon,piter])
		params.append([pnormproc,ppad])
		params.append([pkeep,pkeepsig])
		
		return ["Make3d", params]
		
		
	
class E2RefineParticlesTask(EMClassificationTools, E2Make3DTools):
	'''
	This task will harness the parameters for, and launch, e2refine.py
	'''
	 
	general_documentation = "These are the general parameters for 3D refinement in EMAN2. Please select which particles you wish to use as part of this process, specify your starting model, and fill in other parameters such as symmetry and whether or not the usefilt option should be used."
	project3d_documentation = "These  parameters are used by e2project3d. Several orientation generation techniques provide alternative methods for distributing orientations in the asymmetric unit. Orientations can be generated based on your desired angular spacing, or alternatively on the desired total number of projections. In the latter case EMAN2 will generate a number as close as possible to the specified number, but note that there is no guarantee of a perfect match. You can also vary the method by which projections are generated. If you check the \'include mirror\' option you should be sure to use aligners to that do not perform mirror alignment."
	simmx_documentation = "These  parameters are used by e2simmx, a program that compares each particle to each projection and records quality scores. To do this the particles must first be aligned to the projections using the aligners you specify. Once aligned the \'Main comparator\' is used to record the quality score. These quality values are recorded to an image matrix on handed on to the next stage in the refinement process.\n\nThe shrink parameter causes all projections and particles to be shrunken by the given amount prior to comparison. This can provide a significant time boost, though at the expense of resolution. Note however that the class averaging stage, which  can involve iterative alignment, does not use shrunken data."
	class_documentation = "Most of these parameters are for e2classaverage with the exception of the \"Class separation\" parameter which is the solely used by e2classify. Classification is first performed using this latter program and the output from e2simmx. This is followed by the class averaging stage. The critical argument for the class averaging procedure is the number of iterations. In early stages of refinement this should be relatively large and it should gradually be reduced as your model converges to the answer."
	make3d_documentation = "Iterative Fourier inversion is the preferred method of 3D reconstruction in EMAN2."

	def __init__(self,ptcls_list,usefilt_ptcls_list):
		'''
		@param ptcls_list the list of particle files that will form the primary input to e2refine
		@param usefilt_ptcls_list the list of usefilt particles corresponding in length to the ptcls_list, or None
		'''
		self.ptcls = ptcls_list
		self.usefilt_ptcls = usefilt_ptcls_list
		self.imf = None # will eventually become an E2IntialModelsTool
	 	EMClassificationTools.__init__(self)
	 	E2Make3DTools.__init__(self)
	 	
	 	self.window_title = "e2refine parameters"
	 	self.form_db_name = "bdb:emform.e2refine"
		 	
	class UsefiltColumn:
		def __init__(self,ptcls,usefilt_ptcls):
			if len(ptcls) != len(usefilt_ptcls):
				raise RuntimeError("The usefilt and raw particle lists must be the same length")
			
			self.filt_map = {}
			for i in xrange(0,len(ptcls)):
				self.filt_map[ptcls[i]] = usefilt_ptcls[i]
				
		def get_usefilt_name(self,name):
			return self.filt_map[name]
		
	def run_form(self):
		self.form = EMTableFormModule(self.get_params(),get_application())
		self.form.qt_widget.resize(*self.preferred_size)
		self.form.setWindowTitle(self.window_title)
		get_application().show_specific(self.form)
		QtCore.QObject.connect(self.form,QtCore.SIGNAL("emform_ok"),self.on_form_ok)
		QtCore.QObject.connect(self.form,QtCore.SIGNAL("emform_cancel"),self.on_form_cancel)
		QtCore.QObject.connect(self.form,QtCore.SIGNAL("emform_close"),self.on_form_close)
		QtCore.QObject.connect(self.form,QtCore.SIGNAL("display_file"),self.on_display_file)
		
	def get_params(self):
	 	params = []
		
	#	params.append(self.get_intro_params())
		params.append(self.get_main_params())
		params.append(self.get_main_params_2())
		params.append(self.get_project3d_page())
		params.append(self.get_simmx_page())
		params.append(self.get_classaverage_page())
		params.append(self.get_make3d_page())
		
		return params
	
	def on_form_cancel(self):
		if self.imt != None: self.imt.recover_original_raw_data_list()
		
		self.form.closeEvent(None)
		self.form = None
		self.emit(QtCore.SIGNAL("task_idle"))
	
	def on_form_ok(self,params):
		
		options = EmptyObject()
#		error_message = self.check_main_page(params,options)
		
		for checker in [self.check_main_page,self.check_project3d_page,self.check_simmx_page,self.check_classaverage_page,self.check_make3d_page]:
			error_message = checker(params,options)
			if len(error_message) > 0 :
				self.display_errors(error_message)
				return
			
		self.write_db_entries(params)
		# w'oh if we make it here a lot of checking has occured. Now get the args in order to spawn_single_task
		string_args = []
		bool_args = []
		
		additional_args = []
		
		for get_args in [self.add_general_args,self.add_project3d_args,self.add_simmx_args,self.add_classaverage_args,self.add_make3d_args]:
		  	error = get_args(options,string_args,bool_args,additional_args)
		
			if error != None: # not too fast, something still could have gone wrong
				self.display_errors([error])
				return
		
		temp_file_name = "e2refine_stdout.txt"
		
		# Steve is rethinking how we remember programs arguments
		#self.write_db_parms(options,string_args,bool_args)
		
		print "spawning"
		self.spawn_single_task("e2refine.py",options,string_args,bool_args,additional_args,temp_file_name)
		self.emit(QtCore.SIGNAL("task_idle"))
		self.form.closeEvent(None)
		self.form = None

# This functionality is being redesigned and pends a discussion with Steve ludtke with respect to the history mechanism
#	def write_db_parms(self,options,string_args,bool_args):
#		db = db_open_dict("bdb:e2refine.args")
#		
#		for string in string_args:
#			db[string] = getattr(options,string)
#			
#		for string in bool_args:
#			db[string] = getattr(options,string)
#			
#		db_close_dict("bdb:e2refine.args")
#		
	
	def display_errors(self,error_message):
		'''
		error_message is a list of strings
		'''
		
		if len(error_message) > 0:
			self.show_error_message(error_message)
	 		
	
	def get_main_params(self):
		'''
		General/broad refine params
		'''
		params = []
#		params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits="Choose the particles you wish to refine",choices=None))

		
		if self.ptcls == None:
			p,n = self.get_particle_selection_table([])
		else:
			p,n = self.get_particle_selection_table(self.ptcls)
			if self.usefilt_ptcls != None and len(self.usefilt_ptcls) > 0:
				from emform import EMFileTable
				self.column_data = E2RefineParticlesTask.UsefiltColumn(self.ptcls,self.usefilt_ptcls)
				p.add_column_data(EMFileTable.EMColumnData("Usefilt data",self.column_data.get_usefilt_name,"The usefilt data"))
				
#			p = ParamDef(name="filenames",vartype="url",desc_short="Input file name(s)",desc_long="The names of the particle files you want to use as in the input data for e2refine2d.py",property=None,defaultunits=[],choices=[])
#			n = 1
		
		# I could check to see if the database exists but it seems unnecessary
		# In the event that the database doesn't exist it is created and 
		# a new entry is created on disk. The only inconvenient aspect of this comes
		# if the user hits cancel - then there is a file on disk even though
		# the user never agreed to anything
		db = db_open_dict(self.form_db_name) # see eman wiki for a list of what args are kept in this db
		project_db = db_open_dict("bdb:project")
		
		params.append(p)
		
	   	pmass = ParamDef(name="global.particle_mass",vartype="float",desc_short="Particle mass (kda)",desc_long="The mass of the particle in kilodaltons. Leave blank if unknown",property=None,defaultunits=project_db.get("global.particle_mass",dfl=800),choices=None)
		papix = ParamDef(name="global.apix",vartype="float",desc_short="Angtsrom per pixel",desc_long="The physical distance represented by the pixel spacing",property=None,defaultunits=project_db.get("global.apix",dfl=1.1),choices=None)
		
		params.append([papix,pmass])
		
		piter = ParamDef(name="iter",vartype="int",desc_short="Refinement iterations",desc_long="The number of times 3D refinement should be iterated",property=None,defaultunits=db.get("iter",dfl=3),choices=[])
		plowmem = ParamDef(name="lowmem",vartype="boolean",desc_short="Low mem",desc_long="Causes various programs to restrict memory usage but results in increased CPU time.",property=None,defaultunits=db.get("lowmem",dfl=False),choices=None)

	   	params.append([piter,plowmem])
	
		return ["Particles",params]
		 
	
	def get_main_params_2(self):
		
		params = []
#		params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits="",choices=None))

		# I could check to see if the database exists but it seems unnecessary
		# In the event that the database doesn't exist it is created and 
		# a new entry is created on disk. The only inconvenient aspect of this comes
		# if the user hits cancel - then there is a file on disk even though
		# the user never agreed to anything
		db = db_open_dict(self.form_db_name) # see eman wiki for a list of what args are kept in this db
		project_db = db_open_dict("bdb:project")
		
		self.imt = E2InitialModelsTool()
		p1,n1 = self.imt.get_initial_models_table()
		p1.enable_multiple_selection = False
		params.append(p1)
		
			
		syms = ["icos","oct","tet","d","c","h"]
		
		psym =  ParamDef(name="symname",vartype="string",desc_short="Symmetry",desc_long="Symmetry to be imposed during refinement",property=None,defaultunits=db.get("symname",dfl="c"),choices=syms)
		psymnum = ParamDef(name="symnumber",vartype="string",desc_short="Symmetry number",desc_long="In C,D and H symmetry, this is the symmetry number",property=None,defaultunits=db.get("symnumber",dfl="1"),choices=None)

		params.append([psym,psymnum])
		
		pautomask = ParamDef(name="automask3d",vartype="boolean",desc_short="Auto mask 3D",desc_long="Causes automasking of the 3D volume to occur at the end of each iteration",property=None,defaultunits=db.get("automask3d",dfl=False),choices=None)
		
		params.append(pautomask)
		
		pamthreshold =  ParamDef(name="amthreshold",vartype="float",desc_short="Threshold",desc_long="An isosurface threshold that well defines your structure.",property=None,defaultunits=db.get("amthreshold",dfl=1.1),choices=None)
		pamradius =  ParamDef(name="amradius",vartype="int",desc_short="Radius",desc_long="The radius of a sphere at the the origin which contains seeding points for the flood file operation using the given threshold",property=None,defaultunits=db.get("amradius",dfl=30),choices=None)
		pamnshells =  ParamDef(name="amnshells",vartype="int",desc_short="Mask dilations",desc_long="The number of dilations to apply to the mask after the flood fill operation has finished. Suggest 5% of the boxsize",property=None,defaultunits=db.get("amnshells",dfl=5),choices=None)
		pamngaussshells =  ParamDef(name="amnshellsgauss",vartype="int",desc_short="Post Gaussian dilations",desc_long="The number of dilations to apply to the dilated mask, using a gaussian fall off. Suggest 5% of the boxsize",property=None,defaultunits=db.get("amnshellsgauss",dfl=5),choices=None)
		
		pautomask.dependents = ["amthreshold","amradius","amnshells","amnshellsgauss"] # these are things that become disabled when the pautomask checkbox is checked etc
		
		params.append([pamthreshold,pamradius])
		params.append([pamnshells,pamngaussshells])

		#db_close_dict(self.form_db_name)
		#db_close_dict("bdb:project")
		
		return ["Model",params]

	def add_general_args(self,options,string_args,bool_args,additional_args):
		
		options.path = numbered_path("refine",True)
		
		if options.filenames[0][:4] == "bdb:":
			success,cmd = self.make_v_stack(options.filenames,"all",options,"input")
			if not success:
				return cmd + " failed"
		else:
			success, cmd = self.make_stack(options.filenames, "all",options,"input")
			if not success:
				return cmd + " failed"
			
		string_args.append("input")
		
		if hasattr(options,"usefilt_names"):
			if options.usefilt_names[0][:4] == "bdb:":
				success,cmd = self.make_v_stack(options.usefilt_names,"usefilt",options,"usefilt")# sets the attribute for us
				if not success:
					return cmd + " failed"
			else:
				success, cmd = self.make_stack(options.usefilt_names,"usefilt",options,"usefilt")
				if not success:
					return cmd + " failed"
				
			
		
		error = self.check_model(options)
		
		if error != None:
			return error
		
		opt_attr = ["mass","apix","automask3d"] # these does not necessarily have to be specified
		for attr in opt_attr:
			if hasattr(options,attr): string_args.append(attr) 
		
		options.filenames = [] # important for this to happen so the argument doesn't have all the filenames as args
		string_args.extend(["iter","sym","model","path"])
		bool_args.append("lowmem")
		
		return None # returning None is good
	
	def check_model(self,options):
		
		model = options.model[0] # options.model is a list
		if not file_exists(model): # why did I do this? Oh well doesn't hurt # Retrospective note - it was useful as I did Steve's second round of alterations
			return "the initial model %s does not exist" %model
		
		nx,ny = gimme_image_dimensions2D(options.input)
		if nx != ny:
			return "input images aren't square"
		
		
		x,y,z = gimme_image_dimensions3D(model)
		
		
		if x != y or z != y:
			return "initial model isn't square"
		
		if nx != x:
			scale = float(nx)/x
			new_model = "bdb:"+options.path + "#initial_model"
			
			image = EMData()
			image.read_image(model,0)
			start = (x-nx)/2
			if scale > 1:
				image.clip_inplace(Region(start,start,start,nx,nx,nx))
				t = Transform()
				t.set_scale(scale)
				image.transform(t)	
			else:
				t = Transform()
				t.set_scale(scale)
				image.transform(t)
				image.clip_inplace(Region(start,start,start,nx,nx,nx))
				
			image.write_image(new_model,0) # db got opened here

		 	options.model = new_model
		 	db_close_dict(new_model) # force synchronization so e2refine.py will definetely run -
		else:
			options.model = model # all good
			
		return None
		
		
	def make_stack(self,filenames,out_name,options,attr):
		'''
		This one's a bit more specialized to handle flat files and avoid massive copying
		'''
		if len(filenames) == 1:
			setattr(options,attr,filenames[0])
			return True,""
		else:
			fail = False
			# check if they're all bdb files, in which case we can make a v stack
			for name in filenames:
				if name[0:4] != "bdb:":
					fail = True
					break
				
			if fail: # we can't make a vstack
				# potentially lots of e2proc2d
				progress = QtGui.QProgressDialog("Importing files into database...", "Abort import", 0, len(filenames),None)
				progress.show()
	
		  	   	i = 0
		  	   	setattr(options,attr, "bdb:"+options.path+"#"+out_name)
				for i,name in enumerate(filenames):
					cmd = "e2proc2d.py"
		 			cmd += " "+name
		 			cmd += " "+getattr(options,attr)
		 			success = (os.system(cmd) in (0,12))
		 			if not success:
		 				progress.close()
		 				return False,cmd
		 			else:
		 				progress.setValue(i+1)
		 				get_application().processEvents()
				
				progress.close()
				
				return True,cmd
			else:
				return self.make_input_v_stack(filenames,out_names,options,attr)

	
	def make_v_stack(self,filenames,out_name,options,attr):
	 	
	 	cmd = "e2bdb.py"
	 	for name in filenames:
	 		cmd += " "+name
	 	
	 	cmd += " --makevstack=bdb:"+options.path+"#"+out_name
	 	
	 	print "executing cmd", cmd
	 	
	 	get_application().setOverrideCursor(Qt.BusyCursor)
	 	success = os.system(cmd)
	 	success = (success in (0,11,12))
	 	get_application().setOverrideCursor(Qt.ArrowCursor)
	 	
	 	setattr(options,attr,"bdb:"+options.path+"#"+out_name) # Note important 
	 	
	 	return success,cmd
	 
	
	def check_main_page(self,params,options):
		'''
		Called internally to check that the user has entered correct parameters in the main page
		returns a potentially empty list of error messages, if it is empty it means there are no errors
		Also sets argument attributes of the options object, killing two birds with one stone
		'''
		error_message = []
		#filenames
		if len(params["filenames"]) == 0:
			error_message.append("Please choose files to form the input data set.")
			
		if len(params["model"]) == 0:
			error_message.append("Please choose a starting model.")
			
		options.filenames = params["filenames"]
			#print options.filenames
		#usefilt
		
		if self.usefilt_ptcls != None and len(self.usefilt_ptcls) > 0:
			usefilt_names = [self.column_data.get_usefilt_name(name) for name in params["filenames"]]
			options.usefilt_names = usefilt_names

		
		if params.has_key("global.particle_mass"): 
			if params["global.particle_mass"] <= 0:
				error_message.append("The particle mass must be greater than 0")
			else:
				options.mass = params["global.particle_mass"]
			
		if params.has_key("global.apix"):
			if params["global.apix"] <= 0:
				error_message.append("The angstrom per pixel must be greater than  0")
			else:
				options.apix = params["global.apix"]
				
		if params["automask3d"]:
			# the user wants to do automasking
			names = ["amthreshold","amradius","amnshells","amnshellsgauss"]
			arg = ""
			for i,name in enumerate(names):
				if not params.has_key(name):
					error_message.append("Missing automask parameter %s" %name[2:])
					continue
				elif i == 1:
					if params[name] <=0:
						error_message.append("The automask radius parameter must be greater than 0")
						continue
				elif i in [2,3]:
					if params[name] < 0:
						error_message.append("The automask dilation parameters must be atleast 0")
						continue
				# if we make it here than no error conditions were encountered, so we're safe to just append the argument
				if i != 0:
					arg +=","
				arg+= str(params[name])
		
			options.automask3d=arg
				
		#symmetry
		error_message.extend(self.check_sym(params,options))
		
		# iterations
		if params["iter"] < 1:
			error_message.append("The number of refinement iterations must be atleast 1.")
		else:
			options.iter = params["iter"]
			
		options.lowmem = params["lowmem"]
		options.model = params["model"] # can't get this one wrong
		
		return error_message
	
	def get_usefilt_options(self):
		if self.end_tag != "generic":
			
			n = self.get_total_particles(self.end_tag)
			
			available_filt_files = []
			number = []
			for i,tag in enumerate(self.usefilt_tags):
				if tag != self.end_tag:
					n_ = self.get_total_particles(tag=tag)
					if n_ > 0 and n_ == n:
						available_filt_files.append(self.usefilt_display_names[i])
					
			return available_filt_files
		else:
			return []
		
	def add_project3d_args(self,options,string_args,bool_args,additional_args):
		
		string_args.extend(["orientgen","projector"])
		# sym is already taken care of in the main args
		return None # no error to report
	def get_project3d_page(self):
		params = []
		
		params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=E2RefineParticlesTask.project3d_documentation,choices=None))

		db = db_open_dict(self.form_db_name)
		
		projectors = self.get_projectors_list()
		orientgens = self.get_orientgens_list()
			
		pprojector =  ParamDef(name="projector",vartype="string",desc_short="Projector",desc_long="The method used to generate projections",property=None,defaultunits=db.get("projector",dfl="standard"),choices=projectors)
		
		porientgens =  ParamDef(name="orientgen",vartype="string",desc_short="Orientation generator",desc_long="The method of orientation generation",property=None,defaultunits=db.get("orientgen",dfl="eman"),choices=orientgens)
		
		pmirror = ParamDef(name="incmirror",vartype="boolean",desc_short="Include mirror",desc_long="Include the mirror portion of the asymmetric uni",property=None,defaultunits=db.get("incmirror",False),choices=[])
		
		
		orient_options = ["angle based", "number based"]
		porientoptions = ParamDef(name="orientopt",vartype="choice",desc_short="Method of generating orientation distribution",desc_long="Choose whether you want the orientations generating based on an angle or based on a total number of orientations desired",property=None,defaultunits=db.get("orientopt",dfl=orient_options[0]),choices=orient_options)
		porientoptionsentry  =  ParamDef(name="orientopt_entry",vartype="float",desc_short="value",desc_long="Specify the value corresponding to your choice",property=None,defaultunits=db.get("orientopt_entry",dfl=5),choices=[])
		
		params.append([pprojector,porientgens])
		params.append([porientoptions,porientoptionsentry])
		params.append(pmirror)
		
		#db_close_dict(self.form_db_name)
		
		return ["Project 3D",params]
	
	def check_project3d_page(self,params,options):
		
		error_message = []
		if params["orientopt_entry"] < 0:
			error_message.append("Please enter a positive non zero value for the angle/number of projections in the Project3D settings")
		
		if params["orientgen"] == "rand" and params["orientopt"] == "angle based":
			error_message.append("The random orientation generator doesn't work with the \'angle based\' argument, please choose \'number based\' instead") 
		
		if int(params["orientopt_entry"]) !=  params["orientopt_entry"] and  params["orientopt"] == "number based":
			error_message.append("In project3d - for the number based orientation method the number must be an integer")
		
		options.orientgen = params["orientgen"]
		if params["orientopt"] == "angle based":
			options.orientgen += ":delta="
		else:
			options.orientgen += ":n="
		
		options.orientgen += str(params["orientopt_entry"])	
		
		if params["incmirror"]:
			options.orientgen += ":inc_mirror=1"
		else:
			options.orientgen += ":inc_mirror=0"
			
		
		options.projector = params["projector"]
		
		return error_message
	
class E2RefineChooseDataTask(ParticleWorkFlowTask):
	documentation_string = "This form is for choosing e2refine input and usefilt data. After you hit ok a second form will appear asking for more parameters." 
	def __init__(self):
		ParticleWorkFlowTask.__init__(self)
		self.window_title = "e2refine- getting starting"
		self.preferred_size = (480,300)
		self.form_db_name = "bdb:emform.e2refine"
		
	def get_params(self):
		ptcl_opts = EMParticleOptions()
		self.particles_map, self.particles_name_map,choices = ptcl_opts.get_particle_options()
		choices.append("Specify")
		
		db = db_open_dict(self.form_db_name)
		ppart = ParamDef(name="ptcl_choice",vartype="choice",desc_long="Choose the particle data set you wish to use to generate a starting data for e2refine",desc_short="Particle data",property=None,defaultunits=db.get("ptcl_choice",dfl=""),choices=choices)
		import copy
		usefilt_choices = copy.deepcopy(choices)
		usefilt_choices.append("None")
		usefilt_choices.remove("Specify")
		pusefilt = ParamDef(name="usefilt_ptcl_choice",vartype="choice",desc_long="Choose the particle data set you wish to use to generate a starting data for e2refine",desc_short="Usefilt data",property=None,defaultunits=db.get("usefilt_ptcl_choice",dfl="None"),choices=usefilt_choices)
		params = []		
		params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=E2RefineChooseDataTask.documentation_string,choices=None))
		params.append(ppart)
		params.append(pusefilt)
		return params
	
	def on_form_ok(self,params):
		self.write_db_entries(params)
		if not params.has_key("ptcl_choice"):
			self.form.closeEvent(None)
			self.form = None
			self.emit(QtCore.SIGNAL("task_idle"))
			return
			
		choice = params["ptcl_choice"]
		usefilt_choice = params["usefilt_ptcl_choice"]
		
		if choice == usefilt_choice:
			EMErrorMessageDisplay.run(["The Particle data and usefilt data must be different.\nIf you don't want to include usefilt data choose None"])
			return
		
		if choice == "Specify" or usefilt_choice =="Specify":
			EMErrorMessageDisplay.run(["Specify not currently supported"])
			return
#			if usefilt not in ["Specify","None"]:
#				EMErrorMessageDisplay.run("Usefilt data must be Specify or None")
#				return
#			else:
#				if usefilt == "Specify":
#					EMErrorMessageDisplay.run("Usefilt data must be Specify or None")
#					return
#					self.emit(QtCore.SIGNAL("replace_task"),E2Refine2DWithGenericTask(),"e2refine2d arguments")
#				else:
		else:
			if self.particles_name_map[choice] == "Particles":
				# this is the easiest case
				ptcls = self.particles_map["Particles"]
				if usefilt_choice == "Specify":
					# this will function as a developer warning
					EMErrorMessageDisplay.run(["Specify not currently supported"])
					return
				elif usefilt_choice != "None":
					filt_name = self.particles_name_map[usefilt_choice]
					usefilt_ptcls = self.particles_map[filt_name]
					db = db_open_dict("bdb:project")
					if not db.has_key("global.spr_filt_ptcls_map"): raise NotImplementedException("Something is wrong, the global.spr_filt_ptcls_map is supposed to exist")
					db_map = db["global.spr_filt_ptcls_map"]
					
					intersection_ptcls = []
					intersection_usefilt_ptcls = []
					for name,filt_map in db_map.items():
						if name in ptcls and filt_map.has_key(filt_name): # this is the correct test
							usefilt_name = filt_map[filt_name]
							if EMUtil.get_image_count(name) != EMUtil.get_image_count(usefilt_name):
								raise RuntimeError("The number of images in the usefilt file %s is not consistent with the particles file %s" %(usefilt_name,name))
							intersection_ptcls.append(name)
							intersection_usefilt_ptcls.append(usefilt_name)
				else:
					intersection_ptcls = ptcls
					intersection_usefilt_ptcls = None
				
				
			else:
				# then it's a filtered type, such as phase flipped
				filt_name = self.particles_name_map[choice]
				ptcls = self.particles_map[filt_name]
				
				
				db = db_open_dict("bdb:project")
				if not db.has_key("global.spr_filt_ptcls_map"): raise NotImplementedException("Something is wrong, the global.spr_filt_ptcls_map is supposed to exist")
				if usefilt_choice != "None":
					usefilt_name = self.particles_name_map[usefilt_choice]
					db = db_open_dict("bdb:project")
					db_map = db["global.spr_filt_ptcls_map"]
					if usefilt_name == "Particles":
						prj_ptcls = db["global.spr_ptcls"]
						intersection_ptcls = []
						intersection_usefilt_ptcls = []
						for name,filt_map in db_map.items():
							if filt_map.has_key(filt_name) and name in prj_ptcls: # this is the correct test
								name1 = filt_map[filt_name]
								if EMUtil.get_image_count(name) != EMUtil.get_image_count(name1):
									raise RuntimeError("The number of images in the usefilt file %s is not consistent with the particles file %s" %(usefilt_name,name))
								intersection_ptcls.append(name1)
								intersection_usefilt_ptcls.append(name)
						
					else:
						intersection_ptcls = []
						intersection_usefilt_ptcls = []
						
						for filt_map in db_map.values():
							if filt_map.has_key(filt_name) and filt_map.has_key(usefilt_name):
								name1 = filt_map[filt_name]
								name2 = filt_map[usefilt_name]
								if EMUtil.get_image_count(name1) != EMUtil.get_image_count(name2):
									raise RuntimeError("The number of images in the usefilt file %s is not consistent with the particles file %s" %(usefilt_name,name))
							
								intersection_ptcls.append(name1)
								intersection_usefilt_ptcls.append(name2)
				else:
					intersection_ptcls = ptcls
					intersection_usefilt_ptcls = None
				
				
			self.emit(QtCore.SIGNAL("replace_task"),E2RefineParticlesTask(intersection_ptcls,intersection_usefilt_ptcls),"e2refine2d arguments")
			self.form.closeEvent(None)
			self.form = None
		
		self.write_db_entries(params)

	def write_db_entry(self,key,value):
		pass


class ResolutionReportTask(ParticleWorkFlowTask):
	documentation_string = "This form displays information related to the estimated resolution of refinement results.\nIf you double click on any of the entries in the table you will see the convergence plot and any associated resolution curves."
	warning_string = "\n\n\nNOTE: There are no results available."
	def __init__(self):
		ParticleWorkFlowTask.__init__(self)
		self.window_title = "Resolution estimation"
	
	def get_params(self):
		params = []
		
		p,n = self.get_resolution_table()
		
		if n == 0:
			params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=ResolutionReportTask.documentation_string+ResolutionReportTask.warning_string,choices=None))
		else:
			params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=ResolutionReportTask.documentation_string,choices=None))
			params.append(p)
		return params
	
	def find_first_point_5_crossing(self,xaxis,yaxis):
		'''
		Find the first 0.5 crossing in the FSC - interpolate and try to return an accurate estimate
		Disregards the first five entries
		Assumes the Nyquist frequency is correct
		'''
		idx = 0
		if len(yaxis) > 5:
			idx = 6
		
		soln = -1
		while (idx < len(yaxis)-1 ):
			if yaxis[idx] >= 0.5 and yaxis[idx+1] <= 0.5:
				v1 = yaxis[idx]
				v2 = yaxis[idx+1]
				if v1 != v2:
					d = v1-v2
					offset = v1-0.5
					interp = offset/d
					soln = idx+interp
				else: soln = idx
				break
			else:
				idx += 1
		
		if soln == -1:
			return "invalid"
		elif int(soln) == soln:
			return "%.1f" %(1.0/xaxis(soln))
		else:
			# interpolated frequency
			return "%.1f" %(1.0/(soln/len(yaxis)*xaxis[-1]))
				
		
				
	def get_resolution_table(self):
		'''
		Looks for bdb:r2d_??#classes_?? and the bdb:r2d_??#classes_init file, finds the most recent one, then fills in the number of particles in
		in the class average file and also its dimensions.
		'''
		dirs = get_numbered_directories("refine_")
		
		available_dirs = []
		total_iterations = []
		eotest_res = []
		e2resolution_res = []
		for dir in dirs:
			db_name = "bdb:"+dir+"#convergence.results"
			if db_check_dict(db_name):
				db = db_open_dict(db_name,ro=True)
				keys = db.keys()
				if len(keys) > 0:
					available_dirs.append(dir)
					
					res = get_e2resolution_results_list(keys)
					eo = get_e2eotest_results_list(keys)
					conv = get_convergence_results_list(keys)
					total_iterations.append(len(conv))
					
					if len(res) > 0:
						# get the latest one, this will be the last as guaranteed by sorted results
						last_res = res[-1]
						[xaxis,yaxis] = db[last_res]
						resolution = self.find_first_point_5_crossing(xaxis,yaxis)
						e2resolution_res.append(resolution)
					else:
						e2resolution_res.append("")
						
					if len(eo) > 0:
						last_res = eo[-1]
						[xaxis,yaxis] = db[last_res]
						resolution = self.find_first_point_5_crossing(xaxis,yaxis)
						eotest_res.append(resolution)
					else:
						eotest_res.append("")
				
				#db_close_dict(db_name)

		if len(available_dirs) > 0:
			p = EMParamTable(name="filenames",desc_short="Resolution evaluation",desc_long="")
			pnames = ParamDef(name="Dirs",vartype="stringlist",desc_short="Refinement directory", desc_long="EMAN2 refinement directory", property=None,defaultunits=None,choices=available_dirs)
			piter = ParamDef(name="Iterations",vartype="intlist",desc_short="Total iterations",desc_long="The number of 3D refinement iterations that have occured in this directory",property=None,defaultunits=None,choices=total_iterations)
			peo = ParamDef(name="eo",vartype="stringlist",desc_short="e2eotest",desc_long="0.5 e2eotest resolution estimate",property=None,defaultunits=None,choices=eotest_res)
			pres = ParamDef(name="res",vartype="stringlist",desc_short="e2resolution",desc_long="0.5 e2resolution resolution estimate",property=None,defaultunits=None,choices=e2resolution_res)
			
			p.append(pnames)
			p.append(piter)
			p.append(peo)
			p.append(pres)
			
			setattr(p,"convert_text", resolution_display_convert)
			setattr(p,"icon_type","2d_plot")
			
			return p,len(available_dirs)
		else:
			return None,0
		
def resolution_display_convert(dir):
	'''
	This "display_convert" function breaks the mold a little in that it returns the name of a database that has plots in it. It's handled in e2workflow.py
	'''
	return "bdb:"+dir+"#convergence.results"


def get_e2resolution_results_list(keys):
		'''
		Extract the names from the keys that match the e2resolution.py output naming convention
		(keys is a list of keys in the convergence.results dictionary, in a refinement directory)
		'''
		solns = []
		for k in keys:
			if len(k) > 6 and k[-7:] == "res_fsc":
				solns.append(k)
		solns.sort()
		return solns
	
def get_e2eotest_results_list(keys):
	'''
	Extract the names from the keys that match the e2eotest.py output naming convention
	(keys is a list of keys in the convergence.results dictionary, in a refinement directory)
	'''
	solns = []
	for k in keys:
		if len(k) > 7 and k[0:8] == "even_odd":
			solns.append(k)
	solns.sort()
	return solns

def get_convergence_results_list(keys):
	'''
	Extract the names from the keys that match the e2refine.py convergence plot output naming convention
	(keys is a list of keys in the convergence.results dictionary, in a refinement directory)
	'''
	solns = []
	if "init_00_fsc" in keys:
		solns.append("init_00_fsc")
		
	i = 0
	while True:
		s1 = str(i)
		s2 = str(i+1)
		if len(s1) == 1: s1 = "0"+s1
		if len(s2) == 1: s2 = "0"+s2
		k = s1+"_"+s2+"_fsc"
		if k in keys:
			solns.append(k)
		else:
			break

		i += 1
	
	return solns

class E2EotestTask(EMClassificationTools,E2Make3DTools):
	'''
	Run e2eotest from the workflow setting
	Inherits from E2RefineParticlesTask because it uses some forms that are/almost identical
	'''
	 
	general_documentation = "These are parameters required to run an even-odd test in EMAN2"
	documentation_string = "This form is used to run e2eotest."
	warning_string = "\n\n\nThere are no refinement results available to use as the basis of running e2eotest"
	def __init__(self):
	 	EMClassificationTools.__init__(self)
	 	E2Make3DTools.__init__(self)
	 	self.window_title = "e2eotest parameters"
	 	self.form_db_name = "bdb:emform.e2eotest"
	 	self.dir_and_iter = {} # will eventually be useful information about directories that will work for e2eotest
	 	
#	def run_form(self):
#		self.form = EMTableFormModule(self.get_params(),get_application())
#		self.form.qt_widget.resize(*self.preferred_size)
#		self.form.setWindowTitle(self.window_title)
#		get_application().show_specific(self.form)
#		QtCore.QObject.connect(self.form,QtCore.SIGNAL("emform_ok"),self.on_form_ok)
#		QtCore.QObject.connect(self.form,QtCore.SIGNAL("emform_cancel"),self.on_form_cancel)
#		QtCore.QObject.connect(self.form,QtCore.SIGNAL("emform_close"),self.on_form_close)
#		QtCore.QObject.connect(self.form,QtCore.SIGNAL("display_file"),self.on_display_file)
	
	def run_form(self):
		self.form = EMTableFormModule(self.get_params(),get_application())
		self.form.qt_widget.resize(*self.preferred_size)
		self.form.setWindowTitle(self.window_title)
		get_application().show_specific(self.form)
		QtCore.QObject.connect(self.form,QtCore.SIGNAL("emform_ok"),self.on_form_ok)
		QtCore.QObject.connect(self.form,QtCore.SIGNAL("emform_cancel"),self.on_form_cancel)
		QtCore.QObject.connect(self.form,QtCore.SIGNAL("emform_close"),self.on_form_close)
		QtCore.QObject.connect(self.form,QtCore.SIGNAL("display_file"),self.on_display_file)
		
	
	def get_params(self):
	 	params = []
		
		# do this so that we have 
		self.__set_available_iteration_data()
		
		
		if len(self.dir_and_iter) == 0:
			params.append(self.get_cant_proceed_page())
			return params
		
		params.append(self.get_main_params())
		params.append(self.get_classaverage_page(include_sep=False))
		params.append(self.get_make3d_page())
		
		return params
	
	def get_cant_proceed_page(self):
		params = []		

		params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=E2EotestTask.documentation_string+E2EotestTask.warning_string,choices=None))

		return ["Can't proceed",params]
	def __set_available_iteration_data(self):
		'''
		This function is called in get_params to accrue the directory data
		'''
		dirs = get_numbered_directories("refine_")
		dirs.sort()
		
		nec_files = [ "classes_", "classify_","projections_"]
		
		self.dir_and_iter = {}
		for dir in dirs:
			fail = False
			available_iters = []
			for i in range(0,10):
				for j in range(0,10):
					end = str(i) + str(j)
					for file in nec_files:
						db_first_part = "bdb:"+dir+"#" + file
						db_name = db_first_part + end
						if not db_check_dict(db_name):
							fail = True
							break
					if not fail:
						available_iters.append(end)
					else:
						break
				if fail: break
			
			# might be some empyt ones so just forget those
			if len(available_iters) > 0: 
				available_iters.reverse()
				self.dir_and_iter[dir] = available_iters
	
	def get_main_params(self):
		'''
		General/broad refine params
		'''
		# have to get the directories 
		params = []
		params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=E2EotestTask.general_documentation,choices=None))
		
		# I could check to see if the database exists but it seems unnecessary
		# In the event that the database doesn't exist it is created and 
		# a new entry is created on disk. The only inconvenient aspect of this comes
		# if the user hits cancel - then there is a file on disk even though
		# the user never agreed to anything
		db = db_open_dict(self.form_db_name) # see eman wiki for a list of what args are kept in this db
		
		params.append(ParamDef(name="path and iteration", vartype="dict",desc_short="Directory and iteration",desc_long="Select the directory containing the refinement and the iteration you wish to use as the input", property=None, defaultunits="",choices=self.dir_and_iter  ))
	
		
		plowmem = ParamDef(name="lowmem",vartype="boolean",desc_short="Low mem",desc_long="Causes various programs to restrict memory usage but results in increased CPU time.",property=None,defaultunits=db.get("lowmem",dfl=False),choices=None)
		pusefilt = ParamDef(name="usefilt",vartype="boolean",desc_short="Usefilt",desc_long="Will use the 'usefilt' data for class alignment if it exists in the refinement directory",property=None,defaultunits=db.get("usefilt",dfl=False),choices=None)
		
		syms = ["icos","oct","tet","d","c","h"]
		
		psym =  ParamDef(name="symname",vartype="string",desc_short="Symmetry",desc_long="Symmetry to be imposed during refinement",property=None,defaultunits=db.get("symname",dfl="c"),choices=syms)
		psymnum = ParamDef(name="symnumber",vartype="string",desc_short="Symmetry number",desc_long="In C,D and H symmetry, this is the symmetry number",property=None,defaultunits=db.get("symnumber",dfl="1"),choices=None)
		

		params.append([plowmem,pusefilt])
		params.append([psym,psymnum])
		
		
		#db_close_dict(self.form_db_name)
		
		return ["General",params]
	
	
	def check_main_page(self,params,options):
		error_message = []
		
		options.path = params["path"]
		options.iteration = params["iteration"]
		options.lowmem = params["lowmem"]
		
		if params["usefilt"] == True:
			file = "bdb:"+params["path"]+"#usefilt" # note that the naming convention is assumed
			if not file_exists(file):
				error_message.append("You have checked usefilt but there is not usefilt file in the chosen refinement directory")
			else:
				options.usefilt = file
		
		error_message.extend(self.check_sym(params,options))
		
		return error_message
		
	def add_general_args(self,options,string_args,bool_args,additional_args):
		
		
		if hasattr(options,"usefilt"): string_args.append("usefilt")
		string_args.extend(["path","iteration","sym"])
		bool_args.append("lowmem")
		
		return None # returning None is good
		
	
	def on_form_ok(self,params):

		if len(self.dir_and_iter) == 0: return # The user has the can't proceed page

		options = EmptyObject()
		
		for checker in [self.check_main_page,self.check_classaverage_page,self.check_make3d_page]:
			error_message = checker(params,options)
			if len(error_message) > 0 :
				self.display_errors(error_message)
				return
			

		self.write_db_entries(params)
#		# w'oh if we make it here a lot of checking has occured. Now get the args in order to spawn_single_task
		string_args = []
		bool_args = []
		
		additional_args = ["--force"]
#		
		for get_args in [self.add_general_args,self.add_classaverage_args,self.add_make3d_args]:
			if get_args == self.add_classaverage_args:
				error = get_args(options,string_args,bool_args,additional_args,include_sep=False)
			else:
				error = get_args(options,string_args,bool_args,additional_args)
		
			if error != None: # not too fast, something still could have gone wrong
				self.display_errors([error])
				return
			
		temp_file_name = "e2eotest_stdout.txt"
#		
#		self.write_db_parms(options,string_args,bool_args)
#		
	   	options.filenames = [] # spawn single task expects a filenames attribute
		self.spawn_single_task("e2eotest.py",options,string_args,bool_args,additional_args,temp_file_name)
		self.emit(QtCore.SIGNAL("task_idle"))
		self.form.closeEvent(None)
		self.form = None
#	
class E2ResolutionTask(WorkFlowTask):
	'''

	'''
	 
	general_documentation = "These are parameters required to run an e2resolution.py."
	warning_string = "\n\n\nThere are no refinement results available to use as the basis of running e2resolution"
	def __init__(self):
	 	WorkFlowTask.__init__(self)
	 	self.window_title = "e2resolution parameters"
	 	self.dir_and_iter = {} # will eventually be useful information about directories that will work for e2eotest
	 	
		
	def get_params(self):
		'''
		General/broad refine params
		'''
		# have to get the directories 
		dirs = get_numbered_directories("refine_")
		dirs.sort()
		
		nec_files = ["threed_filt_","threed_mask_"]
		
		self.dir_and_iter = {}
		for dir in dirs:
			fail = False
			available_iters = []
			for i in range(0,10):
				for j in range(0,10):
					end = str(i) + str(j)
					for file in nec_files:
						db_first_part = "bdb:"+dir+"#" + file
						db_name = db_first_part + end
						if not db_check_dict(db_name):
							fail = True
							break
					if not fail:
						available_iters.append(end)
					else:
						break
				if fail: break
			
			# might be some empyt ones so just forget those
			if len(available_iters) > 0: 
				available_iters.reverse()
				self.dir_and_iter[dir] = available_iters
	
		params = []
		if len(self.dir_and_iter) == 0:
			params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=E2ResolutionTask.general_documentation+ E2ResolutionTask.warning_string,choices=None))
			return params
		
		params = []
		params.append(ParamDef(name="blurb",vartype="text",desc_short="",desc_long="",property=None,defaultunits=E2ResolutionTask.general_documentation,choices=None))
		
	
		params.append(ParamDef(name="path and iteration", vartype="dict",desc_short="Directory and iteration",desc_long="Select the directory containing the refinement and the iteration you wish to use as the input", property=None, defaultunits="",choices=self.dir_and_iter  ))
		
		project_db = db_open_dict("bdb:project")
		papix = ParamDef(name="global.apix",vartype="float",desc_short="Angtsrom per pixel",desc_long="The physical distance represented by the pixel spacing",property=None,defaultunits=project_db.get("global.apix",dfl=1.1),choices=None)
		params.append(papix)
		
		#db_close_dict("bdb:project")
		
		return params
	
	def on_form_ok(self,params):

		if len(self.dir_and_iter) == 0: return # the user has been issued a warning about data lacking, ok does nothing

		if  params.has_key("global.apix") and params["global.apix"] <= 0:
			self.show_error_message(["Apix must be greater than  zero"])
			return
		else:
			self.write_db_entries(params)

		options = EmptyObject()			
		options.path = params["path"]
		options.apix = params["global.apix"]
		
		string_args = ["path","apix"]
		bool_args = []
		
		image = "bdb:"+params["path"] + "#threed_filt_"+params["iteration"]
		mask = "bdb:"+params["path"] + "#threed_mask_"+params["iteration"]
		output = "tmp"
		additional_args = [image,mask,output]

		temp_file_name = "e2resolution_stdout.txt"
	   	options.filenames = [] # spawn single task expects a filenames attribute
		self.spawn_single_task("e2resolution.py",options,string_args,bool_args,additional_args,temp_file_name)
		self.emit(QtCore.SIGNAL("task_idle"))
		self.form.closeEvent(None)
		self.form = None
#	

	
if __name__ == '__main__':
	
	from emapplication import EMStandAloneApplication
	em_app = EMStandAloneApplication()
	sprinit = SPRInitTask(em_app)
	window = sprinit.run_form() 
	#em_app.show()
	em_app.execute()	
