from Util import *


class pricespec:
    """ object for storing calculated price and related specifications.

    use this object to store the price, methods and any intermediate results in your option object.
    """
    px = None  # use float data type
    method = None  # 'bs', 'lt', 'mc', 'fd'
    sub_method = None   # indicate specifics about pricing method. ex: 'lsm' or 'naive' for mc pricing of american

    def __init__(self, **kwargs):
        # for k, v in kwargs.items():
        #     if v is not none:  setattr(self, k, v)
        self.add(**kwargs)

    def add(self, **kwargs):
        for k, v in kwargs.items():
            if v is not none:  setattr(self, k, v)
        return self

    def __repr__(self):
        from yaml import dump

        s = dump(self, default_flow_style=0).replace('!!python/object:','').replace('!!python/tuple','')
        s = s.replace('__main__.','')
        # if not new_line:  s = s.replace(',',', ').replace('\n', ',').replace(': ', ':').replace('  ',' ')
        return s


class stock:
    """ class representing an underlying instrument.
    .. sectionauthor:: oleg melnikov
    sets parameters of an equity stock share: s0, vol, ticker, dividend yield, curr, tkr ...
    """
    # def __init__(self, s0=50, vol=.3, q=0, curr=none, tkr=none, desc=none):
    def __init__(self, s0=none, vol=none, q=0, curr=none, tkr=none, desc=none):
        """ class object constructor.
        :param s0: stock price today ( or at the time of evaluation), positive number. used in pricing options.
        :type s0:  float
        :param vol: volatility of this stock as a rate, positive number. used in pricing options.
            ex. if volatility is 30%, enter vol=.3
        :type vol:  float
        :param q:   dividend yield rate, usually used with equity indices. optional
        :type q:    float
        :param curr: currency name/symbol of this stock... optional
        :type curr:  str
        :param tkr:  stock ticker. optional.
        :type tkr:   str
        :param desc: any additional information related to the stock.
        :type desc:  dict
        :return:     __init__() method always implicitly returns self, i.e. a reference to this object
        :rtype:      __main__.stock
        """
        self.s0, self.vol, self.q, self.curr, self.tkr, self.desc = s0, vol, q, curr, tkr, desc


