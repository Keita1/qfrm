from qfrm import *


class European(OptionValuation):
    """ European option class.
    Inherits all methods and properties of OptionValuation class.
    """
    def pxBS(self):
        """ Option valuation via BSM.

        Use BS_params method to draw computed parameters.
        They are also used by other exotic options.
        It's basically a one-liner.

        :return: price of a put or call European option
        :rtype: float

        :Example:

        >>> s = Stock(S0=42, vol=.20)
        >>> European(ref=s, right='put', K=40, T=.5, rf_r=.1).pxBS().px   # .81, p.339
        >>> European(ref=s, right='call', K=40, T=.5, rf_r=.1).pxBS()   # 4.76, p.339
        >>> European(ref=s, right='call', K=40, T=.5, rf_r=.1).pxBS()    # 4.7594223928715316
        >>> European(ref=s, right='put', K=40, T=.5, rf_r=.1).pxBS()    # 0.80859937290009043
        """
        from scipy.stats import norm
        from math import sqrt, exp, log

        _ = self
        d1 = (log(_.ref.S0 / _.K) + (_.rf_r + _.ref.vol ** 2 / 2.) * _.T)/(_.ref.vol * sqrt(_.T))
        d2 = d1 - _.ref.vol * sqrt(_.T)
        px = _.signCP * (
            _.ref.S0 * exp(-_.ref.q * _.T) * norm(_.signCP * d1)
            - _.K * exp(-_.rf_r * _.T) * norm(_.signCP * d2))

        self._pxBS = type('pxBS', (object,),  {'d1':d1, 'd2':d2, 'px':px})  # save params as object pxBS
        return self._pxBS

    def _pxLT(self, nsteps=3, return_tree=False):
        """ Option valuation via binomial (lattice) tree

        This method is not called directly. Instead, OptionValuation calls it via (vectorized) method pxLT()
        See Ch. 13 for numerous examples and theory.

        .. sectionauthor:: Oleg Melnikov

        :param nsteps: number of time steps in the tree
        :type nsteps: int
        :param return_tree: indicates whether a full tree needs to be returned
        :type return_tree: bool
        :return: option price or a chronological tree of stock and option prices
        :rtype:  float|tuple of tuples

        .. seealso::

        Implementing Binomial Trees:   http://papers.ssrn.com/sol3/papers.cfm?abstract_id=1341181

        :Example:

        >>> European().pxLT()  # produce lattice tree pricing with default parameters

        >>> a = European(ref=Stock(S0=810, vol=.2, q=.02), right='call', K=800, T=.5, r=.05)   # 53.39, p.291
        >>> a.pxLT(2)
        53.394716374961348
        >>> a.pxLT((2,20,200))
        (53.394716374961348, 56.40278872645991, 56.324021659469274)
        >>> a.pxLT(2, return_tree=True)  # stock and option values for step 2 (expiry), 1, 0 (now)
        (((663.17191000000003, 810.0, 989.33623), (0.0, 10.0, 189.33623)),
        ((732.91831000000002, 895.18844000000001), (5.0623199999999997, 100.66143)),
        ((810.0,), (53.39472,)))
        """
        from numpy import cumsum, log, arange, insert, exp, sqrt, sum, maximum

        _ = self.LT_params(nsteps)
        S = self.ref.S0 * _['d'] ** arange(nsteps, -1, -1) * _['u'] ** arange(0, nsteps + 1)
        O = maximum(self.signCP * (S - self.K), 0)          # terminal option payouts
        tree = ((S, O),)

        if return_tree:
            for i in range(nsteps, 0, -1):
                O = _['df_dt'] * ((1 - _['p']) * O[:i] + ( _['p']) * O[1:])  #prior option prices (@time step=i-1)
                S = _['d'] * S[1:i+1]                   # prior stock prices (@time step=i-1)
                tree = tree + ((S, O),)
            out = Util.round(tree, to_tuple=True)
        else:
            csl = insert(cumsum(log(arange(nsteps)+1)), 0, 0)         # logs avoid overflow & truncation
            tmp = csl[nsteps] - csl - csl[::-1] + log(_['p'])*arange(nsteps+1) + log(1-_['p'])*arange(nsteps+1)[::-1]
            out = (_['df_T'] * sum(exp(tmp) * tuple(O)))
        return out
