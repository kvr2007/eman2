'''1
# secondrun
def secondrunrecons3d_4nnw_MPI(myid, prjlist, prevol, symmetry="c1", finfo=None, npad=2, mpi_comm=None):
	pass#IMPORTIMPORTIMPORT from utilities     import reduce_EMData_to_root, pad, get_params_proj
	pass#IMPORTIMPORTIMPORT from EMAN2         import Reconstructors
	pass#IMPORTIMPORTIMPORT from utilities     import iterImagesList, model_blank, model_circle, reshape_1d, read_text_file
	pass#IMPORTIMPORTIMPORT from fundamentals  import fft, rops
	pass#IMPORTIMPORTIMPORT from mpi           import MPI_COMM_WORLD
	pass#IMPORTIMPORTIMPORT import types

	if mpi_comm == None:
		mpi_comm = MPI_COMM_WORLD

	if type(prjlist) == types.ListType:
		prjlist = iterImagesList(prjlist)

	if not prjlist.goToNext():
		ERROR("empty input list","recons3d_4nn_MPI",1)

	imgsize = prjlist.image().get_xsize()
	bigsize = imgsize*npad
	bnx     = bigsize//2+1

	prjlist.goToPrev()

	fftvol = EMData()
	weight = EMData()
	print "   NEW"
	#t = read_text_file('fromrun8model.txt',4)
	#  GET FSC
	t = read_text_file('data_model.txt',4)
	pass#IMPORTIMPORTIMPORT from math import sqrt
	for i in xrange(len(t)):
		t[i] = max(t[i],0.0)
		#  This is what is used to get the SSNR
		t[i] = sqrt(2*t[i]/(1.0+t[i]))
	t = reshape_1d(t,len(t),npad*len(t))
	refvol = model_blank(2*bnx,1,1,0.5)
	for i in xrange(len(t)):  refvol.set_value_at(i,t[i])
	"""
	pass#IMPORTIMPORTIMPORT from math import tanh,pi
	fl = 0.15
	aa = 0.15
	for i in xrange(bnx):
		r = float(i)/bigsize
		refvol.set_value_at(i, 0.5*( tanh(pi*(r+fl)/2.0/fl/aa) - tanh(pi*(r-fl)/2.0/2.0/fl/aa) ) )
		print "  FILTER  ",i,refvol.get_value_at(i)
	"""
	#print " DONE refvol"
	params = {"size":imgsize, "npad":npad, "symmetry":symmetry, "fftvol":fftvol, "refvol":refvol, "weight":weight, "weighting":0, "snr":1.0}
	r = Reconstructors.get( "nn4_ctfw", params )
	r.setup()

	pass#IMPORTIMPORTIMPORT from projection import prep_vol, prgs
	pass#IMPORTIMPORTIMPORT from filter import filt_ctf
	#volft,kb = prep_vol(prevol)

	#mask2d = model_circle(imgsize//2-2, imgsize,imgsize)
	#maskbi = model_circle(imgsize//2-2, bigsize,bigsize)
	#  noise model of 2D data.
	models = [None]
	for ml in xrange(len(models)):
		temp = read_text_file('sigma2.txt',2)
		temp = reshape_1d(temp, len(temp), 2*len(temp))
		models[ml] = model_blank(len(temp)+10)
		for lm in xrange(len(temp)):  models[ml].set_value_at(lm,1.0/(temp[lm]*4*imgsize**2/npad))
		#from sys import exit
		#print "metadata/model-%04d.txt"%groupkeys[1][ml]
		#for lm in xrange(len(temp)):  print  lm,models[ml].get_value_at(lm)
		#exit()


	if not (finfo is None): nimg = 0
	ll = 0
	while prjlist.goToNext():
		prj = prjlist.image()

		# horatio active_refactoring Jy51i1EwmLD4tWZ9_00000_1
		# active = prj.get_attr_default('active', 1)
		# if(active == 1):
		if ll%100 == 0:  print "  moved  ",ll
		ll +=1
		prj.set_attr("sigmasq2", models[0])
		#if ll == 0:
		#	write_text_file([range(bigsize),[pqdif[i] for i in xrange(bigsize)] ],"pqdif.txt")
		#	ll+=1
		insert_slices(r, prj)
		if( not (finfo is None) ):
			nimg += 1
			info.write("Image %4d inserted.\n" %(nimg) )
			info.flush()

		if ll%100 == 0:  print "  moved  ",ll
		ll +=1
		prj.set_attr("sigmasq2", models[0])
		#if ll == 0:
		#	write_text_file([range(bigsize),[pqdif[i] for i in xrange(bigsize)] ],"pqdif.txt")
		#	ll+=1
		insert_slices(r, prj)
		if( not (finfo is None) ):
			nimg += 1
			info.write("Image %4d inserted.\n" %(nimg) )
			info.flush()

	if not (finfo is None):
		info.write( "Begin reducing ...\n" )
		info.flush()

	#del qdif, pqdif, mask2d, maskbi

	reduce_EMData_to_root(fftvol, myid, comm=mpi_comm)
	reduce_EMData_to_root(weight, myid, comm=mpi_comm)

	if myid == 0:
		print  "  STARTING FINISH"
		dummy = r.finish(True)
	else:
		pass#IMPORTIMPORTIMPORT from utilities import model_blank
		fftvol = model_blank(imgsize, imgsize, imgsize)
	return fftvol
'''
'''2
#chc5
def recons3d_4nnw_MPI(myid, prjlist, prevol, symmetry="c1", finfo=None, npad=2, mpi_comm=None):
	pass#IMPORTIMPORTIMPORT from utilities     import reduce_EMData_to_root, pad, get_params_proj
	pass#IMPORTIMPORTIMPORT from EMAN2         import Reconstructors
	pass#IMPORTIMPORTIMPORT from utilities     import iterImagesList, model_blank, model_circle, reshape_1d, read_text_file
	pass#IMPORTIMPORTIMPORT from fundamentals  import fft, rops
	pass#IMPORTIMPORTIMPORT from mpi           import MPI_COMM_WORLD
	pass#IMPORTIMPORTIMPORT import types

	if mpi_comm == None:
		mpi_comm = MPI_COMM_WORLD

	if type(prjlist) == types.ListType:
		prjlist = iterImagesList(prjlist)

	if not prjlist.goToNext():
		ERROR("empty input list","recons3d_4nn_MPI",1)

	imgsize = prjlist.image().get_xsize()
	bigsize = imgsize*npad
	bnx     = bigsize//2+1

	prjlist.goToPrev()

	fftvol = EMData()
	weight = EMData()
	"""
	if myid == 0:
		model_blank(bnx, bigsize, bigsize)
		temp = fft(pad(prevol,bigsize,bigsize,bigsize,0.0))
		temp.set_attr("is_complex",0)
		st = 0.5/(bigsize*bigsize)
		for kk in xrange(bigsize):
			for jj in xrange(bigsize):
				for ii in xrange(0,bnx,2):
					#print ii,jj,kk,temp.get_value_at(ii,jj,kk), temp.get_value_at(ii,jj,kk+1)
					refvol.set_value_at_fast(ii//2,jj,kk,st/((temp.get_value_at(ii,jj,kk))**2+(temp.get_value_at(ii+1,jj,kk))**2) )
					#refvol.set_value_at_fast(ii//2,jj,kk,1.0 )
		refvol.set_value_at_fast(0,0,0,0.0)
		del temp

		st = rops(pad(prevol,bigsize,bigsize,bigsize,0.0))*(bigsize**6)/4.
		pass#IMPORTIMPORTIMPORT from utilities import info
		pass#IMPORTIMPORTIMPORT from utilities import write_text_file
		#zizi = [st.get_value_at(i) for i in xrange(st.get_xsize())]
		#for i in xrange(st.get_xsize()):  st.set_value_at(i,1.0)#/st.get_value_at(i))
		#info(st,None,"refvol")
		refvol = model_blank(bigsize,1,1,1.0)
		for i in xrange(st.get_xsize()):  refvol.set_value_at(i,1.0/(211*st.get_value_at(i)))
	else:  refvol = EMData()
	"""
	print "   NEW"
	#t = read_text_file('fromrun8model.txt',4)
	t = read_text_file('../for-pawel/fsc-relion.txt',1)
	pass#IMPORTIMPORTIMPORT from math import sqrt
	for i in xrange(len(t)):
		t[i] = max(t[i],0.0)
		t[i] = sqrt(2*t[i]/(1.0+t[i]))
	t = reshape_1d(t,len(t),npad*len(t))
	refvol = model_blank(2*bnx,1,1,0.5)
	#for i in xrange(len(t)):  refvol.set_value_at(i,t[i])
	"""
	pass#IMPORTIMPORTIMPORT from math import tanh,pi
	fl = 0.15
	aa = 0.15
	for i in xrange(bnx):
		r = float(i)/bigsize
		refvol.set_value_at(i, 0.5*( tanh(pi*(r+fl)/2.0/fl/aa) - tanh(pi*(r-fl)/2.0/2.0/fl/aa) ) )
		print "  FILTER  ",i,refvol.get_value_at(i)
	"""
	#print " DONE refvol"
	params = {"size":imgsize, "npad":npad, "symmetry":symmetry, "fftvol":fftvol, "refvol":refvol, "weight":weight, "weighting":0, "snr":1.0}
	r = Reconstructors.get( "nn4_ctfw", params )
	r.setup()

	pass#IMPORTIMPORTIMPORT from projection import prep_vol, prgs
	pass#IMPORTIMPORTIMPORT from filter import filt_ctf
	#volft,kb = prep_vol(prevol)

	#mask2d = model_circle(imgsize//2-2, imgsize,imgsize)
	#maskbi = model_circle(imgsize//2-2, bigsize,bigsize)

	groupkeys = read_text_file("groupkeys.txt",-1)
	for ml in xrange(3):  groupkeys[ml] = map(int, groupkeys[ml])
	models = [None]*len(groupkeys[0])
	for ml in xrange(len(models)):
		temp = read_text_file("metadata/model-%04d.txt"%groupkeys[1][ml],-1)
		temp = reshape_1d(temp[2], len(temp[0]), 2*len(temp[0]))
		models[ml] = model_blank(len(temp)+10)
		for lm in xrange(len(temp)):  models[ml].set_value_at(lm,1.0/(temp[lm]*4*imgsize**2/npad))
		#from sys import exit
		#print "metadata/model-%04d.txt"%groupkeys[1][ml]
		#for lm in xrange(len(temp)):  print  lm,models[ml].get_value_at(lm)
		#exit()


	if not (finfo is None): nimg = 0
	ll = 0
	while prjlist.goToNext():
		prj = prjlist.image()
		if ll%100 == 0:  print "  moved  ",ll
		ll +=1
		ml = prj.get_attr('groupindex')#int(prj.get_attr('data_path')[4:8])
		prj.set_attr("sigmasq2", models[groupkeys[1].index(ml)])
		insert_slices(r, prj)
		if( not (finfo is None) ):
			nimg += 1
			info.write("Image %4d inserted.\n" %(nimg) )
			info.flush()

	if not (finfo is None):
		info.write( "Begin reducing ...\n" )
		info.flush()

	#del qdif, pqdif, mask2d, maskbi

	reduce_EMData_to_root(fftvol, myid, comm=mpi_comm)
	reduce_EMData_to_root(weight, myid, comm=mpi_comm)

	if myid == 0:
		print  "  STARTING FINISH"
		dummy = r.finish(True)
	else:
		pass#IMPORTIMPORTIMPORT from utilities import model_blank
		fftvol = model_blank(imgsize, imgsize, imgsize)
	return fftvol
'''
'''3
def recons3d_4nnf_MPI(myid, list_of_prjlist, bckgdata, snr = 1.0, sign=1, symmetry="c1", finfo=None, npad=2, mpi_comm=None, smearstep = 0.0, main_node = 0):
	"""
		recons3d_4nn_ctf - calculate CTF-corrected 3-D reconstruction from a set of projections using three Eulerian angles, two shifts, and CTF settings for each projeciton image
		Input
			list_of_prjlist: list of lists of projections to be included in the reconstruction
			bckgdata = [get_im("tsd.hdf"),read_text_file("data_stamp.txt")]
			snr: Signal-to-Noise Ratio of the data 
			sign: sign of the CTF
			symmetry: point-group symmetry to be enforced, each projection will enter the reconstruction in all symmetry-related directions.
	"""
	pass#IMPORTIMPORTIMPORT from utilities  import reduce_EMData_to_root, get_im, send_string_to_all
	pass#IMPORTIMPORTIMPORT from statistics import fsc
	pass#IMPORTIMPORTIMPORT from utilities  import get_image, send_EMData, recv_EMData

	pass#IMPORTIMPORTIMPORT from EMAN2      import Reconstructors
	pass#IMPORTIMPORTIMPORT from utilities  import model_blank, cmdexecute
	pass#IMPORTIMPORTIMPORT from mpi        import MPI_COMM_WORLD, mpi_barrier, mpi_comm_size
	pass#IMPORTIMPORTIMPORT import types
	pass#IMPORTIMPORTIMPORT from statistics import fsc
	pass#IMPORTIMPORTIMPORT import datetime
	
	if mpi_comm == None:
		mpi_comm = MPI_COMM_WORLD
	main_node = 0
	imgsize = list_of_prjlist[0][0].get_xsize()
	
	if( smearstep > 0.0 ):
		#if myid == 0:  print "  Setting smear in prepare_recons_ctf"
		ns = 1
		smear = []
		for j in xrange(-ns,ns+1):
			if( j != 0):
				for i in xrange(-ns,ns+1):
					for k in xrange(-ns,ns+1):
						smear += [i*smearstep,j*smearstep,k*smearstep,1.0]
		# Deal with theta = 0.0 cases
		prj = []
		for i in xrange(-ns,ns+1):
			for k in xrange(-ns,ns+1):
				prj.append(i+k)
		for i in xrange(-2*ns,2*ns+1,1):
			smear += [i*smearstep,0.0,0.0,float(prj.count(i))]
		#if myid == 0:  print "  Smear  ",smear

	#from utilities import model_blank, get_im, read_text_file
	#bckgdata = [get_im("tsd.hdf"),read_text_file("data_stamp.txt")]

	nnx = bckgdata[0].get_xsize()
	nny = bckgdata[0].get_ysize()
	bckgnoise = []
	for i in xrange(nny):
		prj = model_blank(nnx)
		for k in xrange(nnx):  prj[k] = bckgdata[0].get_value_at(k,i)
		bckgnoise.append(prj)

	datastamp = bckgdata[1]

	#  Do the FSC shtick.
	bnx     = imgsize*npad//2+1
	refvol = model_blank(bnx)  # fill fsc with zeroes so the first reconstruction is done using simple Wiener filter.
	refvol.set_attr("fudge", 1.0)

	reconstructed_vols_list = []
	fftvol_file =[]
	weight_file = []
	

	volall_files = []
	volall = []
	fscdat_list = []
	no_of_splits = 2
	for iset in xrange(2):
		reconstructed_vol_files = []
		for iter_no_of_splits in range(no_of_splits):
			if not (finfo is None): nimg = 0
	
			fftvol = EMData()
			weight = EMData()
			if( smearstep > 0.0 ):  fftvol.set_attr("smear", smear)
		
			params = {"size":imgsize, "npad":npad, "snr":snr, "sign":sign, "symmetry":symmetry, "refvol":refvol, "fftvol":fftvol, "weight":weight}
			r = Reconstructors.get( "nn4_ctfw", params )
			r.setup()

			for image in list_of_prjlist[iset][slice(iter_no_of_splits,len(list_of_prjlist[iset]), no_of_splits)]:	
			# for image in list_of_prjlist[iset]:
				try:
					# lll = iset/0
					#raise ValueError('A very specific thing happened')
					stmp = image.get_attr("ptcl_source_image")
				except:
					try:
						stmp = image.get_attr("ctf")
						stmp = round(stmp.defocus,4)
					except:
						ERROR("Either ptcl_source_image or ctf has to be present in the header.","recons3d_4nnw_MPI    %f"%stmp,1, myid)
				try:
					indx = datastamp.index(stmp)
				except:
					ERROR("Problem with indexing ptcl_source_image.","recons3d_4nnf_MPI   %s"%stmp,1, myid)

			if not (finfo is None): 
				finfo.write( "begin reduce\n" )
				finfo.flush()
		
			reduce_EMData_to_root(fftvol, myid, main_node, comm=mpi_comm)
			reduce_EMData_to_root(weight, myid, main_node, comm=mpi_comm)
			
			if not (finfo is None): 
				finfo.write( "after reduce\n" )
				finfo.flush()
	
			if myid == 0:
				tmpid = datetime.datetime.now().strftime('%Y-%m-%d--%I-%M-%f')[:-3]
				fftvol_file.append("fftvol__%s__idx%d_split%d.hdf"%(tmpid, iset, iter_no_of_splits))
				weight_file.append("weight__%s__idx%d_split%d.hdf"%(tmpid, iset, iter_no_of_splits))
				fftvol.write_image(fftvol_file[-1])
				weight.write_image(weight_file[-1])
				del weight
	
				dummy = r.finish(True)
				### finish returns fftvol, will rename to 

				if(iter_no_of_splits == 0):
					reconstructed_vol_files.append("rvol__%s__idx%d_split%d.hdf"%(tmpid, iset, iter_no_of_splits))
					fftvol.write_image(reconstructed_vol_files[-1])
					del fftvol
				else:
					reconstructed_vol_files.append(fftvol)
	
		mpi_barrier(mpi_comm)
			
		### at this point we calculate V[iset]
		### fftvol_file = [FE, FO]
		### weight_file = [WE, WO]
		### reconstructed_vol_files = [VE(disk), VO(memory)]
	
		########################################	
		### code not tested 2015-12-21--13-01-49 
		########################################
		
		nproc = mpi_comm_size(mpi_comm)
		assert nproc > 2
		main_node_odd = main_node
		main_node_eve = (int(main_node)+nproc-1)%int(nproc)
		main_node_all = (int(main_node)+nproc//2)%int(nproc)

		tag_voleve     = 1000
		tag_fftvol_eve = 1001
		tag_weight_eve = 1002

		tag_fftvol_odd = 1003
		tag_weight_odd = 1004
		tag_volall     = 1005
		
		fftvol_file = eval(send_string_to_all(str(fftvol_file), source_node = main_node))
		weight_file = eval(send_string_to_all(str(weight_file), source_node = main_node))
		
		fftvol_odd_file, fftvol_eve_file = fftvol_file[-2:]
		weight_odd_file, weight_eve_file = weight_file[-2:]
		
		if myid == main_node_odd:
			fftvol = get_image( fftvol_odd_file )
			send_EMData(fftvol, main_node_eve, tag_fftvol_odd, mpi_comm)

			weight = get_image( weight_odd_file )
			send_EMData(weight, main_node_all, tag_weight_odd, mpi_comm)
			volodd = reconstructed_vol_files[1]
			del fftvol, weight
			voleve = get_im(reconstructed_vol_files[0])
			fscdat_list.append(fsc(volodd, voleve, 1.0)[1])
			del  volodd, voleve

			volall = recv_EMData(main_node_all, tag_volall, mpi_comm)
			if iset == 0:
				volall_files.append("volall__%s__idx%d.hdf"%(tmpid, iset))
				volall.write_image(volall_files[-1])
			else:
				volall_files.append(volall)

		if myid == main_node_eve:
			ftmp = recv_EMData(main_node_odd, tag_fftvol_odd, mpi_comm)
			fftvol = get_image( fftvol_eve_file )
			Util.add_img( ftmp, fftvol )

			send_EMData(ftmp, main_node_all, tag_fftvol_eve, mpi_comm)
			del ftmp
			weight = get_image( weight_eve_file )
			send_EMData(weight, main_node_all, tag_weight_eve, mpi_comm)

		if myid == main_node_all:


			fftvol = recv_EMData(main_node_eve, tag_fftvol_eve, mpi_comm)
			weight = recv_EMData(main_node_odd, tag_weight_odd, mpi_comm)
			weight_tmp = recv_EMData(main_node_eve, tag_weight_eve, mpi_comm)
			Util.add_img( weight, weight_tmp )

			weight_tmp = None
			volall = recons_ctf_from_fftvol_using_nn4_ctfw(imgsize, fftvol, weight, snr, symmetry, npad = npad)
			send_EMData(volall, main_node_odd, tag_volall, mpi_comm)

	### at this point we calculate fourier_shell_correlation for V[0], V[1]

	if myid == 0:
		fourier_shell_correlation = fsc(get_im(volall_files[0]), volall_files[1], 1.0)[1]
		fourier_shell_correlation[0] = 1.0

		pass#IMPORTIMPORTIMPORT from math import sqrt
		pass#IMPORTIMPORTIMPORT from utilities import reshape_1d
		t = [0.0]*len(fourier_shell_correlation)
		t = reshape_1d(t,len(t),npad*len(t))
		for i in xrange(len(t):
			t[i] = min(max(t[i], 0.0), 0.999)


		ovol = []
		for idx in range(2):
			fftvol = get_im(fftvol_file[idx])
			weight = get_im(weight_file[idx])
			refvol = model_blank(bnx,1,1,0.0)
			for i in xrange(len(t)):  
				refvol.set_value_at(i, t[i])
			refvol.set_attr("fudge", 1.0)
			
			params = {"size":imgsize, "npad":npad, "snr":snr, "sign":sign, "symmetry":symmetry, "refvol":refvol, "fftvol":fftvol, "weight":weight}
			r = Reconstructors.get("nn4_ctfw", params)
			r.setup()
			
			dummy = r.finish(True)
			ovol.append(fftvol)


		cmd = "{} {} {} {} {} {}".format("rm -f", fftvol_file[0], fftvol_file[1], weight_file[0], weight_file[1], results_list[0] )
		junk = cmdexecute(cmd)

	mpi_barrier(mpi_comm)
	if myid == 0:
		return ovol[0], ovol[1], fourier_shell_correlation, fscdat_list[0], fscdat_list[1]
	else:
		return None, None, None, None, None

'''
'''4
def recons3d_4nnf_MPI(myid, list_of_prjlist, bckgdata, snr = 1.0, sign=1, symmetry="c1", finfo=None, npad=2, mpi_comm=None, smearstep = 0.0):
	"""
		recons3d_4nn_ctf - calculate CTF-corrected 3-D reconstruction from a set of projections using three Eulerian angles, two shifts, and CTF settings for each projeciton image
		Input
			list_of_prjlist: list of lists of projections to be included in the reconstruction
			bckgdata = [get_im("tsd.hdf"),read_text_file("data_stamp.txt")]
			snr: Signal-to-Noise Ratio of the data 
			sign: sign of the CTF
			symmetry: point-group symmetry to be enforced, each projection will enter the reconstruction in all symmetry-related directions.
	"""
	pass#IMPORTIMPORTIMPORT from utilities  import reduce_EMData_to_root, random_string, get_im
	pass#IMPORTIMPORTIMPORT from EMAN2      import Reconstructors
	pass#IMPORTIMPORTIMPORT from utilities  import model_blank
	pass#IMPORTIMPORTIMPORT from mpi        import MPI_COMM_WORLD, mpi_barrier
	pass#IMPORTIMPORTIMPORT import types
	pass#IMPORTIMPORTIMPORT from statistics import fsc
	pass#IMPORTIMPORTIMPORT import datetime
	
	if mpi_comm == None:
		mpi_comm = MPI_COMM_WORLD
	main_node = 0
	imgsize = list_of_prjlist[0][0].get_xsize()
	
	if( smearstep > 0.0 ):
		#if myid == 0:  print "  Setting smear in prepare_recons_ctf"
		ns = 1
		smear = []
		for j in xrange(-ns,ns+1):
			if( j != 0):
				for i in xrange(-ns,ns+1):
					for k in xrange(-ns,ns+1):
						smear += [i*smearstep,j*smearstep,k*smearstep,1.0]
		# Deal with theta = 0.0 cases
		prj = []
		for i in xrange(-ns,ns+1):
			for k in xrange(-ns,ns+1):
				prj.append(i+k)
		for i in xrange(-2*ns,2*ns+1,1):
			smear += [i*smearstep,0.0,0.0,float(prj.count(i))]
		#if myid == 0:  print "  Smear  ",smear

	#from utilities import model_blank, get_im, read_text_file
	#bckgdata = [get_im("tsd.hdf"),read_text_file("data_stamp.txt")]

	nnx = bckgdata[0].get_xsize()
	nny = bckgdata[0].get_ysize()
	bckgnoise = []
	for i in xrange(nny):
		prj = model_blank(nnx)
		for k in xrange(nnx):  prj[k] = bckgdata[0].get_value_at(k,i)
		bckgnoise.append(prj)

	datastamp = bckgdata[1]

	#  Do the FSC shtick.
	bnx     = imgsize*npad//2+1
	refvol = model_blank(bnx)  # fill fsc with zeroes so the first reconstruction is done using simple Wiener filter.
	refvol.set_attr("fudge", 1.0)

	results_list = []
	fftvol_file =[]
	weight_file = []

	for iset in xrange(2):
		if not (finfo is None): nimg = 0

		fftvol = EMData()
		weight = EMData()
		if( smearstep > 0.0 ):  fftvol.set_attr("smear", smear)
	
		params = {"size":imgsize, "npad":npad, "snr":snr, "sign":sign, "symmetry":symmetry, "refvol":refvol, "fftvol":fftvol, "weight":weight}
		r = Reconstructors.get( "nn4_ctfw", params )
		r.setup()

		for image in list_of_prjlist[iset]:
			try:
				#raise ValueError('A very specific thing happened')
				stmp = image.get_attr("ptcl_source_image")
			except:
				try:
					stmp = image.get_attr("ctf")
					stmp = round(stmp.defocus,4)
				except:
					ERROR("Either ptcl_source_image or ctf has to be present in the header.","recons3d_4nnw_MPI",1, myid)
			try:
				indx = datastamp.index(stmp)
			except:
				ERROR("Problem with indexing ptcl_source_image.","recons3d_4nnf_MPI",1, myid)
	
			image.set_attr("bckgnoise", bckgnoise[indx])
			insert_slices(r, image)
			if not (finfo is None):
				nimg += 1
				finfo.write(" %4d inserted\n" %(nimg) )
				finfo.flush()

		if not (finfo is None): 
			finfo.write( "begin reduce\n" )
			finfo.flush()
	
		reduce_EMData_to_root(fftvol, myid, main_node, comm=mpi_comm)
		reduce_EMData_to_root(weight, myid, main_node, comm=mpi_comm)
		
		if not (finfo is None): 
			finfo.write( "after reduce\n" )
			finfo.flush()

		if myid == 0:
			tmpid = datetime.datetime.now().strftime('%Y-%m-%d--%I-%M-%f')[:-3]
			fftvol_file.append("fftvol__%s__idx%d.hdf"%(tmpid, iset))
			weight_file.append("weight__%s__idx%d.hdf"%(tmpid, iset))
			fftvol.write_image(fftvol_file[-1])
			weight.write_image(weight_file[-1])

			dummy = r.finish(True)
			results_list.append("rvol__%s__idx%d.hdf"%(tmpid, iset))
			if(iset == 0):  fftvol.write_image(results_list[-1])

		mpi_barrier(mpi_comm)

	if myid == 0:
		fourier_shell_correlation = fsc(get_im(results_list[0]), fftvol, 1.0)[1]

		pass#IMPORTIMPORTIMPORT from math import sqrt
		pass#IMPORTIMPORTIMPORT from utilities import reshape_1d
		t = [0.0]*len(fourier_shell_correlation)
		t = reshape_1d(t,len(t),npad*len(t))
		for i in xrange(len(t)):
			t[i] = min(max(t[i], 0.0), 0.999)

		ovol = []
		for idx in range(2):
			fftvol = get_im(fftvol_file[idx])
			weight = get_im(weight_file[idx])
			refvol = model_blank(bnx,1,1,0.0)
			for i in xrange(min(bnx,len(t))):  
				refvol.set_value_at(i, t[i])
			refvol.set_attr("fudge", 1.0)
			
			params = {"size":imgsize, "npad":npad, "snr":snr, "sign":sign, "symmetry":symmetry, "refvol":refvol, "fftvol":fftvol, "weight":weight}
			r = Reconstructors.get("nn4_ctfw", params)
			r.setup()
			
			dummy = r.finish(True)
			ovol.append(fftvol)


		cmd = "{} {} {} {} {} {}".format("rm -f", fftvol_file[0], fftvol_file[1], weight_file[0], weight_file[1], results_list[0] )
		pass#IMPORTIMPORTIMPORT import subprocess
		outcome = subprocess.call(cmd, shell=True)

	mpi_barrier(mpi_comm)
	if myid == 0:
		return ovol[0], ovol[1], fourier_shell_correlation
	else:
		return None, None, None
'''
"""5
			tmpid = datetime.datetime.now().strftime('%Y-%m-%d--%I-%M-%f')[:-3]
			fftvol_file.append("fftvol__%s__idx%d.hdf"%(tmpid, iset))
			weight_file.append("weight__%s__idx%d.hdf"%(tmpid, iset))
			fftvol.write_image(fftvol_file[-1])
			weight.write_image(weight_file[-1])
			"""