class optionseries:
    """ class representing an option series.

    this class describes the option specs outside of valuation. so, it doesn't contain interest rates needed for pricing.
    this class can be used for plotting and evaluating option packages (strategies like bull spread, straddle, ...).
    it can also be inherited by classes that require an important extension - option valuation.

    sets option series specifications: ref, k, t, .... this is a ligth object with only a few methods.
    .. sectionauthor:: oleg melnikov

    .. seealso::
        http://stackoverflow.com/questions/6535832/python-inherit-the-superclass-init
        http://stackoverflow.com/questions/285061/how-do-you-programmatically-set-an-attribute-in-python
    """
    def __init__(self, ref=none, right=none, k=none, t=none, clone=none, desc=none):
        """ constructor.

        if clone object is supplied, its specs are used.

        :param ref: any suitable object of an underlying instrument (must have s0 & vol variables).
                required, if clone = none.
        :type ref:  object
        :param right: 'call', 'put', and 'other' for more exotic instruments. required, if clone = none.
        :type right:  str
        :param k:   strike price, positive number. required, if clone = none.
        :type k:    float
        :param t:   time to maturity, in years, positive number. required, if clone = none.
        :type t:    float
        :param clone:   another option object from which this object will inherit specifications. optional.
            this is useful if you want to price european option as (for example) american.
            then european option's specs will be used to create a new american option. just makes things simple.
        :type clone:  object inherited from optionvaluation
        :param desc:  any number of describing variables. optional.
        :type desc:   dict
        :return:   __init__() method always implicitly returns self, i.e. a reference to this object
        :rtype:    __main__.optionseries
        """
        self.update(ref=ref, right=right, k=k, t=t, clone=clone, desc=desc)

    def update(self, **kwargs):
        """

        :param kwargs:
        :return:

        :example:

        >>> o = optionseries(ref=stock(s0=50, vol=.3), right='put', k=52, t=2).update(k=53)
        >>> o
        >>> optionseries(clone=o, k=54).update(right='call')

        """
        self.reset()   # delete old calculations, before updating parameters

        if 'clone' in kwargs:
            self.clone = kwargs['clone']
            del kwargs['clone']

        for k, v in kwargs.items():
            if v is not none: setattr(self, k, v)

        return self

    def get_right(self):
        """ returns option's right as a string.
        :return: 'call', 'put', or 'other'
        :rtype: str
        """
        return self._right

    def set_right(self, right='put'):
        if right is not none:
            self._right = right.lower()
            self._signcp = 1 if self._right == 'call' else -1 if self._right == 'put' else 0  # 0 for other rights
        return self

    right = property(get_right, set_right, none, 'option\'s right (str): call or put')

    @property
    def signcp(self): return self._signcp

    @property
    def style(self):
        """ returns option style (european, american, bermudan, asian, binary,...) as a string.
        it first checks whether this object inherited class 'optionvaluation'.
        option style can be drawn from the class name. see example.
        :return: option style for objects inheriting optionvaluation
        :rtype: str | none

        :example:

        >>> american().style
        'american'
        >>> european().style
        'european'
        >>> optionseries().style  # returns none

        """
        if any('optionvaluation' == i.__name__ for i in self.__class__.__bases__):
            return type(self).__name__
        else:
            return none

    @property
    def series(self):
        """ compiles an option series name, including option style (european, american, ...)

        :return: option series name
        :rtype: str

        :example:

            >>> optionseries(ref=stock(s0=50, vol=0.3), k=51, right='call').series
            '51 call'
            >>> optionseries(ref=stock(s0=50, vol=0.3, tkr='ibm'), k=51, right='call').series
            'ibm 51 call'
            >>> optionseries(ref=stock(s0=50, vol=0.3, tkr='ibm'), k=51, t=2, right='call').series
            'ibm 51 2yr call'
        """
        try: tkr = self.ref.tkr + ' '
        except: tkr=''

        k = '' if getattr(self, 'k', none) is none else str(self.k) + ' '
        t = '' if getattr(self, 't', none) is none else str(self.t) + 'yr '
        style = '' if self.style in ['optionseries', 'optionvaluation'] else self.style + ' '
        right = '' if getattr(self, 'right', none) is none else str(self.right) + ' '

        return (tkr + k + t + style + str(right)).rstrip()  # strip trailing spaces

    @property
    def specs(self):
        """ compile option series, rfr, foreign rfr, volatility, dividend yield

        :return: option pricing specifications, including interest rates, volatility, ...
        :rtype: str

        :example:

            >>> optionseries(ref=stock(s0=50, vol=0.3), k=51, right='call').specs
            '51 call,s0=50,vol=0.3,q=0'
            >>> optionseries(ref=stock(s0=50, vol=0.3, tkr='ibm'), k=51, right='call').specs
            'ibm 51 call,s0=50,vol=0.3,q=0'
            >>> optionseries(ref=stock(s0=50, vol=0.3), k=51, t=2, right='call', desc='some option').specs
            '51 2yr call,s0=50,vol=0.3,q=0'
        """
        _ = self

        rf_r = frf_r = q = vol = ''
        if hasattr(_, 'ref'):  # if reference object is specified, read its parameters
            if hasattr(_.ref, 's0'): s0 = (',s0=' + str(_.ref.s0))
            if hasattr(_.ref, 'q'): q = (',q=' + str(_.ref.q))
            if hasattr(_.ref, 'vol'): vol = (',vol=' + str(_.ref.vol))
            vol = (',vol=' + str(_.ref.vol)) if getattr(_.ref, 'vol', 0)!=0 else ''
        if hasattr(_, 'frf_r'): frf_r = (',frf_r=' + str(_.frf_r))
        if hasattr(_, 'rf_r'): rf_r = (',rf_r=' + str(_.rf_r))

        return self.series + s0 + vol + rf_r + q + frf_r

    def full_spec(self, new_line=false):
        """ returns a formatted string containing all variables of this class (recursively)

        :param new_line: whether include new line symbol '\n' or not
        :type new_line: bool
        :return: formatted string with option specifications
        :rtype:  str

        :example:

        >>> optionseries(ref=stock(s0=50, vol=0.3), k=51, right='call').full_spec(false)
        'optionseries,k:51,_right:call,_signcp:1,ref:stock, s0:50, curr:null, desc:null, q:0, tkr:null, vol:0.3,'
        >>> print(optionseries(ref=stock(s0=50, vol=0.3, tkr='ibm', curr='usd'), k=51, right='call').full_spec(true))
            optionseries
            k: 51
            _right: call
            _signcp: 1
            ref: stock
              s0: 50
              curr: usd
              desc: null
              q: 0
              tkr: ibm
              vol: 0.3

        .. seealso::
            docs.python.org/3.4/library/pprint.html
            stackoverflow.com/questions/3229419/pretty-printing-nested-dictionaries-in-python
            dpinte.wordpress.com/2008/10/31/pyaml-dump-option
            alternative serialization(formatting): pprint, pickle
        """
        _ = self

        from yaml import dump

        s = dump(_, default_flow_style=not new_line).replace('!!python/object:','').replace('!!python/tuple','')
        s = s.replace('__main__.','')
        if not new_line:  s = s.replace(',',', ').replace('\n', ',').replace(': ', ':').replace('  ',' ')
        return s

    def __repr__(self):
        """ called by the repr() built-in function to compute the “official” string representation of an object.

        :return: full list of object properties
        :rtype: str

        .. seealso::
            http://stackoverflow.com/questions/1436703/difference-between-str-and-repr-in-python
            https://docs.python.org/2/reference/datamodel.html#object.__repr__
            http://stackoverflow.com/questions/1984162/purpose-of-pythons-repr

        :exmaple:

        >>> o = optionseries(ref=stock(s0=50,vol=.03))
        >>> repr(o)
        >>> o   # equivalent to print(repr(o))

        """
        return self.full_spec(new_line=true)

    def __str__(self):
        """ called by str(object) and the built-in functions format() and print()
        to compute the “informal” or nicely printable string representation of an object.

        :return: full list of object properties
        :rtype: str

        :example:

        >>> o = optionseries(ref=stock(s0=50,vol=.03))
        >>> str(o)
        >>> print(str(o))

        """
        return self.full_spec(new_line=true)

    @property
    def style(self):
        """ retrieve option object name.

        :return: option style
        :rtype: str
        """
        return type(self).__name__

    @property
    def clone(self):  return self

    @clone.setter
    def clone(self, clone=none):
        """

        :param clone:
        :return:

        :example:

        >>> o = optionseries(); o.right='call'
        >>> optionseries(clone=o).right
        >>> optionseries(clone=optionseries().set_right('call')).right

        """
        # copy specs from supplied object
        if clone is not none:
            [setattr(self, v, getattr(clone, v)) for v in vars(clone)]

    def reset(self):
        """ delete calculated attributes.

        :return:
        :rtype:
        """
        # if not getattr(self, 'px_spec', none) is none: del self.px_spec
        self.px_spec = pricespec(px=none)
        return self


