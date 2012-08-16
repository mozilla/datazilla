"""False discovery rate control."""

def rejector(p_values, q=0.1):
    """
    Implements the Benjamini-Hochberg method of false discovery rate control.

    Code by Joseph Kelly, Mozilla metrics.

    See http://en.wikipedia.org/wiki/False_discovery_rate

    Given a list of p-values (floats) for independent comparisons, and a q
    value (the upper bound on the false discovery rate; the expected proportion
    of false rejections of the null hypothesis), returns a dictionary with two
    keys: "status" is a list of boolean values the same length as the given
    list of p-values, where a ``True`` value represents rejection of the null
    hypothesis for that p-value and ``False`` represents acceptance of the null
    hypothesis, and "count" is the number of p-values for which the null
    hypothesis was rejected (these will always be the lowest "count" p-values).

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

    return {"status": output, "count": indicator}