"""6
		pass#IMPORTIMPORTIMPORT from math import sqrt
		pass#IMPORTIMPORTIMPORT from utilities import reshape_1d
		t = [0.0]*len(fourier_shell_correlation)
		t = reshape_1d(t,len(t),npad*len(t))
		for i in xrange(len(t)):
			t[i] = min(max(t[i], 0.0), 0.999)

		ovol = []
		for idx in range(2):
			fftvol = get_im(fftvol_file[idx])
			weight = get_im(weight_file[idx])
			refvol = model_blank(bnx,1,1,0.0)
			for i in xrange(min(bnx,len(t))):  
				refvol.set_value_at(i, t[i])
			refvol.set_attr("fudge", 1.0)
			
			params = {"size":imgsize, "npad":npad, "snr":snr, "sign":sign, "symmetry":symmetry, "refvol":refvol, "fftvol":fftvol, "weight":weight}
			r = Reconstructors.get("nn4_ctfw", params)
			r.setup()
			
			dummy = r.finish(True)
			ovol.append(fftvol)


		cmd = "{} {} {} {} {} {}".format("rm -f", fftvol_file[0], fftvol_file[1], weight_file[0], weight_file[1], results_list[0] )
		pass#IMPORTIMPORTIMPORT import subprocess
		outcome = subprocess.call(cmd, shell=True)
		"""
