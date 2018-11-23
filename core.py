import numpy as np
import ipdb
import scipy.constants as spc
import scipy.special as sps

class Covariance_Matrix(object):
    """ Empty covariance matrix class """
    def __init__(self,params=None):
        self.params = params

class WhiteCovMatrix(Covariance_Matrix):
    def __init__(self,params=None,sigma_prefit=None,bcknd_per_toa=None,sigma_type='frequentist'):
        """
        White covariance matrix, generated from sigma_prefit. Arguments:
        params - dict of efacs and equads per backend with their values,
            format: 'efac_'+'backend_name', 'equad_'+'backend_name';
        sigma_prefit - prefit sigmas from .tim files, array length of ToA
        bcknd_per_toa - array with names of backend used for each ToA
        sigma_type - convention for relation of  efac/equad and pre/post-fit sigmas,
          can be 'bayesian' or 'frequentist'
        """
        Covariance_Matrix.__init__(self,params)
        self.sigma_type = sigma_type
        self.sigma_prefit = sigma_prefit
        self.bcknd_per_toa = bcknd_per_toa

    def get_covmatrix(self):
        self.efvaltoa = WhiteCovMatrix.bcknd_val_per_toa(self,param_prefix='efac_')
        self.eqvaltoa = WhiteCovMatrix.bcknd_val_per_toa(self,param_prefix='equad_')
        if self.sigma_type == 'bayesian':
            cvmsig = WhiteCovMatrix.sigma_bayesian(self)
        elif self.sigma_type == 'frequentist':
            cvmsig = WhiteCovMatrix.sigma_frequentist(self)
        return np.diag(cvmsig**2)

    def sigma_bayesian(self):
        sb = np.multiply(self.sigma_prefit,self.efvaltoa)
        sb = np.power(sb,2) + np.power(self.eqvaltoa,2)
        return np.power(sb,0.5)

    def sigma_frequentist(self):
        sf = np.power(self.sigma_prefit,2)+np.power(self.eqvaltoa,2)
        sf = np.multiply(sf, np.power(self.efvaltoa,2))
        return np.power(sf,0.5)

    def simulate(self,config):
        """
        Simulating white covariance matrix based on the configuration,
        for measurements with subsequent changing in observing backends.
        config - dict with following keywords:
        1) config['sigma_prefit'] - sigma_prefit, one value for all ToA
        2) config['efac'] - efacs per backend, array
        3) config['equad'] - equads per backend, array
        4) config['frac'] - subsequent fractions of observing with each backend
        5) config['ntoa'] - number of ToA, size of covariance matrix
        """
        # Populating a parameter dictionary (efacs and equads with values)
        self.params = dict()
        ef_keys = ['efac_'+str(ii) for ii in range(0,len(config['efac']))]
        ef_values = config['efac']
        self.params.update( dict(zip(ef_keys,ef_values)) )
        eq_keys = ['equad_'+str(ii) for ii in range(0,len(config['equad']))]
        eq_values = config['equad']
        self.params.update( dict(zip(eq_keys,eq_values)) )

        # Check that efac, equad and frac have the same length
        # And that we have at least two backends
        # And that sum of fracs is one

        # Populating parameter per ToA array
        self.bcknd_per_toa = np.array([])
        for ii, frac in enumerate(config['frac']):
            if ii==len(config['frac']):
                nn = config['ntoa'] - len(bcknd_per_toa)
            else:
                nn = np.floor(config['ntoa'] * frac)
            self.bcknd_per_toa = np.append( self.bcknd_per_toa,
                np.repeat(str(ii), nn) )

         # Populating array of prefit_sigma from one given prefit_sigma
        self.sigma_prefit = np.repeat(config['sigma_prefit'],config['ntoa'])

    def bcknd_val_per_toa(self,param_prefix):
        """ Getting an array of parameter values for each backend,
        using an array of backends used for each ToA.
        param_prefix is a prefix for a parameter, i.e. efac_ or equad_ """
        par_for_toa = [param_prefix+backend for backend in self.bcknd_per_toa]
        return [self.params[par] for par in par_for_toa]

class SpinCovMatrix(Covariance_Matrix):
    def __init__(self,params=None,toa=None):
        Covariance_Matrix.__init__(self,params)

    def get_covmatrix(self):
        # [!] FIRST - get tau matrix from toa
        pow1 = .5-self.params['alpha']/2
        pow2 = -.5-self.params['alpha']/2
        pow3 = -.5+self.params['alpha']/2
        part1 = 2**pow1 / self.params['fc']**pow2
        part2 = self.params['p0'] * spc.year**3 * np.sqrt(np.pi) *
                (2*np.pi*tau)**pow3
        part3 = sps.yv(pow1,2*np.pi*tau*self.params['fc']) / 
                sps.gamma(self.params['alpha']/2)
        out = part1 * part2 * part3
