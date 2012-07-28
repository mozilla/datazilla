from scipy.stats import t
from numpy import power
from math import sqrt
from numpy import mean, std


def fdr(p_values, q=0.1):
    """
    Implements the Benjamini-Hochberg method of false discovery rate control.

    Code by Joseph Kelly, Mozilla metrics.

    See http://en.wikipedia.org/wiki/False_discovery_rate

    Given a list of p-values (floats) for independent comparisons, and a q
    value (the upper bound on the false discovery rate; the expected proportion
    of false rejections of the null hypothesis), returns a list of boolean
    values the same length as the given list of p-values, where a ``True``
    value represents rejection of the null hypothesis for that p-value and
    ``False`` represents acceptance of the null hypothesis.

    """
    # setup useful vars
    N = len(p_values)
    index = range(0, N)
    pindex = zip(p_values, index)
    sortedp = sorted(pindex)

    # find cutoff for rejection
    cutoff = [(i+1)*q/N for i in index]
    indicator = 0
    for i in index:
        if(sortedp[i][0] < cutoff[i]):
            indicator = i + 1

    # reject/fail to reject
    status = [True]*indicator + [False]*(N-indicator)
    output = range(0,N)
    for i in index:
        output[sortedp[i][1]] = status[i]

    return output


def welchs_ttest(x1, x2, alpha=None):
    """
    Execute one-sided Welch's t-test.

    Return a dictionary with keys ``p``, ``mean1``, ``mean2``, ``stddev1`` and
    ``stddev2``.

    If an ``alpha`` value is supplied, result dictionary will also contain a
    key ``h0_rejected`` which is ``True`` if the p value is less than alpha
    (null hypothesis rejected), otherwise ``False``.

    Null hypothesis is that means are equal or mean of x2 is less than mean of
    x1. Null hypothesis is rejected if mean of x2 is greater than mean of x1
    (i.e., a performance regression if the supplied data are performance test
    timings).

    Code by Joseph Kelly, Mozilla metrics.

    For more on Welch's t-test, see:
    http://en.wikipedia.org/wiki/Student%27s_t-test#Unequal_sample_sizes.2C_unequal_variance


    """
    n1 = len(x1)
    n2 = len(x2)

    m1 = mean(x1)
    m2 = mean(x2)

    s1 = std(x1)
    s2 = std(x2)

    spooled        = sqrt( power(s1,2)/n1 + power(s2,2)/n2)
    tt             = (m1-m2)/spooled
    df_numerator   = power( power(s1,2)/n1 + power(s2,2)/n2 , 2 )
    df_denominator = power( power(s1,2)/n1 ,2)/(n1-1) + power( power(s2,2)/n2 ,2)/(n2-1)
    df             = df_numerator / df_denominator

    t_distribution = t(df)
    prob = 1 - t_distribution.cdf(tt)

    result = {
        "p": prob,
        "stddev1": s1,
        "stddev2": s2,
        "mean1": m1,
        "mean2": m2,
        }

    if alpha is not None:
        result["h0_rejected"] = prob < alpha

    return result