'''7
	if( smearstep > 0.0 ):
		#if myid == 0:  print "  Setting smear in prepare_recons_ctf"
		ns = 1
		smear = []
		for j in xrange(-ns,ns+1):
			if( j != 0):
				for i in xrange(-ns,ns+1):
					for k in xrange(-ns,ns+1):
						smear += [i*smearstep,j*smearstep,k*smearstep,1.0]
		# Deal with theta = 0.0 cases
		prj = []
		for i in xrange(-ns,ns+1):
			for k in xrange(-ns,ns+1):
				prj.append(i+k)
		for i in xrange(-2*ns,2*ns+1,1):
			smear += [i*smearstep,0.0,0.0,float(prj.count(i))]
		#if myid == 0:  print "  Smear  ",smear
	'''
"""8
	nnx = bckgdata[0].get_xsize()
	nny = bckgdata[0].get_ysize()
	"""
'''9
	bckgnoise = []
	for i in xrange(1):
		prj = model_blank(600,1,1,1)
		#for k in xrange(nnx):  prj[k] = bckgdata[i].get_value_at(k,i)
		bckgnoise.append(prj)
	'''
"""10
	#  Do the FSC shtick.
	if cfsc:
		bnx     = len(cfsc)*npad*2
		refvol  = model_blank(bnx)
		if(npad > 1):
			pass#IMPORTIMPORTIMPORT from utilities import reshape_1d
			bfsc = reshape_1d(cfsc, len(cfsc), bnx)
			for i in xrange(bnx):  refvol[i] = bfsc[i]
			del bfsc
		else:  refvol[i] = cfsc[i]
	else:
		#  Set refvol to longer array so in finish it can be used to return regularization part
		refvol = model_blank(target_size)  # fill fsc with zeroes so the first reconstruction is done using simple Wiener filter.
	"""
'''11
		numbor = len(paramstructure[im][2])
		ipsiandiang = [ paramstructure[im][2][i][0]/1000  for i in xrange(numbor) ]
		allshifts   = [ paramstructure[im][2][i][0]%1000  for i in xrange(numbor) ]
		probs       = [ paramstructure[im][2][i][1] for i in xrange(numbor) ]
		#  Find unique projection directions
		tdir = list(set(ipsiandiang))
		bckgn = prjlist[im][0].get_attr("bckgnoise")
		#  For each unique projection direction:
		for ii in xrange(len(tdir)):
			#  Find the number of times given projection direction appears on the list, it is the number of different shifts associated with it.
			lshifts = findall(tdir[ii], ipsiandiang)
			toprab  = 0.0
			for ki in xrange(len(lshifts)):  toprab += probs[lshifts[ki]]
			recdata = Util.mult_scalar(prjlist[im][allshifts[lshifts[0]]], probs[lshifts[0]]/toprab)
			recdata.set_attr_dict({"padffted":1, "is_complex":0})
			for ki in xrange(1,len(lshifts)):
				Util.add_img(recdata, Util.mult_scalar(prjlist[im][allshifts[lshifts[ki]]], probs[lshifts[ki]]/toprab))
			recdata.set_attr_dict({"padffted":1, "is_complex":1})
			if not upweighted:  recdata = filt_table(recdata, bckgn )
			recdata.set_attr("bckgnoise", bckgn )
			ipsi = tdir[ii]%100000
			iang = tdir[ii]/100000
			r.insert_slice( recdata, Transform({"type":"spider","phi":refang[iang][0],"theta":refang[iang][1],"psi":refang[iang][2]+ipsi*delta}), toprab*avgnorm/norm_per_particle[im])
		'''
'''  Not used anywhere?  07/29/2015  PAP12
def prepare_recons_ctf_fftvol(data, snr, symmetry, myid, main_node_half, pidlist, finfo=None, npad = 2, mpi_comm=None):
	pass#IMPORTIMPORTIMPORT from utilities import reduce_EMData_to_root
	pass#IMPORTIMPORTIMPORT from EMAN2 import Reconstructors
	pass#IMPORTIMPORTIMPORT from mpi import MPI_COMM_WORLD

	if mpi_comm == None:
		mpi_comm = MPI_COMM_WORLD

	nx = data[0].get_xsize()

	fftvol_half = EMData()
	weight_half = EMData()
	half_params = {"size":nx, "npad":npad, "snr":snr, "sign":1, "symmetry":symmetry, "fftvol":fftvol_half, "weight":weight_half}
	half = Reconstructors.get( "nn4_ctf", half_params )
	half.setup()

	for i in pidlist:
		xform_proj = data[i].get_attr( "xform.projection" )
		half.insert_slice(data[i], xform_proj )

	if not(finfo is None):
		finfo.write( "begin reduce half\n" )
		finfo.flush()

	reduce_EMData_to_root(fftvol_half, myid, main_node_half, mpi_comm)
	reduce_EMData_to_root(weight_half, myid, main_node_half, mpi_comm)

	return fftvol_half, weight_half
'''
def rec2D(  lines, idrange=None, snr=None ):
	""" Perform a 2D reconstruction on a set of 1D lines using nearest neighbouring reverse FFT algorithm.
		Input: a set of 1D lines
		Output: a 2D image
	"""
	pass#IMPORTIMPORTIMPORT from EMAN2 import Reconstructors

	assert len(lines) > 0


	size = lines[0].get_xsize();

	if snr is None:
		params = {"size":size, "npad":4, "ndim":2}
	else: 
		params = {"size":size, "npad":4, "ndim":2, "snr":snr}

	r = EMAN2_cppwrap.Reconstructors.get("nn4", params)
	r.setup()

	if idrange is None:
		idrange = list(range( len(lines)))

	t = EMAN2_cppwrap.Transform()
	for i in idrange:
		r.insert_slice( lines[i], t )

	return r.finish(True)


def recons3d_4nn(stack_name, list_proj=[], symmetry="c1", npad=4, snr=None, weighting=1, varsnr=False, xysize=-1, zsize = -1):
	"""
	Perform a 3-D reconstruction using Pawel's FFT Back Projection algorithm.

	Input:
		stack_name - name of the file with projection data.

		list_proj -  list of projections to be used in the reconstruction

		symmetry - Point group of the target molecule (defaults to "C1")

		npad - 

		Angles and shifts are passed in the file header as set_attr. Keywords are phi, theta, psi, sx, sy

		Return:  3D reconstructed volume image

		Usage:
			vol = recons3d_4nn(filepattern, list_proj, symmetry)
	"""
	pass#IMPORTIMPORTIMPORT import types
	pass#IMPORTIMPORTIMPORT from EMAN2 import Reconstructors

	if list_proj == []:
		if type(stack_name) == bytes: nima = EMAN2_cppwrap.EMUtil.get_image_count(stack_name)
		else : nima = len(stack_name)
		list_proj = list(range(nima)) 
	# read first image to determine the size to use
	if type(stack_name) == bytes:
		proj = EMAN2_cppwrap.EMData()
		proj.read_image(stack_name, list_proj[0])
	else:    proj = stack_name[list_proj[0]].copy()

	size = proj.get_xsize()
	# sanity check -- image must be square
	if size != proj.get_ysize():
		global_def.ERROR("input data has to be square","recons3d_4nn",1)

	# reconstructor
	fftvol = EMAN2_cppwrap.EMData()
	weight = EMAN2_cppwrap.EMData()
	params = {"npad":npad, "symmetry":symmetry, "weighting":weighting, "fftvol":fftvol, "weight":weight}
	if ( xysize == -1 and zsize == -1 ):
		params["size"] = size
		if snr != None:
			params["snr"] = snr
			#params["varsnr"] = int(varsnr)
		r = EMAN2_cppwrap.Reconstructors.get("nn4", params)
	else:
		if ( xysize != -1 and zsize != -1):
			rx = float(xysize)/size
			ry = float(xysize)/size
			rz = float(zsize)/size
		elif( xysize != -1):
			rx = float(xysize)/size
			ry = float(xysize)/size
			rz = 1.0
		else:
			rx = 1.0
			ry = 1.0
			rz = float(zsize)/size

		if snr is None:
			params["sizeprojection"] = size
			params["xratio"] = rx
			params["yratio"] = ry
			params["zratio"] = rz
		else:
			params["sizeprojection"] = size
			params["snr"] = snr
			params["varsnr"] = int(varsnr)
			params["xratio"] = rx
			params["yratio"] = ry
			params["zratio"] = rz	
		r = EMAN2_cppwrap.Reconstructors.get("nn4_rect", params)

	r.setup()

	if type(stack_name) == bytes:
		for i in range(len(list_proj)):
			proj.read_image(stack_name, list_proj[i])
			# horatio active_refactoring Jy51i1EwmLD4tWZ9_00000_1
			# active = proj.get_attr_default('active', 1)
			# if active == 1:
			# 	insert_slices(r, proj)
			insert_slices(r, proj)
	else:
		for i in list_proj:
			# horatio active_refactoring Jy51i1EwmLD4tWZ9_00000_1
			# active = stack_name[i].get_attr_default('active', 1)
			# if active == 1:
			# 	insert_slices(r, stack_name[i])
			insert_slices(r, stack_name[i])

	dummy = r.finish(True)
	return fftvol


