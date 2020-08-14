from __future__ import division
import numpy as np
import sys
from array import array
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.gridspec import GridSpec
import scipy.special as sp
from scipy.interpolate import interp1d, RectBivariateSpline
from scipy.integrate import quad,simps
from mpl_toolkits.mplot3d import Axes3D
import time
from ROOT import TColor, TCanvas, TGraph, TGraph2D, gStyle, TStyle, TPad, TH2D, TLegend, TArrow, TLatex, TH1D, TLine, TMultiGraph, gPad
import ROOT

###############################################################  
###############################################################
####     SYSTEM SETUP. DOES NOT CHANGE EVENT-BY-EVENT.    #####
###############################################################  
###############################################################        

#Current time to evaluate how long it takes to run events

time_start = time.time()

#Thickness function. Note that the overall normalization is not needed.
def thick(x,y,lim,step,R,a):
    zz=np.arange(0,lim+step,step)
    def f2p(x,y,z,R,a): #2-parameter fermi distribution for spherical nucleus
        return 1./(1+np.exp((np.sqrt(x**2+y**2+z**2)-R)/a))
    fun=f2p(x,y,zz,R,a)
    return 2.*np.trapz(fun,zz) #use symmetry

#Converts GeV into fm^-1
conv=1/0.197327

#Choose colliding nuclei. Set radius and diffusiveness.
a_A, R_A = 0.55, 6.62 #fm
a_B, R_B = 0.55, 6.62 #fm

#Choose m and the saturation scale at the center of the nuclei.
m = 0.14*conv #fm^-1
Q0_A = 1.24*conv #fm^-1
Q0_B = 1.24*conv #fm^-1

#QCD coupling and number of colors.
g=np.sqrt(np.pi)
Nc=3

#Define a fine grid to evaluate thickness functions, Qs^2, and the source densities.
#A grid within [-14fm, 14fm] with step of 0.1fm gives excellent precision.
#Evaluation is slow but we use it only once.
lim=14 #fm
step=0.1 #fm
size =100
xx=np.arange(-lim,lim+step,step)
yy=np.arange(-lim,lim+step,step)
ll=xx.size
x,y=np.meshgrid(xx,yy)

#Evaluate thickness functions at the center of nuclei.
T0_A=thick(0,0,lim,step,R_A,a_A) #fm^-2
T0_B=thick(0,0,lim,step,R_B,a_B) #fm^-2

#Evaluate density of sources and QS^2.
#First compute TA and TB.
T_A=np.zeros((ll,ll))
T_B=np.zeros((ll,ll))
for j in range(ll):
    for k in range(ll):
        T_A[j,k]=thick(xx[j],yy[k],lim,step,R_A,a_A)
        T_B[j,k]=thick(xx[j],yy[k],lim,step,R_B,a_B)
#To avoid re-computing thickness functions, we interpolate.
#Probability density for nuclei A and B.

n_A=RectBivariateSpline(xx,yy,(Nc**2-1)/(32*np.pi)*Q0_A**2*T_A/T0_A*1/np.log(1+Q0_A**2/m**2*T_A/T0_A))
n_B=RectBivariateSpline(xx,yy,(Nc**2-1)/(32*np.pi)*Q0_B**2*T_B/T0_B*1/np.log(1+Q0_B**2/m**2*T_B/T0_B))
#Saturation scales ^2.
Q2_A=RectBivariateSpline(xx,yy,Q0_A**2*T_A/T0_A)
Q2_B=RectBivariateSpline(xx,yy,Q0_B**2*T_B/T0_B)

#Choose size of box in which coords will be generated by the rejection method.
#A box within -12 to 12 fm is good enough.
lim=12 #fm

#Average number of sources in each nucleus.
N_A=n_A.integral(-lim,lim,-lim,lim)
N_B=n_B.integral(-lim,lim,-lim,lim)

#choose number of events to generate
nev=int(1000000)

#matrix where we store observables, listed below.
obs=np.zeros((nev,12))

#Event number
#impact parameter
#tot number of sources
#rho
#total energy
#tot energy*area
#rms radius: sqrt(<r^2>)
#real part of epsilon_2
#imag part of epsilon_2
#abs value of epsilon_3
#epsilon_2
#epsilon_3

##############################
##############################
### start loop over events ###
##############################
##############################

