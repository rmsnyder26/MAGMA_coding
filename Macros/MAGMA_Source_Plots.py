from __future__ import division
import numpy as np
from array import array
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.gridspec import GridSpec
import scipy.special as sp
from scipy.interpolate import interp1d, RectBivariateSpline
from scipy.integrate import quad,simps
from mpl_toolkits.mplot3d import Axes3D
import time
from ROOT import TColor, TCanvas, TGraph, TGraph2D, gStyle, TStyle, TPad, TH2D, TLegend, TArrow, TLatex
import ROOT
#import gROOT

###############################################################  
###############################################################
####     SYSTEM SETUP. DOES NOT CHANGE EVENT-BY-EVENT.    #####
###############################################################  
###############################################################        

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


#Define grid where event-by-event profile will be evaluated.
#Should be able to resolve structures of size 1/Qs ~ 0.2 fm.
#A 100*100 square from [-9, 9] fm seems to be good enough for all systems.
size=1000 #number of cells along one side
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

#Choose size of box in which coords will be generated by the rejection method.
#A box within -12 to 12 fm is good enough.
lim=12 #fm

#Average number of sources in each nucleus.
N_A=n_A.integral(-lim,lim,-lim,lim)
N_B=n_B.integral(-lim,lim,-lim,lim)

#choose number of events to generate
nev=int(1)

#matrix where we store observables, listed below.
obs=np.zeros((nev,7))
#impact parameter
#tot number of sources
#tot energy
#rms radius: sqrt(<r^2>)
#real part of epsilon_2
#imag part of epsilon_2
#abs value of epsilon_3


##############################
##############################
### start loop over events ###
##############################
##############################

ev=0
for ev in range(nev):

    #Now generate coordinates of the sources.
    #Number of sources A from Poisson distribution.
    A_A=np.random.poisson(N_A)
    #Number of sources B from Poisson distribution.
    A_B=np.random.poisson(N_B)

    #Store tot number of sources.
    obs[ev,1]=A_A+A_B

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

    # b=np.sqrt(767*c/np.pi) #767 fm^2 for Pb-Pb collisions.
    
    # #Or fix the impact parameter.
    b = 0

    #Store impact parameter.
    obs[ev,0]=b
    
    #Shift all sources according to impact parameter.
    x_A=x_A-b/2
    x_B=x_B+b/2

################################################################    
################################################################
########     COMPUTE energy density in the event.     ##########
#####  (this step takes >95% of the computation time)    #######
################################################################
################################################################
    
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
    
    #np.savetxt("Rho.csv", rho, delimiter = ",")

##################################################
############### graphic check ####################
####### check that 2D profiles make sense ########
#################################################


#     #####nucleus A       
#     p1=0-b/2.     #x-position of the center
#     q1=0    #y-position of the center
#     a1=R_A     #radius on the x-axis
#     b1=R_A   #radius on the y-axis
    
#     ###nucleus B
#     p2=0+b/2.     #x-position of the center
#     q2=0    #y-position of the center
#     a2=R_B     #radius on the x-axis
#     b2=R_B   #radius on the y-axis

# #Create python plots of sources

#     t = np.linspace(0, 2*np.pi, 1000)
# #
#     plt.plot(x_A,y_A,'or',ms=6,mfc='w')
#     plt.plot(x_B,y_B,'og',ms=6,mfc='w')
#     plt.plot( p1+a1*np.cos(t) , q1+b1*np.sin(t), 'k--' , dashes=(2,2),lw=2)
#     plt.plot( p2+a2*np.cos(t) , q2+b2*np.sin(t), 'k--' , dashes=(2,2),lw=2)
#     plt.xlabel('$x$ [fm]',fontsize=16)
#     plt.ylabel(r'$y$ [fm]',fontsize=16)
#     plt.title('impact parameter = '+str(b)+' fm',fontsize=14)
#     plt.gca().xaxis.set_tick_params(labelsize = 12)
#     plt.gca().yaxis.set_tick_params(labelsize = 12)
#     plt.tight_layout()
#     #plt.axes().set_aspect('equal')
#     plt.axis([-14,14,-14,14])
#     plt.show()
##################################################
############## Source Plot in ROOT ###############
##################################################