def recons3d_4nnw_MPI(myid, prjlist, bckgdata, snr = 1.0, sign=1, symmetry="c1", finfo=None, npad=2, xysize=-1, zsize=-1, mpi_comm=None, smearstep = 0.0, fsc = None):
	"""
		recons3d_4nn_ctf - calculate CTF-corrected 3-D reconstruction from a set of projections using three Eulerian angles, two shifts, and CTF settings for each projeciton image
		Input
			stack: name of the stack file containing projection data, projections have to be squares
			prjlist: list of projections to be included in the reconstruction or image iterator
			bckgdata = [get_im("tsd.hdf"),read_text_file("data_stamp.txt")]
			snr: Signal-to-Noise Ratio of the data 
			sign: sign of the CTF 
			symmetry: point-group symmetry to be enforced, each projection will enter the reconstruction in all symmetry-related directions.
	"""
	pass#IMPORTIMPORTIMPORT from utilities  import reduce_EMData_to_root, pad
	pass#IMPORTIMPORTIMPORT from EMAN2      import Reconstructors
	pass#IMPORTIMPORTIMPORT from utilities  import iterImagesList, set_params_proj, model_blank
	pass#IMPORTIMPORTIMPORT from mpi        import MPI_COMM_WORLD
	pass#IMPORTIMPORTIMPORT import types

	if mpi_comm == None:
		mpi_comm = mpi.MPI_COMM_WORLD

	if type(prjlist) == list:
		prjlist = utilities.iterImagesList(prjlist)
	if not prjlist.goToNext():
		global_def.ERROR("empty input list","recons3d_4nnw_MPI",1)
	imgsize = prjlist.image().get_xsize()
	if prjlist.image().get_ysize() != imgsize:
		imgsize = max(imgsize, prjlist.image().get_ysize())
		dopad = True
	else:
		dopad = False
	prjlist.goToPrev()

	#  Do the FSC shtick.
	bnx     = imgsize*npad//2+1
	if  fsc:
		pass#IMPORTIMPORTIMPORT from math import sqrt
		pass#IMPORTIMPORTIMPORT from utilities import reshape_1d
		t = [0.0]*len(fsc)
		for i in range(len(fsc)):
			t[i] = min(max(fsc[i],0.0), 0.999)
		t = utilities.reshape_1d(t,len(t),npad*len(t))
		refvol = utilities.model_blank(bnx,1,1,0.0)
		for i in range(len(fsc)):  refvol.set_value_at(i,t[i])
	else:
		refvol = utilities.model_blank(bnx,1,1,1.0)
	refvol.set_attr("fudge", 1.0)

	fftvol = EMAN2_cppwrap.EMData()
	weight = EMAN2_cppwrap.EMData()

	if( smearstep > 0.0 ):
		#if myid == 0:  print "  Setting smear in prepare_recons_ctf"
		ns = 1
		smear = []
		for j in range(-ns,ns+1):
			if( j != 0):
				for i in range(-ns,ns+1):
					for k in range(-ns,ns+1):
						smear += [i*smearstep,j*smearstep,k*smearstep,1.0]
		# Deal with theta = 0.0 cases
		prj = []
		for i in range(-ns,ns+1):
			for k in range(-ns,ns+1):
				prj.append(i+k)
		for i in range(-2*ns,2*ns+1,1):
			smear += [i*smearstep,0.0,0.0,float(prj.count(i))]
		#if myid == 0:  print "  Smear  ",smear
		fftvol.set_attr("smear", smear)

	if (xysize == -1 and zsize == -1 ):
		params = {"size":imgsize, "npad":npad, "snr":snr, "sign":sign, "symmetry":symmetry, "refvol":refvol, "fftvol":fftvol, "weight":weight}
		r = EMAN2_cppwrap.Reconstructors.get( "nn4_ctfw", params )
	else:
		if ( xysize != -1 and zsize != -1):
			rx = float(xysize)/imgsize
			ry = float(xysize)/imgsize
			rz = float(zsize)/imgsize
		elif( xysize != -1):
			rx = float(xysize)/imgsize
			ry = float(xysize)/imgsize
			rz = 1.0
		else:
			rx = 1.0
			ry = 1.0
			rz = float(zsize)/imgsize
		#  There is an error here with sizeprojection  PAP 10/22/2014
		params = {"size":sizeprojection, "npad":npad, "snr":snr, "sign":sign, "symmetry":symmetry, "fftvol":fftvol, "weight":weight,"xratio":rx,"yratio":ry,"zratio":rz}
		r = EMAN2_cppwrap.Reconstructors.get( "nn4_ctf_rect", params )
	r.setup()

	
	#from utilities import model_blank, get_im, read_text_file
	#bckgdata = [get_im("tsd.hdf"),read_text_file("data_stamp.txt")]

	nnx = bckgdata[0].get_xsize()
	nny = bckgdata[0].get_ysize()
	bckgnoise = []
	for i in range(nny):
		prj = utilities.model_blank(nnx)
		for k in range(nnx):  prj[k] = bckgdata[0].get_value_at(k,i)
		bckgnoise.append(prj)

	datastamp = bckgdata[1]
	if not (finfo is None): nimg = 0
	while prjlist.goToNext():
		prj = prjlist.image()
		try:
			stmp = nnx/0
			stmp = prj.get_attr("ptcl_source_image")
		except:
			try:
				stmp = prj.get_attr("ctf")
				stmp = round(stmp.defocus,4)
			except:
				global_def.ERROR("Either ptcl_source_image or ctf has to be present in the header.","recons3d_4nnw_MPI",1, myid)
		try:
			indx = datastamp.index(stmp)
		except:
			global_def.ERROR("Problem with indexing ptcl_source_image.","recons3d_4nnw_MPI",1, myid)

		if dopad:
			prj = utilities.pad(prj, imgsize, imgsize, 1, "circumference")

		prj.set_attr("bckgnoise", bckgnoise[indx])
		insert_slices(r, prj)
		if not (finfo is None):
			nimg += 1
			finfo.write(" %4d inserted\n" %(nimg) )
			finfo.flush()
	del utilities.pad
	if not (finfo is None): 
		finfo.write( "begin reduce\n" )
		finfo.flush()
		
	utilities.reduce_EMData_to_root(fftvol, myid, comm=mpi_comm)
	utilities.reduce_EMData_to_root(weight, myid, comm=mpi_comm)

	if not (finfo is None): 
		finfo.write( "after reduce\n" )
		finfo.flush()

	if myid == 0 :
		dummy = r.finish(True)
	else:
		pass#IMPORTIMPORTIMPORT from utilities import model_blank
		if ( xysize == -1 and zsize == -1 ):
			fftvol = utilities.model_blank(imgsize, imgsize, imgsize)
		else:
			if zsize == -1:
				fftvol = utilities.model_blank(xysize, xysize, imgsize)
			elif xysize == -1:
				fftvol = utilities.model_blank(imgsize, imgsize, zsize)
			else:
				fftvol = utilities.model_blank(xysize, xysize, zsize)
	return fftvol



"""Multiline Comment2"""
"""Multiline Comment3"""

def recons3d_4nnf_MPI(myid, list_of_prjlist, bckgdata, snr = 1.0, sign=1, symmetry="c1", finfo=None, npad=2, mpi_comm=None, smearstep = 0.0):
	"""
		recons3d_4nn_ctf - calculate CTF-corrected 3-D reconstruction from a set of projections using three Eulerian angles, two shifts, and CTF settings for each projeciton image
		Input
			list_of_prjlist: list of lists of projections to be included in the reconstruction
			bckgdata = [get_im("tsd.hdf"),read_text_file("data_stamp.txt")]
			snr: Signal-to-Noise Ratio of the data 
			sign: sign of the CTF
			symmetry: point-group symmetry to be enforced, each projection will enter the reconstruction in all symmetry-related directions.
	"""
	pass#IMPORTIMPORTIMPORT from utilities  import reduce_EMData_to_root, random_string, get_im
	pass#IMPORTIMPORTIMPORT from EMAN2      import Reconstructors
	pass#IMPORTIMPORTIMPORT from utilities  import model_blank
	pass#IMPORTIMPORTIMPORT from mpi        import MPI_COMM_WORLD, mpi_barrier
	pass#IMPORTIMPORTIMPORT import types
	pass#IMPORTIMPORTIMPORT from statistics import fsc
	pass#IMPORTIMPORTIMPORT import datetime
	
	if mpi_comm == None:
		mpi_comm = mpi.MPI_COMM_WORLD

	imgsize = list_of_prjlist[0].get_xsize()
	
	if( smearstep > 0.0 ):
		#if myid == 0:  print "  Setting smear in prepare_recons_ctf"
		ns = 1
		smear = []
		for j in range(-ns,ns+1):
			if( j != 0):
				for i in range(-ns,ns+1):
					for k in range(-ns,ns+1):
						smear += [i*smearstep,j*smearstep,k*smearstep,1.0]
		# Deal with theta = 0.0 cases
		prj = []
		for i in range(-ns,ns+1):
			for k in range(-ns,ns+1):
				prj.append(i+k)
		for i in range(-2*ns,2*ns+1,1):
			smear += [i*smearstep,0.0,0.0,float(prj.count(i))]
		#if myid == 0:  print "  Smear  ",smear

	#from utilities import model_blank, get_im, read_text_file
	#bckgdata = [get_im("tsd.hdf"),read_text_file("data_stamp.txt")]

	nnx = bckgdata[0].get_xsize()
	nny = bckgdata[0].get_ysize()
	bckgnoise = []
	for i in range(nny):
		prj = utilities.model_blank(nnx)
		for k in range(nnx):  prj[k] = bckgdata[0].get_value_at(k,i)
		bckgnoise.append(prj)

	datastamp = bckgdata[1]

	#  Do the FSC shtick.
	bnx     = imgsize*npad//2+1
	refvol = utilities.model_blank(bnx)  # fill fsc with zeroes so the first reconstruction is done using simple Wiener filter.
	refvol.set_attr("fudge", 1.0)

	results_list = []
	fftvol_file =[]
	weight_file = []

	for iset in range(2):
		if not (finfo is None): nimg = 0

		fftvol = EMAN2_cppwrap.EMData()
		weight = EMAN2_cppwrap.EMData()
		if( smearstep > 0.0 ):  fftvol.set_attr("smear", smear)
	
		params = {"size":imgsize, "npad":npad, "snr":snr, "sign":sign, "symmetry":symmetry, "refvol":refvol, "fftvol":fftvol, "weight":weight}
		r = EMAN2_cppwrap.Reconstructors.get( "nn4_ctfw", params )
		r.setup()

		for image in list_of_prjlist[iset]:
			try:
				#raise ValueError('A very specific thing happened')
				stmp = image.get_attr("ptcl_source_image")
			except:
				try:
					stmp = image.get_attr("ctf")
					stmp = round(stmp.defocus,4)
				except:
					global_def.ERROR("Either ptcl_source_image or ctf has to be present in the header.","recons3d_4nnw_MPI",1, myid)
			try:
				indx = datastamp.index(stmp)
			except:
				global_def.ERROR("Problem with indexing ptcl_source_image.","recons3d_4nnf_MPI",1, myid)
	
			image.set_attr("bckgnoise", bckgnoise[indx])
			insert_slices(r, image)
			if not (finfo is None):
				nimg += 1
				finfo.write(" %4d inserted\n" %(nimg) )
				finfo.flush()

		if not (finfo is None): 
			finfo.write( "begin reduce\n" )
			finfo.flush()
	
		utilities.reduce_EMData_to_root(fftvol, myid, main_node, comm=mpi_comm)
		utilities.reduce_EMData_to_root(weight, myid, main_node, comm=mpi_comm)
		
		if not (finfo is None): 
			finfo.write( "after reduce\n" )
			finfo.flush()

		if myid == 0:
			"""Multiline Comment4"""
			dummy = r.finish(True)
			results_list.append(fftvol)
			#if(iset == 0):  fftvol.write_image(results_list[-1])

		mpi.mpi_barrier(mpi_comm)

	if myid == 0:
		fourier_shell_correlation = statistics.fsc(results_list[0], results_list[1], 1.0)[1]
		"""Multiline Comment5"""
	mpi.mpi_barrier(mpi_comm)
	if myid == 0:
		return results_list[0], results_list[1], fourier_shell_correlation
	else:
		return None, None, None

def recons3d_4nnfs_MPI(myid, main_node, prjlist, upweighted = True, finfo=None, mpi_comm=None, smearstep = 0.0, CTF = True, compensate = False, target_size=-1):
	"""
		recons3d_4nn_ctf - calculate CTF-corrected 3-D reconstruction from a set of projections using three Eulerian angles, two shifts, and CTF settings for each projeciton image
		Input
			list_of_prjlist: list of lists of projections to be included in the reconstruction
	"""
	pass#IMPORTIMPORTIMPORT from utilities  import reduce_EMData_to_root, random_string, get_im
	pass#IMPORTIMPORTIMPORT from EMAN2      import Reconstructors
	pass#IMPORTIMPORTIMPORT from utilities  import model_blank
	pass#IMPORTIMPORTIMPORT from filter		import filt_table
	pass#IMPORTIMPORTIMPORT from mpi        import MPI_COMM_WORLD, mpi_barrier
	pass#IMPORTIMPORTIMPORT import types
	pass#IMPORTIMPORTIMPORT from statistics import fsc
	pass#IMPORTIMPORTIMPORT import datetime
	pass#IMPORTIMPORTIMPORT from reconstruction import insert_slices_pdf
	
	if mpi_comm == None:
		mpi_comm = mpi.MPI_COMM_WORLD
	imgsize = prjlist[0].get_ysize()  # It can be Fourier, so take y-size
	"""Multiline Comment6"""
	#from utilities import model_blank, get_im, read_text_file
	#bckgdata = [get_im("tsd.hdf"),read_text_file("data_stamp.txt")]

	
	"""Multiline Comment7"""
	"""Multiline Comment8"""
	#datastamp = bckgdata[1]
	"""Multiline Comment9"""

	refvol = utilities.model_blank(target_size)
	refvol.set_attr("fudge", 1.0)


	if CTF: do_ctf = 1
	else:   do_ctf = 0
	if not (finfo is None): nimg = 0

	fftvol = EMAN2_cppwrap.EMData()
	weight = EMAN2_cppwrap.EMData()
	#if( smearstep > 0.0 ):  fftvol.set_attr("smear", smear)


	pass#IMPORTIMPORTIMPORT from utilities import info
	params = {"size":target_size, "npad":2, "snr":1.0, "sign":1, "symmetry":"c1", "refvol":refvol, "fftvol":fftvol, "weight":weight, "do_ctf": do_ctf}
	r = EMAN2_cppwrap.Reconstructors.get( "nn4_ctfw", params )
	r.setup()
	for image in prjlist:
		if not upweighted: insert_slices_pdf(r, filter.filt_table(image, image.get_attr("bckgnoise")) )
		else:              insert_slices_pdf(r, image)

	if not (finfo is None): 
		finfo.write( "begin reduce\n" )
		finfo.flush()

	utilities.reduce_EMData_to_root(fftvol, myid, main_node, comm=mpi_comm)
	utilities.reduce_EMData_to_root(weight, myid, main_node, comm=mpi_comm)

	if not (finfo is None): 
		finfo.write( "after reduce\n" )
		finfo.flush()


	if myid == main_node:
		dummy = r.finish(compensate)
	mpi.mpi_barrier(mpi_comm)

	if myid == main_node: return fftvol, weight, refvol
	else: return None, None, None