# rho_dict = {}

ev=0
for ev in range(nev):
    obs[ev,0] = ev
    #Now generate coordinates of the sources.
    #Number of sources A from Poisson distribution.
    A_A=np.random.poisson(N_A)
    #Number of sources B from Poisson distribution.
    A_B=np.random.poisson(N_B)

    #Store tot number of sources.
    obs[ev,2]=A_A+A_B

#####################################################################
####     GENERATE COORDS for sources in nucleus A and nucleus B  ####
####     using to a rejection algorithm.                         ####
##################################################################### 

    #Generate sources A.
    x_A=np.zeros(A_A)
    y_A=np.zeros(A_A)
    n0_A=n_A.ev(0,0)

    ##Optimized algorithm to generate coordinates.
    gen=int(10*A_A)    
    cont=0
    while cont>=0:
        loop=cont
        u=np.random.uniform(-lim,lim,size=gen)
        v=np.random.uniform(-lim,lim,size=gen)
        rand=np.random.random(gen,)
        n_eval=n_A.ev(u,v)
        n_eval/=(n0_A*rand)
        coords_ev=np.where(n_eval>1)
        cont=cont+coords_ev[0].size
        x_ev=u[coords_ev[0]]
        y_ev=v[coords_ev[0]]
        if cont<=A_A:
            x_A[loop:cont]=x_ev
            y_A[loop:cont]=y_ev
        else:
            mmax=A_A-loop
            x_A[loop:]=x_ev[0:mmax]
            y_A[loop:]=y_ev[0:mmax]
            break
    
    #Generate sources B
    x_B=np.zeros(A_B)
    y_B=np.zeros(A_B)
    n0_B=n_B.ev(0,0)
    
    ##Optimized algorithm to generate coordinates.
    gen=int(10*A_B)    
    cont=0
    while cont>=0:
        loop=cont
        u=np.random.uniform(-lim,lim,size=gen)
        v=np.random.uniform(-lim,lim,size=gen)
        rand=np.random.random(gen,)
        n_eval=n_B.ev(u,v)
        n_eval/=(n0_B*rand)
        coords_ev=np.where(n_eval>1)
        cont=cont+coords_ev[0].size
        x_ev=u[coords_ev[0]]
        y_ev=v[coords_ev[0]]
        if cont<=A_B:
            x_B[loop:cont]=x_ev
            y_B[loop:cont]=y_ev
        else:
            mmax=A_B-loop
            x_B[loop:]=x_ev[0:mmax]
            y_B[loop:]=y_ev[0:mmax]
            break
    
########################################
#### GENERATE AN IMPACT PARAMETER. #####
########################################        
    
    #Draw a random b-centrality and then compute b using nucleus-nucleus cross section.
    c=np.random.uniform(0,1)

    b=np.sqrt(767*c/np.pi) #767 fm^2 for Pb-Pb collisions.
    
    #Or fix the impact parameter.
    #b = 0.1

    #Store impact parameter.
    obs[ev,1]=b
    
    #Shift all sources according to impact parameter.
    x_A=x_A-b/2
    x_B=x_B+b/2
 

################################################################    
################################################################
########     COMPUTE energy density in the event.     ##########
#####  (this step takes >95% of the computation time)    #######
################################################################
################################################################

    #########################################

    #Define grid where event-by-event profile will be evaluated.
    #Should be able to resolve structures of size 1/Qs ~ 0.2 fm.
    #A 100*100 square from [-9, 9] fm seems to be good enough for all systems.

    dim=14 #fm , the grid stretches from [-dim, +dim]
    grid_step=2*dim/size #fm
    area=grid_step**2 #fm^2

    #grid coordinates
    xx=np.linspace(-dim,dim,size+1)
    yy=np.linspace(dim,-dim,size+1)

    xx=(xx[1:]+xx[:-1])/2
    yy=(yy[1:]+yy[:-1])/2

    #the grid
    x_grid,y_grid=np.meshgrid(xx,yy)

    ###########################################

    #Energy density profiles for A and B.

    rho_A=np.zeros((size,size))
    rho_B=np.zeros((size,size))
    # rho_A_mod=np.zeros((size,size))
    # rho_B_mod=np.zeros((size,size))

    #Optimized algorithm to evaluate sources on the grid.
    #Loop over sources in A.
    for j in range(A_A):
        x_Aj=x_A[j]
        y_Aj=y_A[j]
        x_loop=(x_grid-x_Aj)
        y_loop=(y_grid-y_Aj)
        radius=np.sqrt(x_loop**2+y_loop**2)
        indic=np.where(radius<1/m) #evaluate only within radius 1/m
        indic_x=indic[0]
        indic_y=indic[1]
        ##########################################################################
        ######################## now evaluate rho_A ############################## 
        ## ORIGINAL MAGMA PRESCRIPTION: overall QsA^2 and QsB^2 for each source ##
        ##########################################################################
        #Be careful with impact parameter shift and coords.
        rho_A[indic_x,indic_y]+=8/g**2/Nc*Q2_B.ev(x_Aj-b/2,y_Aj)/(x_loop[indic_x,indic_y]**2+y_loop[indic_x,indic_y]**2+1/Q2_A.ev(x_Aj+b/2,y_Aj)) #fm^-4

        ##########################################################################
        ## MODIFICATION OF GG: let QsA^2 and QsB^2 vary over the source profile ##
        ##########################################################################
        #Be careful with impact parameter shift and coords.
