#!/usr/bin/python

#
# pibsolver.py
#
# Solves the Schrodinger equation for a one-dimensional particle
# in an arbitrary potential using a finite basis of particle-
# in-a-box basis functions.
#
# Requires SciPy, NumPy, and matplotlib
#
# Adapted from EIGENSTATE1D (Fortran) by Nancy Makri
#
# This script generates a text file containing the eigenvalues
# and eigenvectors, a pdf graph of the energy spectrum, and
# a pdf graph showing the potential, eigenvalues, and 
# eigenfunctions.
#
# Author: Kyle N. Crabtree
# Revised by Tomoyuki Hayashi
#

import scipy as sp
import scipy.constants as spc
import scipy.integrate
import math
import numpy
from matplotlib import pyplot as plt
import datetime

#---------------------------
#        VARIABLES         -
#---------------------------

#equilibrium bond length in Angstrom
re = 0.96966

#effective mass in kg
amu = spc.physical_constants['atomic mass constant'][0]
mass = (1.*16./(1.+16.))*amu *2

#minimum x value for partice in a box calculation
xmin = -0.5+re

#maximum x value for particle in a box calculation
#there is no limit, but if xmax<xmin, the values will be swapped
#if xmax = xmin, then xmax will be set to xmin + 1
xmax = 1.5+re

#number of grid points at which to calculate integral
#must be an odd number. If an even number is given, 1 will be added.
#minimum number of grid points is 3
ngrid = 501

#number of PIB wavefunctions to include in basis set
#minimum is 1
nbasis = 100

#if you want to control the plot ranges, you can do so here
make_plots = True
plotymin = 0
plotymax = 0
plotxmin = 0
plotxmax = 0

#dissociation energy in cm-1
de = 37778.617

#force constant in N / m
fk = 774.7188418117737*0.75

#angular frequency in rad/s
omega = numpy.sqrt(fk/mass)

#output file for eigenvalues
outfile = "eigenvalues.txt"

#output PDF for energy spectrum
spectrumfile = "energy.pdf"

#output PDF for potential and eigenfunctions
potentialfile = "potential.pdf"


#--------------------------
#  POTENTIAL DEFINITIONS  -
#--------------------------

#definitions of potential functions
#particle in a box: no potential. Note: you need to manually set plotymin and plotymax above for proper graphing
def box(x):
	return 0

#purely harmonic potential
#energy in cm^-1
prefactor = 0.5 * fk * 1e-20/(spc.h*spc.c*100.0)
def harmonic(x):
	return prefactor*(x-re)*(x-re)

#anharmonic potential
#def anharmonic(x):
#	return 0.5*(x**2.) + 0.05*(x**4.)

#Morse potential
#energy in cm^-1
#alpha in A^-1
alpha = math.sqrt(fk/2.0/(de*spc.h*spc.c*100.0))*1e-10
def morse(x):
	return de*(1.-numpy.exp(-alpha*(x-re)))**2.

#double well potential (minima at x = +/-3)
#def doublewell(x):
#	return x**4.-18.*x**2. + 81.

#potential function used for this calculation
def V(x):
	return morse(x)

#------------------------
#   BEGIN CALCULATION   -
#------------------------


#verify that inputs are sane
if xmax==xmin:
	xmax = xmin+1.
elif xmax<xmin:
	xmin,xmax = xmax,xmin

L = xmax - xmin

#function to compute normalized PIB wavefunction
tl = numpy.sqrt(2./L)
pixl = numpy.pi/L
def pib(x,n,L):
	return tl*math.sin(n*x*pixl)

ngrid = max(ngrid,3)

if not ngrid%2:
	ngrid+=1

nbasis = max(1,nbasis)

#get current time
starttime = datetime.datetime.now()

#create grid
x = numpy.linspace(xmin,xmax,ngrid)

#create Hamiltonian matrix; fill with zeros
H = numpy.zeros((nbasis,nbasis))


#split Hamiltonian into kinetic energy and potential energy terms
#H = T + V
#V is defined above, and will be evaluated numerically

#Compute kinetic energy
#The Kinetic enery operator is T = -hbar^2/2m d^2/dx^2
#in the PIB basis, T|phi(i)> = hbar^2/2m n^2pi^2/L^2 |phi(i)>
#Therefore <phi(k)|T|phi(i)> = hbar^2/2m n^2pi^2/L^2 delta_{ki}
#Kinetic energy is diagonal
kepf = spc.hbar*spc.hbar*math.pi**2./(2.*mass*(L*1e-10)*(L*1e-10)*spc.h*spc.c*100)
for i in range(0,nbasis):
    H[i,i] += kepf*(i+1.)*(i+1.)