def recons3d_4nnstruct_MPI(myid, main_node, prjlist, paramstructure, refang, delta, upweighted = True, mpi_comm=None, CTF = True, target_size=-1, avgnorm = 1.0, norm_per_particle = None):
	"""
		recons3d_4nn_ctf - calculate CTF-corrected 3-D reconstruction from a set of projections using three Eulerian angles, two shifts, and CTF settings for each projeciton image
		Input
			list_of_prjlist: list of lists of projections to be included in the reconstruction
	"""
	pass#IMPORTIMPORTIMPORT from utilities  import reduce_EMData_to_root, random_string, get_im, findall
	pass#IMPORTIMPORTIMPORT from EMAN2      import Reconstructors
	pass#IMPORTIMPORTIMPORT from utilities  import model_blank
	pass#IMPORTIMPORTIMPORT from filter		import filt_table
	pass#IMPORTIMPORTIMPORT from mpi        import MPI_COMM_WORLD, mpi_barrier
	pass#IMPORTIMPORTIMPORT import types
	pass#IMPORTIMPORTIMPORT import datetime
	
	if mpi_comm == None: mpi_comm = mpi.MPI_COMM_WORLD

	refvol = utilities.model_blank(target_size)
	refvol.set_attr("fudge", 1.0)


	if CTF: do_ctf = 1
	else:   do_ctf = 0

	fftvol = EMAN2_cppwrap.EMData()
	weight = EMAN2_cppwrap.EMData()

	pass#IMPORTIMPORTIMPORT from utilities import info
	params = {"size":target_size, "npad":2, "snr":1.0, "sign":1, "symmetry":"c1", "refvol":refvol, "fftvol":fftvol, "weight":weight, "do_ctf": do_ctf}
	r = EMAN2_cppwrap.Reconstructors.get( "nn4_ctfw", params )
	r.setup()
	
	if norm_per_particle == None: norm_per_particle = len(prjlist)*[1.0]

	for im in range(len(prjlist)):
		#  parse projection structure, generate three lists:
		#  [ipsi+iang], [ishift], [probability]
		#  Number of orientations for a given image
		numbor = len(paramstructure[im][2])
		ipsiandiang = [ paramstructure[im][2][i][0]/1000  for i in range(numbor) ]
		allshifts   = [ paramstructure[im][2][i][0]%1000  for i in range(numbor) ]
		probs       = [ paramstructure[im][2][i][1] for i in range(numbor) ]
		#  Find unique projection directions
		tdir = list(set(ipsiandiang))
		bckgn = prjlist[im][0].get_attr("bckgnoise")
		#  For each unique projection direction:
		for ii in range(len(tdir)):
			#  Find the number of times given projection direction appears on the list, it is the number of different shifts associated with it.
			lshifts = utilities.findall(tdir[ii], ipsiandiang)
			toprab  = 0.0
			for ki in range(len(lshifts)):  toprab += probs[lshifts[ki]]
			recdata = EMAN2_cppwrap.Util.mult_scalar(prjlist[im][allshifts[lshifts[0]]], probs[lshifts[0]]/toprab)
			recdata.set_attr_dict({"padffted":1, "is_complex":0})
			for ki in range(1,len(lshifts)):
				EMAN2_cppwrap.Util.add_img(recdata, EMAN2_cppwrap.Util.mult_scalar(prjlist[im][allshifts[lshifts[ki]]], probs[lshifts[ki]]/toprab))
			recdata.set_attr_dict({"padffted":1, "is_complex":1})
			if not upweighted:  recdata = filter.filt_table(recdata, bckgn )
			recdata.set_attr("bckgnoise", bckgn )
			ipsi = tdir[ii]%100000
			iang = tdir[ii]/100000
			r.insert_slice( recdata, EMAN2_cppwrap.Transform({"type":"spider","phi":refang[iang][0],"theta":refang[iang][1],"psi":refang[iang][2]+ipsi*delta}), toprab*avgnorm/norm_per_particle[im])
	#  clean stuff
	del bckgn, recdata, tdir, ipsiandiang, allshifts, probs


	utilities.reduce_EMData_to_root(fftvol, myid, main_node, comm=mpi_comm)
	utilities.reduce_EMData_to_root(weight, myid, main_node, comm=mpi_comm)

	if myid == main_node:
		dummy = r.finish(True)
	mpi.mpi_barrier(mpi_comm)

	if myid == main_node: return fftvol, weight, refvol
	else: return None, None, None

def recons3d_4nnstruct_MPI_test(myid, main_node, prjlist, paramstructure, refang, parameters, delta, upweighted = True, mpi_comm=None, CTF = True, target_size=-1, avgnorm = 1.0, norm_per_particle = None):
	"""
		recons3d_4nn_ctf - calculate CTF-corrected 3-D reconstruction from a set of projections using three Eulerian angles, two shifts, and CTF settings for each projeciton image
		Input
			list_of_prjlist: list of lists of projections to be included in the reconstruction
	"""
	pass#IMPORTIMPORTIMPORT from utilities  import reduce_EMData_to_root, random_string, get_im, findall
	pass#IMPORTIMPORTIMPORT from EMAN2      import Reconstructors
	pass#IMPORTIMPORTIMPORT from utilities  import model_blank
	pass#IMPORTIMPORTIMPORT from filter		import filt_table
	pass#IMPORTIMPORTIMPORT from mpi        import MPI_COMM_WORLD, mpi_barrier
	pass#IMPORTIMPORTIMPORT import types
	pass#IMPORTIMPORTIMPORT from statistics import fsc
	pass#IMPORTIMPORTIMPORT import datetime
	pass#IMPORTIMPORTIMPORT from reconstruction import insert_slices_pdf
	
	if mpi_comm == None: mpi_comm = mpi.MPI_COMM_WORLD

	imgsize = prjlist[0][0].get_ysize()  # It can be Fourier, so take y-size

	refvol = utilities.model_blank(target_size)
	refvol.set_attr("fudge", 1.0)


	if CTF: do_ctf = 1
	else:   do_ctf = 0

	fftvol = EMAN2_cppwrap.EMData()
	weight = EMAN2_cppwrap.EMData()

	pass#IMPORTIMPORTIMPORT from utilities import info
	params = {"size":target_size, "npad":2, "snr":1.0, "sign":1, "symmetry":"c1", "refvol":refvol, "fftvol":fftvol, "weight":weight, "do_ctf": do_ctf}
	r = EMAN2_cppwrap.Reconstructors.get( "nn4_ctfw", params )
	r.setup()
	
	if norm_per_particle == None: norm_per_particle = len(prjlist)*[1.0]

	for im in range(len(prjlist)):
		#  parse projection structure, generate three lists:
		#  [ipsi+iang], [ishift], [probability]
		#  Number of orientations for a given image
		bckgn = prjlist[im][0].get_attr("bckgnoise")
		recdata = EMAN2_cppwrap.Util.mult_scalar(prjlist[im][0], parameters[im][5])
		recdata.set_attr_dict({"padffted":1, "is_complex":1})
		pass#IMPORTIMPORTIMPORT from fundamentals import fshift
		recdata = fundamentals.fshift(recdata, parameters[im][3], parameters[im][4])
		if not upweighted:  recdata = filter.filt_table(recdata, bckgn )
		r.insert_slice( recdata, EMAN2_cppwrap.Transform({"type":"spider","phi":parameters[im][0],"theta":parameters[im][1],"psi":parameters[im][2]}), 1.0)
		"""Multiline Comment10"""
	#  clean stuff
	del bckgn, recdata


	utilities.reduce_EMData_to_root(fftvol, myid, main_node, comm=mpi_comm)
	utilities.reduce_EMData_to_root(weight, myid, main_node, comm=mpi_comm)

	if myid == main_node:
		dummy = r.finish(True)
	mpi.mpi_barrier(mpi_comm)

	if myid == main_node: return fftvol, weight, refvol
	else: return None, None, None


def recons3d_nn_SSNR(stack_name,  mask2D = None, ring_width=1, npad =1, sign=1, symmetry="c1", CTF = False, random_angles = 0):

	"""
	Perform a 3-D reconstruction using nearest neighbor interpolation and 
	calculate 3D spectral signal-to-noise ratio (SSNR)	   
	Input : stack_name - Name of the file with projection data.
		CTF        - 
	        symmetry   - Point group of the target molecule (default "c1")
		npad       - Times of padding applied, default is 1
		sign       - Currently not used, may be used in the future
		w          - The thickness of the shell, default is 1
		filename   - The filename in which you can save the SSNR results 
	Return: reconstructed 3D SSNR volume
        Usage : vol = recons3d_nn_SSNR(stack_name, CTF, symmetry, npad, snr, sign, w, filename])
	CTF true:
	variance at one voxel  = Gamma^2d->3d [ |F_k^2D|^2   +  ctf^2*|P^2D->3D(F^3D)|^2 -
	          -2*Real(conj(F_k^2D)*ctf*P^2D->3D(F^3D))]	
	signal  at one voxel   = Gamma^2d->3d [ |F_k^2D|^2  ]
	SSNR =  sum_rot [ wght*signal/Kn ]/sum_rot[ wght*variance /(Kn(Kn-1))] -1
	Notice: wght is always turned on during SSNR calculation.
	"""
	pass#IMPORTIMPORTIMPORT import types
	pass#IMPORTIMPORTIMPORT from EMAN2 import Reconstructors

	# Yang add a safety on 05/22/07
	if type(stack_name) == bytes: nima = EMAN2_cppwrap.EMUtil.get_image_count(stack_name)
	else :                                   nima = len(stack_name)
	# read first image to determine the size to use
	if type(stack_name) == bytes:
		proj = EMAN2_cppwrap.EMData()
		proj.read_image(stack_name, 0)
	else:    
		proj = stack_name[0].copy()
	#active = proj.get_attr('active')
	size   = proj.get_xsize()
	# sanity check -- image must be square
	if size != proj.get_ysize(): global_def.ERROR("input data has to be square","recons3d_nn_SSNR",1)
	# reconstructor
	SSNR = EMAN2_cppwrap.EMData()
	fftvol = EMAN2_cppwrap.EMData()
	weight = EMAN2_cppwrap.EMData()
	weight2 = EMAN2_cppwrap.EMData()
	vol_ssnr = EMAN2_cppwrap.EMData()
	params = {"size":size, "npad":npad, "symmetry":symmetry, "SSNR":SSNR, "w":ring_width, "fftvol":fftvol, "weight":weight, "weight2":weight2, "vol_ssnr":vol_ssnr}
	if CTF:
		weight3 = EMAN2_cppwrap.EMData()
		params["sign"] = sign
		params["weight3"] = weight3
		r = EMAN2_cppwrap.Reconstructors.get("nnSSNR_ctf", params)
	else:
		r = EMAN2_cppwrap.Reconstructors.get("nnSSNR", params)
	r.setup()

	for i in range(nima):
		if type(stack_name) == bytes:
			proj.read_image(stack_name, i)
		else:
			proj = stack_name[i]
		# horatio active_refactoring Jy51i1EwmLD4tWZ9_00000_1
		# active = proj.get_attr_default('active', 1)
		# if(active == 1):
		pass#IMPORTIMPORTIMPORT import numpy.random
		if(random_angles  == 2):
			pass#IMPORTIMPORTIMPORT from  random import  random
			phi    = 360.0*numpy.random.random()
			theta  = 180.0*numpy.random.random()
			psi    = 360.0*numpy.random.random()
			xform_proj = EMAN2_cppwrap.Transform( {"type":"spider", "phi":phi, "theta":theta, "psi":psi} )
		elif(random_angles  == 3):
			pass#IMPORTIMPORTIMPORT from  random import  random
			phi    = 360.0*numpy.random.random()
			theta  = 180.0*numpy.random.random()
			psi    = 360.0*numpy.random.random()
			tx     = 6.0*(numpy.random.random() - 0.5)
			ty     = 6.0*(numpy.random.random() - 0.5)
			xform_proj = EMAN2_cppwrap.Transform( {"type":"spider", "phi":phi, "theta":theta, "psi":psi, "tx":tx, "ty":ty} )
		elif(random_angles  == 1):
			pass#IMPORTIMPORTIMPORT from  random import  random
			old_xform_proj = proj.get_attr( "xform.projection" )
			dict = old_xform_proj.get_rotation( "spider" )
			dict["psi"] = 360.0*numpy.random.random()
			xform_proj = EMAN2_cppwrap.Transform( dict )
		else:
			xform_proj = proj.get_attr( "xform.projection" )

		if mask2D:
			stats = EMAN2_cppwrap.Util.infomask(proj, mask2D, True)
			proj -= stats[0]
			proj *= mask2D
		r.insert_slice(proj, xform_proj)
		# horatio active_refactoring Jy51i1EwmLD4tWZ9_00000_1  END

	dummy = r.finish(True)
	outlist = [[] for i in range(6)]
	nn = SSNR.get_xsize()
	for i in range(1,nn): outlist[0].append((float(i)-0.5)/(float(nn-1)*2))
	for i in range(1,nn):
		if(SSNR(i,1,0) > 0.0):
			outlist[1].append(max(0.0,(SSNR(i,0,0)/SSNR(i,1,0)-1.)))      # SSNR
		else:
			outlist[1].append(0.0)
	for i in range(1,nn): outlist[2].append(SSNR(i,1,0)/SSNR(i,2,0))	          # variance
	for i in range(1,nn): outlist[3].append(SSNR(i,2,0))				  # number of points in the shell
	for i in range(1,nn): outlist[4].append(SSNR(i,3,0))				  # number of added Fourier points
	for i in range(1,nn): outlist[5].append(SSNR(i,0,0))				  # square of signal
	return [outlist, vol_ssnr]

class memory_store(object):
	def __init__(self, npad):
		self.m_npad = npad
		self.m_imgs = []

	def add_image(self, img):
		self.m_imgs.append(img)

	def get_image(self, id):
		return self.m_imgs[id]