#        rho_A[indic_x,indic_y]+=8/g**2/Nc*Q2_B.ev(x_grid[indic_x,indic_y]-b/2,y_grid[indic_x,indic_y])/(x_loop[indic_x,indic_y]**2+y_loop[indic_x,indic_y]**2+1/Q2_A.ev(x_grid[indic_x,indic_y]+b/2,y_grid[indic_x,indic_y])) #fm^-4
        
        ##########################################################################
        ## Revised magma code where it is only dependent on product of sources ##
        ##########################################################################

        # rho_A_mod[indic_x,indic_y]+=8/g**2/Nc/(x_loop[indic_x,indic_y]**2+y_loop[indic_x,indic_y]**2+1/Q2_A.ev(x_Aj+b/2,y_Aj)) #fm^-4

    #Optimized algorithm to evaluate sources on the grid.
    #Loop over sources in B.
    for j in range(A_B):
        x_Bj=x_B[j]
        y_Bj=y_B[j]
        x_loop=(x_grid-x_B[j])
        y_loop=(y_grid-y_B[j])
        radius=np.sqrt(x_loop**2+y_loop**2)
        indic=np.where(radius<1/m) #evaluate only within radius 1/m
        indic_x=indic[0]
        indic_y=indic[1]
        ##########################################################################
        ######################## now evaluate rho_B ############################## 
        ## ORIGINAL MAGMA PRESCRIPTION: overall QsA^2 and QsB^2 for each source ##
        ##########################################################################
        #Be careful with impact parameter shift and coords.
        rho_B[indic_x,indic_y]+=8/g**2/Nc*Q2_A.ev(x_Bj+b/2,y_Bj)/(x_loop[indic_x,indic_y]**2+y_loop[indic_x,indic_y]**2+1/Q2_B.ev(x_Bj-b/2,y_Bj)) #fm^-4
        ##########################################################################
        ## MODIFICATION OF GG: let QsA^2 and QsB^2 vary over the source profile ##
        ##########################################################################
        #Be careful with impact parameter shift and coords.
#        rho_B[indic_x,indic_y]+=8/g**2/Nc*Q2_A.ev(x_grid[indic_x,indic_y]+b/2,y_grid[indic_x,indic_y])/(x_loop[indic_x,indic_y]**2+y_loop[indic_x,indic_y]**2+1/Q2_B.ev(x_grid[indic_x,indic_y]-b/2,y_grid[indic_x,indic_y])) #fm^-4
    
        ##########################################################################
        ## Revised magma code where it is only dependent on product of sources ##
        ##########################################################################

        # rho_B_mod[indic_x,indic_y]+=8/g**2/Nc/(x_loop[indic_x,indic_y]**2+y_loop[indic_x,indic_y]**2+1/Q2_B.ev(x_Bj-b/2,y_Bj))

    #Compute total energy density profile.
    rho = (rho_A + rho_B)/conv #Gev/fm^3
    # rho_mod = rho_A_mod*rho_B_mod/conv #Gev

    # obs[ev,3] = rho

    # Only need to add rhos above 100,000 a.u. for cutoff. Later we can retrieve them. Otherwise the dictionary will be too big 
    #and will take up too much memory while running the program.

    # if np.sum(rho) >= 100000:
    #     rho_dict[ev] = rho

    # else: 
    #     rho_dict[ev] = 0

