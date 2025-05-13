import numpy as np

# Polynomkoeffizienten, von höchstem bis niedrigstem Grad
coefficients = [
    -5.86175551e-17,  1.36598614e-14, -1.45243157e-12,  9.36020336e-11,
    -4.09892561e-09,  1.29656657e-07, -3.07267464e-06,  5.57166505e-05,
    -7.79153776e-04,  8.35464518e-03, -6.72998147e-02,  3.92710378e-01,
    -1.56939198e+00,  3.92309678e+00, -5.12901760e+00,  2.51227193e+00
]

# Cp-Funktion mit numpy.polyval
def cp_function(v_val):
    return np.polyval(coefficients, v_val)


print(np.polyval(coefficients, 23.87))