def bootstrap_nn(proj_stack, volume_stack, list_proj, niter, media="memory", npad=4, symmetry="c1", output=-1, CTF=False, snr=1.0, sign=1, myseed=None ):
	pass#IMPORTIMPORTIMPORT from random import seed
	pass#IMPORTIMPORTIMPORT from random import randint
	pass#IMPORTIMPORTIMPORT from time   import time
	pass#IMPORTIMPORTIMPORT from sys    import stdout
	pass#IMPORTIMPORTIMPORT from utilities import set_ctf
	pass#IMPORTIMPORTIMPORT from EMAN2 import Reconstructors

	if(output == -1):
		pass#IMPORTIMPORTIMPORT import sys
		output=sys.stdout

	if not(myseed is None):
		random.seed(myseed) 

	nimages = len(list_proj)
	if nimages == 0 :
		print("empty list of projections input!")
		return None


	if media=="memory" :
		store = memory_store(npad)
	else :
		store = EMAN2_cppwrap.file_store(media,npad, 0, CTF)
		if not(output is None):
			output.flush()

	proj = EMAN2_cppwrap.EMData()
	proj.read_image(proj_stack,list_proj[0])

	size = proj.get_xsize()
	if size != proj.get_ysize():
		print("Image projections must be square!")
		return None

	overall_start = time.time()
	for i in range(niter):
		iter_start = time.time()
		mults = nimages*[0]
		for j in range(nimages):
			imgid = random.randint(0,nimages-1)
			mults[imgid]=mults[imgid]+1

		if CTF:
			params = {"size":size, "npad":npad, "symmetry":symmetry, "snr":snr, "sign":sign}
			r = EMAN2_cppwrap.Reconstructors.get("nn4_ctf", params);
		else:
			params = {"size":size, "npad":npad, "symmetry":symmetry, "snr":snr}
			r = EMAN2_cppwrap.Reconstructors.get("nn4", params);

		r.setup()
		if not(output is None):
			output.write( "Bootstrap volume %8d " % i )
			output.flush()

		store.restart()

		if not(output is None):
			output.write( "Inserting images " )
			output.flush()

		for j in range(nimages):
			if mults[j] > 0 :
				img_j = EMAN2_cppwrap.EMData()
				store.get_image( j, img_j );
				phi_j = img_j.get_attr( "phi" )
				tht_j = img_j.get_attr( "theta" )
				psi_j = img_j.get_attr( "psi" )
				tra_j = EMAN2_cppwrap.Transform( {"type":"spider", "phi":phi_j, "theta":tht_j, "psi":psi_j} )

				if CTF:
					cs = img_j.get_attr( "Cs" )
					pixel   = img_j.get_attr( "Pixel_size" )
					defocus = img_j.get_attr( "defocus" )
					voltage = img_j.get_attr( "voltage" )
					ampcont = img_j.get_attr( "amp_contrast" )
					bfactor = 0.0
					utilities.set_ctf( img_j, [defocus, cs, voltage, pixel, bfactor, ampcont] )

				r.insert_slice(img_j, tra_j, mults[j])

				#[mean,sigma,min,max]= Util.infomask(img_j, None, False)
				#output.write( "img %4d %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f %10.3f\n" % (j, mean, sigma, min, max, phi, theta, psi) )
				#output.flush()

		if not(output is None):
			output.write( "Finishing... " )
			output.flush( )

		vol = r.finish(True)

		if not(output is None):
			output.write( "Writing... " )
			output.flush()

		vol.write_image(volume_stack,i)

		if not(output is None):
			output.write( " done!" )
			output.write( " time %15.3f %15.3f \n" % (time.time()-iter_start,time.time()-overall_start) )
			output.flush()


def recons3d_em(projections_stack, max_iterations_count = 100, radius = -1, min_avg_abs_voxel_change = 0.01, use_weights = False, symmetry = "c1"):
	"""
	Reconstruction algorithm basing on the Expectation Maximization method
		projections_stack            -- file or list with projections
		max_iterations_count         -- stop criterion 
		min_avg_abs_voxel_change     -- stop criterion 
		use_weights                  -- true == multiply projections by extra weights
		symmetry                     -- type of symmetry
	#
	"""
	pass#IMPORTIMPORTIMPORT from time import clock
	pass#IMPORTIMPORTIMPORT from utilities import model_blank, model_circle, model_square
	pass#IMPORTIMPORTIMPORT from morphology import threshold_to_minval
	pass#IMPORTIMPORTIMPORT import types
	min_allowed_divisor = 0.0001

	if type(projections_stack) is bytes:
		projections = EMAN2_cppwrap.EMData.read_images(projections_stack)
	else:
		projections = projections_stack

	if len(projections) == 0:
		global_def.ERROR("Stack of projections cannot be empty", "recons3d_em")

	nx = projections[0].get_xsize()
	if (projections[0].get_ysize() != nx) or (projections[0].get_zsize() != 1):
		global_def.ERROR("This procedure works only for square images", "recons3d_em")

	if radius < 0:  radius = nx // 2 - 1
	sphere2D = utilities.model_circle(radius, nx, nx)   
	sphere3D = utilities.model_circle(radius, nx, nx, nx)
	solution = utilities.model_blank(nx, nx, nx)
	a = utilities.model_blank(nx, nx, nx) # normalization volume
	e2D = utilities.model_square(nx, nx, nx)
	sphere3D_volume = utilities.model_blank(nx,nx,nx).cmp("lod",sphere3D,{"negative":0,"normalize":0})
	#print "Parameters:  size=%d  radius=%d  projections_count=%d  max_iterations_count=%d min_avg_abs_voxel_change=%f" % (
	#					nx, radius, len(projections), max_iterations_count, min_avg_abs_voxel_change )

	# ----- create initial solution, calculate weights and normalization image (a)
	projections_angles = []  # list of lists of angles
	projections_data   = []  # list of lists of projections' images with weights
	for proj in projections:
		angles = [] # list of angles
		data = []   # list of projections' images with weights
		RA = proj.get_attr( "xform.projection" )
		EMAN2_cppwrap.Util.mul_img( proj, sphere2D )
		for j in range(RA.get_nsym(symmetry)):
			angdict = RA.get_sym_sparx(symmetry,j).get_rotation("spider") 
			angles.append( [angdict["phi"], angdict["theta"], angdict["psi"]] )
			chao_params = {"anglelist":angles[j],"radius":radius}
			EMAN2_cppwrap.Util.add_img( solution, proj.backproject("chao", chao_params) )
			EMAN2_cppwrap.Util.add_img( a, e2D.backproject("chao", chao_params) )
			if use_weights:
				proj3Dsphere = sphere3D.project("chao", chao_params)
				EMAN2_cppwrap.Util.mul_scalar( proj3Dsphere, 1.0 / EMAN2_cppwrap.Util.infomask(proj3Dsphere, None, True)[3] )
				EMAN2_cppwrap.Util.mul_img( proj, proj3Dsphere )
			data.append(proj)
		projections_angles.append(angles)
		projections_data.append(data)
	a = morphology.threshold_to_minval(a, min_allowed_divisor)  # make sure that voxels' values are not too small (image a is divisior)
	EMAN2_cppwrap.Util.mul_img( solution, sphere3D )
	EMAN2_cppwrap.Util.div_img( solution, a )
	#print "Projections loading COMPLETED"
	# ----- iterations
	prev_avg_absolute_voxel_change = 999999999.0
	time_projection = 0.0
	time_backprojection = 0.0
	time_iterations = time.clock()
	for iter_no in range(max_iterations_count):
		q = utilities.model_blank(nx, nx, nx)
		for i in range(len(projections_angles)):
			for j in range(len(projections_angles[i])):
				chao_params = {"anglelist":projections_angles[i][j],"radius":radius}
				time_start = time.clock()
				w = solution.project("chao", chao_params)
				time_projection += time.clock() - time_start
				p = projections_data[i][j] / morphology.threshold_to_minval(w, min_allowed_divisor)
				time_start = time.clock()
				q += p.backproject("chao", chao_params)
				time_backprojection += time.clock() - time_start
		EMAN2_cppwrap.Util.div_img( q, a )
		EMAN2_cppwrap.Util.mul_img( q, solution ) # q <- new solution  
		avg_absolute_voxel_change = q.cmp("lod",solution,{"mask":sphere3D,"negative":0,"normalize":0}) / sphere3D_volume
		if avg_absolute_voxel_change > prev_avg_absolute_voxel_change:
			#print "Finish and return last good solution"
			break
		prev_avg_absolute_voxel_change = avg_absolute_voxel_change
		solution = q
		#print "Iteration ", iter_no, ",  avg_abs_voxel_change=", avg_absolute_voxel_change 
		if min_avg_abs_voxel_change > avg_absolute_voxel_change:
			break
	time_iterations = time.clock() - time_iterations
	# ----- return solution and exit
	#print "Times: iterations=", time_iterations, "  project=", time_projection, "  backproject=", time_backprojection
	return solution


def recons3d_em_MPI(projections_stack, output_file, max_iterations_count = 100, radius = -1, min_norm_absolute_voxel_change = 0.01, use_weights = False, symmetry = "c1", min_norm_squared_voxel_change = 0.0001):
	"""
	Reconstruction algorithm basing on the Expectation Maximization method.
		projections_stack              -- file or list with projections
		max_iterations_count           -- stop criterion 
		min_norm_absolute_voxel_change -- stop criterion (set -1 to switch off) 
		min_norm_squared_voxel_change  -- stop criterion (set -1 to switch off)
		use_weights                    -- true == multiply projections by extra weights
		symmetry                       -- type of symmetry
	#
	"""
	pass#IMPORTIMPORTIMPORT from time import clock
	pass#IMPORTIMPORTIMPORT from utilities import model_blank, model_circle, model_square, circumference
	pass#IMPORTIMPORTIMPORT from morphology import threshold_to_minval
	pass#IMPORTIMPORTIMPORT import types
	pass#IMPORTIMPORTIMPORT from string import replace
	pass#IMPORTIMPORTIMPORT from mpi import mpi_comm_size, mpi_comm_rank, MPI_COMM_WORLD
	pass#IMPORTIMPORTIMPORT from utilities import reduce_EMData_to_root, bcast_EMData_to_all, bcast_number_to_all, send_EMData, recv_EMData
	min_allowed_divisor = 0.0001

	mpi_n = mpi.mpi_comm_size(mpi.MPI_COMM_WORLD)
	mpi_r = mpi.mpi_comm_rank(mpi.MPI_COMM_WORLD)

	# ----- read projections 
	if type(projections_stack) is bytes:
		all_projs_count = EMAN2_cppwrap.EMUtil.get_image_count(projections_stack)
	else:
		all_projs_count = len(projections_stack)

	if all_projs_count < mpi_n:
		global_def.ERROR("Number of projections cannot be less than number of MPI processes", "recons3d_em")

	projs_begin = (mpi_r * all_projs_count) // mpi_n
	projs_end = ((mpi_r+1) * all_projs_count) // mpi_n

	if type(projections_stack) is bytes:
		projections = EMAN2_cppwrap.EMData.read_images(projections_stack, list(range(projs_begin,projs_end)))
	else:
		#projections = projections_stack[projs_begin:projs_end]
		projections = projections_stack
	# ----------------------------------------------

	nx = projections[0].get_xsize()
	if (projections[0].get_ysize() != nx) or (projections[0].get_zsize() != 1):
		global_def.ERROR("This procedure works only for square images", "recons3d_em")

	if radius < 0: radius = nx // 2 - 1
	sphere2D = utilities.model_circle(radius, nx, nx)   
	sphere3D = utilities.model_circle(radius, nx, nx, nx)
	solution = utilities.model_blank(nx, nx, nx)
	a = utilities.model_blank(nx, nx, nx) # normalization volume
	e2D = utilities.model_square(nx, nx, nx)
	if mpi_r == 0:
		print("MPI processes: ", mpi_n)
		print("Parameters:  size=%d  radius=%d  projections_count=%d  max_iterations_count=%d min_norm_absolute_voxel_change=%f" % (
						nx, radius, all_projs_count, max_iterations_count, min_norm_absolute_voxel_change ))	

	# ----- create initial solution, calculate weights and normalization image (a)
	projections_angles = []  # list of lists of angles
	projections_data   = []  # list of lists of projections' images with weights
	for proj in projections:
		angles = [] # list of angles
		data = []   # list of projections' images with weights
		RA = proj.get_attr( "xform.projection" )
		EMAN2_cppwrap.Util.mul_img( proj, sphere2D )
		for j in range(RA.get_nsym(symmetry)):
			angdict = RA.get_sym_sparx(symmetry,j).get_rotation("spider") 
			angles.append( [angdict["phi"], angdict["theta"], angdict["psi"]] )
			chao_params = {"anglelist":angles[j],"radius":radius}
			EMAN2_cppwrap.Util.add_img( solution, proj.backproject("chao", chao_params) )
			EMAN2_cppwrap.Util.add_img( a, e2D.backproject("chao", chao_params) )
			if use_weights:
				proj3Dsphere = sphere3D.project("chao", chao_params)
				EMAN2_cppwrap.Util.mul_scalar( proj3Dsphere, 1.0 / EMAN2_cppwrap.Util.infomask(proj3Dsphere, None, True)[3] )
				EMAN2_cppwrap.Util.mul_img( proj, proj3Dsphere )
			data.append(proj)
		projections_angles.append(angles)
		projections_data.append(data)
	# reduce_scatter(solution)
	utilities.reduce_EMData_to_root(solution, mpi_r)
	utilities.bcast_EMData_to_all  (solution, mpi_r)
	# reduce_scatter(a)
	utilities.reduce_EMData_to_root(a, mpi_r)
	utilities.bcast_EMData_to_all  (a, mpi_r)
	# ------------------------
	a = morphology.threshold_to_minval(a, min_allowed_divisor)  # make sure that voxels' values are not too small (image a is divisior)
	EMAN2_cppwrap.Util.mul_img( solution, sphere3D )
	EMAN2_cppwrap.Util.div_img( solution, a )
	if mpi_r == 0: print("Projections loading COMPLETED")
	# ----- iterations
	prev_avg_absolute_voxel_change = 999999999.0
	time_projection = 0.0
	time_backprojection = 0.0
	time_iterations = time.clock()
	for iter_no in range(max_iterations_count):
		q = utilities.model_blank(nx, nx, nx)
		for i in range(len(projections_angles)):
			for j in range(len(projections_angles[i])):
				chao_params = {"anglelist":projections_angles[i][j],"radius":radius}
				time_start = time.clock()
				w = solution.project("chao", chao_params)
				time_projection += time.clock() - time_start
				p = projections_data[i][j] / morphology.threshold_to_minval(w, min_allowed_divisor)
				time_start = time.clock()
				q += p.backproject("chao", chao_params)
				time_backprojection += time.clock() - time_start
		# reduce_scatter(q)
		utilities.reduce_EMData_to_root(q, mpi_r)
		utilities.bcast_EMData_to_all  (q, mpi_r)
		# ----------------------
		EMAN2_cppwrap.Util.div_img( q, a )
		EMAN2_cppwrap.Util.mul_img( q, solution ) # q <- new solution  
		norm_absolute_voxel_change = q.cmp("lod",solution,{"mask":sphere3D,"negative":0,"normalize":0}) / q.cmp("lod",utilities.model_blank(nx,nx,nx),{"mask":sphere3D,"negative":0,"normalize":0})
		norm_squared_voxel_change  = q.cmp("sqEuclidean",solution,{"mask":sphere3D}) / q.cmp("sqEuclidean",utilities.model_blank(nx,nx,nx),{"mask":sphere3D})
		if norm_absolute_voxel_change > prev_avg_absolute_voxel_change:
			if mpi_r == 0: print("Finish and return last good solution")
			break
		prev_avg_absolute_voxel_change = norm_absolute_voxel_change
		solution = q
		solution = utilities.circumference(solution, radius-2, radius)
		if (iter_no+1)%5 == 0 and mpi_r == 0:
			solution.write_image(string.replace(output_file, ".hdf", "_%03d.hdf"%(iter_no+1)))
		if mpi_r == 0: print("Iteration ", iter_no+1, ",  norm_abs_voxel_change=", norm_absolute_voxel_change, ",  norm_squared_voxel_change=", norm_squared_voxel_change) 
		if min_norm_absolute_voxel_change > norm_absolute_voxel_change or min_norm_squared_voxel_change > norm_squared_voxel_change:
			break
	time_iterations = time.clock() - time_iterations
	# ----- return solution and exit
	if mpi_r == 0: print("Times: iterations=", time_iterations, "  project=", time_projection, "  backproject=", time_backprojection)
	return solution


