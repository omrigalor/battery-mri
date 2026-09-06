"""Independent Gaussian voltage observations; all information uses base-2 entropy."""
import numpy as np
from scipy.special import logsumexp, expit
from numpy.polynomial.hermite import hermgauss

def posterior(predictions, observed, sigma, prior=(.5,.5)):
    if sigma <= 0: raise ValueError('Noise must be positive')
    p=np.asarray(prior,dtype=float)
    if np.any(p<0) or not np.isclose(p.sum(),1): raise ValueError('Invalid prior')
    residual=(np.asarray(predictions)-np.asarray(observed))/sigma
    ll=-.5*np.sum(residual**2,axis=1)
    with np.errstate(divide='ignore'): weights=ll+np.log(p)
    return np.exp(weights-logsumexp(weights)).tolist()

def entropy(p):
    p=np.clip(p,1e-15,1-1e-15)
    return -p*np.log2(p)-(1-p)*np.log2(1-p)

def eig(a,b,sigma,prior=(.5,.5)):
    # Binary equal-covariance Gaussian likelihood ratio is univariate normal.
    # Deterministic Gauss-Hermite integration avoids Monte Carlo optimizer noise.
    d2=float(np.sum(((np.asarray(a)-b)/sigma)**2))
    x,w=hermgauss(32)
    p=np.clip(prior[0],1e-14,1-1e-14)
    odds=np.log(p/(1-p))
    h=p*np.dot(w,entropy(expit(odds+d2/2+np.sqrt(2*d2)*x)))
    h+=(1-p)*np.dot(w,entropy(expit(odds-d2/2+np.sqrt(2*d2)*x)))
    return float(max(0,entropy(p)-h/np.sqrt(np.pi)))

def trajectory(a,b,y,sigma,prior):
    return [list(prior)]+[posterior([a[:i],b[:i]],y[:i],sigma,prior) for i in range(1,len(y)+1)]
