def exp_smooth(new_n, new_s, new_m, old_n, old_s, old_m, a = 0.05):
    """
    This function takes in new and old smoothed values for mean, sd and
    sample size and returns an exponentially smoothed mean, sd and sample
    size.
    """
    smooth_n = a*new_n + (1-a)*old_n
    smooth_s = a*new_s + (1-a)*old_s
    smooth_m = a*new_m + (1-a)*old_m
    result = {
        "mean": smooth_m,
        "stddev": smooth_s,
        "n": smooth_n
        }
    return result