##nucleus A       
    p1=0-b/2.     #x-position of the center
    q1=0    #y-position of the center
    a1=R_A     #radius on the x-axis
    b1=R_A   #radius on the y-axis
#
##nucleus B
    p2=0+b/2.     #x-position of the center
    q2=0    #y-position of the center
    a2=R_B     #radius on the x-axis
    b2=R_B   #radius on the y-axis

#Draw A_WS x B + A * B_WS. 5 plots in total
    c = TCanvas('c','c',725,275)

    c.SetRightMargin(c.GetRightMargin()/2);
    # c2.SetTopMargin(c2.GetTopMargin()*2);

    #Pad 1 for sources A
    pad1 = TPad("pad1","",0.02, .45, .197, .9, 0, 4, 0)

    pad2 = TPad("pad2","",0.02, 0, 0.197, .45, 0)

    pad3 = TPad("pad3","",0.255, .45, 0.43, .9, 0)

    pad4 = TPad("pad4","",0.255, 0, 0.43, 0.45, 0)

    pad5 = TPad("pad5","",0.518, 0, 0.917, 1, 0)

    pad1.Draw()
    pad2.Draw()
    pad3.Draw()
    pad4.Draw()
    pad5.Draw()

    plus_sign = TLatex()
    plus_sign.SetTextSize(0.15)
    plus_sign.DrawLatex(.21,.45,"+")

    equal_sign = TLatex()
    equal_sign.SetTextSize(0.15)
    equal_sign.DrawLatex(.47,.45,"=")

    A_text = TLatex()
    A_text.SetTextSize(0.075)
    A_text.DrawLatex(.1,.88,"#font[12]{A}")

    B_WS_text = TLatex()
    B_WS_text.SetTextSize(0.075)
    B_WS_text.DrawLatex(.1,.43,"#font[12]{B_{WS}}")

    A_WS_text = TLatex()
    A_WS_text.SetTextSize(0.075)
    A_WS_text.DrawLatex(.34,.88,"#font[12]{A_{WS}}")

    B_text = TLatex()
    B_text.SetTextSize(0.075)
    B_text.DrawLatex(.34,.43,"#font[12]{B}")


# #Plot A Sources
    pad1.cd()
    grA = TGraph(A_A, x_A, y_A)
    grA.GetXaxis().SetLimits(-8,8)
    grA.GetXaxis().SetLabelSize(0.0)
    grA.GetYaxis().SetLabelSize(0.0)
    grA.GetXaxis().SetTickLength(0.)
    grA.GetYaxis().SetTickLength(0.)
    grA.SetMinimum(-8)
    grA.SetMaximum(8)
    grA.SetMarkerColor(2)
    grA.SetMarkerStyle(4)
    grA.SetMarkerSize(.5)

    grA.SetTitle("")
    grA.Draw("AP")

    t = np.linspace(0,2*np.pi,100)
    x_cA = np.zeros(100)
    y_cA = np.zeros(100)
    for i in range(0,100):
        x_cA[i] = a1*np.cos(t[i])
        y_cA[i] = b1*np.sin(t[i])
        i+=1

    grC1 = TGraph(100, x_cA, y_cA)
    grC1.SetLineColor(1)
    grC1.Draw("C")

    c.Update()
#Plot B_WS
    
    pad2.cd()
    gr_B_WS = TH2D("B_WS",";"";"";""", ll, -14, 14, ll, -14, 14)

    for i in range(ll):
        for j in range(ll):
            gr_B_WS.SetBinContent(j+1, ll - i + 1, T_B[i,j])

    gr_B_WS.GetXaxis().SetRangeUser(-8, 8)
    gr_B_WS.GetYaxis().SetRangeUser(-8, 8)
    gr_B_WS.GetXaxis().SetLabelSize(0.0)
    gr_B_WS.GetYaxis().SetLabelSize(0.0)
    gr_B_WS.GetZaxis().SetLabelSize(0.0)
    gr_B_WS.GetXaxis().SetTickLength(0.)
    gr_B_WS.GetYaxis().SetTickLength(0.)
    gr_B_WS.GetZaxis().SetTickLength(0.)
    gr_B_WS.SetStats(0)
    gStyle.SetPalette(55)
    gr_B_WS.Draw("CONT4")

    t = np.linspace(0,2*np.pi,1000)
    x_cB = np.zeros(1000)
    y_cB = np.zeros(1000)
    for i in range(0,1000):
        x_cB[i] = a2*np.cos(t[i])
        y_cB[i] = b2*np.sin(t[i])
        i+=1

    grC2 = TGraph(1000, x_cB, y_cB)
    grC2.SetLineColor(1)
    grC2.Draw("SAME")

    c.Update()