def recons3d_sirt(stack_name, list_proj, radius, lam=1.0e-4, maxit=100, symmetry="c1", tol=0.001):
	"""
	SIRT
		
		tol   -- convergence tolerance
		lam   -- damping parameter
		maxit -- maximum number of iterations
	#
	"""
	pass#IMPORTIMPORTIMPORT from math import sqrt
	pass#IMPORTIMPORTIMPORT from utilities import model_circle
	#  analyze the symmetries Phil's code has all symmetries ready...
	nsym=1

	#  get image size from the first image
	data = EMAN2_cppwrap.EMData()
	data.read_image(stack_name,list_proj[0])
	nx = data.get_xsize()
	mask2d=utilities.model_circle(radius,nx,nx)  # SIRT works for squares only!
	mask2d = 1.0 - mask2d  # invert the mask to get average in corners
	nangles = len(list_proj)
	#
	mask3d=utilities.model_circle(radius,nx,nx,nx) # a 3D mask for error calculation
	#
	# create a volume to hold the reconstruction 
	#
	xvol = EMAN2_cppwrap.EMData()
	xvol.set_size(nx,nx,nx)
	xvol.to_zero()
	#
	# create a volume to hold trans(P)*P*xvol
	#
	pxvol = xvol.copy()
	#  array of symmetrized angles
	symangles=3*[0.0]
	angles = []

	# start iterating
	iter  = 1
	while iter <= maxit:
		if (iter == 1):
			#
			# backproject 2D images first to create the right-hand side of the
			# the normal equation
			#
			bvol = EMAN2_cppwrap.EMData()
			bvol.set_size(nx,nx,nx)
			bvol.to_zero()
			for i in range(nangles):
				# read projections and do initial  backprojection
				data.read_image(stack_name,list_proj[i])
				stat = EMAN2_cppwrap.Util.infomask(data, mask2d, False)
				data = data-stat[0]   # subtract the background average in the corners
				
				RA = data.get_attr( "xform.projection" )

				angles.append(RA)
				#ATTENTION
				#for transform in Symmetry3D.get_symmetries(symmetry):
					#Tf = transform*RA
					# though why do you go from 1 to nysm? why not 0 to nysm-1 ? It should be
					# equivalent unless I am missing something
					#angdict = Tf.get_params("spider")
					# then continue as before
				for ns in range(1,nsym+1):
					# multiply myangles by symmetry using Phil's Transform class
					Tf=RA.get_sym_sparx(symmetry,ns) #
					angdict = Tf.get_rotation("spider")
					#   Chao - please check the order of phi, theta, psi
					symangles[0] = angdict["phi"]
					symangles[1] = angdict["theta"]
					symangles[2] = angdict["psi"]
					myparams = {"anglelist":symangles, "radius":radius}
					bvol += data.backproject("chao", myparams)
			old_rnorm = bnorm = numpy.sqrt(bvol.cmp("dot",bvol,{"mask":mask3d,"negative":0}))
			grad  = bvol
		else:
			#  Insert your favorite MPI here
			pxvol.to_zero() 
			for i in range(nangles):
				# just a single slice of phi, theta, psi
				RA = angles[i]
				for ns in range(1,nsym+1):
					# multiply myangles by symmetry using Phil's Transform class
					Tf = RA.get_sym_sparx(symmetry,ns)#Tf.get_rotation()
					angdict = Tf.get_rotation("spider")
					#				    Chao - please check the order of phi, theta, psi
					symangles[0] = angdict["phi"]
					symangles[1] = angdict["theta"]
					symangles[2] = angdict["psi"]
					myparams = {"anglelist":symangles, "radius":radius}
					data  = xvol.project("chao", myparams) 
					pxvol += data.backproject("chao",myparams)
			grad  = bvol - pxvol

		rnorm = numpy.sqrt(grad.cmp("dot",grad,{"mask":mask3d,"negative":0}))
		print('iter = %3d,  rnorm = %6.3f,  rnorm/bnorm = %6.3f' % (iter,rnorm,rnorm/bnorm))
		if (rnorm < tol or rnorm > old_rnorm): break
		old_rnorm = rnorm
		xvol = xvol + lam*grad
		iter = iter + 1

	return  xvol

def recons3d_wbp(stack_name, list_proj, method = "general", const=1.0E4, symmetry="c1", radius=None): 
	"""
		Weigthed back-projection algorithm.
		stack_name - disk stack with projections or in-core list of images
		list_proj  - list of projections to be used in the reconstruction
		method - "general" Radermacher's Gaussian, "exact" MvHs triangle
		const  - for "general" 1.0e4 works well, for "exact" it should be the diameter of the object
		symmetry - point group symmetry of the object
	""" 
	pass#IMPORTIMPORTIMPORT import types
	pass#IMPORTIMPORTIMPORT from utilities import get_im

	if type(stack_name) == bytes:
		B = EMAN2_cppwrap.EMData()
		B.read_image(stack_name,list_proj[0])
	else : B = stack_name[list_proj[0]].copy()

	ny = B.get_ysize()  # have to take ysize, because xsize is different for real and fft images

	if radius == None: radius = (ny - 1) // 2

	CUBE = EMAN2_cppwrap.EMData()
	CUBE.set_size(ny, ny, ny)
	CUBE.to_zero()

	nsym = EMAN2_cppwrap.Transform.get_nsym(symmetry)
	nimages = len(list_proj)

	ss = [0.0]*(6*nsym*nimages)
	symmetry_transforms = [ [None for i in range(nsym)] for j in range(nimages) ] # list of nimages lists of nsym elements
	for iProj in range(nimages):
		if type(stack_name) == bytes:
			B.read_image(stack_name,list_proj[iProj], True)
		else:
			B = stack_name[list_proj[iProj]]
		transform = B.get_attr("xform.projection")
		for iSym in range(nsym):
			symmetry_transforms[iProj][iSym] = transform.get_sym_sparx(symmetry, iSym)
			d = symmetry_transforms[iProj][iSym].get_params("spider")
			DMnSS = EMAN2_cppwrap.Util.CANG(d["phi"], d["theta"], d["psi"])
			ss[ (iProj*nsym+iSym)*6 : (iProj*nsym+iSym+1)*6 ] = DMnSS["SS"]

	if method=="exact":    
		const = int(const)

	for iProj in range(nimages):
		proj = utilities.get_im(stack_name, list_proj[iProj])
		for iSym in range(nsym):
			B = proj.copy()
			B.set_attr("xform.projection", symmetry_transforms[iProj][iSym])
			if   method=="general":  EMAN2_cppwrap.Util.WTF(B, ss, const, iProj*nsym+iSym+1)  # counting in WTF start from 1!
			elif method=="exact"  :  EMAN2_cppwrap.Util.WTM(B, ss, const, iProj*nsym+iSym+1)  # counting in WTM start from 1!
			EMAN2_cppwrap.Util.BPCQ(B, CUBE, radius)

	return CUBE