###############################################################################
####     CALCULATE "OBSERVABLES". With the energy density, we can move on #####
####     to the calculation of eccentricities, rms size, total energy.    #####
####     Just use algebra of 2D grids.                                    #####
###############################################################################

    #Total energy.

    #If impact parameter too large, the rho may = 0

    e_tot=np.sum(rho)
    obs[ev,4]=e_tot
    obs[ev,5]=e_tot*area
    
    #Recentering correction 
    center_x=np.sum(rho*x_grid)/e_tot
    center_y=np.sum(rho*y_grid)/e_tot
    x_cen=x_grid-center_x
    y_cen=y_grid-center_y
    
    #RMS radius, eccentricity, triangularity
    z=x_cen+y_cen*1.j
    r2=x_cen**2+y_cen**2
    r3=r2**(3/2.)

    #evaluate epsilon_2
    e2_num=rho*z**2
    e2_den=rho*r2
    E2=-np.sum(e2_num)/np.sum(e2_den)
    obs[ev,7]=np.real(E2)
    obs[ev,8]=np.imag(E2)

    #evaluate epsilon_3
    e3_num=rho*z**3
    e3_den=rho*r3
    E3=-np.sum(e3_num)/np.sum(e3_den)
    obs[ev,9]=np.abs(E3)

    #evaluate rms radius
    obs[ev,6]=np.sqrt(np.sum(e2_den)/e_tot)

    #Evaluate e_tot, e2, e3

    e2 = np.sqrt(np.real(E2)**2 + np.imag(E2)**2)
    e3 = np.sqrt(np.real(E3)**2 + np.imag(E3)**2)

    obs[ev,10] = e2
    obs[ev,11] = e3

###################
####End of loop####
###################

###########################################################################################
########     Calculate centrality bins by creating a histogram of total energies.   #######
###########################################################################################

#Sort and define array of total energies to put into histogram.
e_max = np.max(obs[:,4])
e_tot_array = np.sort(obs[:,4])

#Define number of centrality bins
n_bin = 100

#Fill histogram with j bins (j = 10,000 should be sufficient)
hist_e_tot = TH1D("hist","",10000, 0, e_max)

for e_tot in obs[:,4]:
    hist_e_tot.Fill(e_tot)

#The fraction of events above bin i defines the centrality bins and where we put energy lines on the plot

e_line_array = np.zeros(n_bin + 1)
centrality_array = np.zeros(n_bin + 1)

total_integral = hist_e_tot.Integral(1, 10000)
for i in range(101):
    for j in range(1,10000):
        frac_ev = hist_e_tot.Integral(1, j) / total_integral
        if frac_ev >= (1 - i/100):
            centrality_array[i] = hist_e_tot.GetBinCenter(j)
            e_line_array[i] = hist_e_tot.GetBinCenter(j)
            break

##############################################################################
########     Calculate e_n fluctuations and ratios per centrality bin  #######
##############################################################################

#Goes through each total energy for all events (each event has a total energy).
#Assigns energies to centrality bins, ie from 0-1% centrality if there are 100 bins.
#Calculate e_n fluctuations and ratios per bin.

#Initialiing coordinates of centralities and moments as lists.

i = 0
centrality_list = []
e2_2_list_for_coords = []
e2_4_list_for_coords = []
e3_2_list_for_coords = []
ratio_e2_over_e3_list = []
ratio_e3_over_e2_list = []