#Plot A_WS
    
    pad3.cd()
    gr_A_WS = TH2D("A_WS",";"";"";""", ll, -14, 14, ll, -14, 14)

    for i in range(ll):
        for j in range(ll):
            gr_A_WS.SetBinContent(j+1, ll - i + 1, T_A[i,j])

    gr_A_WS.GetXaxis().SetRangeUser(-8, 8)
    gr_A_WS.GetYaxis().SetRangeUser(-8, 8)
    gr_A_WS.GetXaxis().SetLabelSize(0.0)
    gr_A_WS.GetYaxis().SetLabelSize(0.0)
    gr_A_WS.GetZaxis().SetLabelSize(0.0)
    gr_A_WS.GetXaxis().SetTickLength(0.)
    gr_A_WS.GetYaxis().SetTickLength(0.)
    gr_A_WS.SetStats(0)
    gStyle.SetPalette(55)
    gr_B_WS.Draw("CONT4")

    t = np.linspace(0,2*np.pi,1000)
    x_cA = np.zeros(1000)
    y_cA = np.zeros(1000)
    for i in range(0,1000):
        x_cA[i] = p1+a1*np.cos(t[i])
        y_cA[i] = q1+b1*np.sin(t[i])
        i+=1

    grC3 = TGraph(1000, x_cA, y_cA)
    grC3.SetLineColor(1)
    grC3.Draw("SAME")

    c.Update()
#Plot B Sources
    pad4.cd()
    grB = TGraph(A_B, x_B, y_B)

    grB.GetXaxis().SetLimits(-8,8)

    grB.GetXaxis().SetLabelSize(0.0)
    grB.GetYaxis().SetLabelSize(0.0)
    grB.GetXaxis().SetTickLength(0.)
    grB.GetYaxis().SetTickLength(0.)
    grB.SetMinimum(-8)
    grB.SetMaximum(8)
    grB.SetMarkerColor(2)
    grB.SetMarkerStyle(4)
    grB.SetMarkerSize(.5)
    grB.SetTitle("")
    grB.Draw("AP")

    t = np.linspace(0,2*np.pi,1000)
    x_cB = np.zeros(1000)
    y_cB = np.zeros(1000)
    for i in range(0,1000):
        x_cB[i] = a2*np.cos(t[i])
        y_cB[i] = b2*np.sin(t[i])
        i+=1

    grC4 = TGraph(1000, x_cB, y_cB)
    grC4.SetLineColor(1)
    grC4.Draw("SAME")

    c.Update()
#Contour plot of energy density

    #Canvas for overall plot

    pad5.cd()
    gr_dens_rho = TH2D("rho_orig",";"";"";""[#font[12]{GeV fm^{-3}}]", size, -8, 8, size, -8, 8)

    pad5.SetRightMargin(c.GetRightMargin()*5);
    for i in range(0,size):
        for j in range(0, size):
            if rho[i,j] > 0:
                gr_dens_rho.SetBinContent(j + 1, size - i + 1, rho[i, j])
            else: 
                gr_dens_rho.SetBinContent(j + 1, size - i + 1, 1E-7)

    gr_dens_rho.GetZaxis().CenterTitle()
    gr_dens_rho.GetXaxis().SetLabelSize(0.0)
    gr_dens_rho.GetYaxis().SetLabelSize(0.0)
    gr_dens_rho.GetZaxis().SetTitleOffset(1.3)
    gr_dens_rho.GetZaxis().SetTitleSize(0.05)
    gr_dens_rho.SetStats(0)
    gStyle.SetPalette(55)
    gr_dens_rho.Draw("COLZ")

    #Here are the circles showing the radius of the nuclei

    t = np.linspace(0,2*np.pi,1000)
    x_cA = np.zeros(1000)
    y_cA = np.zeros(1000)
    
    for i in range(0,1000):
        x_cA[i] = p1+a1*np.cos(t[i])
        y_cA[i] = q1+b1*np.sin(t[i])
        i+=1

    t = np.linspace(0,2*np.pi,1000)
    x_cB = np.zeros(1000)
    y_cB = np.zeros(1000)
    
    for i in range(0,1000):
        x_cB[i] = p2+a2*np.cos(t[i])
        y_cB[i] = q2+b2*np.sin(t[i])
        i+=1

    grC1_rho = TGraph(1000, x_cA, y_cA)
    grC1_rho.SetLineColor(1)
    grC1_rho.Draw("SAME")

    grC2_rho = TGraph(1000, x_cB, y_cB)
    grC2_rho.SetLineColor(1)
    grC2_rho.Draw("SAME")


