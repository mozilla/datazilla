from scipy.stats import t
from numpy import power
from math import sqrt
from numpy import mean, std


def welchs_ttest(x1, x2, alpha=None):
    """
    Execute one-sided Welch's t-test.

    Return a dictionary with keys ``p``, ``mean1``, ``mean2``, ``stddev1`` and
    ``stddev2``.

    If an ``alpha`` value is supplied, result dictionary will also contain a
    key ``h0_rejected`` which is ``True`` if the p value is less than alpha
    (null hypothesis rejected), otherwise ``False``.

    Null hypothesis is that means are equal or mean of x1 is less than mean of
    x2. Null hypothesis is rejected if mean of x1 is greater than mean of x2
    (i.e., a performance regression if the supplied data are performance test
    timings, presuming x1 is data for the current changeset and x2 is data for
    the parent changeset).

    Original code by Joseph Kelly, Mozilla metrics.

    For more on Welch's t-test, see:
    http://en.wikipedia.org/wiki/Student%27s_t-test#Unequal_sample_sizes.2C_unequal_variance

    """
    n1 = len(x1)
    n2 = len(x2)

    m1 = mean(x1)
    m2 = mean(x2)

    s1 = std(x1, ddof=1)
    s2 = std(x2, ddof=1)

    prob = welchs_ttest_internal(n1, s1, m1, n2, s2, m2)

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



def welchs_ttest_internal(n1, s1, m1, n2, s2, m2):
    """
    Execute one-sided Welch's t-test given pre-calculated means and stddevs.

    Accepts summary data (N, stddev, and mean) for two datasets and performs
    one-sided Welch's t-test, returning p-value.

    """
    v1             = power(s1, 2)
    v2             = power(s2, 2)
    vpooled        = v1/n1 + v2/n2
    spooled        = sqrt(vpooled)
    tt             = (m1-m2)/spooled
    df_numerator   = power(vpooled, 2)
    df_denominator = power(v1/n1, 2)/(n1-1) + power(v2/n2, 2)/(n2-1)
    df             = df_numerator / df_denominator

    t_distribution = t(df)
    return 1 - t_distribution.cdf(tt)