for i in range(0, n_bin -1):

    #Inside the bin we try to only find the events that fit in that bin and create a list per bin.
    #Moments are e2{2}, e2{4}, and e3{2}

    e2_2_list = []
    e2_4_list = []
    e3_2_list = []

    ev_ctr = 0

    #Creating an array of e2s and e3s in each bin

    for e_tot in obs[:,4]:

        if centrality_array[i] >= e_tot >= centrality_array[i+1]:

            e2_2_list.append(obs[ev_ctr , 10])
            e2_4_list.append(obs[ev_ctr , 10])
            e3_2_list.append(obs[ev_ctr , 11])
            ev_ctr += 1
        else:

            ev_ctr += 1

    #Calculating e_2{2} based on e_2_array
    e2_2_array = np.array(e2_2_list)
    n2_2 = len(e2_2_list)

    #if there are no e_tots per bin, that's ok. Make it equivalent to zero. Else calculate as normal
    if n2_2 == 0:
        e2_2 = 0
    else:
        #e_2{2} is the rms of the e_2 array

        #dot product of e_2 array^2
        mean_e2_sqrd = np.dot(e2_2_array, e2_2_array)/n2_2
        
        e2_2 = np.sqrt(mean_e2_sqrd)

    #Calculating e_2{4} based on e_2_array. 
    e2_4_array = np.array(e2_4_list)

    n2_4 = len(e2_4_array)

    if n2_4 == 0:
        e2_4 = 0

    else:
        x_4th_list = []

        for element in e2_4_array:
            element_4th = element**4
            x_4th_list.append(element_4th)

        x_4th_array = np.array(x_4th_list)
        e2_4th = np.sum(x_4th_array)

        mean_e2_sqr = np.dot(e2_4_array, e2_4_array)/n2_4
        mean_e2_4th = e2_4th/n2_4

        if 2*(mean_e2_sqr)**2 < mean_e2_4th:
            e2_4 = 0

        else:
            e2_4 = (2*(mean_e2_sqrd)**2 - mean_e2_4th)**(1/4)

    #Calculating e_3{2} based on e_3_array.

    e3_2_array = np.array(e3_2_list)
    n3_2 = len(e3_2_list)   

    if n3_2 ==0:
        e3_2 = 0
    else:

        mean_e3_sqrd = np.dot(e3_2_array, e3_2_array)/n3_2
        e3_2 = np.sqrt(mean_e3_sqrd)

    #Calculation of e2{2}/e3{2}
    if e2_2 == 0 or e3_2 == 0:
        ratio_e2_over_e3 = 0
    else:
        ratio_e2_over_e3 = e2_2/e3_2

    #Calculation of e2{2}/e3{2}
    if e2_2 == 0 or e3_2 == 0:
        ratio_e3_over_e2 = 0
    else:
        ratio_e3_over_e2 = e3_2/e2_2

    #Append centrality coordinates and e_n{n} fluctuation coordinates to make ROOT TGraphs.

    centrality_list.append(i+0.5)
    e2_2_list_for_coords.append(e2_2)
    e2_4_list_for_coords.append(e2_4)
    e3_2_list_for_coords.append(e3_2)
    ratio_e2_over_e3_list.append(ratio_e2_over_e3)
    ratio_e3_over_e2_list.append(ratio_e3_over_e2)

##############################################################################
########     Outputting coordinates as ROOT Files for plots            #######
##############################################################################

#Convert from lists of coordinates to arrays

centrality_coord = np.array(centrality_list)
e2_2_coord = np.array(e2_2_list_for_coords)
e2_4_coord = np.array(e2_4_list_for_coords)
e3_2_coord = np.array(e3_2_list_for_coords)
ratio_e2_over_e3_coord = np.array(ratio_e2_over_e3_list)
ratio_e3_over_e2_coord = np.array(ratio_e3_over_e2_list)

#Output into ROOT Files

gr_e2_2 = TGraph(n_bin - 1, centrality_coord, e2_2_coord)
gr_e2_4 = TGraph(n_bin - 1, centrality_coord, e2_4_coord)
gr_e3_2 = TGraph(n_bin - 1, centrality_coord, e3_2_coord)
gr_e2_over_e3_ratio = TGraph(n_bin - 1, centrality_coord, ratio_e2_over_e3_coord)
gr_e3_over_e2_ratio = TGraph(n_bin - 1, centrality_coord, ratio_e3_over_e2_coord)

e_n_MAGMA = ROOT.TFile.Open('e_n_fluctuations_MAGMA.root', 'RECREATE')

gr_e2_2.Write('e2_2_MAGMA')
gr_e2_4.Write('e2_4_MAGMA')
gr_e3_2.Write('e3_2_MAGMA')
gr_e2_over_e3_ratio.Write('e2_over_e3_MAGMA')
gr_e3_over_e2_ratio.Write('e3_over_e2_MAGMA')

##############################################################################
########     Output histogram as a ROOT file for plots           #######
##############################################################################