#now, add in potential energy matrix elements <phi(j)|V|phi(i)>
#that is, multiply the two functions by the potential at each grid point and integrate
for i in range(0,nbasis):
	for j in range(0,nbasis):
		if j >= i:
			y = numpy.zeros(ngrid)
			for k in range(0,ngrid):
				p = x[k]
				y[k] += pib(p-xmin,i+1.,L)*V(p)*pib(p-xmin,j+1.,L)
			H[i,j] += sp.integrate.simps(y,x)
		else:
			H[i,j] += H[j,i]


#Solve for eigenvalues and eigenvectors
evalues, evectors = sp.linalg.eigh(H)
evalues = evalues

#get ending time
endtime = datetime.datetime.now()

#------------------------
#    GENERATE OUTPUT    -
#------------------------

print("Results:")
print("-------------------------------------")
print("   v  Energy (cm-1)  Delta E (cm-1)  ")
print("-------------------------------------")
for i in range(min(40,len(evalues))):
    if i>0:
        deltae = evalues[i] - evalues[i-1]        
        print(" {:>3d}  {:>13.3f}  {:>14.3f}  ".format(i,evalues[i],deltae))
    else:
        print(" {:>3d}  {:>13.3f}          ------ ".format(i,evalues[i]))

with open(outfile,'w') as f:
	f.write(str('#pibsolver.py output\n'))
	f.write('#start time ' + starttime.isoformat(' ') + '\n')
	f.write('#end time ' + endtime.isoformat(' ') + '\n')
	f.write(str('#elapsed time ' + str(endtime-starttime) + '\n'))
	f.write(str('#xmin {:1.4f}\n').format(xmin))
	f.write(str('#xmax {:1.4f}\n').format(xmax))
	f.write(str('#grid size {0}\n').format(ngrid))
	f.write(str('#basis size {0}\n\n').format(nbasis))
	f.write(str('#eigenvalues\n'))
	f.write(str('{0:.5e}').format(evalues[0]))
	for i in range(1,nbasis):
		f.write(str('\t{0:.5e}').format(evalues[i]))
	f.write('\n\n#eigenvectors\n')
	for j in range(0,nbasis):
		f.write(str('{0:.5e}').format(evectors[j,0]))
		for i in range(1,nbasis):
			f.write(str('\t{0:.5e}').format(evectors[j,i]))
		f.write('\n')

if make_plots == True:
    #if this is run in interactive mode, make sure plot from previous run is closed
    plt.figure(1)
    plt.close()
    plt.figure(2)
    plt.close()

    
    plt.figure(1)
    #Make graph of eigenvalue spectrum
    title = "EV Spectrum, Min={:1.4f}, Max={:1.4f}, Grid={:3d}, Basis={:3d}".format(xmin,xmax,ngrid,nbasis)
    
    plt.plot(evalues,'ro')
    plt.xlabel('v')
    plt.ylabel(r'E (cm$^{-1}$)')
    plt.title(title)
    plt.savefig(spectrumfile)
    plt.show()
    
    #Make graph with potential and eigenfunctions
    plt.figure(2)
    title = "Wfns, Min={:1.4f}, Max={:1.4f}, Grid={:3d}, Basis={:3d}".format(xmin,xmax,ngrid,nbasis)
    vplot = numpy.zeros(x.size)
    for i in range(0,x.size):
        vplot[i] = V(x[i])
    plt.plot(x,vplot)
    
    if plotxmin == 0:
    	plotxmin = xmin
    if plotxmax == 0:
    	plotxmax = xmax
    if(plotxmin == plotxmax):
    	plotxmin, plotmax = xmin, xmax
    if(plotxmin > plotxmax):
    	plotxmin, plotxmax = plotxmax,plotxmin
    if plotymax == 0:
    	plotymax = 1.25*de
#          plotymax = evalues[10]
    if(plotymin > plotymax):
    	plotymin, plotymax = plotymax,plotymin
    sf = 1.0
    if len(evalues)>2:
        sf = (evalues[2]-evalues[0])/5.0
    for i in range(0,nbasis):
    	plt.plot([xmin,xmax],[evalues[i],evalues[i]],'k-')
    for i in range(0,nbasis):
    	ef = numpy.zeros(ngrid)
    	ef += evalues[i]
    	for j in range(0,nbasis):
    		for k in range(0,ngrid):
    			ef[k] += evectors[j,i]*pib(x[k]-xmin,j+1,L)*sf
    	plt.plot(x,ef)
    
    plt.plot([xmin,xmin],[plotymin,plotymax],'k-')
    plt.plot([xmax,xmax],[plotymin,plotymax],'k-')
    plt.axis([plotxmin,plotxmax,plotymin,plotymax])
    plt.title(title)
    plt.xlabel('$R$ (Angstrom)')
    plt.ylabel(r'V (cm$^{-1}$)')
    plt.savefig(potentialfile)
    plt.show()