##############################################################
    
    # t = np.linspace(0, 2*np.pi, 1000)

    # fig=plt.figure(1)
    # gs = GridSpec(1, 3)
    # color='nipy_spectral_r'

    # ax1 = fig.add_subplot(gs[0,0])
    # plt.contourf(x_grid, y_grid, rho_A, cmap=color, levels=np.linspace(0.01,np.max(rho_A),10))
    # plt.pcolormesh(x_grid, y_grid, rho_A, cmap=color)
    # plt.xlabel('x [fm]',fontsize=16)
    # plt.ylabel('y [fm]',fontsize=16)
    # plt.plot(x_A,y_A,'go',mfc='g',ms=3)
    # plt.gca().xaxis.set_tick_params(labelsize = 12)
    # plt.gca().yaxis.set_tick_params(labelsize = 12)
    # plt.plot( p1+a1*np.cos(t) , q1+b1*np.sin(t), 'k--' , dashes=(2,2),lw=2)
    # #plt.axes().set_aspect('equal')
    # plt.axis([-dim,dim,-dim,dim])
    # plt.tight_layout()
    # #plt.show()

    # ax2 = fig.add_subplot(gs[0,1])
    # plt.pcolormesh(x_grid, y_grid, rho_B,cmap=color)#, levels=np.linspace(0.1,np.max(T_B),10))
    # plt.contourf(x_grid, y_grid, rho_B, cmap=color, levels=np.linspace(0.01,np.max(rho_B),10))
    # plt.xlabel('x [fm]',fontsize=16)
    # plt.ylabel('y [fm]',fontsize=16)
    # plt.plot(x_B,y_B,'go',mfc='w',ms=3)
    # plt.gca().xaxis.set_tick_params(labelsize = 12)
    # plt.gca().yaxis.set_tick_params(labelsize = 12)
    # plt.plot( p2+a2*np.cos(t) , q2+b2*np.sin(t), 'k--' , dashes=(2,2),lw=2)
    # #plt.axes().set_aspect('equal')
    # plt.axis([-dim,dim,-dim,dim])
    # plt.tight_layout()
    # #plt.show()

    # ax3 = fig.add_subplot(gs[0,2])
    #x
    # plt.pcolormesh(x_grid, y_grid, rho, cmap=color)
    # plt.xlabel('x [fm]',fontsize=16)
    # plt.ylabel('y [fm]',fontsize=16)
    # plt.plot(x_A,y_A,'go',mfc='g',ms=3)
    # plt.plot(x_B,y_B,'go',mfc='w',ms=3)
    # plt.axis([-14, 14, -14, 14])
    # plt.plot( p1+a1*np.cos(t) , q1+b1*np.sin(t), 'k--' , dashes=(2,2),lw=2)
    # plt.plot( p2+a2*np.cos(t) , q2+b2*np.sin(t), 'k--' , dashes=(2,2),lw=2)
    # plt.plot(x_A,y_A,'or',ms=6,mfc='w')
    # plt.plot(x_B,y_B,'og',ms=6,mfc='w')
    # plt.gca().xaxis.set_tick_params(labelsize = 12)
    # plt.gca().yaxis.set_tick_params(labelsize = 12)
    # #plt.axes().set_aspect('equal')
    # plt.tight_layout()
    # plt.show()


################################################

#Save plots as pdfs

    c.SaveAs('c.pdf')
    # c2.SaveAs('c2.pdf')