class optionvaluation(optionseries):
    """ adds interest rates and some methods shared by subclasses.

    the class inherits from a simpler class that describes an option.
    """
    def __init__(self, rf_r=none, frf_r=0, seed0=none, *args, **kwargs):
        """ constructor simply saves all identified arguments and passes others to the base (parent) class, optionseries.

        it also calculates net_r, the rate used in computing growth factor a (p.452) for options with dividends and foreign risk free rates.

        :param rf_r:  risk free rate. required, unless clone object supplies it (see optionseries constructor). number in (0,1) interval
        :type rf_r:   float
        :param frf_r: foreign risk free rate.
        :type frf_r: float
        :param seed0: none or positive integer to seed random number generator (rng).
        :type seed0: int, none
        :param args: arguments to be passed to base class constructor.
        :type args: see base class for types of its arguments
        :param kwargs: keyword arguments to be passed to base class constructor.
        :type kwargs: see base class for types of its arguments
        :return:   __init__() method always implicitly returns self, i.e. a reference to this object
        :rtype:    __main__.optionvaluation

        :example:

        >>> optionvaluation(ref=stock(s0=50), rf_r=.05, frf_r=.01)

        """
        self.rf_r, self.frf_r, self.seed0 = rf_r, frf_r, seed0
        super().__init__(*args, **kwargs)  # pass remaining arguments to base (parent) class
        self.reset()

    def lt_specs(self, nsteps=2):
        """ calculates a collection of specs/parameters needed for lattice tree pricing.

        parameters returned:
            dt: time interval between consequtive two time steps
            u: stock price up move factor
            d: stock price down move factor
            a: growth factor, p.452
            p: probability of up move over one time interval dt
            df_t: discount factor over full time interval dt, i.e. per life of an option
            df_dt: discount factor over one time interval dt, i.e. per step

        :param nsteps: number of steps in a tree, positive number. required.
        :type nsteps:  int
        :return:       lt specs
        :rtype:         dict

        :example:

        >>> optionvaluation(ref=stock(s0=42, vol=.2), right='call', k=40, t=.5, rf_r=.1).lt_specs(2)
        {'a': 1.0253151205244289,
         'd': 0.9048374180359595,
         'df_t': 0.951229424500714,
         'df_dt': 0.9753099120283326,
         'dt': 0.25,
         'p': 0.60138570166548,
         'u': 1.1051709180756477}
         >>> s = stock(s0=50, vol=.3)
         >>> optionvaluation(ref=s,right='put', k=52, t=2, rf_r=.05, desc={'hull p.288'}).lt_specs(3)
        {'a': 1.033895113513574,
         'd': 0.7827444773247475,
         'df_t': 0.9048374180359595,
         'df_dt': 0.9672161004820059,
         'dt': 0.6666666666666666,
         'p': 0.5075681589595774,
         'u': 1.2775561233185384}
        """
        assert isinstance(nsteps, int), 'nsteps must be an integer, >2'
        from math import exp, sqrt

        sp = {'dt': self.t / nsteps}
        sp['u'] = exp(self.ref.vol * sqrt(sp['dt']))
        sp['d'] = 1 / sp['u']
        sp['a'] = exp(self.net_r * sp['dt'])   # growth factor, p.452
        sp['p'] = (sp['a'] - sp['d']) / (sp['u'] - sp['d'])
        sp['df_t'] = exp(-self.rf_r * self.t)
        sp['df_dt'] = exp(-self.rf_r * sp['dt'])

        return sp

    def plot_px_convergence(self, nsteps_max=50, ax=none, vs=none):
        """ plots convergence of an option price for different nsteps values.

        if vs object is provided, its plot is added, i.e. call vs.plot_px_convergence(...) to add a plot of the benchmark option.
        this is helpful to compare the convergence of lt price for european vs american options.
        bsm price (a constant line) is also plotted.
        if ax is not provided, create a new ax, then continue.

        :param nsteps_max: sets the range of nsteps, so that the lt price can be computed for each time step.
            i.e. this is the maximum range of the x-axis on the resulting plot. pxlt is called with range(1, nsteps_max).
            required. positive integer.
        :type nsteps_max: int
        :param ax:  optional plot object on which to plot the data.
        :type ax:   matplotlib.axes._subplots.axessubplot
        :param vs:  another option object (i.e. subclass of optionvaluation such as european, american,...)
        :type vs:   object
        :return:    plot the price convergence.
        :rtype:     none

        .. seealso::
            http://stackoverflow.com/questions/510972/getting-the-class-name-of-an-instance-in-python

        :example:

        >>> from american import *; from european import *
        >>> s = stock(s0=50, vol=.3)
        >>> a = american(ref=s, right='put', k=52, t=2, rf_r=.05, desc={'$7.42840, hull p.288'})
        >>> e = european(clone=a)
        >>> a.plot_px_convergence(nsteps_max=50, vs=e)

        """
        import matplotlib.pyplot as plt
        from pandas import dataframe, series

        if ax is none: fig, ax = plt.subplots()
        if 'fig' in locals():
            def onresize(event):  plt.tight_layout()
            cid = fig.canvas.mpl_connect('resize_event', onresize)  # tighten layout on resize event

        lt_prices = [self.calc_lt(n).px_spec.px for n in range(1, nsteps_max + 1)]

        dataframe({'lt price for ' + self.specs: lt_prices,
                   'bs price for ' + self.specs: self.calc_bs().px_spec.px}) \
            .plot(ax=ax, grid=1, title='option price convergence with number of steps')

        if vs is not none: vs.plot_px_convergence(nsteps_max=nsteps_max, ax=ax)

        plt.tight_layout();         plt.show()

    def plot(self):
        """ plot multiple subplots

        .. seealso::

        :example:

        >>> from american import *; from european import *
        >>> s = stock(s0=50, vol=.3)
        >>> a = american(ref=s, right='put', k=52, t=2, rf_r=.05, desc={'$7.42840, hull p.288'})
        >>> a.plot()

        """
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        def onresize(event):  fig.tight_layout()
        cid = fig.canvas.mpl_connect('resize_event', onresize)  # tighten layout on resize event

        self.plot_px_convergence(nsteps_max=50, ax=ax)
        plt.tight_layout();         plt.show()

    @property
    def net_r(self):
        """
        :return: net value of interest rate used to price this option
        :rtype: float

        :example:

        >>> o = optionvaluation(rf_r=0.05); vars(o)
        >>> o.update(rf_r=0.04)
            optionvaluation
            frf_r: 0
            rf_r: 0.04
            seed0: null
        >>> o.update(ref=stock(q=0.01))
            optionvaluation
            frf_r: 0
            ref: stock
              s0: null
              curr: null
              desc: null
              q: 0.01
              tkr: null
              vol: null
            rf_r: 0.04
            seed0: null
        >>> o.net_r
            0.03

        """
        try: q = 0 if self.ref.q is none else self.ref.q
        except: q = 0

        frf_r = 0 if self.frf_r is none else self.frf_r
        rf_r = 0 if self.rf_r is none else self.rf_r

        return rf_r - q - frf_r   # calculate rfr net of yield and foreign rfr