hist_e_tot.Write('Energy_Distribution_MAGMA')

# ##############################################################################
# ########     TH2D Plots for SONIC Hydrodynamic calculations            #######
# ##############################################################################

# #SONIC plots are only for hydrodynamics within 0-1% centrality range.

# ev_ctr =0
# Rho_MAGMA_for_SONIC = ROOT.TFile.Open('Rho_MAGMA_for_SONIC.root', 'RECREATE')

# file_ctr = 0

# for e_tot in obs[:,4]:

# 	#Only want to create 100 files

# 	if file_ctr >= 100:
# 		break

# 	else:
# 		if centrality_array[0] >= e_tot >= centrality_array[1]:
# 			rho_for_SONIC = rho_dict[ev_ctr]
# 			b_for_SONIC = obs[ev_ctr , 10]

# 			c = TCanvas("Canvas_" + str(ev_ctr),"Canvas_" + str(ev_ctr),500,500)
# 			gr_dens_rho = TH2D("Rho_orig_Ev_" + str(ev_ctr),"Rho = A #times B_{WS} + A_{WS} #times B, Total Energy = " + str(round(e_tot,0)) + ", b = " + str(round(b_for_SONIC, 1)) + "fm;""x [fm];""y f[m];"" [GeV*fm^-3]", size, -14, 14, size, -14, 14)

# 			#Assign rho to each bin on the TH2D

# 			for i in range(0,size):
# 				for j in range(0, size):
# 					if rho_for_SONIC[i,j] <= 1E-7:
# 						gr_dens_rho.SetBinContent(j + 1, size - i + 1, 1E-7)
# 					else:
# 						gr_dens_rho.SetBinContent(j + 1, size - i + 1, rho_for_SONIC[i, j])

# 			gr_dens_rho.GetXaxis().SetRangeUser(-14, 14)
# 			gr_dens_rho.GetYaxis().SetRangeUser(-14, 14)
# 			gr_dens_rho.SetStats(0)
# 			gStyle.SetPalette(55)
# 			gr_dens_rho.Draw("COLZ")

# 			gr_dens_rho.Write("Rho_MAGMA_TH2D_Event_" + str(ev_ctr))

# 			ev_ctr += 1
# 			file_ctr +=1
# 		else: 
# 			ev_ctr += 1

# ev_ctr =0
# Rho_MAGMA_test = ROOT.TFile.Open('Rho_MAGMA_SONIC_test.root', 'RECREATE')

# file_ctr = 0

# for e_tot in obs[:,4]:

#     if file_ctr >= 1:
#         break
#     if centrality_array[0] >= e_tot >= centrality_array[1]:
#         rho_for_SONIC = rho_dict[ev_ctr]
#         b_for_SONIC = obs[ev_ctr , 10]

#         c = TCanvas("Canvas_" + str(ev_ctr),"Canvas_" + str(ev_ctr),500,500)
#         gr_dens_rho = TH2D("Rho_orig_Ev_" + str(ev_ctr),"Rho = A #times B_{WS} + A_{WS} #times B, Total Energy = " + str(round(e_tot,0)) + ", b = " + str(round(b_for_SONIC, 1)) + "fm;""x [fm];""y f[m];"" [GeV*fm^-3]", size, -14, 14, size, -14, 14)

#         #Assign rho to each bin on the TH2D

#         for i in range(0,size):
#             for j in range(0, size):
#                 if rho_for_SONIC[i,j] <= 1E-7:
#                     gr_dens_rho.SetBinContent(j + 1, size - i + 1, 1E-7)
#                 else:
#                     gr_dens_rho.SetBinContent(j + 1, size - i + 1, rho_for_SONIC[i, j])

#         gr_dens_rho.GetXaxis().SetRangeUser(-14, 14)
#         gr_dens_rho.GetYaxis().SetRangeUser(-14, 14)
#         gr_dens_rho.SetStats(0)
#         gStyle.SetPalette(55)
#         gr_dens_rho.Draw("COLZ")

#         gr_dens_rho.Write("Rho_MAGMA_TH2D_Test_Event")

#         ev_ctr += 1
#         file_ctr +=1
#     else: 
#         ev_ctr += 1
##############################################################################

#End of program
print('it took', (time.time() - time_start), 's for ', nev, '  Pb-Pb events')