def recons3d_vwbp(stack_name, list_proj, method = "general", const=1.0E4, symmetry="c1",outstack="bdb:temp"): 
	"""
		Weigthed back-projection algorithm.
		stack_name - disk stack with projections or in-core list of images
		list_proj  - list of projections to be used in the reconstruction
		method - "general" Radermacher's Gaussian, "exact" MvHs triangle
		const  - for "general" 1.0e4 works well, for "exact" it should be the diameter of the object
		symmetry - point group symmetry of the object

		WARNING - symmetries not implemented!!!!!!!!!
	""" 
	pass#IMPORTIMPORTIMPORT import types
	pass#IMPORTIMPORTIMPORT from utilities import get_im

	if type(stack_name) == bytes:
		B = EMAN2_cppwrap.EMData()
		B.read_image(stack_name,list_proj[0])
	else : B = stack_name[list_proj[0]].copy()

	ny = B.get_ysize()  # have to take ysize, because xsize is different for real and fft images

	nsym = EMAN2_cppwrap.Transform.get_nsym(symmetry)
	nimages = len(list_proj)

	ss = [0.0]*(6*nsym*nimages)
	symmetry_transforms = [ [None for i in range(nsym)] for j in range(nimages) ] # list of nimages lists of nsym elements
	for iProj in range(nimages):
		if type(stack_name) == bytes:
			B.read_image(stack_name,list_proj[iProj], True)
		else:
			B = stack_name[list_proj[iProj]]
		transform = B.get_attr("xform.projection")
		for iSym in range(nsym):
			symmetry_transforms[iProj][iSym] = transform.get_sym_sparx(symmetry, iSym)
			d = symmetry_transforms[iProj][iSym].get_params("spider")
			DMnSS = EMAN2_cppwrap.Util.CANG(d["phi"], d["theta"], d["psi"])
			ss[ (iProj*nsym+iSym)*6 : (iProj*nsym+iSym+1)*6 ] = DMnSS["SS"]

	if method=="exact":    
		const = int(const)

	for iProj in range(nimages):
		if(iProj%100 == 0):  print("BPCQ  ",iProj)
		CUBE = EMAN2_cppwrap.EMData()
		CUBE.set_size(ny, ny, ny)
		CUBE.to_zero()
		proj = utilities.get_im(stack_name, list_proj[iProj])
		for iSym in range(nsym):
			B = proj.copy()
			B.set_attr("xform.projection", symmetry_transforms[iProj][iSym])
			if   method=="general":  EMAN2_cppwrap.Util.WTF(B, ss, const, iProj*nsym+iSym+1)  # counting in WTF start from 1!
			elif method=="exact"  :  EMAN2_cppwrap.Util.WTM(B, ss, const, iProj*nsym+iSym+1)  # counting in WTM start from 1!
			pass#IMPORTIMPORTIMPORT from filter import filt_tanl
			B = filter.filt_tanl(B, 0.3, 0.1)
			EMAN2_cppwrap.Util.BPCQ(B, CUBE, (B.get_ysize()-1)//2)
		CUBE.write_image(outstack, iProj)
	return CUBE


def prepare_wbp(stack_name, list_proj, method = "general", const=1.0E4, symmetry="c1"):
	"""
		Prepare auxiliary arrays dm and ss.
		Weigthed back-projection algorithm.
		stack_name - disk stack with projections or in-core list of images
		list_proj  - list of projections to be used in the reconstruction
		method - "general" Radermacher's Gaussian, "exact" MvHs triangle
		const  - for "general" 1.0e4 works well, for "exact" it should be the diameter of the object
		symmetry - point group symmetry of the object
	"""
	pass#IMPORTIMPORTIMPORT import types

	if type(stack_name) == bytes:
		B = EMAN2_cppwrap.EMData()
		B.read_image(stack_name,list_proj[0])
	else : B = stack_name[list_proj[0]].copy()

	nx = B.get_xsize()

	RA = EMAN2_cppwrap.Transform()
	nsym = RA.get_nsym(symmetry)

	nimages = len(list_proj)
	ntripletsWnsym = nsym*nimages
	dm=[0.0]*(9*ntripletsWnsym)
	ss=[0.0]*(6*ntripletsWnsym)
	count = 0
	pass#IMPORTIMPORTIMPORT from utilities import get_params_proj
	for i in range(nimages):
		if type(stack_name) == bytes:
			B.read_image(stack_name,list_proj[i], True)
			PHI, THETA, PSI, s2x, s2y = utilities.get_params_proj( B )
		else:  
			PHI, THETA, PSI, s2x, s2y = utilities.get_params_proj( stack_name[list_proj[i]] )
		DMnSS = EMAN2_cppwrap.Util.CANG(PHI,THETA,PSI)
		dm[(count*9) :(count+1)*9] = DMnSS["DM"]
		ss[(count*6) :(count+1)*6] = DMnSS["SS"]
		count += 1
	return dm,ss


def recons3d_swbp(A, transform, L, ss, method = "general", const=1.0E4, symmetry="c1"):
	"""
	    Take one projection, but angles form the entire set.  Build the weighting function for the given projection taking into account all,
		apply it, and backproject.
		The projection number is L counting from zero.
		Weigthed back-projection algorithm.
		stack_name - disk stack with projections or in-core list of images
		method - "general" Radermacher's Gaussian, "exact" MvHs triangle
		const  - for "general" 1.0e4 works well, for "exact" it should be the diameter of the object
		symmetry - point group symmetry of the object
	"""
	B = A.copy()
	nx = B.get_xsize()
	if(method=="exact"  ):    const = int(const)
	nsym = 1
	CUBE = EMAN2_cppwrap.EMData()
	CUBE.set_size(nx, nx, nx)
	CUBE.to_zero()

	org_transform = B.get_attr("xform.projection")

	count = 0
	for j in range(1):
		count += 1   # It has to be there as counting in WTF and WTM start from 1!
		if   (method=="general"):    EMAN2_cppwrap.Util.WTF(B, ss, const, L+1)
		elif (method=="exact"  ):    EMAN2_cppwrap.Util.WTM(B, ss, const, L+1)

		B.set_attr("xform.projection", transform)
		EMAN2_cppwrap.Util.BPCQ(B, CUBE, (B.get_ysize()-1)//2)
		
	B.set_attr("xform.projection", org_transform)
	return CUBE, B

def weight_swbp(A, L, ss, method = "general", const=1.0E4, symmetry="c1"):
	"""
	    Take one projection, but angles form the entire set.  Build the weighting function for the given projection taking into account all,
		apply it, return weighted projection.
		The projection number is L counting from zero.
		Weigthed back-projection algorithm.
		stack_name - disk stack with projections or in-core list of images
		method - "general" Radermacher's Gaussian, "exact" MvHs triangle
		const  - for "general" 1.0e4 works well, for "exact" it should be the diameter of the object
		symmetry - point group symmetry of the object
	"""

	if(method=="exact"  ):    const = int(const)
	nsym = 1
	B = A.copy()
	count = 0
	for j in range(1):
		count += 1   # It has to be there as counting in WTF and WTM start from 1!
		if   (method=="general"):    EMAN2_cppwrap.Util.WTF(B, ss, const, L+1)
		elif (method=="exact"  ):    EMAN2_cppwrap.Util.WTM(B, ss, const, L+1)

	return B

def backproject_swbp(B, transform = None, symmetry="c1"): 
	"""
	    Take one projection, but angles form the entire set.  Build the weighting function for the given projection taking into account all,
		apply it, and backproject.
		The projection number is L counting from zero.
		Weigthed back-projection algorithm.
		stack_name - disk stack with projections or in-core list of images
		method - "general" Radermacher's Gaussian, "exact" MvHs triangle
		const  - for "general" 1.0e4 works well, for "exact" it should be the diameter of the object
		symmetry - point group symmetry of the object
	""" 

	ny = B.get_ysize()
	CUBE = EMAN2_cppwrap.EMData()
	CUBE.set_size(ny, ny, ny)
	CUBE.to_zero()

	org_transform = B.get_attr("xform.projection")
	if transform != None:
		B.set_attr("xform.projection", transform)
	EMAN2_cppwrap.Util.BPCQ(B, CUBE, (B.get_ysize()-1)//2)
	B.set_attr("xform.projection", org_transform)

	return CUBE

def one_swbp(CUBE, B, transform = None, symmetry="c1"): 
	"""
	        Take one projection, but angles form the entire set.  Build the weighting function for the given projection taking into account all,
		apply it, and backproject.
		The projection number is L counting from zero.
		method - "general" Rademacher's Gaussian, "exact" MvHs triangle
		const  - for "general" 1.0e4 works well, for "exact" it should be the diameter of the object
		symmetry - point group symmetry of the object
	""" 
	org_transform = B.get_attr("xform.projection")
	if transform != None:
		B.set_attr("xform.projection", transform)
	EMAN2_cppwrap.Util.BPCQ(B, CUBE, (B.get_ysize()-1)//2)  
	B.set_attr("xform.projection", org_transform)

def recons_ctf_from_fftvol_using_nn4_ctfw(size, fftvol, weight, snr, symmetry, weighting=1, npad = 2):
	pass#IMPORTIMPORTIMPORT from EMAN2 import Reconstructors

	params = {"size":size, "npad":npad, "snr":snr, "sign":1, "symmetry":symmetry, "fftvol":fftvol, "weight":weight, "weighting":weighting}
	# r = Reconstructors.get("nn4_ctf", params)
	r = EMAN2_cppwrap.Reconstructors.get("nn4_ctfw", params)
	r.setup()
	dummy = r.finish(True)
	return fftvol


def rec3D_MPI_with_getting_odd_even_volumes_from_files(fftvol_files, weight_files, reconstructed_vol_files,\
		nx, snr = 1.0, symmetry = "c1", mask3D = None, fsc_curve = None, \
		myid = 0, main_node = 0, rstep = 1.0, finfo=None, \
		npad = 2, mpi_comm=None):
	'''
	  This function is to be called within an MPI program to do a reconstruction on a dataset kept 
	  in the memory, computes reconstruction and through odd-even, in order to get the resolution
	'''
	
	fftvol_odd_file, fftvol_eve_file = fftvol_files 	
	weight_odd_file, weight_eve_file = weight_files
	reconstructed_odd_vol_files, reconstructed_eve_vol_files = reconstructed_vol_files
		
	pass#IMPORTIMPORTIMPORT import os
	pass#IMPORTIMPORTIMPORT from statistics import fsc_mask
	pass#IMPORTIMPORTIMPORT from utilities  import model_blank, model_circle, get_image, send_EMData, recv_EMData
	pass#IMPORTIMPORTIMPORT from mpi        import mpi_comm_size, MPI_COMM_WORLD
	
	if mpi_comm == None:
		mpi_comm = mpi.MPI_COMM_WORLD
	
	nproc = mpi.mpi_comm_size(mpi_comm)

	if nproc==1:
		assert main_node==0
		main_node_odd = main_node
		main_node_eve = main_node
		main_node_all = main_node
	elif nproc==2:
		main_node_odd = main_node
		main_node_eve = (main_node+1)%2
		main_node_all = main_node

		tag_voleve     = 1000
		tag_fftvol_eve = 1001
		tag_weight_eve = 1002
	else:
		#spread CPUs between different nodes to save memory
		main_node_odd = main_node
		main_node_eve = (int(main_node)+nproc-1)%int(nproc)
		main_node_all = (int(main_node)+nproc//2)%int(nproc)

		tag_voleve     = 1000
		tag_fftvol_eve = 1001
		tag_weight_eve = 1002

		tag_fftvol_odd = 1003
		tag_weight_odd = 1004
		tag_volall     = 1005

	if nproc == 1:
		fftvol = utilities.get_image(fftvol_odd_file)
		weight = utilities.get_image(weight_odd_file)
		# volodd = recons_ctf_from_fftvol(nx, fftvol, weight, snr, symmetry, npad = npad)
		volodd = utilities.get_image(reconstructed_odd_vol_files)

		fftvol = utilities.get_image(fftvol_eve_file)
		weight = utilities.get_image(weight_eve_file)
		# voleve = recons_ctf_from_fftvol(nx, fftvol, weight, snr, symmetry, npad = npad)
		voleve = utilities.get_image(reconstructed_eve_vol_files)

		if( not mask3D ):
			nx = volodd.get_xsize()
			ny = volodd.get_ysize()
			nz = volodd.get_zsize()
			mask3D = utilities.model_circle(min(nx,ny,nz)//2 - 2, nx,ny,nz)
		fscdat = statistics.fsc_mask( volodd, voleve, mask3D, rstep, fsc_curve)
		del  volodd, voleve, mask3d

		fftvol = utilities.get_image( fftvol_odd_file )
		fftvol_tmp = utilities.get_image(fftvol_eve_file)
		fftvol += fftvol_tmp
		fftvol_tmp = None

		weight = utilities.get_image( weight_odd_file )
		weight_tmp = utilities.get_image(weight_eve_file)
		weight += weight_tmp
		weight_tmp = None

		volall = recons_ctf_from_fftvol_using_nn4_ctfw(nx, fftvol, weight, snr, symmetry, npad = npad)
		os.system( "rm -f " + fftvol_odd_file + " " + weight_odd_file )
		os.system( "rm -f " + fftvol_eve_file + " " + weight_eve_file )

		return volall,fscdat

	if nproc == 2:
		if myid == main_node_odd:
			fftvol = utilities.get_image( fftvol_odd_file )
			weight = utilities.get_image( weight_odd_file )
			# volodd = recons_ctf_from_fftvol(nx, fftvol, weight, snr, symmetry, npad = npad)
			volodd = utilities.get_image(reconstructed_odd_vol_files)
			voleve = utilities.recv_EMData(main_node_eve, tag_voleve, mpi_comm)
			
			if( not mask3D ):
				nx = volodd.get_xsize()
				ny = volodd.get_ysize()
				nz = volodd.get_zsize()
				mask3D = utilities.model_circle(min(nx,ny,nz)//2 - 2, nx,ny,nz)
			fscdat = statistics.fsc_mask( volodd, voleve, mask3D, rstep, fsc_curve)
			del  volodd, voleve, mask3D
		else:
			assert myid == main_node_eve
			fftvol = utilities.get_image( fftvol_eve_file )
			weight = utilities.get_image( weight_eve_file )
			# voleve = recons_ctf_from_fftvol(nx, fftvol, weight, snr, symmetry, npad = npad)
			voleve = utilities.get_image(reconstructed_eve_vol_files)
			utilities.send_EMData(voleve, main_node_odd, tag_voleve, mpi_comm)

		if myid == main_node_odd:
			fftvol = utilities.get_image( fftvol_odd_file )
			fftvol_tmp = utilities.recv_EMData( main_node_eve, tag_fftvol_eve, mpi_comm)
			fftvol += fftvol_tmp
			fftvol_tmp = None

			weight = utilities.get_image( weight_odd_file )
			weight_tmp = utilities.recv_EMData( main_node_eve, tag_weight_eve, mpi_comm)
			weight += weight_tmp
			weight_tmp = None

			volall = recons_ctf_from_fftvol_using_nn4_ctfw(nx, fftvol, weight, snr, symmetry, npad = npad)
			os.system( "rm -f " + fftvol_odd_file + " " + weight_odd_file )

			return volall,fscdat
		else:
			assert myid == main_node_eve
			fftvol = utilities.get_image( fftvol_eve_file )
			weight = utilities.get_image( weight_eve_file )
			utilities.send_EMData(fftvol, main_node_odd, tag_fftvol_eve, mpi_comm)
			utilities.send_EMData(weight, main_node_odd, tag_weight_eve, mpi_comm)
			os.system( "rm -f " + fftvol_eve_file + " " + weight_eve_file )
			return utilities.model_blank(nx,nx,nx), None

	# cases from all other number of processors situations
	if myid == main_node_odd:
		fftvol = utilities.get_image( fftvol_odd_file )
		utilities.send_EMData(fftvol, main_node_eve, tag_fftvol_odd, mpi_comm)

		if not(finfo is None):
			finfo.write("fftvol odd sent\n")
			finfo.flush()

		weight = utilities.get_image( weight_odd_file )
		utilities.send_EMData(weight, main_node_all, tag_weight_odd, mpi_comm)

		if not(finfo is None):
			finfo.write("weight odd sent\n")
			finfo.flush()

		# volodd = recons_ctf_from_fftvol(nx, fftvol, weight, snr, symmetry, npad = npad)
		volodd = utilities.get_image(reconstructed_odd_vol_files)
		
		del fftvol, weight
		voleve = utilities.recv_EMData(main_node_eve, tag_voleve, mpi_comm)

		if( not mask3D ):
			nx = volodd.get_xsize()
			ny = volodd.get_ysize()
			nz = volodd.get_zsize()
			mask3D = utilities.model_circle(min(nx,ny,nz)//2 - 2, nx,ny,nz)

		fscdat = statistics.fsc_mask(volodd, voleve, mask3D, rstep, fsc_curve)
		del  volodd, voleve, mask3D
		volall = utilities.recv_EMData(main_node_all, tag_volall, mpi_comm)
		os.system( "rm -f " + fftvol_odd_file + " " + weight_odd_file )
		return volall, fscdat

	if myid == main_node_eve:
		ftmp = utilities.recv_EMData(main_node_odd, tag_fftvol_odd, mpi_comm)
		fftvol = utilities.get_image( fftvol_eve_file )
		EMAN2_cppwrap.Util.add_img( ftmp, fftvol )
		utilities.send_EMData(ftmp, main_node_all, tag_fftvol_eve, mpi_comm)
		del ftmp

		weight = utilities.get_image( weight_eve_file )
		utilities.send_EMData(weight, main_node_all, tag_weight_eve, mpi_comm)

		# voleve = recons_ctf_from_fftvol(nx, fftvol, weight, snr, symmetry, npad = npad)
		voleve = utilities.get_image(reconstructed_eve_vol_files)
		
		utilities.send_EMData(voleve, main_node_odd, tag_voleve, mpi_comm)
		os.system( "rm -f " + fftvol_eve_file + " " + weight_eve_file )

		return utilities.model_blank(nx,nx,nx), None


	if myid == main_node_all:
		fftvol = utilities.recv_EMData(main_node_eve, tag_fftvol_eve, mpi_comm)
		if not(finfo is None):
			finfo.write( "fftvol odd received\n" )
			finfo.flush()

		weight = utilities.recv_EMData(main_node_odd, tag_weight_odd, mpi_comm)
		weight_tmp = utilities.recv_EMData(main_node_eve, tag_weight_eve, mpi_comm)
		EMAN2_cppwrap.Util.add_img( weight, weight_tmp )
		weight_tmp = None

		volall = recons_ctf_from_fftvol_using_nn4_ctfw(nx, fftvol, weight, snr, symmetry, npad = npad)
		utilities.send_EMData(volall, main_node_odd, tag_volall, mpi_comm)

		return utilities.model_blank(nx,nx,nx),None

	return utilities.model_blank(nx,nx,nx),None


